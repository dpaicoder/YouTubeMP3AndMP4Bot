import os
import subprocess
from pytube import YouTube
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Directory to save downloaded audio
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a YouTube link and I’ll convert it to MP3!")

# Handle YouTube link and convert to MP3
async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "youtu" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    try:
        await update.message.reply_text("📥 Downloading and converting audio...")

        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()

        out_file = audio_stream.download(output_path=DOWNLOAD_DIR)
        base, _ = os.path.splitext(out_file)
        mp3_path = base + ".mp3"

        # Convert to MP3 using ffmpeg
        subprocess.run([
            "ffmpeg", "-i", out_file, "-vn", "-ab", "192k", "-ar", "44100", "-y", mp3_path
        ])

        os.remove(out_file)

        file_size = os.path.getsize(mp3_path) / (1024 * 1024)
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

# Main
if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not found in environment.")
        exit()

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))

    print("✅ Bot is running...")
    app.run_polling()
