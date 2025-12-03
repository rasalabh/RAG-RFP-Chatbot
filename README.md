# RAG RFP Chatbot

A production-ready Retrieval-Augmented Generation (RAG) chatbot designed specifically for RFP (Request for Proposal) document analysis. Built with modern AI technologies to provide accurate, context-aware responses from your RFP documents.

## Overview

This application enables users to upload RFP documents and interact with them through natural language queries. The system uses advanced RAG techniques to retrieve relevant information from documents and generate precise answers using Google's Gemini LLM.

### Key Highlights
- **Local-First Architecture**: All processing happens on your machine
- **Production-Grade RAG**: Optimized chunking, embedding, and retrieval pipeline
- **Dynamic Configuration**: Real-time parameter tuning without server restarts
- **Source Citations**: Every answer includes document sources and page numbers
- **Modern UI**: Dark-themed, responsive interface with real-time updates

## Features

### Core Functionality
- ✅ **Multi-Format Support**: Upload PDF, Word (.docx), and Excel (.xlsx) documents
- ✅ **File Management**: Delete uploaded files directly from the UI
- ✅ **Intelligent Chunking**: Configurable chunk size and overlap for optimal retrieval
- ✅ **Semantic Search**: FAISS-powered vector similarity search
- ✅ **Context-Aware Responses**: Gemini 2.5 Flash LLM with temperature control
- ✅ **Source Attribution**: Automatic citation with file names and page numbers
- ✅ **Persistent Storage**: Local vector index saves processing time

### Advanced Features
- 🎛️ **Dynamic Settings Panel**: Adjust chunk size, overlap, Top K, and temperature in real-time
- 📊 **Optimized for RFPs**: Custom text splitting with separators for structured documents
- 🔒 **Local Processing**: All embeddings and vector storage happen locally
- ⚡ **Fast Inference**: Uses lightweight `all-MiniLM-L6-v2` for embeddings
- 🧪 **RAG Evaluation Metrics**: Real-time quality assessment with Context Relevance, Faithfulness, and Answer Relevance scores

## Tech Stack

### Backend

#### **FastAPI** - Web Framework
**Why FastAPI?**
- **Performance**: ASGI-based, async support, ~3x faster than Flask
- **Type Safety**: Pydantic models ensure request/response validation
- **Auto Documentation**: Built-in Swagger UI at `/docs`
- **Modern Python**: Native async/await, Python 3.7+ features
- **Production Ready**: Used by Microsoft, Uber, Netflix

#### **LangChain** - RAG Orchestration
**Why LangChain?**
- **Modular Pipeline**: Easy to swap components (LLM, embeddings, vector stores)
- **Best Practices**: Built-in text splitters with semantic separators
- **LLM Agnostic**: Switch between OpenAI, Gemini, local models seamlessly
- **Active Ecosystem**: 1000+ integrations, frequent updates
- **Production Patterns**: Pre-built chains for RAG, agents, and more

#### **FAISS** - Vector Database
**Why FAISS over ChromaDB?**
- **Performance**: 10-100x faster similarity search (C++ optimized)
- **No Dependencies**: ChromaDB had installation issues on Windows
- **Memory Efficient**: ~50% less memory usage than ChromaDB
- **Battle-Tested**: Created by Meta AI, used at scale by Google, Microsoft
- **Offline-First**: No server required, fully local operation
- **Simple**: Single file storage, easy backup/restore

**ChromaDB Issues Encountered:**
- Installation failures on Windows due to SQLite compilation
- Heavier dependency chain (requires Docker for production)
- Overkill for single-user use cases

#### **HuggingFace Embeddings** - Text Vectorization
**Why HuggingFace `all-MiniLM-L6-v2`?**
- **Local Execution**: No API calls, completely offline
- **Cost-Free**: No usage limits or API keys
- **Fast**: 384-dimensional vectors, optimized for CPU
- **Quality**: 93.5% accuracy on semantic similarity benchmarks
- **Small Footprint**: 90MB model size
- **Production Ready**: Used in 50,000+ commercial applications

**Alternative Considered:**
- OpenAI Embeddings: ❌ Costs $0.0001/1K tokens, requires internet
- Cohere: ❌ API-based, privacy concerns

