from kafka import KafkaConsumer
import json, os, uuid
import pandas as pd
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.vector_store.client import create_collection
from backend.forecasting.forecast import train_prophet_model
from backend.vector_store.client import wait_for_qdrant

wait_for_qdrant() 

collection = "smart_demand_docs"
create_collection(collection)
qdrant = QdrantClient("qdrant", port=6333)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

demandsense_consumer = KafkaConsumer(
    "demandsense-data",
    bootstrap_servers="kafka:29092",
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

sales_consumer = KafkaConsumer(
    "sales-events",
    bootstrap_servers="kafka:29092",
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

from threading import Thread
POS_CSV_PATH = os.path.join("backend", "forecasting", "pos_data", "pos_data.csv")
RETRAIN_THRESHOLD = 100
sales_tracker = {}

def handle_demandsense():
    for msg in demandsense_consumer:
        data = msg.value
        vector = embedder.encode(data["text"]).tolist()
        qdrant.upsert(
            collection_name=collection,
            points=[PointStruct(id=str(uuid.uuid4()), vector=vector, payload=data)]
        )
        print(f"[Qdrant] Stored doc from {data['location']}, source={data['source']}")

def handle_sales_events():
    global sales_tracker
    for msg in sales_consumer:
        event = msg.value
        store_id = event["store_id"]
        product_id = event["product_id"]
        quantity = event["quantity"]
        date = event.get("timestamp", datetime.utcnow().isoformat())[:10]

        if os.path.exists(POS_CSV_PATH):
            df = pd.read_csv(POS_CSV_PATH)
        else:
            df = pd.DataFrame(columns=[
                "store_id", "product_id", "date", "quantity",
                "temperature", "social_mentions", "news_mentions"
            ])

        row_idx = df[
            (df["store_id"] == store_id) &
            (df["product_id"] == product_id) &
            (df["date"] == date)
        ].index

        if len(row_idx) > 0:
            df.loc[row_idx, "quantity"] += quantity
        else:
            df = pd.concat([df, pd.DataFrame([{
                "store_id": store_id,
                "product_id": product_id,
                "date": date,
                "quantity": quantity,
                "temperature": 0,
                "social_mentions": 0,
                "news_mentions": 0
            }])], ignore_index=True)

        os.makedirs(os.path.dirname(POS_CSV_PATH), exist_ok=True)
        df.to_csv(POS_CSV_PATH, index=False)

        key = f"{store_id}-{product_id}"
        sales_tracker[key] = sales_tracker.get(key, 0) + quantity

        if sales_tracker[key] >= RETRAIN_THRESHOLD:
            print(f"[Retrain Trigger] Retraining Prophet for {product_id}")
            train_prophet_model(df, product_id)
            sales_tracker[key] = 0

if __name__ == "__main__":
    Thread(target=handle_demandsense, daemon=True).start()
    Thread(target=handle_sales_events, daemon=True).start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[Shutdown] Stopping consumers.")
