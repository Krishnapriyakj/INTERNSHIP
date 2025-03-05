from langchain_ollama import OllamaLLM, OllamaEmbeddings

from config import settings

def get_llm():
    return OllamaLLM(model=settings.ollama_model)


def get_embedding_function():
    return OllamaEmbeddings(model=settings.embedding_model)