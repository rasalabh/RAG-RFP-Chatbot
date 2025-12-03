# RAG RFP Chatbot - Setup Guide

This guide provides step-by-step instructions to set up, run, and use the RAG RFP Chatbot on your local machine.

## Prerequisites

*   **Python 3.9+**: Ensure Python is installed.
*   **Google API Key**: You need a free API key for Google Gemini. Get it [here](https://makersuite.google.com/app/apikey).
*   **Git**: To clone the repository.

---

## 1. Installation

### Clone the Repository
```bash
git clone <your-repo-url>
cd "RAG RFP Chatbot"
```

### Create a Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 2. Configuration

1.  **Create Environment File**:
    Copy the example file to create your local configuration.
    ```bash
    cp .env.example .env
    # OR on Windows Command Prompt:
    copy .env.example .env
    ```

2.  **Add API Key**:
    Open `.env` in a text editor and paste your Google API Key:
    ```env
    GOOGLE_API_KEY=your_actual_api_key_here
    ```

---

## 3. Running the Application

Start the backend server:

```bash
python -m uvicorn main:app --reload
```

You should see output indicating the server is running at `http://127.0.0.1:8000`.

---

## 4. Using the Chatbot

1.  **Open Browser**: Go to [http://localhost:8000](http://localhost:8000).
2.  **Upload Documents**:
    *   Click **"Upload Documents"**.
    *   Select your RFP files. Supported formats: **PDF (.pdf), Word (.docx), Excel (.xlsx)**.
3.  **Process Documents**:
    *   Click **"Process Docs"**.
    *   Wait for the confirmation message (e.g., "Successfully ingested 5 documents...").
4.  **Start Chatting**:
    *   Type your question in the chat box (e.g., "What is the project budget?").
    *   The bot will answer with citations to the source documents.

---

## 5. Features & Controls

### RAG Settings Panel
*   **Chunk Size**: Controls how much text is grouped together (Default: 1000).
*   **Overlap**: Controls context overlap between chunks (Default: 200).
*   **Top K**: Number of chunks to retrieve for each answer (Default: 5).
*   **Temperature**: Controls LLM creativity (0.0 = factual, 1.0 = creative).

### RAG Evaluation
*   Enable the **"Enable Evaluation"** checkbox to see quality metrics for every answer.
*   Metrics include: **Context Relevance**, **Faithfulness**, and **Answer Relevance**.

### File Management
*   Hover over any file in the list to see the **Delete (✕)** button.
*   **Note**: After deleting a file, you must click **"Process Docs"** again to update the search index.

---

## 6. Project Structure

```
RAG RFP Chatbot/
├── main.py                  # FastAPI Backend
├── rag_engine.py            # RAG Logic & Document Loaders
├── rag_evaluator.py         # Evaluation Metrics System
├── requirements.txt         # Dependencies
├── .env                     # API Keys (Not committed to Git)
├── static/                  # Frontend Assets
│   ├── index.html
│   ├── style.css
│   └── script.js
├── data/                    # Document Storage (Local only)
└── faiss_index/             # Vector Database (Local only)
```

## Troubleshooting

*   **"Index not found"**: You must upload files and click "Process Docs" first.
*   **"ImportError"**: Ensure you installed all requirements (`pip install -r requirements.txt`).
*   **Slow Responses**: If using "Enable Evaluation", responses take 2x longer because the LLM evaluates itself.
