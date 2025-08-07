# backend/core/llm.py

import google.generativeai as genai
from typing import AsyncGenerator, List, Dict

class GeminiLLM:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        print("Initializing Gemini LLM for generation...")
        self.model = genai.GenerativeModel(model_name)
        print("Gemini LLM initialized.")

    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """Helper function to format chat history for the prompt."""
        if not chat_history:
            return "No previous conversation history."
        
        formatted_history = []
        for message in chat_history:
            role = "User" if message.get('sender') == 'user' else "Assistant"
            formatted_history.append(f"{role}: {message.get('text')}")
        
        return "\n".join(formatted_history)

    async def generate_answer_stream(
        self, 
        question: str, 
        context_chunks: list[str],
        chat_history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        Generates a streamed answer, now with conversation history.
        """
        if not context_chunks:
            yield "I could not find any relevant information in the document to answer your question."
            return

        context_str = "\n---\n".join(context_chunks)
        history_str = self._format_chat_history(chat_history)

        # --- UPDATED PROMPT WITH CHAT HISTORY ---
        prompt = f"""
        You are a helpful assistant for the ExplainMyDoc.ai application.
        Your goal is to answer the user's "CURRENT QUESTION" based *only* on the provided "DOCUMENT CONTEXT".
        Use the "CHAT HISTORY" to understand the context of the conversation, for example, to resolve pronouns like "he", "she", or "it".
        Do not use any external knowledge. If the answer is not in the context, say so. Explain the answer in simple, clear terms.

        ---
        CHAT HISTORY:
        {history_str}
        ---
        DOCUMENT CONTEXT:
        {context_str}
        ---
        CURRENT QUESTION:
        {question}
        ---

        ANSWER:
        """
        
        print("Generating streamed answer with LLM (with history)...")
        try:
            response_stream = await self.model.generate_content_async(prompt, stream=True)
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            print(f"Error during LLM stream generation: {e}")
            yield f"An error occurred while generating the answer: {e}"

llm_instance = GeminiLLM()