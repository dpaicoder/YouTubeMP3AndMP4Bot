import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp
import asyncio
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get token from environment variable
TOKEN = os.getenv("BOT_TOKEN")

def is_valid_youtube_url(url):
    """Validate if the URL is from YouTube"""
    try:
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in ['youtube.com', 'youtu.be'])
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    welcome_message = (
        "👋 Welcome to YouTube to MP3 Bot!\n\n"
        "Simply send me a YouTube video URL, and I'll convert it to MP3 for you.\n"
        "Example: https://www.youtube.com/watch?v=example"
    )
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    help_text = (
        "🔍 How to use this bot:\n\n"
        "1. Send a YouTube video URL\n"
        "2. Wait for the bot to process your request\n"
        "3. Receive your MP3 file\n\n"
        "⚠️ Note: Video size must be under 50MB due to Telegram limitations"
    )
    await update.message.reply_text(help_text)

async def convert_to_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Convert YouTube video to MP3"""
    url = update.message.text
    chat_id = update.message.chat_id
    
    if not is_valid_youtube_url(url):
        await update.message.reply_text(
            "❌ Please send a valid YouTube URL.\n"
            "Example: https://www.youtube.com/watch?v=example"
        )
        return

    try:
        # Send processing message
        status_message = await update.message.reply_text("⏳ Processing your request...")
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': f'downloads/{chat_id}/%(title)s.%(ext)s',
            'noplaylist': True,
        }
        
        # Create downloads directory if it doesn't exist
        os.makedirs(f'downloads/{chat_id}', exist_ok=True)
        
        # Download and convert
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first to check file size
            info = ydl.extract_info(url, download=False)
            
            # Check if duration is too long (15 minutes max)
            if info.get('duration', 0) > 900:  # 15 minutes in seconds
                await status_message.edit_text("❌ Video is too long. Please choose a video under 15 minutes.")
                return
            
            # Download the video
            info = ydl.extract_info(url, download=True)
            video_title = info['title']
            mp3_file = f"downloads/{chat_id}/{video_title}.mp3"
        
        # Check if file exists and size is within limits
        if os.path.exists(mp3_file):
            file_size = os.path.getsize(mp3_file) / (1024 * 1024)  # Convert to MB
            if file_size > 50:
                await status_message.edit_text("❌ File size too large for Telegram (max 50MB)")
                return
            
            # Send the MP3 file
            await status_message.edit_text("📤 Uploading your MP3...")
            with open(mp3_file, 'rb') as audio:
                await update.message.reply_audio(
                    audio,
                    title=video_title,
                    performer="YouTube to MP3 Bot",
                    caption="🎵 Here's your MP3!"
                )
        
        # Clean up
        if os.path.exists(mp3_file):
            os.remove(mp3_file)
        if os.path.exists(f'downloads/{chat_id}'):
            os.rmdir(f'downloads/{chat_id}')
        await status_message.delete()
        
    except Exception as e:
        logger.error(f"Error processing {url}: {str(e)}")
        error_message = (
            "❌ Sorry, an error occurred while processing your request.\n"
            "Please make sure:\n"
            "- The video is not private\n"
            "- The video is available in your country\n"
            "- The URL is correct"
        )
        await update.message.reply_text(error_message)
        if 'status_message' in locals():
            await status_message.delete()

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    if update:
        await update.message.reply_text(
            "❌ An unexpected error occurred. Please try again later."
        )

def main():
    """Start the bot"""
    try:
        # Create application
        application = Application.builder().token(TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert_to_mp3))
        
        # Add error handler
        application.add_error_handler(error_handler)

        # Run the bot
        logger.info("Bot started")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}")

if __name__ == "__main__":
    main()
