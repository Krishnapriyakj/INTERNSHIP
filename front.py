import streamlit as st
import requests

# FastAPI endpoint
API_URL = "http://127.0.0.1:8000/chat/"

st.title("Conversational NCD Chatbot")
st.write("Ask health-related questions or start an NCD risk assessment.")

# User input
user_id = st.text_input("User ID", "user123")
user_question = st.text_area("Your Question", "")

if st.button("Send Query"):
    if not user_question.strip():
        st.warning("Please enter a question.")
    else:
        # API request payload
        payload = {"user_id": user_id, "question": user_question}
        response = requests.post(API_URL, json=payload)
        
        if response.status_code == 200:
            bot_response = response.json().get("response", "No response received.")
            st.success(bot_response)
        else:
            st.error("Error communicating with the chatbot API.")
