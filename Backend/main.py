"""
Document Q&A Bot — Main Entry Point
=====================================
This is the CLI interface that orchestrates the entire RAG pipeline.

Three modes of operation:
  1. INGEST: Process documents → Extract text → Chunk → Embed → Store in ChromaDB
  2. QUERY:  Ask a single question → Retrieve context → Generate answer
  3. CHAT:   Interactive Q&A loop for continuous conversation

Usage:
  python main.py ingest              # Ingest all documents from data/ folder
  python main.py query "question"    # Ask a single question
  python main.py chat                # Start interactive Q&A session
"""

import argparse
import logging
import sys
from pathlib import Path

from tqdm import tqdm

from config import DATA_DIR, SUPPORTED_EXTENSIONS, RELEVANCE_THRESHOLD
from document_processor.extractor import extract_text
from document_processor.chunker import chunk_text
from embeddings.generator import generate_embeddings
from vector_store.chroma_store import (
    add_documents,
    query,
    get_collection_count,
    delete_collection,
)
from rag.answer_engine import generate_answer
from embeddings.generator import generate_single_embedding

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def ingest_documents():
    """
    Ingest all supported documents from the data/ directory.

    This runs the first half of the RAG pipeline:
      1. Scan data/ for PDF, DOCX, TXT files
      2. Extract text from each file
      3. Split text into overlapping chunks
      4. Generate embeddings for all chunks
      5. Store chunks + embeddings in ChromaDB

    After ingestion, the documents are searchable via the query command.
    """
    # Find all supported files in the data directory
    files = [
        f for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        print(f"\n❌ No supported documents found in '{DATA_DIR}'")
        print(f"   Supported formats: {SUPPORTED_EXTENSIONS}")
        print(f"   Please add PDF, DOCX, or TXT files and try again.")
        return

    print(f"\n📁 Found {len(files)} document(s) to process:")
    for f in files:
        print(f"   • {f.name}")
    print()

    all_chunks = []
    all_metadatas = []

    # Step 1 & 2: Extract text and chunk each document
    for file_path in tqdm(files, desc="Processing documents"):
        try:
            # Extract raw text from the document
            text = extract_text(str(file_path))

            if not text.strip():
                logger.warning(f"No text extracted from {file_path.name}, skipping")
                continue

            # Split text into overlapping chunks
            chunks = chunk_text(text)

            # Create metadata for each chunk (needed for source citation later)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_metadatas.append({
                    "source": file_path.name,
                    "chunk_index": i,
                })

            logger.info(f"Processed {file_path.name}: {len(chunks)} chunks")

        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            print(f"   ⚠️ Error processing {file_path.name}: {e}")
            continue

    if not all_chunks:
        print("\n❌ No text was extracted from any documents.")
        return

    # Step 3: Generate embeddings for all chunks
    print(f"\n🔢 Generating embeddings for {len(all_chunks)} chunks...")
    embeddings = generate_embeddings(all_chunks)

    # Step 4: Store in ChromaDB
    print(f"\n💾 Storing in vector database...")
    count = add_documents(all_chunks, embeddings, all_metadatas)

    total = get_collection_count()
    print(f"\n✅ Ingestion complete!")
    print(f"   • Processed: {len(files)} document(s)")
    print(f"   • Created: {count} chunks")
    print(f"   • Total in database: {total} chunks")


def query_documents(question: str):
    """
    Answer a question using the RAG pipeline.

    This runs the second half of the RAG pipeline:
      1. Check if documents have been ingested
      2. Embed the user's question
      3. Search ChromaDB for similar chunks
      4. Build a prompt with context and question
      5. Generate an answer with Gemini
      6. Display the answer with source citations

    Args:
        question: The user's question about the ingested documents.
    """
    # Check if there are any documents in the vector store
    count = get_collection_count()
    if count == 0:
        print("\n❌ No documents in the database.")
        print("   Run 'python main.py ingest' first to add documents.")
        return

    print(f"\n🔍 Searching through {count} document chunks...")

    # Step 1: Embed the question (convert it to a vector)
    question_embedding = generate_single_embedding(question)

    # Step 2: Search for similar chunks in ChromaDB
    results = query(question_embedding)

    # Extract the retrieved chunks with their metadata
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

    if not retrieved_chunks:
        print("\n❌ No relevant documents found for your question.")
        return

    # Check if the retrieved chunks are actually relevant.
    # If the best match (lowest distance) is still above the threshold,
    # the question is likely out of scope — skip the expensive LLM call.
    best_distance = min(chunk["distance"] for chunk in retrieved_chunks)
    if best_distance > RELEVANCE_THRESHOLD:
        logger.info(
            f"Best distance ({best_distance:.2f}) exceeds threshold "
            f"({RELEVANCE_THRESHOLD}). Skipping LLM call."
        )
        print("=" * 60)
        print("📝 ANSWER")
        print("=" * 60)
        print(
            "I don't have enough information in the provided documents "
            "to answer this question."
        )
        print()
        print("💡 Tip: This question may be outside the scope of your ingested documents.")
        print()
        return

    # Step 3: Generate answer using the retrieved context
    print("🤖 Generating answer...\n")
    result = generate_answer(question, retrieved_chunks)

    # Display the answer
    print("=" * 60)
    print("📝 ANSWER")
    print("=" * 60)
    print(result["answer"])
    print()

    # Only display sources if the bot actually used them to answer.
    # If the bot says it doesn't have enough info, showing sources is misleading.
    answer_text = result["answer"]
    answer_lower = answer_text.lower()
    no_info_phrases = [
        "don't have enough information",
        "do not have enough information",
        "cannot answer",
        "not enough information",
        "no relevant information",
    ]
    has_answer = not any(phrase in answer_lower for phrase in no_info_phrases)

    if has_answer:
        # Filter to only sources actually cited in the answer text.
        # The LLM cites as [Source 1], [Source 2], etc.
        # We only show sources that appear in the answer.
        cited_sources = [
            source for source in result["sources"]
            if f"[Source {source['source_number']}]" in answer_text
        ]

        if cited_sources:
            print("-" * 60)
            print("📚 SOURCES CITED")
            print("-" * 60)
            for source in cited_sources:
                print(
                    f"   [Source {source['source_number']}] "
                    f"{source['file']} (chunk {source['chunk_index']})"
                )
        print()
    else:
        print("💡 Tip: This question may be outside the scope of your ingested documents.")
        print()


def chat_mode():
    """
    Start an interactive Q&A session.

    The user can ask multiple questions in a loop.
    Type 'quit', 'exit', or 'q' to stop.
    """
    count = get_collection_count()
    if count == 0:
        print("\n❌ No documents in the database.")
        print("   Run 'python main.py ingest' first to add documents.")
        return

    print("\n" + "=" * 60)
    print("💬 DOCUMENT Q&A CHAT")
    print("=" * 60)
    print(f"📚 {count} document chunks loaded and ready.")
    print("Type your questions below. Type 'quit' to exit.\n")

    while True:
        try:
            question = input("You: ").strip()

            if not question:
                continue

            if question.lower() in ("quit", "exit", "q"):
                print("\n👋 Goodbye!")
                break

            query_documents(question)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            # Catch API errors (503, rate limits, etc.) so the chat doesn't crash
            print(f"\n⚠️ Error: {e}")
            print("   Please try again in a moment.\n")


def main():
    """Parse command line arguments and run the appropriate command."""
    parser = argparse.ArgumentParser(
        description="Document Q&A Bot — RAG-powered document question answering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py ingest              Process all documents in data/ folder
  python main.py query "question"    Ask a single question
  python main.py chat                Start interactive Q&A session
  python main.py reset               Clear the vector database
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ingest command
    subparsers.add_parser("ingest", help="Ingest documents from the data/ folder")

    # Query command
    query_parser = subparsers.add_parser("query", help="Ask a single question")
    query_parser.add_argument("question", type=str, help="Your question about the documents")

    # Chat command
    subparsers.add_parser("chat", help="Start interactive Q&A session")

    # Reset command
    subparsers.add_parser("reset", help="Clear the vector database")

    args = parser.parse_args()

    if args.command == "ingest":
        ingest_documents()
    elif args.command == "query":
        query_documents(args.question)
    elif args.command == "chat":
        chat_mode()
    elif args.command == "reset":
        delete_collection()
        print("✅ Vector database cleared.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
