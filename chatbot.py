from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma

# ChromaDB Path
CHROMA_DB_PATH = "chroma_db"

# Define the prompt template for RAG with integrated NCD assessment
PROMPT_TEMPLATE = """
You are an AI health assistant that answers medical questions.
Use the following context to help answer the user's query.
If the context is not helpful, answer the question to the best of your ability.

Context:
{context}

---

User: {question}
AI:"""

# Initialize LLM model
model = OllamaLLM(model="llama3.2")

def get_embedding_function():
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings

def retrieve_relevant_info(query_text):
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embedding_function)

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
    response_text = model.invoke(prompt)

    return response_text