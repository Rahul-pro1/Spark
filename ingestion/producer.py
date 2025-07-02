import json
import time
import requests
import datetime
import os
import pandas as pd
import praw
from kafka import KafkaProducer
from dotenv import load_dotenv
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.forecasting.generate_pos_data import generate_dataset

load_dotenv()

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

DEMAND_TOPICS = [
    "heatwave", "floods", "rainfall", "fuel shortage", "public holiday",
    "festival", "public transport strike", "food price hike", "concert", "sports event"
]

CITIES = ["Texas", "Austin", "Dallas"]

def fetch_news_articles(query, location="Texas"):
    url = f"https://gnews.io/api/v4/search?q={query}%20{location}&lang=en&country=us&max=5&apikey={GNEWS_API_KEY}"
    res = requests.get(url)
    articles = res.json().get("articles", [])
    docs = []
    for a in articles:
        text = f"news_event: {query}, location: {location}, headline: {a['title']}, summary: {a['description']}"
        docs.append({
            "text": text,
            "location": location,
            "source": "news",
            "tags": [query],
            "timestamp": str(datetime.datetime.now().date())
        })
    return docs

def fetch_reddit_trends(subreddit_name="Austin"):
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent="SmartDemandSense by u/your_username"
        )
        subreddit = reddit.subreddit(subreddit_name)
        docs = []
        for post in subreddit.hot(limit=5):
            text = f"reddit_trend: {post.title}, subreddit: {subreddit_name}"
            docs.append({
                "text": text,
                "location": subreddit_name,
                "source": "reddit",
                "tags": ["reddit"],
                "timestamp": str(datetime.datetime.now().date())
            })
        return docs
    except Exception as e:
        print(f"[Reddit Error] Skipping {subreddit_name} due to: {e}")
        return []

def fetch_weather_alerts(city="Dallas"):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    res = requests.get(url).json()
    desc = res['weather'][0]['description']
    temp = res['main']['temp']
    text = f"weather_report: location: {city}, temperature: {temp}°C, condition: {desc}"
    return [{
        "text": text,
        "location": city,
        "source": "weather",
        "tags": [desc],
        "timestamp": str(datetime.datetime.now().date())
    }]

def fetch_pos_data(csv_path="../backend/forecasting/pos_data/pos_data.csv"):
    df = pd.read_csv(csv_path)
    docs = []
    for _, row in df.iterrows():
        text = (
            f"sku_id: {row['sku_id']}, store_id: {row['store_id']}, units_sold: {row['units_sold']}, "
            f"date: {row['date']}, temperature: {row['temperature']}, social_mentions: {row['social_mentions']}, "
            f"news_mentions: {row['news_mentions']}"
        )
        docs.append({
            "text": text,
            "location": row["store_id"],
            "source": "pos_data",
            "tags": ["pos", row["sku_id"]],
            "timestamp": row["date"]
        })
    return docs

def produce():
    all_docs = []
    for topic in DEMAND_TOPICS:
        for loc in CITIES:
            all_docs += fetch_news_articles(topic, loc)
            time.sleep(0.5)

    for loc in CITIES:
        all_docs += fetch_reddit_trends(loc)
        time.sleep(5)

    for city in CITIES:
        all_docs += fetch_weather_alerts(city)
        time.sleep(0.5)

    all_docs += fetch_pos_data()

    for doc in all_docs:
        producer.send("demandsense-data", doc)
        print(f"[Kafka] Sent ({doc['source']}): {doc['text'][:80]}...")
        time.sleep(0.5)

    print(f"Published {len(all_docs)} documents.")

if __name__ == "__main__":
    produce()
