from embeddings.embedder import Embedder
from vector_store.client import create_collection, search
from llm.llm import generate_reasoning

collection = "smart_demand_docs"
create_collection(collection)

query = "What is the expected demand for Gatorade in Texas this week?"
embedder = Embedder()
print("Embedding...")
query_vector = embedder.get_embedding(query)

print("Searching...")
results = search(collection, query_vector, location="Texas")

print("Search results...", results)

print("Reasoning...")
reasoning = generate_reasoning(query, results)
print("\n=== Forecast Reasoning ===")
print(reasoning)
