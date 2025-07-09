FROM python:3.10-slim

WORKDIR /app

COPY . /app
COPY ../backend /app/backend  

RUN pip install --no-cache-dir -r /app/backend/requirements.txt \
    && pip install kafka-python sentence-transformers praw requests pandas python-dotenv

CMD ["python", "ingestion/consumer.py"]
