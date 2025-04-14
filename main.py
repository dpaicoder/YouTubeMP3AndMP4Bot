from telegram.ext import ApplicationBuilder, CommandHandler
import os

# Initialize the bot
async def start(update, context):
    await update.message.reply_text('Hello, I am your YouTube Downloader bot!')

# Main function to run the bot
async def main():
    bot_token = os.getenv("BOT_TOKEN")  # Make sure to set BOT_TOKEN in Railway settings
    app = ApplicationBuilder().token(bot_token).build()

    # Register the /start command handler
    start_handler = CommandHandler('start', start)
    app.add_handler(start_handler)

    # Run the bot
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
