import os
import subprocess
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Directory to save downloaded audio
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a YouTube link, and I’ll convert it to MP3!")

# Handle YouTube link and convert to MP3
async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    # Check if the URL contains 'youtube.com' or 'youtu.be'
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    try:
        await update.message.reply_text("📥 Downloading and converting audio...")

        # Initialize yt-dlp downloader
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
        }

        # Download audio from YouTube
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)

        # Get the downloaded file path
        downloaded_file_path = os.path.join(DOWNLOAD_DIR, f"{info_dict['id']}.mp3")

        # Check if the file is too large
        file_size = os.path.getsize(downloaded_file_path) / (1024 * 1024)  # MB
        if file_size > 49:
            await update.message.reply_text("⚠️ Audio is too large (>50MB). Try a shorter video.")
            os.remove(downloaded_file_path)
            return

        with open(downloaded_file_path, "rb") as audio_file:
            await update.message.reply_audio(audio_file, title=info_dict.get('title'))

        os.remove(downloaded_file_path)

    except Exception as e:
        print("❌ Error:", e)
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

# Main function
if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN not found in environment.")
        exit()

    app = ApplicationBuilder().token(token).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))

    print("✅ Bot is running...")
    app.run_polling()
