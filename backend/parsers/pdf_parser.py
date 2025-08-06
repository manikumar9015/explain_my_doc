# backend/parsers/pdf_parser.py

import io
from pypdf import PdfReader
from fastapi import UploadFile

def parse_pdf(file: UploadFile) -> str:
    """
    Extracts text content from an uploaded PDF file.

    Args:
        file: The uploaded PDF file object from FastAPI.

    Returns:
        A string containing all the extracted text from the PDF.
    """
    try:
        # Read the file content into an in-memory buffer
        pdf_content = file.file.read()
        pdf_stream = io.BytesIO(pdf_content)

        # Create a PDF reader object
        reader = PdfReader(pdf_stream)
        
        # Extract text from each page
        all_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                all_text.append(text)
        
        # Join all pages' text into a single string
        return "\n".join(all_text)
    
    except Exception as e:
        # Handle potential errors, e.g., corrupted file, not a PDF
        print(f"Error parsing PDF: {e}")
        return f"Error: Could not parse the PDF file. Reason: {e}"