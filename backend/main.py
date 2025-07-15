from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import pandas as pd
import datetime
from embeddings.embedder import Embedder
from vector_store.client import create_collection, search
from llm.llm import generate_reasoning, extract_signals_with_llm
from forecasting.forecast import forecast_sku_demand
from explainability.explainer import extract_reasons
from dotenv import load_dotenv
from typing import Optional
from enum import Enum
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="kafka:29092",  
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class RequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMPLETED = "COMPLETED"

class RestockRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    store_id: str
    product_id: str
    requested_quantity: int = Field(..., gt=0)
    priority: Priority = Priority.MEDIUM
    reason: str = Field(..., min_length=1)
    status: RequestStatus = RequestStatus.PENDING
    requested_by: Optional[str] = None
    approved_by: Optional[str] = None
    approved_quantity: Optional[int] = Field(None, ge=0)
    estimated_delivery_date: Optional[datetime.datetime] = None
    actual_delivery_date: Optional[datetime.datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime.datetime] = Field(default_factory=datetime.datetime.utcnow)
    updated_at: Optional[datetime.datetime] = None

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    location: str = "Texas"
    sku_id: str = "SKU123"

collection = "smart_demand_docs"
create_collection(collection)
pos_df = pd.read_csv("forecasting/pos_data/pos_data.csv")

@app.post("/query")
def query_handler(payload: QueryRequest):
    query = f"sku_id: {payload.sku_id}, location: {payload.location}, forecast for demand tomorrow"
    embedder = Embedder()
    query_vector = embedder.get_embedding(query)
    since = (datetime.datetime.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    results = search(collection, query_vector, location=payload.location, since=since)
    signals = extract_signals_with_llm(results)
    predicted_demand, confidence = forecast_sku_demand(payload.sku_id, signals, pos_df)
    answer = generate_reasoning(payload.query, results)
    reasons = extract_reasons(results)
    return {
        "response": answer,
        "forecast": {
            "sku": payload.sku_id,
            "predicted_demand": predicted_demand,
            "confidence": confidence
        },
        "explanation": reasons,
        "signals": signals
    }

@app.post("/restock-request")
def create_restock_request(request: RestockRequest):
    producer.send("restock-requests", request.dict())
    return {"status": "success", "message": "Restock request published to Kafka"}