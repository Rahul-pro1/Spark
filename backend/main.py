from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from embeddings.embedder import Embedder
from vector_store.client import search
from llm.llm import generate_reasoning

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

@app.post("/query")
def query_handler(payload: QueryRequest):
    query = payload.query
    embedder = Embedder()
    query_vector = embedder.get_embedding(query)
    results = search("smart_demand_docs", query_vector, location="Texas")
    answer = generate_reasoning(query, results)
    return {"response": answer}
