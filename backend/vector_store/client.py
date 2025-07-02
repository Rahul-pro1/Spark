from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue, Range
)
import uuid
import datetime

client = QdrantClient(host="localhost", port=6333)

def create_collection(collection_name="smart_demand_docs", vector_size=384):
    if not client.collection_exists(collection_name):
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )

def insert_document(collection_name, vector, payload):
    if isinstance(payload.get("timestamp"), str):
        payload["timestamp"] = datetime.datetime.strptime(payload["timestamp"], "%Y-%m-%d").timestamp()
    elif isinstance(payload.get("timestamp"), datetime.datetime):
        payload["timestamp"] = payload["timestamp"].timestamp()

    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=vector,
        payload=payload
    )
    client.upsert(collection_name=collection_name, points=[point])

def search(collection_name, query_vector, location=None, since=None, limit=5):
    filters = []

    if location:
        filters.append(FieldCondition(key="location", match=MatchValue(value=location)))

    if since:
        if isinstance(since, str):
            since = datetime.datetime.strptime(since, "%Y-%m-%d").timestamp()
        filters.append(FieldCondition(key="timestamp", range=Range(gte=since)))
        
    return client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        query_filter=Filter(must=filters) if filters else None
    )
