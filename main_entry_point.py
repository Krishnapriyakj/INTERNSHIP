"""Main application entry point."""
from fastapi import FastAPI
import uvicorn

from api.routes import router

# Initialize FastAPI
app = FastAPI(title="Conversational NCD Chatbot", version="1.1")

# Include routers
app.include_router(router, tags=["chat"])

if __name__ == "__main__":
    print("Starting FastAPI server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)