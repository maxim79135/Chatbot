#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""choice group bot"""

import logging
from abc import ABC

from telegram import Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler, Updater)

# Enable logging
logging.basicConfig(
    #  filename='bot.log', filemode='w',
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

class ChoiceGroupConversation(CommonConversation):
    """Contain choice group conversation functions"""

    CHOICE_GROUP, CONFIRM_GROUP, TRY_AGAIN = range(3)
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

    def choice_group(self, update: Update, context: CallbackContext) -> int:
        text = update.message.text
        context.user_data['choice'] = text
        #  context.user_data['attempt_num'] =
        if text in group_list:  # TODO: add group_list
            update.message.reply_text(f'Твоя группа {text}?')
            return self.CONFIRM_GROUP
        update.message.reply_text('Похоже такой группы нет, попробуй еще раз')
        return self.CHOICE_GROUP

    def choice_group_entry(self, update: Update, _: CallbackContext) -> int:
        update.message.reply_text('Какая у тебя группа?')
        return self.CHOICE_GROUP

    def fallback(self, update: Update, context: CallbackContext) -> int:
        update.message.reply_text('done')
        context.user_data.clear()
        return ConversationHandler.END

def main() -> None:
    updater = Updater("1147885266:AAFNCRzr3aDZacN5CQ55EHNx7pK35RKdejw")

    dispatcher = updater.dispatcher

    cgc = ChoiceGroupConversation()
    choice_group_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('choice_group', cgc.choice_group_entry)],
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
    )
    dispatcher.add_handler(choice_group_conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