#### **Google Gemini 2.5 Flash** - LLM
**Why Gemini 2.5 Flash?**
- **Free Tier**: 1500 requests/day, sufficient for development
- **Fast**: 2x faster than Gemini Pro
- **Long Context**: 1M token context window
- **Grounded**: Better at following instructions vs GPT-3.5
- **Multimodal Ready**: Future support for images, PDFs

**Alternative Considered:**
- GPT-4: ❌ Expensive ($0.03/1K tokens)
- Local LLMs (Llama): ❌ Requires GPU, slower inference

### Frontend

#### **Vanilla JavaScript** - No Framework Overhead
**Why No React/Vue?**
- **Performance**: Zero bundle size, instant page loads
- **Simplicity**: No build step, no compilation
- **Learning Curve**: Easier for maintenance
- **SEO-Friendly**: No hydration issues

#### **CSS3 with Custom Properties** - Modern Styling
- **Dark Theme**: Optimized for long reading sessions
- **Glassmorphism**: Modern UI aesthetics
- **Responsive**: Works on desktop, tablets
- **Performance**: No CSS-in-JS overhead

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Upload    │  │   Settings   │  │   Chat Messages  │   │
│  │   PDFs      │  │   Panel      │  │   + Citations    │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘   │
└─────────┼─────────────────┼───────────────────┼─────────────┘
          │                 │                   │
          ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  /upload    /ingest          /chat        /files     │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      RAG Engine (rag_engine.py)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  PDF Loader  │→│ Text Splitter│→│   Embeddings     │  │
│  │  (PyPDF)     │  │  (LangChain) │  │  (HuggingFace)   │  │
│  └──────────────┘  └──────────────┘  └─────────┬────────┘  │
│                                                  │           │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────▼────────┐  │
│  │   Gemini LLM │←│   Retriever  │←│  FAISS Vector DB │  │
│  │   (Response) │  │   (Top-K)    │  │  (Local Index)   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Document Ingestion**:
   ```
   PDF Upload → PyPDFLoader → Text Splitter (with overlap) → 
   HuggingFace Embeddings → FAISS Index → Save to disk
   ```

2. **Query Processing**:
   ```
   User Query → Embedding → FAISS Search (Top K) → 
   Context Assembly → Gemini Prompt → Response + Sources
   ```

## Project Structure

```
RAG RFP Chatbot/
├── main.py                  # FastAPI application & API endpoints
├── rag_engine.py            # Core RAG logic (ingestion, querying)
├── rag_evaluator.py         # RAG evaluation metrics module
├── test_evaluation.py       # Test script for evaluation API
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (API keys)
├── .env.example             # Template for environment setup
├── README.md                # This file
├── SETUP_GUIDE.md           # Detailed setup instructions
│
├── static/                  # Frontend assets
│   ├── index.html           # Main UI
│   ├── style.css            # Styling with dark theme
│   └── script.js            # Frontend logic
│
├── data/                    # Uploaded PDF documents
│   └── (your RFP files here)
│
└── faiss_index/             # Persisted vector database
    ├── index.faiss          # FAISS index file
    └── index.pkl            # Metadata (chunk mappings)
```

## Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager
- Google API key (free tier)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "RAG RFP Chatbot"
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your Google API key
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

   Get your free API key: https://makersuite.google.com/app/apikey

4. **Run the application**:
   ```bash
   python -m uvicorn main:app --reload
   ```

5. **Open in browser**:
   ```
   http://localhost:8000
   ```

### First Use

1. **Upload Documents**: Click "Upload PDFs" and select your RFP files
2. **Process Documents**: Click "Process Docs" to index them (one-time operation)
3. **Start Chatting**: Ask questions about your documents!

### Configuration

Adjust these settings in the UI sidebar:

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| **Chunk Size** | 1000 | 100-2000 | Characters per chunk (larger = more context) |
| **Overlap** | 200 | 0-500 | Character overlap between chunks |
| **Top K** | 5 | 1-10 | Number of chunks to retrieve |
| **Temperature** | 0.7 | 0.0-1.0 | LLM creativity (0=factual, 1=creative) |
| **Enable Evaluation** | Off | On/Off | Show RAG quality metrics (Context, Faithfulness, Relevance) |

