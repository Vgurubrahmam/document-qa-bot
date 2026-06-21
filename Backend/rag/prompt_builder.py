"""
Prompt Builder
===============
This module constructs the prompts sent to the Gemini LLM.

How it fits in the RAG pipeline:
  Retrieved Chunks → [PROMPT CONSTRUCTION] → LLM → Answer

The prompt is the most critical part of preventing hallucinations.
It explicitly tells the LLM:
  1. Only answer based on the provided context
  2. Cite sources for every claim
  3. Admit when it doesn't have enough information

A well-crafted prompt is the difference between a reliable Q&A bot
and one that confidently makes up incorrect answers.
"""

import logging

logger = logging.getLogger(__name__)

# The system instruction that governs the LLM's behavior.
# This is the "personality" and "rules" of the Q&A bot.
SYSTEM_INSTRUCTION = """You are a helpful document Q&A assistant. Your job is to answer
questions based ONLY on the provided context from documents.

Present all answers in a clean, modern, and highly readable format optimized for web and mobile interfaces.

RESPONSE STRUCTURE GUIDELINES:
Your response MUST be organized using the following Markdown sections:

### Answer
Provide a concise, direct response (1-3 sentences max).

### Explanation
Expand on the answer using the retrieved context. Keep paragraphs short (2-5 lines). Use bold text only for critical terms and concepts.

### Key Points
Summarize important takeaways, features, steps, or terminology using bullet points. Avoid dense prose.

### Sources
List the supporting source citations used in the response (e.g., "[Source 1]", "[Source 2]") in a separate list. Do not append citations after every single sentence in the text; instead, group them naturally at the end of related sections or list them here.

STRICT RAG RULES:
1. Answer ONLY based on the provided context. Do NOT use any outside knowledge.
2. If the context does not contain enough information to answer the question,
   say: "I don't have enough information in the provided documents to answer this question." under the "### Answer" section, and omit the other sections.
3. Cite your sources using [Source X] notation, where X is the source number shown in the context.
4. If multiple sources support your answer, list all of them under "### Sources".
"""


def build_prompt(question: str, retrieved_chunks: list[dict]) -> str:
    """
    Construct the full prompt to send to the LLM.

    The prompt has three parts:
      1. Context section: The retrieved document chunks, numbered for citation
      2. Question section: The user's question
      3. Instruction: Reminder to format using the standard response structure

    Args:
        question: The user's question.
        retrieved_chunks: List of dicts, each containing:
            - "text": The chunk text
            - "source": Source file name
            - "chunk_index": Index of the chunk within the source

    Returns:
        The complete prompt string ready to send to the LLM.
    """
    if not retrieved_chunks:
        logger.warning("No context chunks provided for prompt construction")
        return (
            f"Question: {question}\n\n"
            "No relevant documents were found. Please respond that you "
            "don't have enough information to answer."
        )

    # Build the context section with numbered sources
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        source = chunk.get("source", "Unknown")
        context_parts.append(
            f"[Source {i}] (From: {source})\n"
            f"{chunk['text']}\n"
        )

    context_section = "\n---\n".join(context_parts)

    # Assemble the full prompt
    prompt = (
        f"CONTEXT FROM DOCUMENTS:\n"
        f"{'=' * 40}\n"
        f"{context_section}\n"
        f"{'=' * 40}\n\n"
        f"QUESTION: {question}\n\n"
        f"Please answer the question based ONLY on the context above. "
        f"Format your response with the standard headings: '### Answer', '### Explanation', '### Key Points', and '### Sources'."
    )

    logger.info(f"Built prompt with {len(retrieved_chunks)} context chunks")
    return prompt


def get_system_instruction() -> str:
    """Return the system instruction for the LLM."""
    return SYSTEM_INSTRUCTION
