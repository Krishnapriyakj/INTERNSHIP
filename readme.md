# eHealth Chatbot Project
## Overview

This project is an **eHealth Chatbot** built using **FastAPI**, **LangChain**, **Ollama (Llama3.2)**, and **ChromaDB**. It provides medical Q&A, **cancer and NCD (Non-Communicable Disease) risk assessment**, and **hospital appointment scheduling with token generation**.

## Features

- **Conversational AI**: Uses LangChain with Llama3.2 to answer health-related questions.
- **Retrieval-Augmented Generation (RAG)**: Retrieves relevant medical documents from ChromaDB for accurate responses.
- **giveCancer & NCD Risk Assessment**: Asks structured health-related questions to assess risk levels.
- **Hospital Appointment Booking**: Schedules appointments with token generation for seamless hospital visits.
- **Session-based Assessment**: Maintains user responses and adapts the next questions accordingly.

## Project Structure

```
├── main.py                # Main application entry point
├── config.py              # Configuration settings
├── models/
│   └── schema.py          # Pydantic models/schemas
├── services/
│   ├── llm_service.py     # LLM and embeddings functionality
│   ├── rag_service.py     # RAG retrieval functionality
│   ├── ncd_service.py     # NCD and cancer assessment logic
│   └── appointment_service.py # Hospital appointment & token generation logic
├── data/
│   └── ncd_questions.json # NCD questions, risks, recommendations
├── api/
│   └── routes.py          # API endpoints
├── requirements.txt       # Project dependencies
├── README.md              # Project documentation
```

## Installation

### Prerequisites

- Python 3.9+
- [Ollama](https://ollama.com/) installed and running
- FastAPI & Uvicorn

### Setup

1. Clone the repository:
   ```sh
   git clone <repository-url>
   cd <repository-folder>
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Start the FastAPI server:
   ```sh
   python main.py
   ```
4. Access the API at:
   ```
   http://127.0.0.1:8000/docs
   ```

## API Endpoints

| Method | Endpoint        | Description                                      |
| ------ | --------------- | ------------------------------------------------ |
| POST   | `/chat/`        | Chat with the AI for health queries & assessment |

## Usage

- Ask general medical questions.
- Start a **cancer or NCD risk assessment** by mentioning "NCD risk" or "Cancer risk" in the chat.
- Answer a sequence of questions to receive a risk evaluation.
- Book a hospital appointment and receive a **token for your visit**.

## License

This project is licensed under the MIT License.

