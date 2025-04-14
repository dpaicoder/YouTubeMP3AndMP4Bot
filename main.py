import os
from pytube import YouTube
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Create download directory
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a YouTube video link and I’ll convert it to MP3!")

# Function to handle YouTube links
async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "youtu" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    try:
        await update.message.reply_text("📥 Downloading audio...")

        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        out_file = audio_stream.download(output_path=DOWNLOAD_DIR)

        mp3_path = out_file.replace(".mp4", ".mp3")
        os.rename(out_file, mp3_path)

        with open(mp3_path, "rb") as audio_file:
            await update.message.reply_audio(audio_file, title=yt.title)

        os.remove(mp3_path)

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⚠️ Something went wrong. Try again later.")

# Create and run the bot
if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))

    print("✅ Bot is running...")
    app.run_polling()
