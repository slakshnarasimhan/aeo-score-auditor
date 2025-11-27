FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies  
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Playwright is optional - install locally for JS-heavy sites
# See ENABLE_PLAYWRIGHT.md for instructions
# Default: HTTP fetcher (fast, works for most sites)

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
