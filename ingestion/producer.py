import json
import time
import requests
from kafka import KafkaProducer
import datetime
import praw
from dotenv import load_dotenv
import os

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
        docs.append({
            "text": a["title"] + " - " + a["description"],
            "location": location,
            "source": "news",
            "tags": [query],
            "timestamp": str(datetime.datetime.now().date())
        })
    return docs

def fetch_reddit_trends(subreddit_name="Austin"):
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent="SmartDemandSenseBot"
    )
    subreddit = reddit.subreddit(subreddit_name)
    docs = []
    for post in subreddit.hot(limit=5):
        docs.append({
            "text": post.title,
            "location": subreddit_name,
            "source": "reddit",
            "tags": ["reddit"],
            "timestamp": str(datetime.datetime.now().date())
        })
    return docs

def fetch_weather_alerts(city="Dallas"):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    res = requests.get(url).json()
    desc = res['weather'][0]['description']
    temp = res['main']['temp']
    text = f"Weather in {city} is {desc} with temperature {temp}°C"
    return [{
        "text": text,
        "location": city,
        "source": "weather",
        "tags": [desc],
        "timestamp": str(datetime.datetime.now().date())
    }]

def produce():
    all_docs = []

    for topic in DEMAND_TOPICS:
        for loc in CITIES:
            all_docs += fetch_news_articles(topic, loc)
            time.sleep(0.5) 

    # for loc in CITIES:
    #     all_docs += fetch_reddit_trends(loc)
    #     time.sleep(10)

    for city in CITIES:
        all_docs += fetch_weather_alerts(city)
        time.sleep(0.5)

    for doc in all_docs:
        producer.send("demandsense-data", doc)
        print(f"[Kafka] Sent: {doc['text'][:60]}...")
        time.sleep(1)

    print(f"Published {len(all_docs)} demand-related documents.")


if __name__ == "__main__":
    produce()
