from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # or "microsoft/phi-2"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device=-1)

def generate_reasoning(query, context_docs):
    context = "\n".join([doc.payload['text'] for doc in context_docs])
    prompt = f"""Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"""
    output = generator(prompt, max_new_tokens=300, do_sample=True)[0]["generated_text"]
    return output.split("Answer:")[-1].strip()
