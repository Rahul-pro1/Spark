from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from embeddings.embedder import Embedder
from vector_store.client import create_collection, search
from llm.llm import generate_reasoning
from forecasting.forecast import forecast_sku_demand
from explainability.explainer import extract_reasons

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
    query = payload.query
    embedder = Embedder()
    query_vector = embedder.get_embedding(query)
    results = search(collection, query_vector, location=payload.location)

    answer = generate_reasoning(query, results)
    predicted_demand, confidence = forecast_sku_demand(payload.sku_id, results, pos_df)
    reasons = extract_reasons(results)

    return {
        "response": answer,
        "forecast": {
            "sku": payload.sku_id,
            "predicted_demand": predicted_demand,
            "confidence": confidence
        },
        "explanation": reasons
    }
