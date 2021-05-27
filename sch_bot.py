#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOICE_GROUP, CONFIRM_GROUP, TRY_AGAIN = range(3)

group_list = [
    'gr1',
    'gr2',
    'gr3',
    'gr4',
    'gr5'
]

no_patterns =[
    'нет',
    'неа',
    'не',
    'н',
    'не хочу',
    'no',
    'nope',
]

yes_patterns =[
    'д',
    'да{0,30}',
    'ага',
    'угу',
    'хочу',
    'yes',
    'yeap',
    'yeap',
]

"""
def start(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        "Hi! My name is Doctor Botter. I will hold a more complex conversation with you. "
        "Why don't you tell me something about yourself?",
        reply_markup=markup,
    )

    return CHOOSING


def regular_choice(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    context.user_data['choice'] = text
    update.message.reply_text(f'Your {text.lower()}? Yes, I would love to hear about that!')

    return TYPING_REPLY


def custom_choice(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        'Alright, please send me the category first, for example "Most impressive skill"'
    )

    return TYPING_CHOICE


def received_information(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text(
        "Neat! Just so you know, this is what you already told me:"
        f"{facts_to_str(user_data)} You can tell me more, or change your opinion"
        " on something.",
        reply_markup=markup,
    )

    return CHOOSING

def done(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text(
        f"I learned these facts about you: {facts_to_str(user_data)}Until next time!",
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END
"""

def try_again(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    if answer in yes_patterns:
        update.message.reply_text('Ok, try again')
        return CHOICE_GROUP
    return ConversationHandler.END


def confirm_group(update: Update, context: CallbackContext) -> int:
    answer = update.message.text
    if answer in yes_patterns:
        update.message.reply_text(f"I remember your group is {context.user_data['choice']}")
        # save user group
        return ConversationHandler.END
    elif answer in no_patterns:
        return TRY_AGAIN

    update.message.reply_text('I dont understand. Tell me yes or no')
    return CONFIRM_GROUP

def choice_group(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    context.user_data['choice'] = text
    #  context.user_data['attempt_num'] =
    if text in group_list:
        update.message.reply_text(f'Your group is {text}?')
        return CONFIRM_GROUP
    update.message.reply_text("I don't know")
    return CHOICE_GROUP

def choice_group_entry(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Tell me your group')
    return CHOICE_GROUP

def done(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('done')
    user_data.clear()
    return ConversationHandler.END

def main() -> None:
    """main"""
    # Create the Updater and pass it your bot's token.
    updater = Updater("1147885266:AAFNCRzr3aDZacN5CQ55EHNx7pK35RKdejw")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    choice_group_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('choice_group', choice_group_entry)],
        states={
            CHOICE_GROUP: [
                MessageHandler(Filters.text, choice_group),
            ],
            CONFIRM_GROUP: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), confirm_group
                )
            ],
            TRY_AGAIN: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), try_again,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
    )
    dispatcher.add_handler(choice_group_conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

