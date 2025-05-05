import streamlit as st
import random
import time
from datetime import datetime, timedelta
import pandas as pd

# Set page configuration
st.set_page_config(
    page_title="eHealth Assistant",
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS to style the app
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stTextInput, .stButton, .stSelectbox {
        margin-bottom: 10px;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.8rem;
        margin-bottom: 0.5rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #e6f7ff;
        border: 1px solid #91d5ff;
    }
    .chat-message.bot {
        background-color: #f6ffed;
        border: 1px solid #b7eb8f;
    }
    .chat-container {
        height: 400px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #ddd;
        border-radius: 5px;
        margin-bottom: 10px;
        background-color: white;
    }
    .service-button {
        margin: 5px;
        padding: 10px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'registered' not in st.session_state:
    st.session_state.registered = False
if 'user_details' not in st.session_state:
    st.session_state.user_details = {}
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_service' not in st.session_state:
    st.session_state.current_service = None
if 'appointments' not in st.session_state:
    st.session_state.appointments = []

# Dummy data for hospitals and doctors
hospitals = {
    "General Hospital": ["Dr. Smith (Cardiology)", "Dr. Johnson (Neurology)", "Dr. Wilson (Orthopedics)"],
    "City Medical Center": ["Dr. Brown (Pediatrics)", "Dr. Davis (Dermatology)", "Dr. Miller (Psychiatry)"],
    "Community Health Hospital": ["Dr. Jones (Gynecology)", "Dr. Garcia (Internal Medicine)", "Dr. Taylor (Oncology)"]
}

# Function to add a message to the chat
def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

# Function for the initial welcome message after registration
def send_welcome_message():
    add_message("bot", "Hi, I'm your eHealth Assistant! I can help you with medical queries and other healthcare services.")
    time.sleep(0.5)
    add_message("bot", "What service would you like to use today?")

# Function to handle registration
def register_user():
    st.session_state.user_details = {
        "name": st.session_state.name,
        "age": st.session_state.age,
        "gender": st.session_state.gender,
        "email": st.session_state.email,
        "phone": st.session_state.phone,
        "medical_history": st.session_state.medical_history
    }
    st.session_state.registered = True
    send_welcome_message()

# Function to schedule an appointment
def schedule_appointment(hospital, doctor, date, time_slot):
    new_appointment = {
        "hospital": hospital,
        "doctor": doctor,
        "date": date,
        "time": time_slot,
        "status": "Confirmed"
    }
    st.session_state.appointments.append(new_appointment)
    return new_appointment

# NCD Assessment questions
ncd_questions = [
    "Do you smoke?",
    "Do you consume alcohol regularly?",
    "Do you exercise regularly?",
    "Do you have a family history of diabetes?",
    "Do you have a family history of heart disease?",
    "Have you been experiencing frequent headaches?",
    "Do you have high blood pressure?",
    "Have you been feeling unusually tired lately?"
]

# Cancer Assessment questions
cancer_questions = [
    "Have you noticed any unusual lumps or swelling?",
    "Have you experienced unexplained weight loss?",
    "Do you have a family history of cancer?",
    "Have you noticed any changes in your skin?",
    "Have you been experiencing persistent pain?",
    "Have you noticed any changes in bowel or bladder habits?",
    "Have you had any unusual bleeding or discharge?",
    "Do you have a persistent cough or hoarseness?"
]

# Medical conditions and their symptoms for the medical query feature
medical_conditions = {
    "Common Cold": ["Runny nose", "Cough", "Sore throat", "Mild fever", "Sneezing"],
    "Influenza": ["High fever", "Body aches", "Extreme fatigue", "Headache", "Dry cough"],
    "Migraine": ["Severe headache", "Nausea", "Sensitivity to light", "Vision changes"],
    "Allergies": ["Sneezing", "Itchy eyes", "Rash", "Nasal congestion", "Watery eyes"],
    "Gastroenteritis": ["Nausea", "Vomiting", "Diarrhea", "Stomach cramps", "Low fever"]
}

# Function to handle different bot services
def handle_service(service):
    st.session_state.current_service = service
    
    if service == "hospital_appointment":
        add_message("bot", "Let's schedule a hospital appointment for you.")
        add_message("bot", "Please select a hospital, doctor, date, and time for your appointment.")
    
    elif service == "ncd_assessment":
        add_message("bot", "I'll help you assess your risk for Non-Communicable Diseases.")
        add_message("bot", "I'll ask you a few questions about your health and lifestyle. Please answer yes or no.")
        st.session_state.assessment_index = 0
        add_message("bot", ncd_questions[0])
    
    elif service == "cancer_assessment":
        add_message("bot", "I'll help you assess potential cancer risk factors.")
        add_message("bot", "I'll ask you a few questions. Please answer yes or no to the best of your knowledge.")
        st.session_state.assessment_index = 0
        add_message("bot", cancer_questions[0])
    
    elif service == "medical_queries":
        add_message("bot", "I can help answer your medical questions.")
        add_message("bot", "Please describe your symptoms or ask a health-related question.")

# Handle user input for different services
def process_user_input(user_input):
    # Record user message
    add_message("user", user_input)
    
    # First message after welcome - determine which service
    if len(st.session_state.messages) == 3:  # After welcome messages
        if "appointment" in user_input.lower() or "hospital" in user_input.lower():
            handle_service("hospital_appointment")
        elif "ncd" in user_input.lower() or "non-communicable" in user_input.lower():
            handle_service("ncd_assessment")
        elif "cancer" in user_input.lower():
            handle_service("cancer_assessment")
        elif "question" in user_input.lower() or "query" in user_input.lower() or "medical" in user_input.lower():
            handle_service("medical_queries")
        else:
            add_message("bot", "I'm not sure which service you need. Please select one of the following:")
            add_message("bot", "• Hospital Appointment\n• NCD Assessment\n• Cancer Assessment\n• Medical Queries")
    
    # Process based on current service
    elif st.session_state.current_service == "hospital_appointment":
        if "appointment" in st.session_state.messages[-3].get("content", "").lower():
            # This is a response to the initial appointment prompt
            add_message("bot", "Great! Let me help you schedule an appointment.")
            
            # Get available appointment dates (next 7 days)
            today = datetime.now()
            available_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 8)]
            available_times = ["9:00 AM", "10:00 AM", "11:00 AM", "2:00 PM", "3:00 PM", "4:00 PM"]
            
            # Create dropdown selections for appointment booking
            st.session_state.show_appointment_form = True
        else:
            add_message("bot", "Your appointment has been scheduled. Is there anything else I can help you with?")
            st.session_state.current_service = None
    
    elif st.session_state.current_service == "ncd_assessment":
        if hasattr(st.session_state, 'assessment_index'):
            # Process answer to current question
            if st.session_state.assessment_index < len(ncd_questions) - 1:
                st.session_state.assessment_index += 1
                add_message("bot", ncd_questions[st.session_state.assessment_index])
            else:
                # Assessment complete
                risk_level = "moderate"  # This would normally be calculated based on answers
                add_message("bot", f"Thank you for completing the NCD risk assessment. Based on your answers, your risk level appears to be {risk_level}.")
                add_message("bot", "Would you like some personalized health recommendations?")
                st.session_state.show_recommendations = True
    
    elif st.session_state.current_service == "cancer_assessment":
        if hasattr(st.session_state, 'assessment_index'):
            # Process answer to current question
            if st.session_state.assessment_index < len(cancer_questions) - 1:
                st.session_state.assessment_index += 1
                add_message("bot", cancer_questions[st.session_state.assessment_index])
            else:
                # Assessment complete
                risk_factors = random.randint(0, 3)  # This would normally be calculated based on answers
                add_message("bot", f"Thank you for completing the cancer risk assessment. Based on your answers, we've identified {risk_factors} potential risk factors.")
                if risk_factors > 1:
                    add_message("bot", "It's recommended to consult with a healthcare provider for a more thorough evaluation.")
                else:
                    add_message("bot", "Your risk factors appear to be low. Continue with regular health check-ups.")
                st.session_state.current_service = None
    
    elif st.session_state.current_service == "medical_queries":
        # Simple symptom checker
        symptoms = [s.lower() for s in user_input.lower().split()]
        possible_conditions = []
        
        for condition, condition_symptoms in medical_conditions.items():
            for symptom in condition_symptoms:
                if any(s in symptom.lower() for s in symptoms):
                    possible_conditions.append(condition)
                    break
        
        if possible_conditions:
            response = f"Based on the symptoms you've described, you might be experiencing: {', '.join(possible_conditions)}."
            response += "\n\nPlease note that this is not a professional diagnosis. If symptoms persist, please consult a healthcare provider."
            add_message("bot", response)
        else:
            add_message("bot", "I'm not able to identify a specific condition based on that information. Could you provide more details about your symptoms? Alternatively, I recommend consulting with a healthcare provider.")

