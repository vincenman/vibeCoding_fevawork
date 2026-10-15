import os
from openai import AzureOpenAI
import fitz
from unidecode import unidecode
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

endpoint = "https://aigenius-lab.openai.azure.com/"
model_name = "gpt-4o-mini"
deployment = "gpt-4o-mini"

subscription_key = os.environ["AZURE_OPENAI_API_KEY"]
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

telegram_api_key =""


history = {}

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARN)
logger = logging.getLogger(__name__)

# Call ChatGPT using /chatgpt command
async def chatgpt(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Hello! I'm a chatbot based on GPT-3.5-turbo. Please type your message to start chatting.")

# Handle user messages
async def message_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    user_input = update.message.text

    if user_id not in history:
        history[user_id] = []

    messages = []

    for input_text, completion_text in history[user_id]:
        messages.append({"role": "user", "content": input_text})
        messages.append({"role": "assistant", "content": completion_text})

    messages.append({"role": "user", "content": user_input})

    completion = client.chat.completions.create(     
        messages=messages,
        max_tokens=4096,
        model=deployment
    )

    completion_text = completion.choices[0].message.content
    await update.message.reply_text(completion_text)

    history[user_id].append((user_input, completion_text))

def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main() -> None:
    
    application = Application.builder().token(telegram_api_key).build()

    application.add_handler(CommandHandler("chatgpt", chatgpt))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    application.add_error_handler(error_handler)
    
    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
