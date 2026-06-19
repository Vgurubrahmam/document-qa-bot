"""
Document Text Extractor
========================
This module handles extracting raw text from different document formats.
It supports PDF, DOCX, and TXT files.

How it fits in the RAG pipeline:
  Documents → [TEXT EXTRACTION] → Raw Text → Chunking → Embedding → Storage

This is the first step — we need raw text before we can do anything else.
"""

import logging
from pathlib import Path

from pypdf import PdfReader
from docx import Document

from config import SUPPORTED_EXTENSIONS

# Set up logging for this module
logger = logging.getLogger(__name__)


def extract_text(file_path: str) -> str:
    """
    Extract text content from a document file.

    This function detects the file type by its extension and calls
    the appropriate extraction method. It acts as a single entry point
    for all supported document formats.

    Args:
        file_path: Path to the document file (PDF, DOCX, or TXT).

    Returns:
        The extracted text as a single string.

    Raises:
        ValueError: If the file type is not supported.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get the file extension (e.g., ".pdf") and check if we support it
    extension = path.suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: '{extension}'. "
            f"Supported types: {SUPPORTED_EXTENSIONS}"
        )

    logger.info(f"Extracting text from: {path.name}")

    # Dispatch to the correct extraction function based on file type
    if extension == ".pdf":
        return _extract_from_pdf(path)
    elif extension == ".docx":
        return _extract_from_docx(path)
    elif extension == ".txt":
        return _extract_from_txt(path)


def _extract_from_pdf(file_path: Path) -> str:
    """
    Extract text from a PDF file using pypdf.

    pypdf reads the PDF page by page. We concatenate all pages
    with newlines between them to preserve some document structure.

    Args:
        file_path: Path to the PDF file.

    Returns:
        All text from the PDF as a single string.
    """
    try:
        reader = PdfReader(str(file_path))
        text_parts = []

        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
            else:
                logger.warning(
                    f"No text extracted from page {page_number} of {file_path.name}. "
                    "This page might contain only images."
                )

        full_text = "\n".join(text_parts)
        logger.info(
            f"Extracted {len(full_text)} characters from {len(reader.pages)} pages"
        )
        return full_text

    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise


def _extract_from_docx(file_path: Path) -> str:
    """
    Extract text from a DOCX (Word) file using python-docx.

    DOCX files store text in paragraphs. We join all paragraph
    texts with newlines to maintain the document structure.

    Args:
        file_path: Path to the DOCX file.

    Returns:
        All text from the DOCX as a single string.
    """
    try:
        doc = Document(str(file_path))
        # Each paragraph is a block of text in the Word document
        text_parts = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]

        full_text = "\n".join(text_parts)
        logger.info(
            f"Extracted {len(full_text)} characters from {len(text_parts)} paragraphs"
        )
        return full_text

    except Exception as e:
        logger.error(f"Failed to extract text from DOCX: {e}")
        raise


def _extract_from_txt(file_path: Path) -> str:
    """
    Extract text from a plain text file.

    We try UTF-8 first (the most common encoding), and fall back
    to latin-1 if UTF-8 decoding fails. Latin-1 can decode any
    byte sequence, so it serves as a reliable fallback.

    Args:
        file_path: Path to the TXT file.

    Returns:
        The file content as a string.
    """
    try:
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning(
                f"UTF-8 decoding failed for {file_path.name}, falling back to latin-1"
            )
            text = file_path.read_text(encoding="latin-1")

        logger.info(f"Extracted {len(text)} characters from text file")
        return text

    except Exception as e:
        logger.error(f"Failed to read text file: {e}")
        raise
