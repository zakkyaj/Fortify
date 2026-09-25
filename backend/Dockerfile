FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/

EXPOSE 8000

# Run with uvicorn; reload is off in production image
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
