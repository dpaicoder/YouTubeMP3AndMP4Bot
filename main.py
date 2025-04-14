import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import asyncio
from urllib.parse import urlparse

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

def is_valid_youtube_url(url):
    try:
        parsed = urlparse(url)
        valid_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
        return any(domain in parsed.netloc for domain in valid_domains)
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "👋 Welcome to YouTube to MP3 Bot!\n\n"
        "Simply send me a YouTube video URL, and I'll convert it to MP3 for you.\n"
        "Supported formats:\n"
        "✅ https://youtube.com/...\n"
        "✅ https://youtu.be/...\n"
        "✅ https://m.youtube.com/..."
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🔍 How to use this bot:\n\n"
        "1. Send a YouTube video URL\n"
        "2. Wait for the bot to process your request\n"
        "3. Receive your MP3 file\n\n"
        "⚠️ Limitations:\n"
        "- Maximum video length: 15 minutes\n"
        "- Maximum file size: 50MB\n"
        "- Only single videos (no playlists)"
    )
    await update.message.reply_text(help_text)

async def convert_to_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    chat_id = update.message.chat_id
    status_message = None
    
    if not is_valid_youtube_url(url):
        await update.message.reply_text(
            "❌ Please send a valid YouTube URL.\n"
            "Example: https://youtu.be/xxxxx or https://youtube.com/watch?v=xxxxx"
        )
        return

    try:
        status_message = await update.message.reply_text("⏳ Processing your request...")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'downloads/{chat_id}/%(title)s.%(ext)s',
            'noplaylist': True,
            'quiet': False,
            'no_warnings': False
        }
        
        os.makedirs(f'downloads/{chat_id}', exist_ok=True)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await status_message.edit_text("🔍 Checking video...")
                info = ydl.extract_info(url, download=False)
                
                if info.get('duration', 0) > 900:  # 15 minutes
                    await status_message.edit_text("❌ Video is too long. Maximum duration is 15 minutes.")
                    return
                
                await status_message.edit_text("⬇️ Downloading and converting...")
                info = ydl.extract_info(url, download=True)
                video_title = info['title']
                mp3_file = f"downloads/{chat_id}/{video_title}.mp3"
                
                if os.path.exists(mp3_file):
                    file_size = os.path.getsize(mp3_file) / (1024 * 1024)  # MB
                    if file_size > 50:
                        await status_message.edit_text("❌ File size exceeds Telegram's 50MB limit.")
                        return
                    
                    await status_message.edit_text("📤 Uploading your MP3...")
                    with open(mp3_file, 'rb') as audio:
                        await update.message.reply_audio(
                            audio,
                            title=video_title,
                            performer="YouTube to MP3 Bot",
                            caption="🎵 Here's your MP3!"
                        )
                    await status_message.delete()
                else:
                    await status_message.edit_text("❌ Failed to create MP3 file.")
                    
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            if "private video" in error_msg:
                await status_message.edit_text("❌ This video is private")
            elif "not available in your country" in error_msg:
                await status_message.edit_text("❌ This video is not available in the current region")
            elif "video unavailable" in error_msg:
                await status_message.edit_text("❌ This video is unavailable or has been removed")
            else:
                await status_message.edit_text(f"❌ Download error: {str(e)[:100]}")
            logger.error(f"Download error: {str(e)}")

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if status_message:
            await status_message.edit_text(
                "❌ An error occurred. Please try again later."
            )
    finally:
        try:
            if os.path.exists(f'downloads/{chat_id}'):
                for file in os.listdir(f'downloads/{chat_id}'):
                    os.remove(os.path.join(f'downloads/{chat_id}', file))
                os.rmdir(f'downloads/{chat_id}')
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update:
        await update.message.reply_text(
            "❌ An unexpected error occurred. Please try again later."
        )

def main():
    try:
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_to_mp3))
        application.add_error_handler(error_handler)

        logger.info("Bot started")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")

if __name__ == "__main__":
    main()
