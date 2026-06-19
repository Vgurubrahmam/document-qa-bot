# 📄 Document Q&A Bot — RAG Backend

A production-grade **Retrieval-Augmented Generation (RAG)** system that answers questions about your documents using semantic search and Google Gemini.

This backend provides both a **CLI interface** for local experimentation and a **FastAPI REST API** to connect with modern frontend clients (such as the React + Vite frontend).

---

## ✨ Features

- **REST API & CLI Interface** — Run queries in the command line or serve them over HTTP for a web app.
- **Multi-format support** — Ingest PDF, DOCX, and TXT documents.
- **Semantic search** — Finds relevant content by meaning, not just keywords, using ChromaDB.
- **Grounded answers** — Responses are based strictly on your documents to prevent LLM hallucinations.
- **Source citations** — Every answer includes `[Source X]` references mapped to specific document chunks.
- **Persistent storage** — Embeddings are stored in ChromaDB and persist across application restarts.
- **CORS Enabled** — Ready-to-go integration with frontend applications.

---

## 🏗️ Architecture

```
                        ┌─────────────────────────────────────────────┐
                        │              INGESTION PIPELINE             │
                        │                                             │
  ┌──────────┐     ┌────┴─────┐     ┌──────────┐     ┌────────────┐  │
  │ PDF/DOCX │────▶│   Text   │────▶│  Text    │────▶│ Embedding  │  │
  │   /TXT   │     │Extraction│     │ Chunking │     │ Generation │  │
  └──────────┘     └──────────┘     └──────────┘     └──────┬─────┘  │
                                                            │        │
                                                     ┌──────▼─────┐  │
                                                     │  ChromaDB  │  │
                                                     │  (Vector   │  │
                                                     │   Store)   │  │
                                                     └──────┬─────┘  │
                        └──────────────────────────────────┼────────┘
                                                            │
  ┌─────────────────────────────────────────────────────────┼────────┐
  │                     QUERY / API PIPELINE                │        │
  │                                                         │        │
  │   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──▼───┐    │
  │   │  React   │────▶│ FastAPI  │────▶│Similarity│────▶│Prompt│    │
  │   │ Frontend │     │  Server  │     │  Search  │     │Builder│    │
  │   └──────────┘     └────┬─────┘     └──────────┘     └───┬──┘    │
  │                         │                                │       │
  │                         │                         ┌──────▼─────┐ │
  │                         │                         │   Gemini   │ │
  │                         └────────────────────────▶│  2.5 Flash │ │
  │                                                   └──────┬─────┘ │
  │                                                          │       │
  │                                                   ┌──────▼─────┐ │
  │                                                   │   Cited    │ │
  │                                                   │   Answer   │ │
  │                                                   └────────────┘ │
  └──────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Backend/
├── .env.example              # API key template (copy to .env)
├── .gitignore                # Files excluded from version control
├── requirements.txt          # Python dependencies
├── config.py                 # Centralized configuration & constants
├── api.py                    # FastAPI web server endpoint handlers
├── main.py                   # CLI entry point (ingest / query / chat / reset)
│
├── document_processor/       # Document ingestion layer
│   ├── __init__.py
│   ├── extractor.py          # PDF, DOCX, TXT → raw text
│   └── chunker.py            # Raw text → overlapping chunks
│
├── embeddings/               # Embedding layer
│   ├── __init__.py
│   └── generator.py          # Text → 768-dim vectors (Gemini API)
│
├── vector_store/             # Storage & retrieval layer
│   ├── __init__.py
│   └── chroma_store.py       # ChromaDB persistence & similarity search
│
├── rag/                      # Generation layer
│   ├── __init__.py
│   ├── prompt_builder.py     # Prompt templates & anti-hallucination rules
│   └── answer_engine.py      # Gemini answer generation with citations
│
├── data/                     # Source documents directory (git-ignored)
└── chroma_db/                # Vector database storage (git-ignored)
```

---

## 🛠️ Tech Stack

