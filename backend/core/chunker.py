# backend/core/chunker.py

from langchain.text_splitter import RecursiveCharacterTextSplitter

def chunk_text(text: str) -> list[str]:
    """
    Splits a long text into smaller, manageable chunks.

    Args:
        text: The full text content of the document.

    Returns:
        A list of strings, where each string is a text chunk.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        # Set a chunk size that's reasonable for context.
        # This can be tuned depending on the LLM's context window.
        chunk_size=1000, 
        
        # Add a small overlap between chunks to maintain context continuity.
        chunk_overlap=200, 
        
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = text_splitter.split_text(text)
    print(f"Text split into {len(chunks)} chunks.")
    return chunks