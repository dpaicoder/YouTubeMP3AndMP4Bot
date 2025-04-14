async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "youtu" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link.")
        return

    try:
        await update.message.reply_text("📥 Downloading audio...")

        yt = YouTube(url)

        # Get best audio stream
        audio_stream = yt.streams.filter(only_audio=True).first()
        if not audio_stream:
            await update.message.reply_text("❌ No audio stream found.")
            return

        out_file = audio_stream.download(output_path=DOWNLOAD_DIR)

        # Ensure output is .mp3
        base, ext = os.path.splitext(out_file)
        mp3_path = base + ".mp3"
        os.rename(out_file, mp3_path)

        # Check file size (Telegram bots have a 50MB limit)
        file_size = os.path.getsize(mp3_path) / (1024 * 1024)  # in MB
        if file_size > 49:
            await update.message.reply_text("⚠️ The audio file is too large for Telegram (>50MB). Try a shorter video.")
            os.remove(mp3_path)
            return

        # Send audio
        with open(mp3_path, "rb") as audio_file:
            await update.message.reply_audio(audio_file, title=yt.title)

        os.remove(mp3_path)

    except Exception as e:
        print("❌ Error occurred:", e)
        await update.message.reply_text(f"⚠️ Error: {e}")
