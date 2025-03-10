from pydantic_settings import BaseSettings
from pydantic import ConfigDict  # Import ConfigDict

class Settings(BaseSettings):
    app_name: str = "Conversational NCD Chatbot"
    app_version: str = "1.2"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    chroma_db_path: str = "chroma_db"
    ollama_model: str = "llama3.2"
    embedding_model: str = "nomic-embed-text"

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
