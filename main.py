from fastapi import FastAPI
from api.routes import router

app = FastAPI(title="Conversational NCD Chatbot", version="1.1")
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
