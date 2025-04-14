import os
from pytube import YouTube
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from moviepy.editor import AudioFileClip

# Create a directory for downloads
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a YouTube video link and I’ll convert it to MP3!")

# Handle YouTube link and download MP3
async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    print(f"📩 Received: {url}")

    if "youtu" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    try:
        await update.message.reply_text("📥 Downloading audio...")

        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()

        if not audio_stream:
            await update.message.reply_text("❌ No audio stream found.")
            return

        out_file = audio_stream.download(output_path=DOWNLOAD_DIR)
        base, _ = os.path.splitext(out_file)
        mp3_path = base + ".mp3"

        # Convert to real MP3 format
        audio_clip = AudioFileClip(out_file)
        audio_clip.write_audiofile(mp3_path, codec='libmp3lame')
        audio_clip.close()
        os.remove(out_file)

        file_size = os.path.getsize(mp3_path) / (1024 * 1024)
        print(f"📦 File size: {file_size:.2f}MB")

        if file_size > 49:
            await update.message.reply_text("⚠️ Audio is too large (>50MB). Try a shorter video.")
            os.remove(mp3_path)
            return

        with open(mp3_path, "rb") as audio_file:
            await update.message.reply_audio(audio_file, title=yt.title)

        os.remove(mp3_path)

    except Exception as e:
        print("❌ Error:", e)
        await update.message.reply_text(f"⚠️ Error: {e}")

# Main entry point
if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN is missing!")
        exit()

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))

    print("✅ Bot is running...")
    app.run_polling()
