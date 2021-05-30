#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""get teacher schedule"""

import logging
from abc import ABC
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)

from parsers.schedule import TeacherScheduleParser

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)


group_list = [
    'gr1',
    'gr2',
    'gr3',
    'gr4',
    'gr5'
]


class CommonConversation(ABC):
    """Common comversation class"""

    no_patterns = [
        'нет',
        'ytn',
        'yt',
        'неа',
        'не',
        #  'не{0,30}',  TODO: add regex
        'н',
        'не хочу',
        'no',
        'nope',
    ]

    yes_patterns = [
        'д',
        'да',
        'lf',
        #  'да{0,30}', TODO: add regex
        'ага',
        'угу',
        'хочу',
        'yes',
        'yeap',
        'yeap',
    ]

class TeacherScheduleConversation(CommonConversation):
    """Contain teacher schedule conversation functions"""

    # States
    ST_CHOICE_TEACHER, ST_CONFIRM_TEACHER, ST_CHOICE_DATE, ST_INPUT_DATE, ST_TRY_AGAIN = map(chr, range(5))
    ST_END = ConversationHandler.END

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
    ) = map(chr, range(5, 13))

    def choice_teacher(self, update: Update, context: CallbackContext) -> int:
        full_name = update.message.text
        teacher_list = tsp.find_teacher(full_name)
        if len(teacher_list) == 0:
            #  buttons = [
                #  [
                    #  InlineKeyboardButton(text='Да', callback_data=str(self.TRY_AGAIN_YES)),
                    #  InlineKeyboardButton(text='Нет', callback_data=str(self.TRY_AGAIN_NO))
                #  ]
            #  ]
            #  keyboard = InlineKeyboardMarkup(buttons)
            #  update.message.reply_text(f'Не могу никого найти с ФИО: {full_name}, попробуешь еще раз?',
                                      #  reply_markup=keyboard)
            #  return self.TRY_AGAIN

            update.message.reply_text(f'Не могу никого найти с ФИО: {full_name}, попробуй еще раз')
            return self.ST_END
        elif len(teacher_list) == 1:
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
            #  return self.END
        #  else:
        return self.fallback(update, context)  # TODO: add teacher choice
    '''
            context.user_data['teacher_list'] = teacher_list
            update.message.reply_text('Я нашел несколько совпадений. Выбери ')
            buttons = []
            tl_text = ''
            for index, teacher in enumerate(teacher_list):
                tl_text += f'{index}: {teacher["name"]}, {teacher["dep"]}\n'
                buttons.append([InlineKeyboardButton(text=str(index), callback_data=str(self.CHOICE_TEACHER_FROM_LIST))])
                #  buttons.append(InlineKeyboardButton(text=str(index), callback_data=str(NAME)),
            keyboard = InlineKeyboardMarkup(buttons)

            update.callback_query.answer()
            update.callback_query.edit_message_text(text=tl_text, reply_markup=keyboard)
    '''

    def choice_date(self, update: Update, _: CallbackContext) -> int:
        buttons = [
            [
                InlineKeyboardButton(text='Сегодня', callback_data=str(self.CP_DATE_TODAY)),
                InlineKeyboardButton(text='Завтра', callback_data=str(self.CP_DATE_TOMORROW)),
                InlineKeyboardButton(text='Ввести дату', callback_data=str(self.CP_DATE_CHOICE))
            ]
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        #  update.message.reply_text('На какой день расписание интересует?',
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
            logger.info(f'Update type in send_sch: {type(update)}')
            sch = tsp.get_schedule(context.user_data['teacher'], context.user_data['date'])
            if update.callback_query:
                send_message = update.callback_query.edit_message_text
            else:
                send_message = update.message.reply_text

            if sch:
                #  update.callback_query.answer()
                send_message('\n'.join(sch))
                #  update.message.reply_text('\n'.join(sch))
                #  update.callback_query.edit_message_text('\n'.join(sch))
            else:
                #  update.callback_query.answer()
                send_message(f'{context.user_data["date"].strftime("%d.%m.%y")} у {context.user_data["teacher"]["name"]} нет занятий')
                #  update.callback_query.edit_message_text(f'{context.user_data["date"].strftime("%d.%m.%y")} у {context.user_data["teacher"]["name"]} нет занятий')
                #  update.message.reply_text(f'{context.user_data["date"].strftime("%d.%m.%y")} у {context.user_data["teacher"]["name"]} нет занятий')
        except ValueError:
            send_message('Похоже на сайте ВятГУ не нашлось расписания для данного преподавателя')
            #  update.callback_query.edit_message_text('Похоже на сайте ВятГУ не нашлось расписания для данного преподавателя')
        return self.ST_END

    def input_date_entry(self, update: Update, _: CallbackContext) -> int:
        update.callback_query.edit_message_text('Напиши дату в формате ДД.ММ.ГГ (например 23.03.21), или напиши /cancel для отмены.')
        return self.ST_INPUT_DATE

    def input_date(self, update: Update, context: CallbackContext) -> int:
        if update.message.text == '/cancel':
            return self.fallback(update, context)
        try:
            date = datetime.strptime(update.message.text, '%d.%m.%y')
            logger.info(f'recive date {date.strftime("%d.%m.%y")}')
            context.user_data['date'] = date
            logger.info(f'Update type in input_date: {type(update)}')
            return self.send_sch(update, context)
        except ValueError:
            update.message.reply_text('Не понимаю тебя, попробуй еще раз. Напоминаю формат даты ДД.ММ.ГГ (например 30.09.21), или напиши /cancel для отмены.')
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

    def sch_teacher_entry(self, update: Update, _: CallbackContext) -> int:
        update.message.reply_text('Напиши ФИО преподавателя в порядке Фамилия Имя Отчество')
        return self.ST_CHOICE_TEACHER

    def cancel(self, update: Update, context: CallbackContext) -> int:
        update.callback_query.edit_message_text('Отменено')
        context.user_data.clear()
        return self.ST_END

    def fallback(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('done')
        context.user_data.clear()
        return self.ST_END


tsp = TeacherScheduleParser()
updater = Updater("1147885266:AAFNCRzr3aDZacN5CQ55EHNx7pK35RKdejw")

dispatcher = updater.dispatcher

tsc = TeacherScheduleConversation()
choice_group_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('sch_teacher', tsc.sch_teacher_entry)],
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
    },
    fallbacks=[MessageHandler(Filters.regex('^Done$'), tsc.fallback)],
)
dispatcher.add_handler(choice_group_conv_handler)

updater.start_polling()
updater.idle()
