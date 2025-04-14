FROM python:3.10-slim

RUN apt-get update && apt-get install -y ffmpeg &&     pip install --no-cache-dir yt-dlp python-telegram-bot flask python-dotenv

WORKDIR /app
COPY . .

CMD ["python", "main.py"]