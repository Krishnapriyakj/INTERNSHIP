# Chroma Integration with LangChain and Ollama

This project demonstrates how to use Chroma as a vector database, Ollama embeddings, and a language model to process queries and retrieve relevant document-based responses.

## Setup Instructions for Windows

### 1. Clone the Repository

If you haven't already cloned the repository, open your terminal (Command Prompt, PowerShell, or Windows Terminal) and run:

```bash
git clone <repository-url>
cd <repository-folder>
```

Replace `<repository-url>` with the actual repository URL.

---

### 2. Activate the Virtual Environment

Activate the `venv` environment using the following command:

- **Command Prompt**:

  ```bash
  venv\Scripts\activate
  ```

- **PowerShell**:

  ```bash
  .\venv\Scripts\Activate.ps1
  ```

- **Git Bash** (or other bash shell):
  ```bash
  source venv/Scripts/activate
  ```

You should see `(venv)` at the beginning of your terminal prompt, indicating that the virtual environment is active.

---

### 3. Install Dependencies

Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

This will install all dependencies, including `langchain`, `chroma`, `ollama`, and others.

---

### 4. Set Up Chroma Database and Prepare Files

1. Place your PDF files in the folder named `test`. You can create this folder if it doesn't exist.
2. Run the indexing script to populate your Chroma database with document embeddings:

```bash
python your_indexing_script.py
```

Replace `your_indexing_script.py` with the filename of the script you are using for indexing, e.g., `main.py`.

---

### 5. Query the System

To use the query system, run the query script:

```bash
python your_query_script.py
```

Replace `your_query_script.py` with the filename of the query-related script, e.g., `query.py`.

Follow the prompts to enter your query. The system will process the query and provide a response based on the documents stored in the Chroma database.

---

### 6. Deactivate the Virtual Environment

Once you're done, deactivate the virtual environment:

```bash
deactivate
```

---

## Troubleshooting

- **PowerShell Execution Policy Error**:  
  If you encounter an error like `execution of scripts is disabled on this system`, you need to allow script execution. Run the following in an _elevated PowerShell_ (run as Administrator):

  ```bash
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```

- **Dependencies Issue**:  
  Ensure that all required libraries are listed in `requirements.txt`. You can generate this file using:

  ```bash
  pip freeze > requirements.txt
  ```

---

## Notes

- This project is developed and tested using a Linux environment. Windows users may need to adapt paths (use `\` instead of `/`).
- Ensure that the `chroma_db` directory is accessible and properly configured.

---

Feel free to reach out if you have any issues setting up or using this project! 😊

---

Let me know if you need changes or further clarification!
