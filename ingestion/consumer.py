from kafka import KafkaConsumer
import json
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import uuid
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.vector_store.client import create_collection

# collection = "smart_demand_docs"
# create_collection(collection)

consumer = KafkaConsumer(
    "demandsense-data",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda x: json.loads(x.decode("utf-8"))
)

qdrant = QdrantClient("localhost", port=6333)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

for msg in consumer:
    data = msg.value
    vector = embedder.encode(data["text"]).tolist()
    qdrant.upsert(
        collection_name="smart_demand_docs",
        points=[PointStruct(id=str(uuid.uuid4()), vector=vector, payload=data)]
    )
    print(f"Stored doc from {data['location']}")
