#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""get student schedule"""

import logging
from abc import ABC

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

from parsers.schedule import StudentScheduleParser, TeacherScheduleParser

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

    CHOICE_GROUP, CONFIRM_GROUP, TRY_AGAIN = range(3)
    END = ConversationHandler.END
    #  def __init__(self):
    #  self.CHOICE_GROUP, self.CONFIRM_GROUP, self.TRY_AGAIN = range(3)

    def try_again(self, update: Update, _: CallbackContext) -> int:
        answer = update.message.text
        if answer in self.yes_patterns:
            #  update.message.reply_text('')
            return self.CHOICE_GROUP
        update.message.reply_text('Окей, давай в другой раз')
        return ConversationHandler.END

    def confirm_group(self, update: Update, context: CallbackContext) -> int:
        answer = update.message.text
        if answer in self.yes_patterns:
            update.message.reply_text('Понял, принял')
            # save user group
            print(context.user_data['choice'])
            return ConversationHandler.END
        if answer in self.no_patterns:
            update.message.reply_text('Значит мы немного не поняли друг друга\nПопробуешь еще раз?')
            return self.TRY_AGAIN

        update.message.reply_text('А можно по конкретнее: да или нет?')
        return self.CONFIRM_GROUP

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
	    return self.END
        elif len(teacher_list) == 1:
            context.user_data['teacher'] = teacher_list[0]
            buttons = [
                [
                    InlineKeyboardButton(text='Да', callback_data=str(self.CONFIRM_TEACHER_YES)),
                    InlineKeyboardButton(text='Нет', callback_data=str(self.CONFIRM_TEACHER_NO))
                    InlineKeyboardButton(text='Отмена', callback_data=str(self.CONFIRM_TEACHER_CANCEL))
                ]
            ]
            keyboard = InlineKeyboardMarkup(buttons)
            update.message.reply_text(f'{teacher_list[0]["name"]}, {teacher_list[0]["dep"]}\nПравильно?',
                                      reply_markup=keyboard)
            return self.COMFIRM_TEACHER
            #  return self.END
        else:
	    return self.fallback(update, context)  # TODO: add teacher choice
"""
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
"""

    def choice_date(self, update: Update, _: CallbackContext) -> int:
	buttons = [
	    [
		InlineKeyboardButton(text='Сегодня', callback_data=str(self.DATE_TODAY)),
		InlineKeyboardButton(text='Завтра', callback_data=str(self.DATE_TOMORROW))
		InlineKeyboardButton(text='Ввести дату', callback_data=str(self.DATE_CHOICE))
	    ]
	]
	keyboard = InlineKeyboardMarkup(buttons)
	update.message.reply_text('На какой день расписание интересует?'
				  reply_markup=keyboard)
	return self.CHOICE_DATE
	
	
    def send_sch_today(self, update: Update, context: CallbackContext) -> int:
	context.user_data['date'] = datetime.today()
        return self.send_sch(update, context)

    def send_sch_tomorrow(self, update: Update, context: CallbackContext) -> int:
	context.user_data['date'] = datetime.today() + timedelta(days=1)
        return self.send_sch(update, context)

    def send_sch(self, update: Update, context: CallbackContext) -> int:
	try:
	    sch = tsp.get_schedule(context.user_data['teacher'], context.user_data['date'])
	    if sch:
		update.message.reply_text('\n'.join(sch))
	    else:
		update.message.reply_text(f'{context.user_data["date"].strftime("%d.%m.%y")} у {context.user_data["teacher"]["name"]} нет занятий')
	except ValueError:
		update.message.reply_text('Похоже на сайте ВятГУ не нашлось расписания для данного преподавателя')
	return self.END

    def input_date_enrty(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('Напиши дату в формате ДД.ММ.ГГ (например 23.03.21), или напиши /cancel для отмены.')
        return self.INPUT_DATE

    def input_date(self, update: Update, context: CallbackContext) -> int:
	if update.message.text == '/cancel':
	    return fallback(update, context)
	try:
	    date = datetime.strptime(update.message.text, '%d.%m.%y')
	    context.user_data['date'] = date
	    return self.send_sch(update, context)
	except ValueError:
	    update.message.reply_text('Непонимаю тебя, попробуй еще раз. Напоминаю формат даты ДД.ММ.ГГ (например 30.09.21), или напиши /cancel для отмены.')
	    return self.INPUT_DATE
	
    def sch_teacher_entry(self, update: Update, _: CallbackContext) -> int:
        update.message.reply_text('Напиши ФИО преподавателя в порядке Фамилия Имя Отчество')
        return self.CHOICE_TEACHER

    def fallback(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('done')
        context.user_data.clear()
        return self.END


tsp = TeacherScheduleParser()
updater = Updater("1147885266:AAFNCRzr3aDZacN5CQ55EHNx7pK35RKdejw")

dispatcher = updater.dispatcher

tsc = TeacherScheduleConversation()
choice_group_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('sch_teacher', tsc.sch_teacher_entry)],
    states={
	tsc.CHOICE_TEACHER: [
	    MessageHandler(Filters.text, tsc.choice_teacher),
	],
	tsc.CONFIRM_TEACHER: [
	    CallbackQueryHandler(tsc.choice_date, pattern='^' + str(tsc.CONFIRM_TEACHER_YES) + '$'),
	    CallbackQueryHandler(tsc.sch_teacher_entry, pattern='^' + str(tsc.CONFIRM_TEACHER_NO) + '$'),
	    CallbackQueryHandler(tsc.fallback, pattern='^' + str(tsc.CONFIRM_TEACHER_CANCEL) + '$'),
	],
	tsc.CHOICE_DATE: [
	    CallbackQueryHandler(tsc.send_sch_today, pattern='^' + str(tsc.DATE_TODAY) + '$'),
	    CallbackQueryHandler(tsc.send_sch_tomorrow, pattern='^' + str(tsc.DATE_TOMORROW) + '$'),
	    CallbackQueryHandler(tsc.input_date_entry, pattern='^' + str(tsc.DATE_CHOICE) + '$'),
	],
	tsc.INPUT_DATE: [
	    MessageHandler(Filters.text, tsc.input_date),
	],
    },
    fallbacks=[MessageHandler(Filters.regex('^Done$'), tsc.fallback)],
)
dispatcher.add_handler(choice_group_conv_handler)

updater.start_polling()
updater.idle()
