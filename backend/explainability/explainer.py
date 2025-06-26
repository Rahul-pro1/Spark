def extract_reasons(context_docs):
    reasons = []
    for doc in context_docs[:3]:
        reasons.append({
            "source": doc.payload.get("source", "unknown"),
            "snippet": doc.payload.get("text", "")[:150]
        })
    return reasons
