#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Schedule telegram bot"""

import sqlite3
import logging
from abc import ABC
from choice_group_bot import ChoiceGroupConversation

from telegram import Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

# SETTINGS SECTION
TOKEN = '1147885266:AAFNCRzr3aDZacN5CQ55EHNx7pK35RKdejw'
DB_NAME = 'bot.db'

# func has same names: /start -> bot_start()
available_bot_commands = [
    '/start',
    '/sch',
    '/sch_tomorrow',
    '/sch_teacher',
    #  '/sch_auto',
    '/feedback',
    '/choice_group',
]

REPLY, CHOICE_GROUP, GIVE_FEEDBACK = map(chr, range(3))
# State definitions for second level conversation
#  SELECTING_LEVEL, SELECTING_GENDER = map(chr, range(4, 6))
# State definitions for descriptions conversation
#  SELECTING_FEATURE, TYPING = map(chr, range(6, 8))
# Meta states
#  STOPPING, SHOWING = map(chr, range(8, 10))
# Shortcut for ConversationHandler.END
END = ConversationHandler.END

group_list = [
    'gr1',
    'gr2',
    'gr3',
    'gr4',
    'gr5'
]


def bot_start(update: Update, context: CallbackContext):
    if False:
    #  if user exist:
        update.message.reply_text('Я тебя помню, если хочешь изменить свою группу скажи прямо.')
    else:
        update.message.reply_text('Привет, я чат-бот ВятГУ. Умею показывать расписание, отвечать на часто задаваемые вопросы, а также сохранять обратную связь.\nНапиши свой вопрос или воспользуйся кнопками на клавиатуре')
    return END


def make_desicion(update: Update, context: CallbackContext):
    message = update.message.text
    #  print(dir(update.message))
    print((update.message.from_user.id))
    if message in ['gr', 'гр']:
        update.message.reply_text('Скажи свою группу')
        return CHOICE_GROUP
    update.message.reply_text(update.message.text)
    return END
        # call choice_group conversation

    #  if message in available_bot_commands:
        #  return locals()['bot_'+message[1:]](update, context)
    # else:
    #     is_faq, faq_answer = faq_or_feedback(message) # True - faq; False - feedback
    #     if is_faq:
    #         if faq_answer in available_bot_commands:
    #             return locals()['bot_'+faq_answer[1:]](update, context)
    #         else:
    #             response = insert_data(faq_answer)
    #             update.message.reply_text(insert_data(faq_answer))
    #             return END


def save_feedback(update: Update, _: CallbackContext):
    print(update.message.text)
    return END

def reply(update: Update, _: CallbackContext):
    update.message.reply_text(update.message.text)
    return END

def stop(update: Update, _: CallbackContext):
    update.message.reply_text('Stopped')
    return END

def main() -> None:
    conn = sqlite3.connect(DB_NAME)

    updater = Updater(TOKEN)

    dispatcher = updater.dispatcher

    cgc = ChoiceGroupConversation()
    choice_group_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.text, cgc.choice_group)],
        states={
            cgc.CHOICE_GROUP: [
                MessageHandler(Filters.text, cgc.choice_group),
            ],
            cgc.CONFIRM_GROUP: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), cgc.confirm_group
                )
            ],
            cgc.TRY_AGAIN: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), cgc.try_again,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), cgc.fallback)],
        map_to_parent={
            END: END,
        }
    )

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.text, make_desicion)],
        states={
            #  FAQ: [CallbackQueryHandler(start, pattern='^' + str(END) + '$')],
            REPLY: [MessageHandler(Filters.text, reply)],
            CHOICE_GROUP: [choice_group_conv_handler],  # TODO: add map_parent
            GIVE_FEEDBACK: [MessageHandler(Filters.text, save_feedback)],
            #  GET_TODAY_SCHEDULE: selection_handlers,
            #  GET_TOMORROW_SCHEDULE: selection_handlers,
            #  GET_LINK_SCHEDULE: selection_handlers,
            #  GET_TEACHER_SCHEDULE: [get_teacher_schedule_conv_handler],
            #  GET_LINK_TEACHER_SCHEDULE: [get_link_teacher_schedule_conv_handler],
            #  STOPPING: [CommandHandler('start', start)],
        },
        fallbacks=[MessageHandler(Filters.text, stop)],
        #  fallbacks=[CommandHandler('stop', stop)],
    )

    dispatcher.add_handler(conv_handler)
    #  dispatcher.add_handler(MessageHandler(Filters.text, reply))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
