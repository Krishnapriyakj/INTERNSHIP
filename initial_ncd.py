# Install dependencies if not already installed
# pip install langchain langchain-ollama ollama langchain-chroma chromadb

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma

# Initialize FastAPI
app = FastAPI(title="NCD Chatbot API", version="1.0")

# ChromaDB Path
CHROMA_DB_PATH = "chroma_db"

# Define the prompt template for RAG
PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

# Initialize LLM model
model = OllamaLLM(model="llama3.2")

# Function to set up ChromaDB for RAG retrieval
def get_embedding_function():
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings

def retrieve_relevant_info(query_text):
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embedding_function)

    # Retrieve relevant documents
    results = db.similarity_search_with_score(query_text, k=2)
    
    if not results:
        return "No relevant information found."

    # Extract context from retrieved documents
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    # Format the prompt with retrieved context
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    # Get response from LLM
    response_text = model.invoke(prompt)
    
    return response_text

# Request model for chatbot queries
class QueryRequest(BaseModel):
    question: str

@app.post("/chat/")
async def chat(query: QueryRequest):
    """Handles chatbot queries with RAG-based responses"""
    response = retrieve_relevant_info(query.question)
    return {"response": response}

# Request model for NCD assessment responses
class NCDResponse(BaseModel):
    age: int
    gender: str
    smoke: str
    diet_balance: int
    family_hypertension: str
    stress_level: int
    chest_pain: str
    breathing_difficulty: str

def analyze_risk(responses):
    risk_score = 0

    # Simple risk scoring system (Can be improved with medical logic)
    if responses.smoke.lower() == "yes":
        risk_score += 2
    if responses.family_hypertension.lower() == "yes":
        risk_score += 2
    if responses.stress_level >= 7:
        risk_score += 2
    if responses.chest_pain.lower() == "yes":
        risk_score += 3
    if responses.breathing_difficulty.lower() == "yes":
        risk_score += 3

    # Determine risk level
    if risk_score <= 3:
        return "Low risk. Maintain a healthy lifestyle!"
    elif risk_score <= 6:
        return "Moderate risk. Consider lifestyle changes and regular check-ups."
    else:
        return "High risk. Consult a doctor for further evaluation."

@app.post("/ncd-assessment/")
async def ncd_assessment(data: NCDResponse):
    """Handles the NCD Risk Assessment"""
    risk_result = analyze_risk(data)
    return {"risk_level": risk_result}

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server...")  # Debug print
    uvicorn.run("initial_ncd:app", host="127.0.0.1", port=8000)



