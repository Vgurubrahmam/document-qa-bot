"""
Answer Engine
==============
This module generates answers to user questions using Google Gemini,
grounded in the context retrieved from the vector store.

How it fits in the RAG pipeline:
  Retrieved Chunks → Prompt Construction → [ANSWER GENERATION] → Cited Answer

This is the final step of the pipeline — where everything comes together.
The LLM receives the carefully constructed prompt (with context and
anti-hallucination instructions) and generates a grounded answer.
"""

import logging
from google import genai
from google.genai import types

from config import (
    GOOGLE_API_KEY,
    GENERATION_MODEL,
    GENERATION_TEMPERATURE,
    MAX_OUTPUT_TOKENS,
)
from rag.prompt_builder import build_prompt, get_system_instruction

logger = logging.getLogger(__name__)

# Initialize the Gemini client
client = genai.Client(api_key=GOOGLE_API_KEY)


def generate_answer(question: str, retrieved_chunks: list[dict]) -> dict:
    """
    Generate an answer to a question using retrieved document context.

    This function:
      1. Takes the retrieved chunks and formats them into a prompt
      2. Sends the prompt to Gemini with anti-hallucination system instructions
      3. Returns the answer along with source information

    Args:
        question: The user's question.
        retrieved_chunks: List of dicts with keys "text", "source", "chunk_index".
                         These are the relevant chunks found by similarity search.

    Returns:
        A dict with:
          - "answer": The generated answer text
          - "sources": List of source dicts used for the answer
          - "question": The original question (for reference)
    """
    # Build the prompt with context and question
    prompt = build_prompt(question, retrieved_chunks)

    try:
        # Call the Gemini API with configured parameters
        response = client.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=get_system_instruction(),
                temperature=GENERATION_TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            ),
        )

        answer_text = response.text
        logger.info("Answer generated successfully")

        # Build the source list for citation reference
        sources = []
        for i, chunk in enumerate(retrieved_chunks, start=1):
            sources.append({
                "source_number": i,
                "file": chunk.get("source", "Unknown"),
                "chunk_index": chunk.get("chunk_index", "N/A"),
            })

        return {
            "answer": answer_text,
            "sources": sources,
            "question": question,
        }

    except Exception as e:
        logger.error(f"Failed to generate answer: {e}")
        raise
