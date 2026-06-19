"""
Centralized Configuration Module
=================================
This module is the single source of truth for all project settings.
Every other module imports its configuration from here, which means:
  - No magic numbers scattered across the codebase
  - Change a setting once, and it takes effect everywhere
  - Environment variables are loaded and validated in one place
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# We use an explicit path so it works regardless of where you run the command from.
# Path(__file__).parent resolves to the Backend/ directory where config.py lives.
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

# --- API Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Validate that the API key is set
# We check at import time so the app fails fast with a clear message
# instead of crashing deep inside an API call.
if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY is not set. "
        "Please create a .env file with your API key. "
        "See .env.example for the template."
    )

# --- Path Configuration ---
# Using pathlib.Path for cross-platform compatibility
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DB_DIR.mkdir(exist_ok=True)

# --- Chunking Configuration ---
# Chunk size in characters. 1000 chars ≈ 150-200 words.
# This balances granularity (small enough to be specific)
# vs. context (large enough to contain complete ideas).
CHUNK_SIZE = 1000

# Overlap between consecutive chunks in characters.
# 200 chars = 20% overlap. This ensures information at
# chunk boundaries doesn't get lost during retrieval.
CHUNK_OVERLAP = 200

# --- Model Configuration ---
# Embedding model: converts text into numerical vectors
EMBEDDING_MODEL = "gemini-embedding-001"

# Generation model: generates natural language answers
GENERATION_MODEL = "gemini-2.5-flash"

# --- Retrieval Configuration ---
# ChromaDB collection name (like a "table" in a database)
COLLECTION_NAME = "document_qa_collection"

# Number of most-similar chunks to retrieve per query
TOP_K = 5

# --- Generation Configuration ---
# Temperature controls randomness. Lower = more deterministic/factual.
# For RAG, we want factual answers, not creative ones.
GENERATION_TEMPERATURE = 0.3

# Maximum tokens in the generated response
MAX_OUTPUT_TOKENS = 2048

# --- Embedding Batch Configuration ---
# Number of texts to embed in a single API call.
# Keeps API calls manageable and avoids rate limits.
EMBEDDING_BATCH_SIZE = 100

# --- Supported File Types ---
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# --- Relevance Threshold ---
# ChromaDB returns cosine distances (lower = more similar).
# If ALL retrieved chunks have a distance above this threshold,
# we skip the expensive LLM call and respond immediately that
# the question is out of scope. This saves ~90s on irrelevant queries.
# Calibrated from real data:
#   In-scope queries  → best distance ~0.55
#   Out-of-scope      → best distance ~0.97
RELEVANCE_THRESHOLD = 0.85
