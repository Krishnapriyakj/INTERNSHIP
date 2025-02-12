# Install dependencies if not already installed
# pip install fastapi uvicorn langchain langchain-ollama ollama langchain-chroma chromadb

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging, time
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma

# Initialize FastAPI
app = FastAPI(title="NCD Chatbot API", version="1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Logging
logging.basicConfig(level=logging.INFO)

# ChromaDB Path
CHROMA_DB_PATH = "chroma_db"

# Initialize LLM model
model = OllamaLLM(model="llama3.2")

# Define the prompt template for RAG
PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

# Session tracking
session_timestamp = time.time()
TIMEOUT_DURATION = 60  # 1-minute timeout

def reset_session():
    global session_timestamp
    session_timestamp = time.time()

def check_session():
    global session_timestamp
    if time.time() - session_timestamp > TIMEOUT_DURATION:
        reset_session()
        return "Session expired. Restarting..."
    return None

@app.middleware("http")
async def timeout_middleware(request, call_next):
    session_expired = check_session()
    if session_expired:
        return {"response": session_expired}
    response = await call_next(request)
    reset_session()
    return response

def get_embedding_function():
    """Initialize embeddings for ChromaDB"""
    return OllamaEmbeddings(model="nomic-embed-text")

def retrieve_relevant_info(query_text):
    """Retrieve relevant documents and generate a response using RAG"""
    try:
        embedding_function = get_embedding_function()
        db = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embedding_function)
        results = db.similarity_search_with_score(query_text, k=2)
        if not results:
            return "No relevant information found."
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
        prompt = prompt_template.format(context=context_text, question=query_text)
        response_text = model.invoke(prompt)
        return response_text
    except Exception as e:
        logging.error(f"Error in RAG retrieval: {e}")
        return "An error occurred while retrieving information."

class QueryRequest(BaseModel):
    question: str

@app.post("/chat/")
async def chat(query: QueryRequest):
    """Handles chatbot queries with RAG-based responses"""
    response = retrieve_relevant_info(query.question)
    return {"response": response}

class NCDResponse(BaseModel):
    age: int
    gender: str
    smoke: str
    exposure: str
    tobacco_use: str
    alcohol_consumption: str
    diet_balance: int
    family_hypertension: str
    stress_level: int
    chest_pain: str
    breathing_difficulty: str
    change_voice: str
    blood_sputum: str
    swallowing_difficulty: str
    weight_loss: str
    nodule_mass: str
    skin_changes: str

def analyze_risk(responses: NCDResponse):
    """Analyze NCD risk based on responses"""
    risk_score = 0
    risk_factors = {
        'smoke': 2, 'exposure': 1, 'tobacco_use': 2, 'alcohol_consumption': 2,
        'family_hypertension': 2, 'stress_level': 2, 'chest_pain': 3,
        'breathing_difficulty': 3, 'change_voice': 1, 'blood_sputum': 4,
        'swallowing_difficulty': 3, 'weight_loss': 3, 'nodule_mass': 4, 'skin_changes': 2
    }
    
    for key, value in risk_factors.items():
        if getattr(responses, key, "no").lower() == "yes":
            risk_score += value
    
    if risk_score <= 5:
        return "Low risk. Maintain a healthy lifestyle!"
    elif risk_score <= 10:
        return "Moderate risk. Consider lifestyle changes and regular check-ups."
    else:
        return "High risk. Consult a doctor for further evaluation."

@app.post("/ncd-assessment/")
async def ncd_assessment(data: NCDResponse):
    """Handles the NCD Risk Assessment"""
    try:
        risk_result = analyze_risk(data)
        return {"risk_level": risk_result}
    except Exception as e:
        logging.error(f"Error in NCD assessment: {e}")
        raise HTTPException(status_code=500, detail="Error processing assessment")

@app.get("/health/")
async def health_check():
    """Health check endpoint to verify the API is running"""
    return {"status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)