import sys
import os
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)

def test_chat_exit_assessment():
    # Start the NCD assessment
    start_response = client.post("/chat/", json={"user_id": "123", "question": "Start NCD assessment"})
    assert start_response.status_code == 200
    assert "Let's begin the assessment" in start_response.json()["response"]

    # Exit the assessment
    exit_response = client.post("/chat/", json={"user_id": "123", "question": "stop"})
    assert exit_response.status_code == 200
    assert "Assessment stopped" in exit_response.json()["response"]

    # Verify that the session is cleaned up by trying to continue the assessment
    continue_response = client.post("/chat/", json={"user_id": "123", "question": "male"})
    assert continue_response.status_code == 200
    assert "Let's begin the assessment" not in continue_response.json()["response"]  # Assessment should not continue