# backend/parsers/txt_parser.py

from fastapi import UploadFile

def parse_txt(file: UploadFile) -> str:
    """
    Reads and decodes text from an uploaded TXT file.

    Args:
        file: The uploaded TXT file object from FastAPI.

    Returns:
        A string containing the content of the text file.
    """
    try:
        # Read the file content as bytes
        file_content = file.file.read()
        
        # Decode the bytes into a string (UTF-8 is a safe default)
        return file_content.decode('utf-8')

    except Exception as e:
        # Handle potential errors, e.g., decoding errors
        print(f"Error parsing TXT: {e}")
        return f"Error: Could not parse the TXT file. Reason: {e}"