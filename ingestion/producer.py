import json, time, requests, datetime, os
import praw
from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()

GNEWS_API_KEY = os.getenv("GNEWS_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

producer = KafkaProducer(
    bootstrap_servers="kafka:29092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

DEMAND_TOPICS = ["heatwave", "festival", "fuel shortage", "concert", "public holiday"]
CITIES = ["Texas", "Austin", "Dallas"]

def fetch_news_articles(query, location):
    url = f"https://gnews.io/api/v4/search?q={query}%20{location}&lang=en&country=us&max=5&apikey={GNEWS_API_KEY}"
    res = requests.get(url)
    articles = res.json().get("articles", [])
    return [{
        "text": f"news_event: {query}, location: {location}, headline: {a['title']}, summary: {a['description']}",
        "location": location,
        "source": "news",
        "tags": [query],
        "timestamp": str(datetime.datetime.now().date())
    } for a in articles]

def fetch_reddit_trends(subreddit_name="Austin"):
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent="SmartDemandSense by u/your_username"
        )
        subreddit = reddit.subreddit(subreddit_name)
        return [{
            "text": f"reddit_trend: {post.title}, subreddit: {subreddit_name}",
            "location": subreddit_name,
            "source": "reddit",
            "tags": ["reddit"],
            "timestamp": str(datetime.datetime.now().date())
        } for post in subreddit.hot(limit=5)]
    except Exception:
        return []

def fetch_weather_alerts(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    res = requests.get(url).json()
    desc = res['weather'][0]['description']
    temp = res['main']['temp']
    return [{
        "text": f"weather_report: location: {city}, temperature: {temp}°C, condition: {desc}",
        "location": city,
        "source": "weather",
        "tags": [desc],
        "timestamp": str(datetime.datetime.now().date())
    }]

def produce():
    all_docs = []
    for loc in CITIES:
        for topic in DEMAND_TOPICS:
            all_docs += fetch_news_articles(topic, loc)
        all_docs += fetch_reddit_trends(loc)
        all_docs += fetch_weather_alerts(loc)

    for doc in all_docs:
        producer.send("demandsense-data", doc)
        print(f"[Kafka] Sent ({doc['source']}): {doc['text'][:80]}...")

    print(f"[✓] Published {len(all_docs)} documents to 'demandsense-data'.")
    producer.flush(timeout=10)
    producer.close()


if __name__ == "__main__":
    produce()
