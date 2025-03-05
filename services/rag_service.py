from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma

from config import settings
from services import llm_service

PROMPT_TEMPLATE = """
You are an AI health assistant that answers medical questions.
Use the following context to help answer the user's query.
If the context is not helpful, answer the question to the best of your ability.

Context:
{context}

---

User: {question}
AI:"""


def retrieve_relevant_info(query_text):
    embedding_function = llm_service.get_embedding_function()
    db = Chroma(persist_directory=settings.chroma_db_path, embedding_function=embedding_function)

    # Retrieve relevant documents
    results = db.similarity_search_with_score(query_text, k=2)

    context_text = ""  # Initialize as empty string

    if results:
        # Extract context from retrieved documents
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    # Format the prompt with retrieved context
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    # Get response from LLM
    llm = llm_service.get_llm()
    response_text = llm.invoke(prompt)

    return response_text