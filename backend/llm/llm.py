import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.5-flash",
    google_api_key=os.environ["GOOGLE_API_KEY"],
    temperature=0.7,
    convert_system_message_to_human=True,
)

prompt = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are a demand forecasting assistant. Use the news, weather, sales data, and social media context below to answer the user's query.

Context:
{context}

Question:
{question}

Answer:
"""
)

chain = LLMChain(llm=llm, prompt=prompt)

def generate_reasoning(query, context_docs):
    context = "\n".join([
        f"[{doc.payload.get('source', '').upper()}] {doc.payload.get('text', '')}"
        for doc in context_docs
    ])
    response = chain.run({"context": context, "question": query})
    return response.strip()
