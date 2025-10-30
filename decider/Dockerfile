FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for security
RUN adduser --disabled-password --gecos "" myuser && \
    chown -R myuser:myuser /app

# Copy application code
COPY . .

# Switch to non-root user
USER myuser

# Add user's local bin to PATH
ENV PATH="/home/myuser/.local/bin:$PATH"

# Cloud Run will set the PORT environment variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
