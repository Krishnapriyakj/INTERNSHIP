from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_chat_general_response():
    response = client.post("/chat/", json={"user_id": "123", "question": "What is NCD?"})
    assert response.status_code == 200
    assert "response" in response.json()

def test_chat_ncd_assessment_start():
    response = client.post("/chat/", json={"user_id": "123", "question": "Start NCD assessment"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert "Let's begin the assessment" in response.json()["response"]

def test_chat_ncd_assessment_progress():
    client.post("/chat/", json={"user_id": "123", "question": "Start NCD assessment"})
    response = client.post("/chat/", json={"user_id": "123", "question": "male"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert "Do you smoke?" in response.json()["response"]

def test_chat_ncd_assessment_invalid_response():
    client.post("/chat/", json={"user_id": "123", "question": "Start NCD assessment"})
    response = client.post("/chat/", json={"user_id": "123", "question": "unknown"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert "Please answer with one of the following" in response.json()["response"]

def test_chat_ncd_assessment_completion():
    client.post("/chat/", json={"user_id": "123", "question": "Start NCD assessment"})
    client.post("/chat/", json={"user_id": "123", "question": "male"})
    client.post("/chat/", json={"user_id": "123", "question": "yes"})  
    client.post("/chat/", json={"user_id": "123", "question": "6"})  
    client.post("/chat/", json={"user_id": "123", "question": "yes"})    
    client.post("/chat/", json={"user_id": "123", "question": "yes"}) 
    
    
    response = client.post("/chat/", json={"user_id": "123", "question": "4"})  # Last question answer

    
    print("Chatbot Response:", response.json()) 
    
    assert response.status_code == 200
    assert "Assessment complete" in response.json()["response"]


def test_chat_rag_service():
    response = client.post("/chat/", json={"user_id": "123", "question": "Tell me about diabetes"})
    assert response.status_code == 200
    assert "response" in response.json()
    assert len(response.json()["response"]) > 0
