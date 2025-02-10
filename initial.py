#pip install fastapi uvicorn
import uvicorn
from fastapi import FastAPI

# Initialize FastAPI app
app = FastAPI(title="Chatbot Server", version="1.0")

# Root endpoint to check if the server is running
@app.get("/")
def root():
    return {"message": "FastAPI Server is Running!"}

# Greet endpoint
@app.get("/greet/{name}")
def greet(name: str):
    return {"message": f"Hello, {name}!"}

# Run the server
if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

