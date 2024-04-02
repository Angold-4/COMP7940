#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import requests

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import configparser


class HKBU_ChatGPT():
    def __init__(self, config_path='./config.ini'):
        # Assuming you meant config_path here, not config_
        if isinstance(config_path, str):
            self.config = configparser.ConfigParser()
            self.config.read(config_path)
        elif isinstance(config_path, configparser.ConfigParser):
            self.config = config_path

    def submit(self, message):
        conversation = [{"role": "user", "content": message}]
        url = (self.config['CHATGPT']['BASICURL'] +
            "/deployments/" + self.config['CHATGPT']['MODELNAME'] +
            "/chat/completions/?api-version=" +
            self.config['CHATGPT']['APIVERSION'])
        headers = {'Content-Type': 'application/json',
                   'api-key': self.config['CHATGPT']['ACCESS_TOKEN']}
        payload = {'messages': conversation}
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # This will raise an exception for 4xx/5xx errors
            data = response.json()
            return data['choices'][0]['message']['content']
        except requests.RequestException as e:
            return f"Error: {str(e)}"



# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"User {user.id} started the conversation.")
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    logger.info(f"User {update.effective_user.id} asked for help.")
    await update.message.reply_text("Help!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config = configparser.ConfigParser()
    config.read('config.ini')
    try:
        user_message = update.message.text
        logger.info(f"User {update.effective_user.id} said: {user_message}")
        reply_message = chatgpt.submit(user_message)
        await update.message.reply_text(reply_message)
        logger.info(f"Bot sent a ChatGPT response: {reply_message}")
    except Exception as e:
        logger.error(f"Failed to get response from OpenAI: {e}")
        await update.message.reply_text("Sorry, I can't respond right now. Please try again later.")


def main() -> None:
    global chatgpt
    config = configparser.ConfigParser()
    config.read('config.ini')
    chatgpt = HKBU_ChatGPT(config)
    TOKEN = config['TELEGRAM']['ACCESS_TOKEN']
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    # Checking for new updates from Telegram.
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
