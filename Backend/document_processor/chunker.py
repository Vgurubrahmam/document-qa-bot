"""
Text Chunker
=============
This module splits large text documents into smaller, overlapping chunks.

How it fits in the RAG pipeline:
  Documents → Text Extraction → [CHUNKING] → Embedding → Storage

Why chunking is necessary:
  1. Embedding models have input size limits
  2. Smaller chunks = more precise retrieval
  3. The LLM gets focused context instead of entire documents

Overlap between chunks prevents information loss at boundaries.
"""

import logging
from config import CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks while respecting word boundaries.

    The algorithm:
      1. Start at position 0
      2. Take `chunk_size` characters forward
      3. If that lands in the middle of a word, back up to the last space
      4. Save that chunk
      5. Move forward by (chunk_size - chunk_overlap) characters
      6. Repeat until we've consumed all the text

    Args:
        text: The full text to split into chunks.
        chunk_size: Maximum number of characters per chunk (default from config).
        chunk_overlap: Number of overlapping characters between consecutive chunks.

    Returns:
        A list of text chunks. Empty chunks are filtered out.

    Example:
        >>> text = "The quick brown fox jumps over the lazy dog."
        >>> chunks = chunk_text(text, chunk_size=20, chunk_overlap=5)
        >>> # Each chunk will be ~20 chars with ~5 chars shared with the next
    """
    # Validate inputs
    if not text or not text.strip():
        logger.warning("Empty text provided for chunking")
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) must be smaller than "
            f"chunk_size ({chunk_size})"
        )

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate the end position for this chunk
        end = start + chunk_size

        # If the end goes past the text, just take what's left
        if end >= text_length:
            chunk = text[start:].strip()
            if chunk:
                chunks.append(chunk)
            break

        # Try to find a word boundary (space) near the end
        # We look backwards from `end` to avoid splitting a word
        # Only look back within a reasonable range (last 20% of chunk)
        boundary_search_start = end - (chunk_size // 5)
        last_space = text.rfind(" ", boundary_search_start, end)

        if last_space > start:
            # Found a space — cut at the word boundary
            end = last_space

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move forward by (chunk_size - overlap) characters
        # This creates the overlap between consecutive chunks
        start += chunk_size - chunk_overlap

    logger.info(f"Split text into {len(chunks)} chunks (chunk_size={chunk_size}, overlap={chunk_overlap})")
    return chunks
