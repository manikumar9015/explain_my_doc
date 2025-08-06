# backend/parsers/docx_parser.py

import io
import docx
from fastapi import UploadFile

def parse_docx(file: UploadFile) -> str:
    """
    Extracts text content from an uploaded DOCX file.

    Args:
        file: The uploaded DOCX file object from FastAPI.

    Returns:
        A string containing all the extracted text from the DOCX.
    """
    try:
        # Read the file content into an in-memory buffer
        file_content = file.file.read()
        file_stream = io.BytesIO(file_content)

        # Open the DOCX document
        document = docx.Document(file_stream)
        
        # Extract text from each paragraph
        all_text = []
        for para in document.paragraphs:
            if para.text:
                all_text.append(para.text)
        
        # Join all paragraphs' text into a single string
        return "\n".join(all_text)

    except Exception as e:
        # Handle potential errors, e.g., corrupted file, not a DOCX
        print(f"Error parsing DOCX: {e}")
        return f"Error: Could not parse the DOCX file. Reason: {e}"