from langchain_core.prompts import ChatPromptTemplate
from services.llm_service import get_llm

# Improved decision maker prompt template
DECISION_MAKER = ChatPromptTemplate.from_template("""
Analyse the given prompt and return only one among the 3 values based upon their use:

"book_appointment" - If the prompt is asking to book an appointment or schedule a visit to a hospital.
This can enable users to book an appointment with the hospital.
Example keywords: book appointment, schedule visit, make appointment, book a slot, doctor appointment

"cancer_risk_assessment" - If the prompt is asking to assess the cancer risk or evaluate cancer likelihood.
This can enable users to assess their cancer risk based on the given parameters.
Example keywords: cancer risk, cancer assessment, cancer check, cancer screening, cancer evaluation

"ncd_risk_assessment" - If the prompt is asking to assess non-communicable disease risks or general health risks.
This can enable users to assess their health risks related to conditions like diabetes, heart disease, etc.
Example keywords: ncd risk, health risk, risk assessment, health check, health evaluation, chronic disease risk

"generic" - If not following any other usecase, a 'generic' indicates the response may be a general LLM response or RAG response.

Return ONLY ONE of: "book_appointment", "cancer_risk_assessment", "ncd_risk_assessment", or "generic".
No explanations or additional text.

PROMPT: {prompt}
""")

async def determine_intent(user_question: str) -> str:
    """Determine the user's intent from their question."""
    llm = get_llm()
    
    # Preprocess the question to help with intent recognition
    question_lower = user_question.lower().strip()
    
    # Direct keyword matching for more reliability
    if any(keyword in question_lower for keyword in ["book appointment", "schedule appointment", "make appointment", "book a slot"]):
        return "book_appointment"
    
    if any(keyword in question_lower for keyword in ["cancer risk", "cancer assessment", "cancer check", "cancer screening"]):
        return "cancer_risk_assessment"
    
    if any(keyword in question_lower for keyword in ["ncd risk", "ncd assessment", "health risk", "health check", "health assessment", "chronic disease"]):
        return "ncd_risk_assessment"
    
    # Use LLM for more nuanced understanding if no direct match
    decision = llm.invoke(DECISION_MAKER.format(prompt=user_question))
    
    # Clean up the response
    decision = decision.strip().lower().replace('"', '')
    
    if decision in ["book_appointment", "cancer_risk_assessment", "ncd_risk_assessment", "generic"]:
        return decision
    else:
        # Default to generic if we can't determine intent
        return "generic"
