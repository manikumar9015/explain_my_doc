# backend/core/llm.py

import google.generativeai as genai

# The API key is already configured in embedder.py,
# so we do not need to configure it again here.

class GeminiLLM:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initializes the Gemini LLM for text generation.
        """
        print("Initializing Gemini LLM for generation...")
        self.model = genai.GenerativeModel(model_name)
        print("Gemini LLM initialized.")

    async def generate_answer(self, question: str, context_chunks: list[str]) -> str:
        """
        Generates an answer based on the question and provided context.

        Args:
            question (str): The user's question.
            context_chunks (list[str]): A list of relevant text chunks from the database.

        Returns:
            str: The generated answer.
        """
        if not context_chunks:
            return "I could not find any relevant information in the document to answer your question."

        # --- This is our Prompt Engineering ---
        context_str = "\n---\n".join(context_chunks)
        prompt = f"""
        You are a helpful assistant for the ExplainMyDoc.ai application.
        Your goal is to answer a user's question based *only* on the provided context from a document.
        Do not use any external knowledge or information not present in the context. If the answer is not in the context, clearly state that the information is not available in the provided text.
        Explain the answer in simple, clear terms.

        CONTEXT:
        {context_str}

        QUESTION:
        {question}

        ANSWER:
        """
        
        print("Generating answer with LLM...")
        try:
            # Use generate_content_async for asynchronous operations
            response = await self.model.generate_content_async(prompt)
            print("Answer generated successfully.")
            return response.text
        except Exception as e:
            print(f"Error during LLM generation: {e}")
            return f"An error occurred while generating the answer: {e}"

# Create a single, global instance of the LLM handler
llm_instance = GeminiLLM()