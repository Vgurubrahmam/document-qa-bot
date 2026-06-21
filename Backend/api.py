"""
FastAPI REST API Layer
=======================
This module exposes the existing RAG backend as HTTP endpoints
so the React frontend can communicate with it.

This is a thin wrapper — no business logic is duplicated here.
Each endpoint calls the same functions used by the CLI (main.py).

Usage:
  uvicorn api:app --reload --port 8000

Endpoints:
  POST /api/upload   - Upload documents to data/ folder
  POST /api/ingest   - Trigger document ingestion pipeline
  POST /api/query    - Ask a question about ingested documents
  GET  /api/status   - Get database status (document count, files)
  POST /api/reset    - Clear the vector database
"""

import logging
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import DATA_DIR, SUPPORTED_EXTENSIONS, RELEVANCE_THRESHOLD
from document_processor.extractor import extract_text
from document_processor.chunker import chunk_text
from embeddings.generator import generate_embeddings, generate_single_embedding
from vector_store.chroma_store import (
    add_documents,
    query,
    get_collection_count,
    delete_collection,
)
from rag.answer_engine import generate_answer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --- FastAPI App ---
app = FastAPI(
    title="Document Q&A Bot API",
    description="RAG-powered document question answering API",
    version="1.0.0",
)

# Enable CORS so the React frontend (on port 5173) can call the API (on port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---
class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    question: str


class StatusResponse(BaseModel):
    document_count: int
    files: list[str]


class MessageResponse(BaseModel):
    message: str


# --- Endpoints ---

@app.get("/")
async def root():
    """Root endpoint returning API status."""
    return {
        "status": "online",
        "message": "Document Q&A Bot API is running. Visit /docs for Swagger interactive documentation."
    }


@app.post("/api/upload", response_model=MessageResponse)
async def upload_documents(files: list[UploadFile] = File(...)):
    """
    Upload one or more documents to the data/ directory.
    Accepts PDF, DOCX, and TXT files.
    """
    uploaded = []

    for file in files:
        # Validate file extension
        suffix = Path(file.filename).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: '{suffix}'. Supported: {SUPPORTED_EXTENSIONS}"
            )

        # Save the file to the data/ directory
        file_path = DATA_DIR / file.filename
        try:
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            uploaded.append(file.filename)
            logger.info(f"Uploaded: {file.filename}")
        except Exception as e:
            logger.error(f"Failed to save {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save {file.filename}")

    return {"message": f"Uploaded {len(uploaded)} file(s): {', '.join(uploaded)}"}


@app.post("/api/ingest", response_model=MessageResponse)
async def ingest_documents():
    """
    Process all documents in the data/ folder:
    extract text → chunk → embed → store in ChromaDB.
    """
    # Find all supported files
    files = [
        f for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        raise HTTPException(
            status_code=400,
            detail="No supported documents found in data/ folder."
        )

    all_chunks = []
    all_metadatas = []

    # Extract and chunk each document
    for file_path in files:
        try:
            text = extract_text(str(file_path))
            if not text.strip():
                continue

            chunks = chunk_text(text)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadatas.append({
                    "source": file_path.name,
                    "chunk_index": i,
                })
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            continue

    if not all_chunks:
        raise HTTPException(status_code=400, detail="No text extracted from any documents.")

    # Generate embeddings and store in ChromaDB
    try:
        embeddings = generate_embeddings(all_chunks)
        count = add_documents(all_chunks, embeddings, all_metadatas)
        total = get_collection_count()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion pipeline failed. Check if GOOGLE_API_KEY environment variable is set correctly. Error: {str(e)}"
        )

    return {
        "message": f"Ingestion complete. Processed {len(files)} file(s), "
                   f"created {count} chunks. Total in database: {total}."
    }


@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Answer a question using the RAG pipeline:
    embed question → search ChromaDB → generate answer with Gemini.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Check if documents have been ingested
    count = get_collection_count()
    if count == 0:
        raise HTTPException(
            status_code=400,
            detail="No documents in the database. Please ingest documents first."
        )

    # Embed the question
    try:
        question_embedding = generate_single_embedding(question)
    except Exception as e:
        logger.error(f"Failed to generate embedding for query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate embedding for query. Check API key configuration. Error: {str(e)}"
        )

    # Search for similar chunks
    results = query(question_embedding)

    # Extract retrieved chunks
    retrieved_chunks = []
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        retrieved_chunks.append({
            "text": doc,
            "source": meta.get("source", "Unknown"),
            "chunk_index": meta.get("chunk_index", "N/A"),
            "distance": dist,
        })

    # Relevance check — skip LLM if all chunks are too distant
    if retrieved_chunks:
        best_distance = min(chunk["distance"] for chunk in retrieved_chunks)
        if best_distance > RELEVANCE_THRESHOLD:
            return {
                "answer": "I don't have enough information in the provided documents to answer this question.",
                "sources": [],
                "question": question,
            }

    # Generate answer
    try:
        result = generate_answer(question, retrieved_chunks)
    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Answer generation failed. Check API key configuration. Error: {str(e)}"
        )

    # Filter to only cited sources
    answer_text = result["answer"]
    cited_sources = [
        source for source in result["sources"]
        if f"[Source {source['source_number']}]" in answer_text
    ]

    return {
        "answer": result["answer"],
        "sources": cited_sources,
        "question": question,
    }


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get the current status of the vector database and uploaded files."""
    count = get_collection_count()

    # List files in data/ directory
    files = [
        f.name for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    return {
        "document_count": count,
        "files": files,
    }


@app.post("/api/reset", response_model=MessageResponse)
async def reset_database():
    """Clear the vector database and remove all uploaded files."""
    delete_collection()

    # Also remove files from data/ directory
    for f in DATA_DIR.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            f.unlink()

    return {"message": "Database cleared and all documents removed."}
