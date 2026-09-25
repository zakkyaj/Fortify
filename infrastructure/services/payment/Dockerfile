FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# /data is where the SQLite database lives (mounted as a volume)
RUN mkdir -p /data

EXPOSE 5002

CMD ["python", "app.py"]
