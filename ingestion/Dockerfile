FROM smart-demand-base:latest

WORKDIR /app

COPY . /app

COPY ../backend /app/backend

RUN pip install --no-cache-dir -r /app/backend/requirements.txt

RUN pip install requests praw httpx

CMD ["python", "ingestion/consumer.py"]
