#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""choice group bot"""

import logging
from abc import ABC

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)

from parsers.schedule import StudentScheduleParser
from utils import DBManager
from functools import reduce

# Enable logging
logging.basicConfig(
    #  filename='bot.log', filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

DB_NAME = 'bot.db'

logger = logging.getLogger(__name__)


group_list = [
    'gr1',
    'gr2',
    'gr3',
    'gr4',
    'gr5'
]

class ChoiceGroupConversation():
    """Contain choice group conversation functions"""

    (
        ST_CHOICE_GROUP,
        ST_CONFIRM_GROUP,
        ST_TRY_AGAIN
    ) = map(chr, range(3))
    ST_END = ConversationHandler.END

    (
        CP_CONFIRM_GROUP_YES,
        CP_CONFIRM_GROUP_NO,
        CP_TRY_AGAIN_YES,
        CP_TRY_AGAIN_NO
    ) = map(chr, range(3, 7))

    def choice_group_entry(self, update: Update, _: CallbackContext) -> int:
        keyboard = [
            ['Расписание сегодня', 'Расписание завтра'],
            ['Расписание на конкретную дату', 'Ссылка на расписание'],
            ['Расписание преподавателя'],
            ['Показать мою группу', 'Изменить группу'],
            ['Помощь', 'Оставить обратную связь']
        ]
        available_bot_commands = [
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
        keyboard_func_list = reduce(lambda x, y: x+y, keyboard)
        bot_commands_dict = dict(zip(keyboard_func_list, available_bot_commands[1:]))
        print(bot_commands_dict)
        update.message.reply_text('fga',
                                  reply_markup=ReplyKeyboardMarkup(keyboard))
        return self.ST_CHOICE_GROUP

    def choice_group(self, update: Update, context: CallbackContext) -> int:
        group_name = ssp.proceed_group_name(update.message.text)
        logger.info(f'user input: {update.message.text}, finded group: {group_name}')
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
        logger.info(f'update user with id {user_tg_id} group to {context.user_data["group_name"]}')
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

    def cancel(self, update: Update, context: CallbackContext) -> int:
        if update.callback_query:
            send_message = update.callback_query.edit_message_text
        else:
            send_message = update.message.reply_text
        send_message('Отменено')
        context.user_data.clear()
        return self.ST_END


ssp = StudentScheduleParser()
db_manager = DBManager(DB_NAME)
updater = Updater("1147885266:AAFNCRzr3aDZacN5CQ55EHNx7pK35RKdejw")

dispatcher = updater.dispatcher

cgc = ChoiceGroupConversation()
choice_group_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('choice_group', cgc.choice_group_entry)],
    states={
        cgc.ST_CHOICE_GROUP: [
            MessageHandler(Filters.text, cgc.choice_group),
        ],
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
)
dispatcher.add_handler(choice_group_conv_handler)

updater.start_polling()
updater.idle()