**Recommended for RFPs**:
- Chunk Size: **1000** (captures complete requirements)
- Overlap: **200** (20% overlap prevents information loss)
- Top K: **5** (covers multi-section answers)
- Temperature: **0.3-0.5** (factual, low hallucination)

## RAG Evaluation

This chatbot includes a comprehensive RAG evaluation system to assess the quality of responses across multiple dimensions.

### Evaluation Metrics

When evaluation is enabled (via the UI checkbox or API parameter), each response is assessed on:

#### 1. **Context Relevance** (0-1 score)
- **What it measures**: Are the retrieved document chunks actually relevant to the user's query?
- **Why it matters**: Irrelevant chunks waste the LLM's context window and can lead to poor answers
- **Pass threshold**: ≥ 0.7
- **Example**: 
  - Query: "What is the budget?"
  - Good: Chunks containing pricing, cost estimates
  - Bad: Chunks about team qualifications

#### 2. **Faithfulness** (0-1 score)
- **What it measures**: Is the answer grounded in the retrieved sources, or is it hallucinated?
- **Why it matters**: Ensures all claims are supported by your documents
- **Pass threshold**: ≥ 0.8
- **Example**:
  - Context: "Budget is $500K"
  - Faithful: "The budget is $500,000"
  - Unfaithful: "The budget is $500K and includes consulting fees" (if consulting fees not mentioned)

