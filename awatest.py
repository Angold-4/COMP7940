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
import os
import aiohttp

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

async def query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config = configparser.ConfigParser()
    config.read('config.ini')
    try:
        user_message = update.message.text
        logger.info(f"User {update.effective_user.id} said: {user_message}")
        # read the content of query.txt
        with open("template/query.txt", "r", encoding='utf-8') as file:
            query_message = file.read()
        # append the knowledge to the query
        with open("template/knowledge.txt", "r", encoding='utf-8') as file:
            knowledge_message = file.read()
        query_message += knowledge_message
        # append the user message to the query
        query_message += "\n The user asked about this person with the following message:\n"
        query_message += user_message
        reply_message = chatgpt.submit(query_message)
        await update.message.reply_text(reply_message)
        logger.info(f"Bot sent a ChatGPT response: {reply_message}")
    except Exception as e:
        logger.error(f"Failed to get response from OpenAI: {e}")
        await update.message.reply_text("Sorry, I can't respond right now. Please try again later.")
    
async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    file_name = document.file_name
    file_extension = os.path.splitext(file_name)[1].lower()

    # Check if the file extension is valid (.txt or .md)
    if file_extension not in ['.txt', '.md']:
        await update.message.reply_text("Sorry, only text files (.txt) and markdown files (.md) are supported.")
        return

    # Get the file
    file = await context.bot.get_file(document.file_id)
    print(f"File: {file}")

    print(f"Downloading file from {file.file_path}")

    # Define a path to save the file temporarily
    local_file_path = f"./{file_name}"

    # Use aiohttp to download the file
    async with aiohttp.ClientSession() as session:
        async with session.get(file.file_path) as resp:
            if resp.status == 200:
                with open(local_file_path, 'wb') as fd:
                    while True:
                        chunk = await resp.content.read(1024)
                        if not chunk:
                            break
                        fd.write(chunk)

    print(f"File downloaded to {local_file_path}")

    # Now that the file is downloaded, you can process it as before
    # Read the text from the file
    with open(local_file_path, 'r', encoding='utf-8') as file:
        text_content = file.read()

    # Process the text_content as needed...

    # Delete the downloaded file after reading its content
    os.remove(local_file_path)

    # Load encapsulation instructions
    with open('template/encapsulate.txt', 'r', encoding='utf-8') as file:
        encapsulate_instruction = file.read()

    # Combine instruction with text content
    full_message = encapsulate_instruction + "\n" + text_content
    
    encapsulated_summary = chatgpt.submit(full_message)
    
    # Append the encapsulated summary to knowledge.txt
    with open("template/knowledge.txt", "a", encoding='utf-8') as file:
        file.write(f"{encapsulated_summary}\n")
    
    await update.message.reply_text("Your document has been processed and the knowledge has been encapsulated.")


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
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, query))

    application.add_handler(MessageHandler(filters.Document.ALL, document_handler))

    # Run the bot until the user presses Ctrl-C
    # Checking for new updates from Telegram.
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
