"""
Embedding Generator
====================
This module converts text into numerical vectors (embeddings)
using Google Gemini's text-embedding-004 model.

How it fits in the RAG pipeline:
  Documents → Text Extraction → Chunking → [EMBEDDING] → Storage

What are embeddings?
  An embedding is a list of numbers (a vector) that captures the
  *meaning* of a text. Similar texts produce similar vectors.
  This is what enables semantic search — finding text by meaning,
  not just keyword matching.

  Example: "I love dogs" and "I adore puppies" would have very
  similar embedding vectors even though they share no words.
"""

import logging
from google import genai
from tqdm import tqdm

from config import GOOGLE_API_KEY, EMBEDDING_MODEL, EMBEDDING_BATCH_SIZE

logger = logging.getLogger(__name__)

# Initialize the Google Gemini client once.
# This client is used for all embedding requests.
client = genai.Client(api_key=GOOGLE_API_KEY)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of text strings.

    This function processes texts in batches to:
      1. Stay within API rate limits
      2. Handle large document sets efficiently
      3. Show progress via a progress bar

    Args:
        texts: List of text strings to embed. Each string is typically
               a chunk from the chunking step.

    Returns:
        A list of embedding vectors. Each vector is a list of floats
        (768 numbers for text-embedding-004). The order matches the
        input texts — texts[i] corresponds to embeddings[i].

    Raises:
        Exception: If the API call fails after all retries.
    """
    if not texts:
        logger.warning("No texts provided for embedding")
        return []

    all_embeddings = []
    total_batches = (len(texts) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE

    logger.info(
        f"Generating embeddings for {len(texts)} texts "
        f"in {total_batches} batches"
    )

    # Process texts in batches with a progress bar
    for i in tqdm(range(0, len(texts), EMBEDDING_BATCH_SIZE),
                  desc="Generating embeddings",
                  total=total_batches):
        batch = texts[i : i + EMBEDDING_BATCH_SIZE]

        try:
            # Call the Gemini embedding API
            # The API accepts a list of texts and returns a list of embeddings
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
            )

            # Extract the embedding vectors from the response
            # Each item in response.embeddings has a .values attribute
            # which is the list of floats
            batch_embeddings = [embedding.values for embedding in response.embeddings]
            all_embeddings.extend(batch_embeddings)

        except Exception as e:
            logger.error(f"Failed to generate embeddings for batch {i}: {e}")
            raise

    logger.info(f"Generated {len(all_embeddings)} embeddings successfully")
    return all_embeddings


def generate_single_embedding(text: str) -> list[float]:
    """
    Generate an embedding for a single text string.

    This is a convenience function used primarily for embedding
    user queries during the retrieval step.

    Args:
        text: The text to embed (typically a user's question).

    Returns:
        A single embedding vector (list of 768 floats).
    """
    try:
        response = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        return response.embeddings[0].values

    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise
