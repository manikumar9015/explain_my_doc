# backend/core/embedder.py

import os
import google.generativeai as genai
from dotenv import load_dotenv

class GeminiEmbedder:
    def __init__(self, model_name: str = "models/text-embedding-004"):
        """
        Initializes the Gemini Embedder.
        It configures the API key and specifies the embedding model.
        """
        # Load environment variables from .env file
        load_dotenv()
        
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")
        
        # The model name for the latest text embedding model
        self.model_name = model_name
        
        print("Configuring Gemini API...")
        genai.configure(api_key=self.api_key)
        print("Gemini Embedder initialized.")

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generates embeddings for a list of text chunks using the Gemini API.
        This is an async function.
        """
        if not texts or not any(texts):
            return []
            
        print(f"Generating embeddings for {len(texts)} documents with Gemini...")
        
        # The Gemini API can handle batching automatically.
        result = await genai.embed_content_async(
            model=self.model_name,
            content=texts,
            task_type="RETRIEVAL_DOCUMENT" # Important for RAG
        )
        
        print("Embeddings generated successfully.")
        return result['embedding']

# Create a single, global instance of the embedder to be used by the app.
embedder_instance = GeminiEmbedder()