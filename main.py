from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict

from ncd_assessment import QueryRequest  # Import the request model
from ncd_assessment import ncd_assessment

# Initialize FastAPI
app = FastAPI(title="Conversational NCD Chatbot", version="1.1")

@app.post("/chat/", summary="Chat with the AI for health queries and NCD assessment")
async def chat(query: QueryRequest) -> Dict[str, str]:
    """Handles chatbot queries and dynamically assesses NCD risk within the conversation."""
    return await ncd_assessment(query)  # Delegate to ncd_assessment function


if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)