| Component            | Technology                | Purpose                                   |
|----------------------|---------------------------|-------------------------------------------|
| Language             | Python 3.11+              | Core runtime                              |
| Framework            | FastAPI                   | REST API server framework                 |
| ASGI Server          | Uvicorn                   | High-performance web server               |
| Embedding Model      | Gemini `text-embedding-004` | Converts text to 768-dim semantic vectors |
| Generation Model     | Gemini `gemini-2.5-flash` | Generates natural language answers        |
| Vector Database      | ChromaDB                  | Persistent storage & similarity search    |
| PDF Extraction       | `pypdf`                   | Reads PDF documents                       |
| DOCX Extraction      | `python-docx`             | Reads Word documents                      |
| Environment Config   | `python-dotenv`           | Secure API key management                 |
| Progress Bars        | `tqdm`                    | Visual progress during ingestion          |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11 or 3.12** — Check with `python --version` or `py --version`
- **Google Gemini API Key** — Obtain from [Google AI Studio](https://aistudio.google.com/apikey)

### 1. Clone & Navigate

```bash
cd document-qa-bot/Backend
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

```bash
# Copy the template
cp .env.example .env
```

Open `.env` in your editor and replace `your_api_key_here` with your actual Gemini API key:

```env
GOOGLE_API_KEY=your_actual_api_key_here
```

> ⚠️ **Never commit your `.env` file to Git.** It is already listed in `.gitignore`.

### 5. Add Initial Documents

Place your PDF, DOCX, or TXT files into the `data/` folder:

```
Backend/
  └── data/
      ├── research_paper.pdf
      ├── company_policy.docx
      └── meeting_notes.txt
```

---

## 💻 Running the API Server

Start the FastAPI application locally using Uvicorn:

```bash
# Run server using virtual environment's python or globally
uvicorn api:app --reload --port 8000
```

- **API Documentation**: Interactive documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (Swagger UI).
- **Default Port**: `8000` (can be changed via `--port`).

---

## 📖 API Reference

### 1. Get System Status
- **URL**: `/api/status`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "document_count": 9,
    "files": ["company_handbook.pdf", "product_spec.docx"]
  }
  ```

### 2. Upload Documents
- **URL**: `/api/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Payload**: Form field `files` containing binary document files.
- **Response**:
  ```json
  {
    "message": "Uploaded 2 file(s): handbook.pdf, readme.txt"
  }
  ```

### 3. Ingest Documents
- **URL**: `/api/ingest`
- **Method**: `POST`
- **Response**:
  ```json
  {
    "message": "Ingestion complete. Processed 2 file(s), created 35 chunks. Total in database: 35."
  }
  ```

### 4. Ask a Question
- **URL**: `/api/query`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "question": "What is the return policy?"
  }
  ```
- **Response**:
  ```json
  {
    "answer": "The return policy is 30 days with receipt [Source 1]. Items must be in original packaging [Source 2].",
    "sources": [
      {
        "text": "Our return policy allows refunds within 30 days of purchase with a receipt...",
        "source": "handbook.pdf",
        "chunk_index": 4,
        "distance": 0.354,
        "source_number": 1
      },
      {
        "text": "All items returned must be in their original packaging and unused...",
        "source": "handbook.pdf",
        "chunk_index": 5,
        "distance": 0.412,
        "source_number": 2
      }
    ],
    "question": "What is the return policy?"
  }
  ```

### 5. Reset Database
- **URL**: `/api/reset`
- **Method**: `POST`
- **Response**:
  ```json
  {
    "message": "Database cleared and all documents removed."
  }
  ```

---

## 🖥️ CLI Usage

Alternatively, you can run and manage the RAG system directly from the terminal without starting the web server.

### Ingest Documents
```bash
python main.py ingest
```

### Ask a Single Question
```bash
python main.py query "What are the key findings?"
```

### Interactive Chat Mode
```bash
python main.py chat
```

### Reset Database
```bash
python main.py reset
```

---

## ⚙️ Configuration

All settings are centralized in [`config.py`](config.py). Key parameters:

| Parameter              | Default         | Description                                          |
|------------------------|-----------------|------------------------------------------------------|
| `CHUNK_SIZE`           | `1000`          | Characters per chunk (~150–200 words)                |
| `CHUNK_OVERLAP`        | `200`           | Overlapping characters between chunks (20%)          |
| `EMBEDDING_MODEL`      | `text-embedding-004` | Google embedding model                          |
| `GENERATION_MODEL`     | `gemini-2.5-flash`   | Google generation model                         |
| `TOP_K`                | `5`             | Number of chunks retrieved per query                 |
| `RELEVANCE_THRESHOLD`  | `0.7`           | Distance threshold (lower is more strictly relevant) |
| `GENERATION_TEMPERATURE` | `0.3`         | Lower = more factual, higher = more creative         |
| `MAX_OUTPUT_TOKENS`    | `2048`          | Maximum length of generated answers                  |

---

## 📋 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'pypdf'` or `'docx'` | You may be running `uvicorn` using a different Python installation than where you ran `pip install`. Use `py -3.12 -m uvicorn api:app --reload --port 8000` or make sure your virtual environment is active. |
| `ValueError: GOOGLE_API_KEY is not set` | Create a `.env` file with your API key in the `Backend` directory. See [Configure API Key](#4-configure-api-key). |
| `No supported documents found` | Place PDF, DOCX, or TXT files in the `Backend/data/` folder. |
| `No documents in the database` | Run `python main.py ingest` or hit `/api/ingest` before querying. |
| CORS Errors in Frontend | Ensure `api.py` includes `CORSMiddleware` with `allow_origins=["*"]` (or the frontend origin). |
| ChromaDB errors after code changes | Delete the `Backend/chroma_db/` folder or run `python main.py reset` to start fresh. |

---

## 📄 License

This project is for educational purposes as part of a RAG learning exercise.
