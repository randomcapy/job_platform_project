"""
ai/resume_parser.py — Extracts plain text from uploaded PDF resumes.

WHY THIS EXISTS:
AI models (like Sentence-BERT) work with text, not PDFs. Before we can
compute semantic embeddings, we need to convert the PDF binary into
clean, readable text. PyMuPDF (imported as 'fitz') is fast, accurate,
and handles multi-column layouts better than alternatives like pdfminer.

WHY NOT JUST READ THE FILE AS TEXT?
PDFs are binary formats with complex encoding. They contain fonts,
images, vector graphics, and text streams. A raw read would return
garbage. PyMuPDF parses the internal structure and reconstructs text.
"""

import fitz  # PyMuPDF — fitz is the original C library name
import os


def extract_text_from_pdf(filepath: str) -> str:
    """
    Opens a PDF and extracts all text content page by page.

    Args:
        filepath: Absolute or relative path to the PDF file.

    Returns:
        A single string containing all text from all pages,
        joined with newlines between pages.

    How it works:
        1. fitz.open() loads the PDF into memory
        2. We iterate over each page
        3. page.get_text("text") extracts plain text from that page
        4. We join all pages into one document string
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"PDF not found at path: {filepath}")

    extracted_pages = []

    # Open the PDF document
    doc = fitz.open(filepath)

    for page_num in range(len(doc)):
        page = doc[page_num]
        # "text" mode extracts text in reading order (top-to-bottom, left-to-right)
        text = page.get_text("text")
        extracted_pages.append(text)

    doc.close()

    # Join all pages and strip excessive whitespace
    full_text = "\n".join(extracted_pages).strip()

    return full_text if full_text else "No text could be extracted from this PDF."
