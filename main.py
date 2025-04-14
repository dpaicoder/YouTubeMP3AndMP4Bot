import os
from pytube import YouTube
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Replace this with a folder inside the container
DOWNLOAD_DIR = "downloads"

# Create download directory if not exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a YouTube video link and I'll send you the MP3!")

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if not ("youtube.com" in url or "youtu.be" in url):
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    try:
        await update.message.reply_text("📥 Downloading audio, please wait...")

        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        out_file = audio_stream.download(output_path=DOWNLOAD_DIR)

        base, ext = os.path.splitext(out_file)
        mp3_file = base + '.mp3'
        os.rename(out_file, mp3_file)

        # Send audio back to user
        with open(mp3_file, 'rb') as audio:
            await update.message.reply_audio(audio, title=yt.title)

        # Clean up
        os.remove(mp3_file)

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("⚠️ Failed to download audio. Try again later.")

async def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not found in environment variables!")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_audio))

    print("✅ Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