# Main app layout
def main():
    # Display header
    st.title("eHealth Assistant")
    
    # Registration form
    if not st.session_state.registered:
        st.subheader("Welcome to eHealth Assistant")
        st.markdown("Please register to use our services")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Full Name", key="name", placeholder="John Doe")
            st.number_input("Age", min_value=1, max_value=120, key="age", value=30)
            st.selectbox("Gender", ["Male", "Female", "Other"], key="gender")
        
        with col2:
            st.text_input("Email", key="email", placeholder="john.doe@example.com")
            st.text_input("Phone", key="phone", placeholder="555-123-4567")
            st.text_area("Brief Medical History (if any)", key="medical_history", placeholder="Any existing conditions, allergies, medications...")
        
        if st.button("Register", use_container_width=True):
            if st.session_state.name and st.session_state.email and st.session_state.phone:
                register_user()
            else:
                st.error("Please fill in all required fields (Name, Email, Phone)")
    
    # Chatbot interface (only shown after registration)
    else:
        # Display greeting with user's name
        st.markdown(f"### Hello, {st.session_state.user_details['name']}! 👋")
        
        # Chat container
        chat_container = st.container()
        with chat_container:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for message in st.session_state.messages:
                role_class = "user" if message["role"] == "user" else "bot"
                st.markdown(f'<div class="chat-message {role_class}"><p>{message["content"]}</p></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Special UI elements based on context
        if st.session_state.current_service == "hospital_appointment" and hasattr(st.session_state, 'show_appointment_form') and st.session_state.show_appointment_form:
            # Hospital appointment form
            st.subheader("Book Your Appointment")
            col1, col2 = st.columns(2)
            
            with col1:
                hospital = st.selectbox("Select Hospital", list(hospitals.keys()))
                doctor = st.selectbox("Select Doctor", hospitals[hospital])
            
            with col2:
                # Get available dates (next 7 days)
                today = datetime.now()
                available_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 8)]
                date = st.selectbox("Select Date", available_dates)
                
                # Available time slots
                time_slots = ["9:00 AM", "10:00 AM", "11:00 AM", "2:00 PM", "3:00 PM", "4:00 PM"]
                time_slot = st.selectbox("Select Time", time_slots)
            
            if st.button("Confirm Appointment", use_container_width=True):
                appointment = schedule_appointment(hospital, doctor, date, time_slot)
                st.session_state.show_appointment_form = False
                add_message("bot", f"Great! Your appointment has been scheduled with {doctor} at {hospital} on {date} at {time_slot}.")
                add_message("bot", "Is there anything else I can help you with?")
                st.experimental_rerun()
        
        # NCD Assessment recommendations
        elif st.session_state.current_service == "ncd_assessment" and hasattr(st.session_state, 'show_recommendations') and st.session_state.show_recommendations:
            st.subheader("Health Recommendations")
            st.markdown("""
            Based on your assessment, here are some general health recommendations:
            
            1. Maintain a balanced diet rich in fruits, vegetables, and whole grains
            2. Aim for at least 150 minutes of moderate exercise each week
            3. Limit alcohol consumption and avoid smoking
            4. Schedule regular health check-ups
            5. Monitor your blood pressure and blood sugar regularly
            """)
            
            if st.button("Thank you for the recommendations", use_container_width=True):
                add_message("user", "Thank you for the recommendations")
                add_message("bot", "You're welcome! Taking proactive steps for your health can make a big difference. Is there anything else I can help you with today?")
                st.session_state.show_recommendations = False
                st.session_state.current_service = None
                st.experimental_rerun()
        
        # Service buttons (only shown at the beginning or when no service is active)
        elif not st.session_state.current_service and len(st.session_state.messages) <= 3:
            st.subheader("Available Services")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🏥 Hospital Appointment", key="btn_appointment", use_container_width=True):
                    add_message("user", "I'd like to schedule a hospital appointment")
                    handle_service("hospital_appointment")
                    st.experimental_rerun()
                
                if st.button("❤️ NCD Assessment", key="btn_ncd", use_container_width=True):
                    add_message("user", "I want to take the NCD assessment")
                    handle_service("ncd_assessment")
                    st.experimental_rerun()
            
            with col2:
                if st.button("🔍 Cancer Assessment", key="btn_cancer", use_container_width=True):
                    add_message("user", "I want to take the cancer assessment")
                    handle_service("cancer_assessment")
                    st.experimental_rerun()
                
                if st.button("❓ Medical Queries", key="btn_query", use_container_width=True):
                    add_message("user", "I have some medical questions")
                    handle_service("medical_queries")
                    st.experimental_rerun()
        
        # User input field
        user_input = st.text_input("Type your message...", key="user_input")
        if st.button("Send", key="send_button", use_container_width=True):
            if user_input:
                process_user_input(user_input)
                st.session_state.user_input = ""  # Clear the input field
                st.experimental_rerun()

# Run the app
if __name__ == "__main__":
    main()