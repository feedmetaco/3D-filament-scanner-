FROM python:3.11-slim

# Install Tesseract OCR
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend ./backend
COPY requirements.txt .

# Copy and make start script executable
COPY backend/start.sh .
RUN chmod +x start.sh

# Use start script to properly expand PORT variable
CMD ["./start.sh"]
