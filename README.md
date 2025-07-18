# Smart Demand-Sense
**Smart Demand-Sense** is an AI-powered, real-time demand forecasting and inventory planning system. It leverages LLMs and a RAG pipeline to extract demand signals from:

- News articles (via GNews)
- Reddit discussions (via PRAW)
- OpenWeather API
- POS transaction data

The system forecasts SKU-level demand using Prophet and suggests restocking actions. It also provides a LangChain based LLM with added context from a RAG pipeline to explain or summarize the forecast. It is built as a modular, containerized architecture using **FastAPI**, **Kafka**, **Qdrant**, and **Next.js**.

---

## Architecture

```plaintext
+-------------+       +----------------+       +-------------+
|             |       |                |       |             |
|  Frontend   +<----->+   FastAPI API  +<----->+  Prophet    |
|  (Next.js)  |       |   (backend)    |       |  Forecaster |
+-------------+       +--------+-------+       +-------------+
                                 |
                                 v
                        +--------+--------+
                        |                 |
                        |  Qdrant Vector  |
                        |     Store       |
                        +--------+--------+
                                 ^
                                 |
           +---------------------+---------------------+
           |                                           |
+----------+-----------+              +----------------+--------------+
|    Kafka Producer    |              |          Kafka Consumer       |
| (scrapes GNews, etc) |              |   (Vectorizes + inserts to DB)|
+----------------------+              +-------------------------------+

```

---

## Getting Started

### 1. Clone the Repo
```bash
git clone https://github.com/your-username/smart-demandsense.git
cd smart-demandsense
```

### 2. Create `.env` File in Root

```env
GNEWS_API_KEY=your_key
REDDIT_CLIENT_ID=your_id
REDDIT_SECRET=your_secret
OPENWEATHER_API_KEY=your_key
QDRANT_HOST=http://qdrant:6333
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
TOPIC_NAME=demand-signals
```

---

### 3. Build and Run All Services

```bash
docker compose up --build
```

### 4. Manually Trigger Scraper (Optional)

```bash
docker compose exec ingestion python ingestion/producer.py
```
---

## Features

- RAG-based vector search with Qdrant
- Demand forecasting using Facebook Prophet
- Real-time ingestion using Kafka
- LLM integration ready (for summarization/explanation)
- Modular, Docker-based setup

---

## Example Usage

### Forecast from pre-ingested data:
```
POST /forecast
{
  "sku_id": "COLA-2L-BTL",
  "days_ahead": 7
}
```

## Requirements (If Running Locally)

- Python 3.10+
- Docker & Docker Compose
- Qdrant, Kafka, Zookeeper
- GNews, Reddit, and OpenWeather API keys

---
