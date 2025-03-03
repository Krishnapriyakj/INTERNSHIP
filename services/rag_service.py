"""RAG retrieval service for finding relevant information."""
from langchain_chroma import Chroma

from config import CHROMA_DB_PATH
from services.llm_service import get_embedding_function, format_prompt, generate_llm_response

def retrieve_relevant_info(query_text):
    """Retrieve relevant information using RAG."""
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embedding_function)

    # Retrieve relevant documents
    results = db.similarity_search_with_score(query_text, k=2)
    
    if not results:
        return "I couldn't find relevant information, but I can try to answer your query directly."

    # Extract context from retrieved documents
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    # Format the prompt with retrieved context
    prompt = format_prompt(context_text, query_text)

    # Get response from LLM
    return generate_llm_response(prompt)