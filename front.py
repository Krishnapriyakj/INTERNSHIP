# frontend.py
import streamlit as st
import requests
import time
import json
from datetime import datetime

# FastAPI backend URL
BACKEND_URL = "http://127.0.0.1:8000"

def init_session_state():
    """Initialize all session state variables with default values"""
    defaults = {
        'user_id': None,
        'registered': False,
        'user_details': {},
        'current_service': None,
        'appointment_stage': None,
        'hospital_data_loaded': False,
        'hospital_departments': [],
        'available_days': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        'ncd_assessment': {
            'current_question': 0,
            'answers': {},
            'questions': None,
            'loaded': False
        },
        'cancer_assessment': {
            'current_question': 0,
            'answers': {},
            'questions': None,
            'loaded': False
        },
        'chat_history': []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def load_hospital_data():
    """Fetch hospital data from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/hospitals/all")
        if response.status_code == 200:
            data = response.json()
            if 'hospitals' in data:
                departments = set()
                for hospital in data['hospitals']:
                    if hospital.get('Department'):
                        departments.add(hospital['Department'].strip())
                st.session_state.hospital_departments = sorted(departments)
                st.session_state.hospital_data_loaded = True
                return True
        return False
    except Exception as e:
        st.error(f"Failed to load hospital data: {str(e)}")
        return False

def load_ncd_questions():
    """Fetch NCD questions from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/data/ncd_questions")
        if response.status_code == 200:
            st.session_state.ncd_assessment['questions'] = response.json().get('questions', [])
            st.session_state.ncd_assessment['loaded'] = True
            return True
        return False
    except Exception as e:
        st.error(f"Failed to load NCD questions: {str(e)}")
        return False

def load_cancer_questions():
    """Fetch Cancer questions from backend"""
    try:
        response = requests.get(f"{BACKEND_URL}/data/cancer_questions")
        if response.status_code == 200:
            st.session_state.cancer_assessment['questions'] = response.json().get('questions', [])
            st.session_state.cancer_assessment['loaded'] = True
            return True
        return False
    except Exception as e:
        st.error(f"Failed to load Cancer questions: {str(e)}")
        return False

def show_appointment_booking():
    st.subheader("🏥 Hospital Appointment Booking")
    
    # Load hospital data if not loaded
    if not st.session_state.hospital_data_loaded:
        with st.spinner("Loading hospital data..."):
            if not load_hospital_data():
                st.error("Failed to load hospital data. Please try again later.")
                if st.button("Back to Services"):
                    st.session_state.current_service = None
                    st.rerun()
                return
    
    if st.session_state.appointment_stage == "day_selection":
        day = st.selectbox("Select day", st.session_state.available_days)
        department = st.selectbox("Select department", st.session_state.hospital_departments)
        time_slot = st.selectbox("Select time", ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"])
        
        if st.button("Check Availability"):
            try:
                response = requests.get(
                    f"{BACKEND_URL}/hospitals/availability",
                    params={"day": day, "department": department, "time": time_slot}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('available'):
                        st.session_state.appointment_stage = "slot_selection"
                        st.session_state.appointment_data = {
                            "day": day,
                            "department": department,
                            "time": time_slot,
                            "options": data['hospitals']
                        }
                        st.rerun()
                    else:
                        st.warning("No availability for selected criteria")
                else:
                    st.error("Failed to check availability")
            except Exception as e:
                st.error(f"Error checking availability: {str(e)}")
    
    # Update the slot selection part in show_appointment_booking()
    elif st.session_state.appointment_stage == "slot_selection":
        st.write("Available slots:")
        options = st.session_state.appointment_data['options']
    
        # Create a list of formatted options
        slot_options = [f"{idx+1}. {opt['Hospital Name']} - Dr. {opt['Doctor']} ({opt['Time']})" 
                   for idx, opt in enumerate(options)]
    
        # Use radio buttons for clearer selection
        selected_slot = st.radio("Choose a hospital:", slot_options, index=None)
    
        if selected_slot:
            selected_idx = slot_options.index(selected_slot)
            st.session_state.appointment_data['selected_hospital'] = options[selected_idx]
        
            if st.button("Confirm Selection"):
               st.session_state.appointment_stage = "confirm_details"
               st.rerun()
        else:
            st.warning("Please select a hospital from the list")
    
        if st.button("Back to Options"):
            st.session_state.appointment_stage = "day_selection"
            st.rerun()
    
    elif st.session_state.appointment_stage == "confirm_details":
        hospital = st.session_state.appointment_data['selected_hospital']
        st.write("### Appointment Details")
        st.write(f"**Hospital:** {hospital['Hospital Name']}")
        st.write(f"**Department:** {hospital['Department']}")
        st.write(f"**Doctor:** {hospital['Doctor']}")
        st.write(f"**Day:** {st.session_state.appointment_data['day']}")
        st.write(f"**Time:** {hospital['Time']}")
        
        st.write("### Your Information")
        st.write(f"**Name:** {st.session_state.user_details['name']}")
        st.write(f"**Age:** {st.session_state.user_details['age']}")
        
        if st.button("Confirm Appointment"):
            appointment_data = {
                "user_id": st.session_state.user_id,
                "user_name": st.session_state.user_details['name'],
                "user_age": st.session_state.user_details['age'],
                "hospital": hospital['Hospital Name'],
                "department": hospital['Department'],
                "doctor": hospital['Doctor'],
                "day": st.session_state.appointment_data['day'],
                "time": hospital['Time']
            }
            
            # Process payment if needed (age 18-50)
            if 18 <= st.session_state.user_details['age'] <= 50:
                st.session_state.appointment_stage = "payment"
                st.rerun()
            else:
                try:
                    response = requests.post(
                        f"{BACKEND_URL}/appointments/book",
                        json=appointment_data
                    )
                    if response.status_code == 200:
                        st.success("Appointment booked successfully!")
                        time.sleep(2)
                        st.session_state.current_service = None
                        st.session_state.appointment_stage = None
                        st.rerun()
                    else:
                        st.error("Failed to book appointment")
                except Exception as e:
                    st.error(f"Error booking appointment: {str(e)}")
    
    # Update the payment part in show_appointment_booking()
    elif st.session_state.appointment_stage == "payment":
        st.write("### Payment Required (₹20)")
        st.write("Please complete the payment to confirm your appointment")
    
    # Generate QR code
        st.image("https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=upi://pay?pa=hospital@upi&pn=Hospital&am=20.00", 
            caption="Scan to pay ₹20", width=200)
    
        if st.button("I've completed payment"):
           try:
              appointment_data = {
                  "user_id": st.session_state.user_id,
                  "user_name": st.session_state.user_details['name'],
                  "user_age": st.session_state.user_details['age'],
                  **st.session_state.appointment_data['selected_hospital'],
                  "day": st.session_state.appointment_data['day']
              }
            
              with st.spinner("Verifying payment..."):
                response = requests.post(
                    f"{BACKEND_URL}/appointments/book",
                    json=appointment_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        st.success(f"""
                        Payment successful!
                        Appointment confirmed:
                        - Hospital: {result['details']['Hospital Name']}
                        - Doctor: {result['details']['Doctor']}
                        - Time: {result['details']['Time']}
                        - Token: {result['token']}
                        """)
                        time.sleep(3)
                        st.session_state.current_service = None
                        st.session_state.appointment_stage = None
                        st.rerun()
                    else:
                        st.error("Payment verification failed. Please try again.")
                else:
                    st.error("Failed to verify payment")
           except Exception as e:
               st.error(f"Error processing payment: {str(e)}")
    
        if st.button("Cancel Appointment"):
           st.session_state.current_service = None
           st.session_state.appointment_stage = None
           st.rerun()

def show_ncd_assessment():
    st.subheader("💊 NCD Risk Assessment")
    
    # Load questions if not loaded
    if not st.session_state.ncd_assessment['loaded']:
        with st.spinner("Loading assessment questions..."):
            if not load_ncd_questions():
                st.error("Failed to load assessment questions")
                if st.button("Back to Services"):
                    st.session_state.current_service = None
                    st.rerun()
                return
    
    questions = st.session_state.ncd_assessment['questions']
    current_idx = st.session_state.ncd_assessment['current_question']
    
    # Check if assessment is complete
    if current_idx >= len(questions):
        try:
            response = requests.post(
                f"{BACKEND_URL}/assessments/ncd",
                json={
                    "user_id": st.session_state.user_id,
                    "answers": st.session_state.ncd_assessment['answers']
                }
            )
            
            if response.status_code == 200:
                results = response.json().get('results', 'No results available')
                st.success("Assessment complete!")
                st.markdown(results)
                
                if st.button("Back to Services"):
                    st.session_state.current_service = None
                    st.session_state.ncd_assessment = {
                        'current_question': 0,
                        'answers': {},
                        'questions': None,
                        'loaded': False
                    }
                    st.rerun()
            else:
                st.error("Failed to get assessment results")
        except Exception as e:
            st.error(f"Error processing assessment: {str(e)}")
        return
    
    current_question = questions[current_idx]
    
    # Check question dependencies
    if 'depends_on' in current_question:
        dep_key = current_question['depends_on']
        dep_condition = current_question['condition']
        if st.session_state.ncd_assessment['answers'].get(dep_key) != dep_condition:
            st.session_state.ncd_assessment['current_question'] += 1
            st.rerun()
    
    st.write(f"Question {current_idx + 1}/{len(questions)}: {current_question['question']}")
    
    if current_question['valid_answers'] == "numeric":
        answer = st.number_input("Your answer", min_value=0)
    else:
        answer = st.selectbox("Your answer", current_question['valid_answers'])
    
    if st.button("Submit Answer"):
        st.session_state.ncd_assessment['answers'][current_question['key']] = answer
        st.session_state.ncd_assessment['current_question'] += 1
        st.rerun()
    
    if st.button("Back to Services"):
        st.session_state.current_service = None
        st.session_state.ncd_assessment = {
            'current_question': 0,
            'answers': {},
            'questions': None,
            'loaded': False
        }
        st.rerun()

def show_cancer_assessment():
    st.subheader("🦠 Cancer Risk Assessment")
    
    # Load questions if not loaded
    if not st.session_state.cancer_assessment['loaded']:
        with st.spinner("Loading assessment questions..."):
            if not load_cancer_questions():
                st.error("Failed to load assessment questions")
                if st.button("Back to Services"):
                    st.session_state.current_service = None
                    st.rerun()
                return
    
    questions = st.session_state.cancer_assessment['questions']
    current_idx = st.session_state.cancer_assessment['current_question']
    
    # Check if assessment is complete
    if current_idx >= len(questions):
        try:
            response = requests.post(
                f"{BACKEND_URL}/assessments/cancer",
                json={
                    "user_id": st.session_state.user_id,
                    "answers": st.session_state.cancer_assessment['answers']
                }
            )
            
            if response.status_code == 200:
                results = response.json().get('results', 'No results available')
                st.success("Assessment complete!")
                st.markdown(results)
                
                if st.button("Back to Services"):
                    st.session_state.current_service = None
                    st.session_state.cancer_assessment = {
                        'current_question': 0,
                        'answers': {},
                        'questions': None,
                        'loaded': False
                    }
                    st.rerun()
            else:
                st.error("Failed to get assessment results")
        except Exception as e:
            st.error(f"Error processing assessment: {str(e)}")
        return
    
    current_question = questions[current_idx]
    
    st.write(f"Question {current_idx + 1}/{len(questions)}: {current_question['question']}")
    answer = st.slider("Rate (0-9)", 0, 9, 5)
    
    if st.button("Submit Rating"):
        st.session_state.cancer_assessment['answers'][current_question['key']] = answer
        st.session_state.cancer_assessment['current_question'] += 1
        st.rerun()
    
    if st.button("Back to Services"):
        st.session_state.current_service = None
        st.session_state.cancer_assessment = {
            'current_question': 0,
            'answers': {},
            'questions': None,
            'loaded': False
        }
        st.rerun()

def show_general_query():
    st.subheader("❓ General Medical Query")
    
    # Initialize chat if not exists
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Hi! I'm your health assistant. Ask me any medical questions."}
        ]
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input for new message
    if prompt := st.chat_input("Type your medical question here"):
        # Add user message to chat
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get assistant response
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/chat/query",
                    json={
                        "user_id": st.session_state.user_id,
                        "question": prompt
                    }
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    assistant_response = response_data.get("response", "I couldn't process your question.")
                    
                    # Add assistant response to chat
                    st.session_state.chat_messages.append({"role": "assistant", "content": assistant_response})
                    with st.chat_message("assistant"):
                        st.markdown(assistant_response)
                else:
                    error_msg = "Sorry, I encountered an error processing your question."
                    st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                    with st.chat_message("assistant"):
                        st.markdown(error_msg)
            
            except Exception as e:
                error_msg = f"Connection error: {str(e)}"
                st.session_state.chat_messages.append({"role": "assistant", "content": error_msg})
                with st.chat_message("assistant"):
                    st.markdown(error_msg)
    
    if st.button("Back to Services", key="general_back"):
        st.session_state.current_service = None
        st.rerun()

def main():
    st.set_page_config(page_title="Health Assistant", page_icon="🩺")
    st.title("Health Assistant")
    
    # Initialize session state
    init_session_state()
    
    if not st.session_state.registered:
        with st.form("registration_form"):
            st.subheader("User Registration")
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=1, max_value=120)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            email = st.text_input("Email")
            
            if st.form_submit_button("Register"):
                st.session_state.user_details = {
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "email": email
                }
                st.session_state.user_id = f"user_{int(time.time())}"
                st.session_state.registered = True
                st.success("Registration successful!")
                time.sleep(1)
                st.rerun()
    else:
        if not st.session_state.current_service:
            st.subheader(f"Welcome, {st.session_state.user_details['name']}!")
            st.write("How can I help you today?")
            
            cols = st.columns(2)
            with cols[0]:
                if st.button("🏥 Hospital Appointment", use_container_width=True):
                    st.session_state.current_service = "appointment"
                    st.session_state.appointment_stage = "day_selection"
                    st.rerun()
            
            with cols[0]:
                if st.button("💊 NCD Assessment", use_container_width=True):
                    st.session_state.current_service = "ncd"
                    st.rerun()
            
            with cols[1]:
                if st.button("🦠 Cancer Assessment", use_container_width=True):
                    st.session_state.current_service = "cancer"
                    st.rerun()
            
            with cols[1]:
                if st.button("❓ General Medical Query", use_container_width=True):
                    st.session_state.current_service = "general"
                    st.rerun()
        else:
            if st.session_state.current_service == "appointment":
                show_appointment_booking()
            elif st.session_state.current_service == "ncd":
                show_ncd_assessment()
            elif st.session_state.current_service == "cancer":
                show_cancer_assessment()
            elif st.session_state.current_service == "general":
                show_general_query()

if __name__ == "__main__":
    main()