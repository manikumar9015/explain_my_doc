# backend/core/llm.py

import google.generativeai as genai
from typing import AsyncGenerator, List, Dict

class GeminiLLM:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        print("Initializing Gemini LLM for generation...")
        self.model = genai.GenerativeModel(model_name)
        print("Gemini LLM initialized.")

    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        if not chat_history:
            return "No previous conversation history."
        formatted_history = []
        for message in chat_history:
            role = "User" if message.get('sender') == 'user' else "Assistant"
            formatted_history.append(f"{role}: {message.get('text')}")
        return "\n".join(formatted_history)

    async def _generate_draft_answer(
        self, 
        question: str, 
        context_str: str,
        history_str: str
    ) -> str:
        """Internal method to generate the first draft of an answer."""
        
        draft_prompt = f"""
        You are a helpful assistant. Your task is to generate a draft answer to the user's "CURRENT QUESTION" based on the "DOCUMENT CONTEXT" and "CHAT HISTORY".

        CHAT HISTORY:
        {history_str}
        ---
        DOCUMENT CONTEXT:
        {context_str}
        ---
        CURRENT QUESTION:
        {question}
        ---
        DRAFT ANSWER:
        """
        print("Generating draft answer...")
        # We need the full draft, so we don't stream this part.
        response = await self.model.generate_content_async(draft_prompt)
        print("Draft answer generated.")
        return response.text

    async def generate_answer_stream(
        self, 
        question: str, 
        context_chunks: list[str],
        chat_history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        Generates a refined, streamed answer using a draft-and-critique loop.
        """
        if not context_chunks:
            yield "I could not find any relevant information in the document to answer your question."
            return

        context_str = "\n---\n".join(context_chunks)
        history_str = self._format_chat_history(chat_history)

        # --- STEP 1: Generate the initial draft ---
        draft_answer = await self._generate_draft_answer(question, context_str, history_str)

        # --- STEP 2: Critique and refine the draft ---
        critique_prompt = f"""
        You are a meticulous fact-checker and editor. Your task is to refine a "DRAFT ANSWER" about a document.
        Review the "DRAFT ANSWER" against the "ORIGINAL DOCUMENT CONTEXT". You MUST follow these rules:
        1.  Ensure the final answer is **100% based on the provided "ORIGINAL DOCUMENT CONTEXT"**. Remove any information not explicitly mentioned in the context.
        2.  Correct any inaccuracies or misinterpretations in the draft.
        3.  Improve the clarity and conciseness of the answer.
        4.  Maintain a helpful and direct tone.
        5.  After providing the final answer, suggest 2-3 follow-up questions based on the context, each prefixed with "SUGGESTION:".

        ---
        ORIGINAL DOCUMENT CONTEXT:
        {context_str}
        ---
        CHAT HISTORY:
        {history_str}
        ---
        CURRENT QUESTION:
        {question}
        ---
        DRAFT ANSWER:
        {draft_answer}
        ---

        REFINED AND FINAL ANSWER:
        """
        
        print("Generating refined answer with critique...")
        try:
            # This is the final output that we stream to the user
            response_stream = await self.model.generate_content_async(critique_prompt, stream=True)
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            print(f"Error during refined stream generation: {e}")
            yield f"An error occurred while generating the refined answer: {e}"

llm_instance = GeminiLLM()