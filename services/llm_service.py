"""LLM service for generating responses."""
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate

from config import LLM_MODEL, EMBEDDING_MODEL, PROMPT_TEMPLATE

def get_llm_model():
    """Initialize and return the LLM model."""
    return OllamaLLM(model=LLM_MODEL)

def get_embedding_function():
    """Initialize and return embeddings model."""
    return OllamaEmbeddings(model=EMBEDDING_MODEL)

def format_prompt(context, question):
    """Format the prompt with context and question."""
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    return prompt_template.format(context=context, question=question)

def generate_llm_response(prompt):
    """Generate response from LLM model."""
    model = get_llm_model()
    return model.invoke(prompt)