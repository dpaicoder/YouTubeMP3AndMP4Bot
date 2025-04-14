from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp
import os
import uuid
import sqlite3
from flask import Flask, render_template, request
from threading import Thread
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads/")
MAX_FREE_DOWNLOADS = 5
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

DB = "db.sqlite"

app = Flask(__name__)

# --- Database Setup ---
def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            url TEXT,
            file_type TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

init_db()

# --- Flask Web Dashboard ---
@app.route("/admin")
def dashboard():
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        stats = cur.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
        users = cur.execute("SELECT COUNT(DISTINCT user_id) FROM downloads").fetchone()[0]
        logs = cur.execute("SELECT user_id, username, url, file_type, date FROM downloads ORDER BY date DESC LIMIT 20").fetchall()
    return render_template("dashboard.html", stats=stats, users=users, logs=logs)

def run_flask():
    app.run(host="0.0.0.0", port=3000)

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎧 MP3", callback_data='audio'),
         InlineKeyboardButton("🎬 MP4", callback_data='video')],
        [InlineKeyboardButton("📜 History", callback_data='history')],
        [InlineKeyboardButton("ℹ️ About", callback_data='about')]
    ]
    await update.message.reply_text("👋 Welcome!
Send a YouTube link and choose format:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["format"] = query.data

    if query.data == "about":
        await query.edit_message_text("🎧 YouTube MP3/MP4 Bot
Free tool to download YouTube videos as audio or video.")
    elif query.data == "history":
        user_id = query.from_user.id
        with sqlite3.connect(DB) as conn:
            logs = conn.execute("SELECT url, file_type, date FROM downloads WHERE user_id=? ORDER BY date DESC LIMIT 5", (user_id,)).fetchall()
        msg = "\n".join([f"{x[1].upper()} - {x[0][:50]}..." for x in logs]) or "No history found."
        await query.edit_message_text(f"📜 Your Download History:\n{msg}")
    elif query.data in ["audio", "video"]:
        await query.edit_message_text("✅ Format selected. Now send the YouTube URL.")

def check_limit(user_id):
    today = datetime.now().date()
    with sqlite3.connect(DB) as conn:
        count = conn.execute("SELECT COUNT(*) FROM downloads WHERE user_id=? AND date >= ?", (user_id, today)).fetchone()[0]
    return count < MAX_FREE_DOWNLOADS

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "N/A"
    fmt = context.user_data.get("format", "audio")

    if not check_limit(user_id):
        await update.message.reply_text("🚫 Daily limit reached (5 downloads). Try again tomorrow.")
        return

    filename = str(uuid.uuid4())
    ext = "mp3" if fmt == "audio" else "mp4"
    out_path = f"{DOWNLOAD_DIR}{filename}.{ext}"

    ydl_opts = {
        'format': 'bestaudio/best' if fmt == "audio" else 'best',
        'outtmpl': f'{DOWNLOAD_DIR}{filename}.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}] if fmt == "audio" else [],
        'quiet': True
    }

    try:
        await update.message.reply_text("⏬ Downloading...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        await update.message.reply_text("✅ Sending file...")
        if fmt == "audio":
            await update.message.reply_audio(audio=open(out_path, 'rb'))
        else:
            await update.message.reply_video(video=open(out_path, 'rb'))
        os.remove(out_path)
        with sqlite3.connect(DB) as conn:
            conn.execute("INSERT INTO downloads (user_id, username, url, file_type) VALUES (?, ?, ?, ?)", (user_id, username, url, fmt))
            conn.commit()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CallbackQueryHandler(button))
    app_telegram.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download))
    app_telegram.run_polling()