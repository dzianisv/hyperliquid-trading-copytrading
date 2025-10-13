FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .

# Create a requirements file without GUI dependencies
RUN grep -v "PyInstaller\|keyring" requirements.txt > requirements-bot.txt && \
    pip install --no-cache-dir -r requirements-bot.txt && \
    rm requirements-bot.txt

# Copy application code
COPY src/ ./src/
COPY bot_runner.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default to position bot
ENV BOT_TYPE=position

# Run the bot
CMD ["python", "bot_runner.py"]
