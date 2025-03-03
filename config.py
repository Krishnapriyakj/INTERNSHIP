"""Configuration settings for the NCD Chatbot application."""

# ChromaDB Path
CHROMA_DB_PATH = "chroma_db"

# RAG prompt template
PROMPT_TEMPLATE = """
You are an AI health assistant that answers medical questions.
Use the following context to help answer the user's query.
Only provide a risk assessment if the user explicitly asks for it.

Context:
{context}

---

User: {question}
AI:"""

# Model names
LLM_MODEL = "llama3.2"
EMBEDDING_MODEL = "nomic-embed-text"