#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""Schedule for student teachers"""

import logging
from datetime import datetime, timedelta
from functools import reduce

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          ConversationHandler, Filters,
                          MessageHandler, Updater)

from parsers.schedule import StudentScheduleParser, TeacherScheduleParser
from sentiment.core import get_sent
from desicion import faq_or_feedback
from postprocessor import insert_faq_data

from utils import DBManager

# Enable logging
logging.basicConfig(
    #  filename='bot.log', filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)
logger = logging.getLogger(__name__)

# ============= SETTINGS SECTION ==============
TOKEN = '1147885266:AAFNCRzr3aDZacN5CQ55EHNx7pK35RKdejw'
DB_NAME = 'bot.db'

# buttons order same as available bot commands
BOT_KEYBOARD = [
    ['Расписание сегодня', 'Расписание завтра'],
    ['Расписание на конкретную дату', 'Ссылка на расписание'],
    ['Расписание преподавателя'],
    ['Показать мою группу', 'Изменить группу'],
    ['Помощь', 'Оставить обратную связь']
]

# func has same names: /start -> bot_start()
BOT_COMMANDS = [
    '/start',
    '/sch_today',
    '/sch_tomorrow',
    '/sch_date',
    '/sch_link',
    '/sch_teacher',
    '/get_group',
    '/choice_group',
    '/help',
    #  '/sch_auto',
    '/feedback',
]

_keyboard_func_list = reduce(lambda x, y: x+y, BOT_KEYBOARD)
BOT_COMMANDS_DICT = dict(zip(_keyboard_func_list, BOT_COMMANDS[1:]))
# ============= End Settings ==============


class BaseConversation():
    """Contain base conversation functions"""

    ST_END = ConversationHandler.END
    ST_STOP = 'stop'

    @staticmethod
    def redirect(from_func: callable, to_func: callable) -> callable:
        def func(update: Update, context: CallbackContext) -> int:
            from_func(update, context)
            return to_func(update, context)
        return func

    def cancel(self, update: Update, context: CallbackContext) -> int:
        if update.callback_query:
            send_message = update.callback_query.edit_message_text
        else:
            send_message = update.message.reply_text
        send_message('Отменено')
        context.user_data.clear()
        return self.ST_END

    def fallback(self, _: Update, context: CallbackContext) -> int:
        logger.warning('%s fallback called', type(self))
        context.user_data.clear()
        return self.ST_END


class ChoiceGroupConversation(BaseConversation):
    """Contain choice group conversation functions"""

    (
        ST_CHOICE_GROUP,
        ST_CONFIRM_GROUP,
        ST_TRY_AGAIN
    ) = map(chr, range(3))

    (
        CP_CONFIRM_GROUP_YES,
        CP_CONFIRM_GROUP_NO,
        CP_TRY_AGAIN_YES,
        CP_TRY_AGAIN_NO
    ) = map(chr, range(3, 7))

    def choice_group_entry(self, update: Update, _: CallbackContext) -> int:
        update.message.reply_text('Какая у тебя группа?')
        return self.ST_CHOICE_GROUP

    def choice_group(self, update: Update, context: CallbackContext) -> int:
        if update.message.text == '/cancel':
            return self.cancel(update, context)
        group_name = ssp.proceed_group_name(update.message.text)
        logger.debug('user input: %s, finded group: %s', update.message.text, group_name)
        if group_name:
            context.user_data['group_name'] = group_name
            buttons = [
                [
                    InlineKeyboardButton(text='Да', callback_data=str(self.CP_CONFIRM_GROUP_YES)),
                    InlineKeyboardButton(text='Нет', callback_data=str(self.CP_CONFIRM_GROUP_NO)),
                ]
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            update.message.reply_text(f'Твоя группа {group_name}?',
                                      reply_markup=keyboard)
            return self.ST_CONFIRM_GROUP

        buttons = [
            [
                InlineKeyboardButton(text='Да', callback_data=str(self.CP_TRY_AGAIN_YES)),
                InlineKeyboardButton(text='Нет', callback_data=str(self.CP_TRY_AGAIN_NO)),
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.message.reply_text('Похоже такой группы нет, повторить попытку?',
                                  reply_markup=keyboard)
        return self.ST_TRY_AGAIN

    def save_group(self, update: Update, context: CallbackContext) -> int:
        user_tg_id = update.callback_query.from_user.id
        logger.info('update user with id %s group to %s', user_tg_id, context.user_data["group_name"])
        db_manager.update_user(user_tg_id, context.user_data['group_name'])
        update.callback_query.edit_message_text(f'Запомнил, {context.user_data["group_name"]}')
        return self.ST_END

    def try_again_entry(self, update: Update, _: CallbackContext) -> int:
        buttons = [
            [
                InlineKeyboardButton(text='Да', callback_data=str(self.CP_TRY_AGAIN_YES)),
                InlineKeyboardButton(text='Нет', callback_data=str(self.CP_TRY_AGAIN_NO)),
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.edit_message_text('Повторить попытку?',
                                                reply_markup=keyboard)
        return self.ST_TRY_AGAIN

    def try_again(self, update: Update, _: CallbackContext) -> int:
        update.callback_query.edit_message_text('Напиши свою группу')
        return self.ST_CHOICE_GROUP


class TeacherScheduleConversation(BaseConversation):
    """Contain teacher schedule conversation functions"""

    # States
    (
        ST_CHOICE_TEACHER,
        ST_CONFIRM_TEACHER,
        ST_CHOICE_DATE,
        ST_INPUT_DATE,
        ST_TRY_AGAIN,
        ST_CHOICE_TEACHER_FROM_LIST
    ) = map(chr, range(7, 13))

    # Callback patterns
    (
        CP_CONFIRM_TEACHER_YES,
        CP_CONFIRM_TEACHER_NO,
        CP_CONFIRM_TEACHER_CANCEL,
        CP_DATE_TODAY,
        CP_DATE_TOMORROW,
        CP_DATE_CHOICE,
        CP_TRY_AGAIN_YES,
        CP_TRY_AGAIN_NO,
    ) = map(chr, range(13, 21))

    def sch_teacher_entry(self, update: Update, _: CallbackContext) -> int:
        update.message.reply_text('Напиши ФИО преподавателя в порядке Фамилия Имя Отчество')
        return self.ST_CHOICE_TEACHER

    def choice_teacher(self, update: Update, context: CallbackContext) -> int:
        if update.message.text == '/cancel':
            return self.cancel(update, context)
        full_name = update.message.text
        teacher_list = tsp.find_teacher(full_name)
        logger.debug('Choice teacher: user input: %s, finded teacher: %s', full_name, teacher_list)
        if len(teacher_list) == 0:
            buttons = [
                [
                    InlineKeyboardButton(text='Да', callback_data=str(self.CP_TRY_AGAIN_YES)),
                    InlineKeyboardButton(text='Нет', callback_data=str(self.CP_TRY_AGAIN_NO)),
                ]
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            update.message.reply_text(f'Не могу никого найти с ФИО: {full_name}\nПовторить попытку?',
                                      reply_markup=keyboard)
            return self.ST_TRY_AGAIN
        if len(teacher_list) == 1:
            context.user_data['teacher'] = teacher_list[0]
            buttons = [
                [
                    InlineKeyboardButton(text='Да', callback_data=str(self.CP_CONFIRM_TEACHER_YES)),
                    InlineKeyboardButton(text='Нет', callback_data=str(self.CP_CONFIRM_TEACHER_NO)),
                    InlineKeyboardButton(text='Отмена', callback_data=str(self.CP_CONFIRM_TEACHER_CANCEL))
                ]
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            update.message.reply_text(f'{teacher_list[0]["name"]}\n{teacher_list[0]["dep"]}\nПравильно?',
                                      reply_markup=keyboard)
            return self.ST_CONFIRM_TEACHER

        context.user_data['teacher_list'] = teacher_list
        update.message.reply_text('Я нашел несколько совпадений. Выбери ')
        buttons = []
        tl_text = ''
        for index, teacher in enumerate(teacher_list):
            tl_text += f'{index}: {teacher["name"]}, {teacher["dep"]}\n'
            buttons.append([InlineKeyboardButton(text=str(index), callback_data=str(index))])
        keyboard = InlineKeyboardMarkup(buttons)

        #  update.callback_query.answer()
        update.message.reply_text(text=tl_text, reply_markup=keyboard)
        return self.ST_CHOICE_TEACHER_FROM_LIST

    def choice_date(self, update: Update, _: CallbackContext) -> int:
        buttons = [
            [
                InlineKeyboardButton(text='Сегодня', callback_data=str(self.CP_DATE_TODAY)),
                InlineKeyboardButton(text='Завтра', callback_data=str(self.CP_DATE_TOMORROW)),
                InlineKeyboardButton(text='Ввести дату', callback_data=str(self.CP_DATE_CHOICE))
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.edit_message_text(text='На какой день расписание интересует?',
                                                reply_markup=keyboard)
        return self.ST_CHOICE_DATE

    def send_sch_today(self, update: Update, context: CallbackContext) -> int:
        context.user_data['date'] = datetime.today()
        return self.send_sch(update, context)

    def send_sch_tomorrow(self, update: Update, context: CallbackContext) -> int:
        context.user_data['date'] = datetime.today() + timedelta(days=1)
        return self.send_sch(update, context)

    def send_sch(self, update: Update, context: CallbackContext) -> int:
        try:
            sch = tsp.get_schedule(context.user_data['teacher'], context.user_data['date'])
            if update.callback_query:
                send_message = update.callback_query.edit_message_text
            else:
                send_message = update.message.reply_text

            if sch:
                #  update.callback_query.answer()
                send_message('\n'.join(sch))
            else:
                #  update.callback_query.answer()
                send_message(f'{context.user_data["date"].strftime("%d.%m.%y")} у '
                             f'{context.user_data["teacher"]["name"]} нет занятий')
        except ValueError:
            send_message('Похоже на сайте ВятГУ не нашлось расписания для данного преподавателя')
        return self.ST_END

    def input_date_entry(self, update: Update, _: CallbackContext) -> int:
        update.callback_query.edit_message_text('Напиши дату в формате ДД.ММ.ГГ (например 23.03.21),\
                                                или напиши /cancel для отмены.')
        return self.ST_INPUT_DATE

    def input_date(self, update: Update, context: CallbackContext) -> int:
        if update.message.text == '/cancel':
            return self.fallback(update, context)
        try:
            date = datetime.strptime(update.message.text, '%d.%m.%y')
            logger.info('recive date %s', date.strftime("%d.%m.%y"))
            context.user_data['date'] = date
            return self.send_sch(update, context)
        except ValueError:
            update.message.reply_text('Не понимаю тебя, попробуй еще раз. Напоминаю формат даты ДД.ММ.ГГ\
                                      (например 30.09.21), или напиши /cancel для отмены.')
            return self.ST_INPUT_DATE

    def try_again_entry(self, update: Update, _: CallbackContext) -> int:
        buttons = [
            [
                InlineKeyboardButton(text='Да', callback_data=str(self.CP_TRY_AGAIN_YES)),
                InlineKeyboardButton(text='Нет', callback_data=str(self.CP_TRY_AGAIN_NO)),
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        update.callback_query.edit_message_text('Повторить попытку?',
                                                reply_markup=keyboard)
        return self.ST_TRY_AGAIN

    def try_again(self, update: Update, _: CallbackContext) -> int:
        update.callback_query.edit_message_text('Напиши ФИО преподавателя в порядке Фамилия Имя Отчество')
        return self.ST_CHOICE_TEACHER

    def choice_teacher_from_list(self, update: Update, context: CallbackContext) -> int:
        teacher_index = int(update.callback_query.data)
        logger.info('teacher index: %s', teacher_index)

        context.user_data['teacher'] = context.user_data['teacher_list'][teacher_index]

        return self.choice_date(update, context)


class FeedbackConversation(BaseConversation):
    """Contain feedback conversation functions"""

    # States
    (
        ST_RECIVE_FEEDBACK,
    ) = map(chr, range(21, 22))

    def feedback_entry(self, update: Update, _: CallbackContext) -> int:
        update.message.reply_text('Напиши то что думаешь')
        #  reply_markup=ReplyKeyboardRemove())
        return self.ST_RECIVE_FEEDBACK

    def save_feedback(self, update: Update, context: CallbackContext) -> int:
        if update.message.text == '/cancel':
            return self.cancel(update, context)
        user_tg_id = update.message.from_user.id
        feedback = update.message.text
        sent = get_sent(feedback)
        db_manager.save_feedback(user_tg_id, feedback, sent)
        if sent == 'positive':
            update.message.reply_text('Спасибо, будем стараться дальше)')
        elif sent == 'negative':
            update.message.reply_text('Спасибо за обратную связь. Я передам эту информацию компетентным людям.')
        update.message.reply_text('Спасибо за обратную связь.')
        return self.ST_END


class StudentScheduleConversation(BaseConversation):
    """Contain feedback conversation functions"""

    # States
    (
        ST_CHOICE_GROUP,
        ST_INPUT_DATE,
        ST_SEND_SCH,
    ) = map(chr, range(22, 25))

    def sch_today(self, update: Update, context: CallbackContext) -> int:
        context.user_data['link'] = False
        context.user_data['date'] = datetime.today()
        return self.send_sch(update, context)

    def sch_tomorrow(self, update: Update, context: CallbackContext) -> int:
        context.user_data['link'] = False
        context.user_data['date'] = datetime.today() + timedelta(days=1)
        return self.send_sch(update, context)

    def sch_date(self, update: Update, context: CallbackContext) -> int:
        context.user_data['link'] = False
        update.message.reply_text('Напиши дату в формате ДД.ММ.ГГ (например 23.03.21),\
                                                или напиши /cancel для отмены.')
        return self.ST_INPUT_DATE

    def input_date(self, update: Update, context: CallbackContext) -> int:
        if update.message.text == '/cancel':
            return self.cancel(update, context)
        try:
            date = datetime.strptime(update.message.text, '%d.%m.%y')
            logger.info('recive date %s', date.strftime("%d.%m.%y"))
            context.user_data['date'] = date
            return self.send_sch(update, context)
        except ValueError:
            update.message.reply_text('Не понимаю тебя, попробуй еще раз. Напоминаю формат даты ДД.ММ.ГГ\
                                      (например 30.09.21), или напиши /cancel для отмены.')
            return self.ST_INPUT_DATE

    def sch_link(self, update: Update, context: CallbackContext) -> int:
        context.user_data['link'] = True
        return self.send_sch(update, context)

    def send_sch(self, update: Update, context: CallbackContext) -> int:
        if update.callback_query:
            user_tg_id = update.callback_query.from_user.id
            send_message = update.callback_query.edit_message_text
        else:
            user_tg_id = update.message.from_user.id
            send_message = update.message.reply_text

        group_name = db_manager.get_user_group(user_tg_id)
        if group_name:
            try:
                if context.user_data.get('link'):
                    sch = ssp.get_link(group_name)
                    if sch:
                        send_message(sch)
                    else:
                        send_message('Похоже на сайте нет расписания на текущую неделю')
                else:
                    sch = ssp.get_schedule(group_name, context.user_data['date'])
                    if sch:
                        if isinstance(sch, list):  # text schedule
                            update.message.reply_text('\n'.join(sch))
                        else:
                            context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(sch, 'rb'))
                    else:
                        send_message('В этот день нет занятий')

            except ValueError:
                send_message('Похоже твоей группы уже нет, выбери свою группу /choice_group')
            return self.ST_END

        send_message('Я не знаю твою группу, подскажешь?')
        return self.ST_CHOICE_GROUP


ssc = StudentScheduleConversation()
cgc = ChoiceGroupConversation()
tsc = TeacherScheduleConversation()
fc = FeedbackConversation()


ST_CHOICE_GROUP = chr(44)
ST_GET_GROUP = chr(45)
ST_FEEDBACK = fc.ST_RECIVE_FEEDBACK
#  ST_FEEDBACK = chr(46)
ST_SCH_TEACHER = chr(47)
ST_SCH = chr(48)
ST_END = ConversationHandler.END

def bot_start(update: Update, _: CallbackContext):
    if db_manager.user_exist(update.message.from_user.id):
        update.message.reply_text('''Мы уже знакомы, но я напомню. Я чат-бот ВятГУ. Умею показывать расписание,
                                  отвечать на часто задаваемые вопросы, 
                                  а также сохранять обратную связь.
                                  \nНапиши свой вопрос или воспользуйся кнопками на клавиатуре''',
                                  reply_markup=ReplyKeyboardMarkup(BOT_KEYBOARD))
        #  update.message.reply_text('Я тебя помню, но если ты просто хочешь\
                                  #  изменить свою группу скажи прямо.',
                                  #  reply_markup=ReplyKeyboardMarkup(BOT_KEYBOARD))
    else:
        db_manager.insert_user(update.message.from_user.id)
        update.message.reply_text('Привет, я чат-бот ВятГУ. Умею показывать расписание,\
                                  отвечать на часто задаваемые вопросы, \
                                  а также сохранять обратную связь.\
                                  \nНапиши свой вопрос или воспользуйся кнопками на клавиатуре',
                                  reply_markup=ReplyKeyboardMarkup(BOT_KEYBOARD))

# for student schedule use dump code, don't blame me. I am dump too
def bot_sch_today(update: Update, context: CallbackContext):
    return ssc.sch_today(update, context)

def bot_sch_tomorrow(update: Update, context: CallbackContext):
    return ssc.sch_tomorrow(update, context)

def bot_sch_date(update: Update, context: CallbackContext):
    return ssc.sch_date(update, context)

def bot_sch_link(update: Update, context: CallbackContext):
    return ssc.sch_link(update, context)

def bot_sch_teacher(update: Update, _: CallbackContext):
    update.message.reply_text('Напиши ФИО преподавателя в порядке Фамилия Имя Отчество')
    return ST_SCH_TEACHER

def bot_choice_group(update: Update, _: CallbackContext):
    update.message.reply_text('Какая у тебя группа?')
    return ST_CHOICE_GROUP

def bot_help(update: Update, _: CallbackContext):
    update.message.reply_text('это хепл,надо красиво оформить')
    return ST_END

def bot_feedback(update: Update, _: CallbackContext):
    update.message.reply_text('Напиши то что думаешь')
    #  reply_markup=ReplyKeyboardRemove())
    return ST_FEEDBACK

def bot_get_group(update: Update, _: CallbackContext):
    user_tg_id = update.message.from_user.id
    group_name = db_manager.get_user_group(user_tg_id)
    if group_name:
        update.message.reply_text(f'Твоя группа: {group_name}')
    else:
        update.message.reply_text('Похоже у тебя еще не выбрана группа')

def bot_stop(update: Update, _: CallbackContext):
    update.message.reply_text('bot stop called')
    return ST_END

def make_desicion(update: Update, context: CallbackContext):

    def command_not_implemented():
        # TODO: send mail to admin
        logger.critical('Not implemented!!! user message: %s, command: %s', message, command)
        update.message.reply_text('Похоже данная команда еще не реализована, но я уже сообщил своему созаделю об этом')
        return ST_END

    message = update.message.text
    command = BOT_COMMANDS_DICT.get(message)
    try:
        if message in BOT_COMMANDS:
            return globals()['bot_'+message[1:]](update, context)
        if command in BOT_COMMANDS:
            return globals()['bot_'+command[1:]](update, context)
    except KeyError:
        return command_not_implemented()

    is_faq, faq_answer = faq_or_feedback(message)  # True - faq; False - feedback
    if is_faq:
        if faq_answer in BOT_COMMANDS:
            try:
                return globals()['bot_'+command[1:]](update, context)
            except KeyError:
                return command_not_implemented()
        else:
            response = insert_faq_data(faq_answer)
            update.message.reply_text(response)
            return ST_END
    else:
        sent = get_sent(message)
        db_manager.save_feedback(update.message.from_user.id, message, sent)
        if sent == 'positive':
            update.message.reply_text('Спасибо, будем стараться дальше)')
        elif sent == 'negative':
            update.message.reply_text('Спасибо за обратную связь. Я передам эту информацию компетентным людям.')
        else:
            update.message.reply_text('Спасибо за обратную связь.')
        return ST_END


ssp = StudentScheduleParser()
tsp = TeacherScheduleParser()

db_manager = DBManager(DB_NAME)

updater = Updater(TOKEN)

dispatcher = updater.dispatcher

choice_group_conv_handler = ConversationHandler(
    #  entry_points=[CommandHandler('choice_group', cgc.choice_group_entry)],
    entry_points=[MessageHandler(Filters.text, cgc.choice_group)],
    states={
        cgc.ST_CHOICE_GROUP: [MessageHandler(Filters.text, cgc.choice_group)],
        #  ssc.ST_CHOICE_GROUP: [MessageHandler(Filters.text, cgc.choice_group)],
        cgc.ST_CONFIRM_GROUP: [
            CallbackQueryHandler(cgc.save_group, pattern='^' + str(cgc.CP_CONFIRM_GROUP_YES) + '$'),
            CallbackQueryHandler(cgc.try_again_entry, pattern='^' + str(cgc.CP_CONFIRM_GROUP_NO) + '$'),
        ],
        cgc.ST_TRY_AGAIN: [
            CallbackQueryHandler(cgc.try_again, pattern='^' + str(cgc.CP_TRY_AGAIN_YES) + '$'),
            CallbackQueryHandler(cgc.cancel, pattern='^' + str(cgc.CP_TRY_AGAIN_NO) + '$'),
        ],
    },
    fallbacks=[MessageHandler(Filters.text, cgc.cancel)],
    map_to_parent={
        cgc.ST_END: ST_END,
    }
)


sch_teacher_conv_handler = ConversationHandler(
    #  entry_points=[CommandHandler('sch_teacher', tsc.sch_teacher_entry)],
    entry_points=[MessageHandler(Filters.text, tsc.choice_teacher)],
    states={
        tsc.ST_CHOICE_TEACHER: [
            MessageHandler(Filters.text, tsc.choice_teacher),
        ],
        tsc.ST_CONFIRM_TEACHER: [
            CallbackQueryHandler(tsc.choice_date, pattern='^' + str(tsc.CP_CONFIRM_TEACHER_YES) + '$'),
            CallbackQueryHandler(tsc.try_again_entry, pattern='^' + str(tsc.CP_CONFIRM_TEACHER_NO) + '$'),
            CallbackQueryHandler(tsc.cancel, pattern='^' + str(tsc.CP_CONFIRM_TEACHER_CANCEL) + '$'),
        ],
        tsc.ST_CHOICE_DATE: [
            CallbackQueryHandler(tsc.send_sch_today, pattern='^' + str(tsc.CP_DATE_TODAY) + '$'),
            CallbackQueryHandler(tsc.send_sch_tomorrow, pattern='^' + str(tsc.CP_DATE_TOMORROW) + '$'),
            CallbackQueryHandler(tsc.input_date_entry, pattern='^' + str(tsc.CP_DATE_CHOICE) + '$'),
        ],
        tsc.ST_INPUT_DATE: [
            MessageHandler(Filters.text, tsc.input_date),
        ],
        tsc.ST_TRY_AGAIN: [
            CallbackQueryHandler(tsc.try_again, pattern='^' + str(tsc.CP_TRY_AGAIN_YES) + '$'),
            CallbackQueryHandler(tsc.cancel, pattern='^' + str(tsc.CP_TRY_AGAIN_NO) + '$'),
        ],
        tsc.ST_CHOICE_TEACHER_FROM_LIST: [
            CallbackQueryHandler(tsc.choice_teacher_from_list)
        ],
    },
    fallbacks=[MessageHandler(Filters.text, tsc.cancel)],
    map_to_parent={
        cgc.ST_END: ST_END,
    }
)


conv_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.text, make_desicion)],
    states={
        # START no need state
        #  SCH_TODAY:
        #  SCH_TOMORROW:
        #  SCH_DATE:
        #  SCH_LINK:
        ST_SCH_TEACHER: [sch_teacher_conv_handler],
        ST_GET_GROUP: [choice_group_conv_handler],
        ST_CHOICE_GROUP: [choice_group_conv_handler],
        # HELP no need state
        #  fc.ST_RECIVE_FEEDBACK: [MessageHandler(Filters.text, fc.save_feedback)],
        ST_FEEDBACK: [MessageHandler(Filters.text, fc.save_feedback)],

        ssc.ST_INPUT_DATE: [MessageHandler(Filters.text, ssc.input_date)],
        ssc.ST_CHOICE_GROUP: [MessageHandler(Filters.text, cgc.choice_group)],
        cgc.ST_CHOICE_GROUP: [MessageHandler(Filters.text, cgc.choice_group)],
        cgc.ST_CONFIRM_GROUP: [
            CallbackQueryHandler(BaseConversation.redirect(cgc.save_group, ssc.send_sch),
                                 pattern='^' + str(cgc.CP_CONFIRM_GROUP_YES) + '$'),
            CallbackQueryHandler(cgc.try_again_entry, pattern='^' + str(cgc.CP_CONFIRM_GROUP_NO) + '$'),
        ],
        cgc.ST_TRY_AGAIN: [
            CallbackQueryHandler(cgc.try_again, pattern='^' + str(cgc.CP_TRY_AGAIN_YES) + '$'),
            CallbackQueryHandler(cgc.cancel, pattern='^' + str(cgc.CP_TRY_AGAIN_NO) + '$'),
        ],
    },
    fallbacks=[MessageHandler(Filters.text, ssc.cancel)],
)

dispatcher.add_handler(conv_handler)

updater.start_polling()
updater.idle()
