"""
ChromaDB Vector Store
======================
This module manages the persistent vector database using ChromaDB.
It handles storing document embeddings and performing similarity searches.

How it fits in the RAG pipeline:
  Embedding → [VECTOR STORE (storage)] → ...
  ... → Query Embedding → [VECTOR STORE (search)] → Retrieved Chunks → Answer

ChromaDB is an in-process vector database — no separate server needed.
It stores data to disk so embeddings survive between app restarts.
"""

import hashlib
import logging
import chromadb

from config import CHROMA_DB_DIR, COLLECTION_NAME, TOP_K

logger = logging.getLogger(__name__)

# Initialize the persistent ChromaDB client.
# PersistentClient saves data to the specified directory on disk.
# This means once you embed documents, you don't need to do it again.
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))


def get_or_create_collection():
    """
    Get the existing collection or create a new one.

    A collection in ChromaDB is like a table in a SQL database.
    All our document chunks, embeddings, and metadata go into
    a single collection.

    Returns:
        A ChromaDB Collection object.
    """
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Document Q&A Bot collection"}
    )
    logger.info(f"Collection '{COLLECTION_NAME}' ready with {collection.count()} documents")
    return collection


def add_documents(
    chunks: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
) -> int:
    """
    Add document chunks to the vector store.

    Each chunk is stored with:
      - Its text content (for retrieval and display)
      - Its embedding vector (for similarity search)
      - Metadata (source file name, chunk index) for citation

    We generate deterministic IDs based on content hash to prevent
    duplicate entries if the same document is ingested twice.

    Args:
        chunks: List of text chunks to store.
        embeddings: Corresponding embedding vectors for each chunk.
        metadatas: Metadata dicts for each chunk (e.g., {"source": "file.pdf", "chunk_index": 0}).

    Returns:
        The number of documents added.
    """
    collection = get_or_create_collection()

    # Generate deterministic IDs based on chunk content
    # This prevents duplicates — same text always gets the same ID
    ids = [
        hashlib.md5(chunk.encode()).hexdigest()
        for chunk in chunks
    ]

    # ChromaDB's add method handles everything in one call
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.info(f"Added {len(chunks)} chunks to the vector store")
    return len(chunks)


def query(query_embedding: list[float], n_results: int = TOP_K) -> dict:
    """
    Search the vector store for chunks most similar to the query.

    This is the core of semantic search. Given a query embedding
    (the user's question converted to a vector), we find the K
    stored chunks whose embeddings are closest to it.

    Args:
        query_embedding: The embedding vector of the user's question.
        n_results: Number of results to return (default from config).

    Returns:
        A dict with keys:
          - "documents": List of matching text chunks
          - "metadatas": List of metadata dicts for each match
          - "distances": List of distance scores (lower = more similar)
    """
    collection = get_or_create_collection()

    # Check if the collection has any documents
    if collection.count() == 0:
        logger.warning("Vector store is empty. Please ingest documents first.")
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    logger.info(f"Found {len(results['documents'][0])} matching chunks")
    return results


def get_collection_count() -> int:
    """Return the number of documents in the collection."""
    collection = get_or_create_collection()
    return collection.count()


def delete_collection():
    """
    Delete the entire collection.

    Use this when you want to re-ingest all documents from scratch.
    This is a destructive operation — all stored embeddings are lost.
    """
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
        logger.info(f"Deleted collection '{COLLECTION_NAME}'")
    except Exception as e:
        logger.warning(f"Could not delete collection: {e}")
