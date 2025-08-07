# backend/core/llm.py

import google.generativeai as genai
from typing import AsyncGenerator

class GeminiLLM:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        print("Initializing Gemini LLM for generation...")
        self.model = genai.GenerativeModel(model_name)
        print("Gemini LLM initialized.")

    # --- THIS FUNCTION IS NOW AN ASYNC GENERATOR ---
    async def generate_answer_stream(self, question: str, context_chunks: list[str]) -> AsyncGenerator[str, None]:
        """
        Generates a streamed answer based on the question and context.
        Yields chunks of the answer as they are generated.
        """
        if not context_chunks:
            yield "I could not find any relevant information in the document to answer your question."
            return

        context_str = "\n---\n".join(context_chunks)
        prompt = f"""
        You are a helpful assistant for the ExplainMyDoc.ai application.
        Your goal is to answer a user's question based *only* on the provided context from a document.
        Do not use any external knowledge. If the answer is not in the context, say so.
        Explain the answer in simple, clear terms.

        CONTEXT:
        {context_str}

        QUESTION:
        {question}

        ANSWER:
        """
        
        print("Generating streamed answer with LLM...")
        try:
            # Use generate_content with stream=True to get an async iterator
            response_stream = await self.model.generate_content_async(prompt, stream=True)
            
            # Iterate through the stream and yield each part's text
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            print(f"Error during LLM stream generation: {e}")
            yield f"An error occurred while generating the answer: {e}"

llm_instance = GeminiLLM()