#### 3. **Answer Relevance** (0-1 score)
- **What it measures**: Does the answer actually address the user's question?
- **Why it matters**: Prevents tangential or off-topic responses
- **Pass threshold**: ≥ 0.7
- **Example**:
  - Query: "When is the deadline?"
  - Relevant: "The deadline is December 31, 2024"
  - Irrelevant: "The project involves multiple phases" (doesn't answer when)

### Overall Score

The overall score is a weighted average:
```
Overall = (Context Relevance × 0.3) + (Faithfulness × 0.4) + (Answer Relevance × 0.3)
```

Faithfulness is weighted highest (40%) because hallucinations are the most critical issue in RAG systems.

### Using Evaluation

#### Via UI
1. Check the **"Enable Evaluation"** checkbox in the RAG Settings panel
2. Ask your question
3. See metrics displayed below the answer with:
   - Color-coded progress bars (green = good, yellow = medium, red = poor)
   - Percentage scores for each metric
   - Pass/Fail verdicts
   - Actionable recommendations

#### Via API
```python
import requests

response = requests.post("http://localhost:8000/chat", json={
    "message": "What is the project budget?",
    "top_k": 5,
    "temperature": 0.7,
    "evaluate": True  # Enable evaluation
})

data = response.json()
print(f"Answer: {data['response']}")
print(f"Overall Score: {data['evaluation']['overall_score']}")
print(f"Context Relevance: {data['evaluation']['metrics']['context_relevance']['score']}")
```

#### Via Test Script
Run the included test script for automated evaluation:

```bash
python test_evaluation.py
```

This will:
- Test multiple queries automatically
- Display formatted results with color coding
- Show recommendations for improvement
- Provide raw JSON for debugging

### Interpreting Results

| Overall Score | Verdict | Action |
|---------------|---------|--------|
| **≥ 0.7** | PASS | Response is high quality, no action needed |
| **0.5 - 0.7** | MARGINAL | Review individual metrics, tune parameters |
| **< 0.5** | FAIL | Adjust chunk size, Top K, or improve documents |

**Common Issues and Fixes:**

- **Low Context Relevance**: Increase chunk size or Top K
- **Low Faithfulness**: Lower temperature (try 0.3), check for document quality
- **Low Answer Relevance**: Rephrase query, check if documents contain the answer

### Technical Implementation

The evaluation system uses **LLM-as-Judge** approach:
- Gemini 2.5 Flash (same LLM) evaluates its own responses
- Uses structured prompts to assess each dimension
- Temperature set to 0.1 for consistent scoring
- Parses verdicts and provides actionable feedback

**Files involved:**
- `rag_evaluator.py`: Core evaluation logic
- `rag_engine.py`: Integration with RAG pipeline  
- `main.py`: API endpoint support
- `script.js`: Frontend display logic
- `test_evaluation.py`: Automated testing

### Performance Note

Enabling evaluation **doubles the API calls** to Gemini (one for answer, one for evaluation). For production use with high traffic, consider:
- Sampling (evaluate 10% of queries)
- Batch evaluation during development/testing
- Caching evaluation results for similar queries


## Deployment

### Local Production

```bash
# Install production server
pip install gunicorn

# Run with 4 workers
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t rag-chatbot .
docker run -p 8000:8000 -v $(pwd)/data:/app/data -v $(pwd)/faiss_index:/app/faiss_index rag-chatbot
```

### Cloud Deployment

**Recommended Platforms**:
- **Railway.app**: Zero-config, auto-deploys from Git
- **Render**: Free tier, persistent storage
- **Fly.io**: Global edge deployment

**Important**: Add these to `.gitignore`:
```
.env
data/
faiss_index/
__pycache__/
```

## API Documentation

### Endpoints

#### `GET /`
Returns the main UI (HTML page)

#### `POST /upload`
Upload PDF documents

**Request**: `multipart/form-data`
```json
{
  "files": ["file1.pdf", "requirements.docx", "budget.xlsx"]
}
```

**Response**:
```json
{
  "message": "Successfully uploaded 2 files",
  "files": ["file1.pdf", "file2.pdf"]
}
```

#### `POST /ingest`
Process uploaded documents

**Request**:
```json
{
  "chunk_size": 1000,
  "chunk_overlap": 200
}
```

**Response**:
```json
{
  "message": "Successfully ingested 5 documents and created 326 chunks (Size: 1000, Overlap: 200)."
}
```

#### `POST /chat`
Ask a question

**Request**:
```json
{
  "message": "What is the project budget?",
  "top_k": 5,
  "temperature": 0.7,
  "evaluate": false
}
```

**Response (without evaluation)**:
```json
{
  "response": "The project budget is $500,000...",
  "sources": [
    {"file": "rfp_document.pdf", "page": 3},
    {"file": "rfp_document.pdf", "page": 5}
  ],
  "evaluation": null
}
```

**Response (with evaluation enabled)**:
```json
{
  "response": "The project budget is $500,000...",
  "sources": [
    {"file": "rfp_document.pdf", "page": 3},
    {"file": "rfp_document.pdf", "page": 5}
  ],
  "evaluation": {
    "overall_score": 0.85,
    "overall_verdict": "PASS",
    "metrics": {
      "context_relevance": {
        "score": 0.9,
        "verdict": "PASS"
      },
      "faithfulness": {
        "score": 0.8,
        "verdict": "FAITHFUL"
      },
      "answer_relevance": {
        "score": 0.85,
        "verdict": "RELEVANT"
      }
    },
    "recommendations": ["✅ All metrics performing well!"]
  }
}
```

#### `GET /files`
List uploaded documents

**Response**:
```json
{
  "files": ["rfp_document.pdf", "proposal.docx", "budget.xlsx"]
}
```

#### `DELETE /files/{filename}`
Delete a specific file

**Response**:
```json
{
  "message": "Successfully deleted file.pdf",
  "recommendation": "Please re-process documents to update the index"
}
```

## Security

### Best Practices

1. **Environment Variables**: Never commit `.env` to Git
   ```bash
   echo ".env" >> .gitignore
   ```

2. **API Key Protection**: Restrict your Google API key to your IP
   - Go to Google Cloud Console → Credentials
   - Add IP restrictions

3. **File Upload Limits**: Configured in `main.py`
   ```python
   # Add to FastAPI config
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:8000"],
       max_age=3600,
   )
   ```

4. **Input Validation**: Pydantic models validate all inputs
   - Chunk size: 100-2000
   - Temperature: 0.0-1.0
   - Top K: 1-10

5. **Production Hardening**:
   ```bash
   # Use HTTPS in production
   uvicorn main:app --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem
   ```

### Data Privacy

- ✅ **All processing is local** (except LLM API calls)
- ✅ **Documents stay on your machine**
- ✅ **Embeddings generated locally**
- ⚠️ **Queries sent to Google Gemini** (consider self-hosted LLM for sensitive data)

## Configuration

### Environment Variables

Create a `.env` file:

```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here

# Optional RAG Configuration
CHUNK_SIZE=1000              # Default chunk size
CHUNK_OVERLAP=200            # Default overlap
TOP_K_RESULTS=5              # Default retrieval count

# Optional Server Config
HOST=0.0.0.0
PORT=8000
WORKERS=4
```

### Advanced Configuration

Edit `rag_engine.py` to customize:

```python
# Change embedding model
self.embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"  # Better quality, slower
)

# Change LLM
self.llm = ChatGoogleGenerativeAI(
    model="gemini-pro",  # More capable, slower
    temperature=0.3
)

# Custom text splitters
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ". ", " ", ""],  # Customize separators
    chunk_size=1000,
    chunk_overlap=200
)
```

## Troubleshooting

### Common Issues

#### 1. **ModuleNotFoundError**
```
ModuleNotFoundError: No module named 'langchain'
```

**Solution**:
```bash
pip install -r requirements.txt
```

#### 2. **API Key Error**
```
Error: GOOGLE_API_KEY not found
```

**Solution**:
- Check `.env` file exists
- Verify API key is correct
- Restart server after editing `.env`

#### 3. **FAISS Index Not Found**
```
Index not found. Please upload documents and ingest them first.
```

**Solution**:
1. Upload PDFs via the UI
2. Click "Process Docs"
3. Wait for confirmation message

#### 4. **Out of Memory**
```
MemoryError: Unable to allocate array
```

**Solution**:
- Reduce chunk size (smaller chunks = less memory)
- Process fewer documents at once
- Increase system RAM

#### 5. **Slow Responses**
**Symptoms**: Queries take >10 seconds

**Solutions**:
- **Reduce Top K**: Try 3 instead of 5
- **Smaller Model**: Use `all-MiniLM-L6-v2` (default is already optimized)
- **Enable GPU**: Install `faiss-gpu` if you have CUDA

#### 6. **"Answer not available in context"**
**Symptoms**: Bot can't find answers in uploaded docs

**Solutions**:
- **Increase Chunk Size**: Try 1200-1500
- **Increase Top K**: Try 6-8
- **Check Document Quality**: Ensure PDFs have selectable text (not scanned images)
- **Lower Temperature**: Try 0.3 for more focused answers

### Debug Mode

Enable detailed logging:

```python
# Add to main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

View logs:
```bash
python -m uvicorn main:app --log-level debug
```

### Performance Optimization

1. **Embeddings Cache**: Already enabled (HuggingFace caches automatically)
2. **Persistent Index**: FAISS index saves to disk, no re-indexing needed
3. **Async Processing**: FastAPI handles concurrent requests efficiently

## Support

### Getting Help

1. **Check Documentation**:
   - [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup
   - This README - Architecture and troubleshooting

2. **Common Resources**:
   - [LangChain Docs](https://python.langchain.com/)
   - [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)
   - [FastAPI Docs](https://fastapi.tiangolo.com/)

3. **Debugging Steps**:
   - Check browser console (F12) for errors
   - Check terminal for server logs
   - Verify `.env` file configuration
   - Test with a single, small PDF first

### Contributing

Contributions welcome! Areas for improvement:
- [ ] Add support for Word documents (.docx)
- [ ] Implement batch processing for large document sets
- [ ] Add user authentication
- [ ] Export chat history
- [ ] Multi-language support
- [ ] Custom prompt templates

### License

MIT License - feel free to use in commercial projects.

---

## Changelog

### v1.1.0 (Current)
- ✅ **RAG Evaluation System**: Context Relevance, Faithfulness, Answer Relevance metrics
- ✅ **Visual Evaluation UI**: Color-coded progress bars and verdict badges
- ✅ **Test Script**: Automated evaluation testing with `test_evaluation.py`
- ✅ **LLM-as-Judge**: Uses Gemini for quality assessment
- ✅ Dynamic settings panel
- ✅ Source citations
- ✅ FAISS vector storage
- ✅ Gemini 2.5 Flash integration
- ✅ Dark theme UI

### v1.0.0
- ✅ Initial release with core RAG functionality
- ✅ PDF upload and processing
- ✅ Local embeddings and vector storage

### Roadmap

- 🚧 **v1.2**: Conversation history persistence and export
- 🚧 **v1.3**: Multi-user support with authentication
- 🚧 **v1.4**: Advanced RAG metrics (Noise Robustness, Information Synthesis)
- 🚧 **v2.0**: Self-hosted LLM option (Llama 3, Mistral)

---

**Built with ❤️ for RFP professionals**
