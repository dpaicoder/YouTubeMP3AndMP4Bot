FROM python:3.10-slim

# Install ffmpeg
RUN apt update && apt install -y ffmpeg

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Run the bot
CMD ["python", "main.py"]
