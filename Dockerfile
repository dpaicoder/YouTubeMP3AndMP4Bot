FROM python:3.11-slim

WORKDIR /app

# Copy all files to the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable for bot token
ENV BOT_TOKEN="your-bot-token"

# Command to run the bot
CMD ["python", "main.py"]
