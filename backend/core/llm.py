# import google.generativeai as genai
# from typing import AsyncGenerator, List, Dict

# class GeminiLLM:
#     def __init__(self, model_name: str = "gemini-2.5-flash"):
#         print("Initializing Gemini LLM for generation...")
#         self.model = genai.GenerativeModel(model_name)
#         print("Gemini LLM initialized.")

#     def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
#         if not chat_history:
#             return "No previous conversation history."
#         formatted_history = []
#         for message in chat_history:
#             role = "User" if message.get('sender') == 'user' else "Assistant"
#             formatted_history.append(f"{role}: {message.get('text')}")
#         return "\n".join(formatted_history)

#     async def _generate_draft_answer(
#         self, 
#         question: str, 
#         context_str: str,
#         history_str: str
#     ) -> str:
#         """Internal method to generate the first draft of an answer."""
        
#         draft_prompt = f"""
#         You are a helpful assistant. Your task is to generate a draft answer to the user's "CURRENT QUESTION" based on the "DOCUMENT CONTEXT" and "CHAT HISTORY".

#         CHAT HISTORY:
#         {history_str}
#         ---
#         DOCUMENT CONTEXT:
#         {context_str}
#         ---
#         CURRENT QUESTION:
#         {question}
#         ---
#         DRAFT ANSWER:
#         """
#         print("Generating draft answer...")
#         response = await self.model.generate_content_async(draft_prompt)
#         return response.text

#     async def generate_answer_stream(
#         self, 
#         question: str, 
#         context_chunks: list[str],
#         chat_history: List[Dict[str, str]]
#     ) -> AsyncGenerator[str, None]:
#         """
#         Generates a refined, streamed answer using a draft-and-critique loop.
#         """
#         if not context_chunks:
#             yield "I could not find any relevant information in the document to answer your question."
#             return

#         context_str = "\n---\n".join(context_chunks)
#         history_str = self._format_chat_history(chat_history)

#         draft_answer = await self._generate_draft_answer(question, context_str, history_str)

#         critique_prompt = f"""
#         You are a meticulous fact-checker and editor. Your task is to refine a "DRAFT ANSWER" about a document.
#         Review the "DRAFT ANSWER" against the "ORIGINAL DOCUMENT CONTEXT". You MUST follow these rules:
#         1.  Ensure the final answer is **100% based on the provided "ORIGINAL DOCUMENT CONTEXT"**. Remove any information not explicitly mentioned in the context.
#         2.  Correct any inaccuracies or misinterpretations in the draft.
#         3.  Improve the clarity and conciseness of the answer.
#         4.  Maintain a helpful and direct tone.
#         5.  After providing the final answer, suggest 2-3 follow-up questions based on the context, each prefixed with "SUGGESTION:".

#         ---
#         ORIGINAL DOCUMENT CONTEXT:
#         {context_str}
#         ---
#         CHAT HISTORY:
#         {history_str}
#         ---
#         CURRENT QUESTION:
#         {question}
#         ---
#         DRAFT ANSWER:
#         {draft_answer}
#         ---

#         REFINED AND FINAL ANSWER:
#         """
        
#         print("Generating refined answer with critique...")
#         try:
#             response_stream = await self.model.generate_content_async(critique_prompt, stream=True)
#             async for chunk in response_stream:
#                 if chunk.text:
#                     yield chunk.text
#         except Exception as e:
#             print(f"Error during refined stream generation: {e}")
#             yield f"An error occurred while generating the refined answer: {e}"
            
#     async def summarize_conversation(self, chat_history: List[Dict[str, str]]) -> str:
#         """
#         Takes a full conversation history and synthesizes it into a structured document.
#         """
#         print("Invoking Summarizer Agent...")
        
#         full_conversation_str = self._format_chat_history(chat_history)
        
#         summarizer_prompt = f"""
#         You are a professional editor and report generator named "DocuMentor AI".
#         Your task is to transform a raw conversation log between a User and an AI Assistant into a clean, structured, and easy-to-read document.

#         **Instructions:**
#         1.  Read the entire "CONVERSATION LOG" to understand the key topics discussed.
#         2.  Do NOT just copy the conversation. Synthesize the information.
#         3.  Create a title for the document based on the content.
#         4.  Use Markdown for formatting: use headings (`#`, `##`), subheadings, bullet points (`*`), and bold text (`**`) to structure the information logically.
#         5.  Group related questions and answers into coherent sections.
#         6.  Summarize the key findings and answers. Ignore conversational pleasantries like "hello" or "thank you".
#         7.  The final output should be a professional-looking document, ready to be saved as a PDF.

#         ---
#         CONVERSATION LOG:
#         {full_conversation_str}
#         ---

#         STRUCTURED DOCUMENT (IN MARKDOWN):
#         """
        
#         try:
#             response = await self.model.generate_content_async(summarizer_prompt)
#             print("Structured summary generated successfully.")
#             return response.text
#         except Exception as e:
#             print(f"Error during summary generation: {e}")
#             return f"Error: Could not generate the document summary. Reason: {e}"

# llm_instance = GeminiLLM()

# backend/core/llm.py

import google.generativeai as genai
from typing import AsyncGenerator, List, Dict

class GeminiLLM:
    def __init__(self, model_name: str = "gemini-1.5-flash-latest"):
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

    async def generate_answer_stream(
        self, 
        question: str, 
        context_chunks: list[str],
        chat_history: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        if not context_chunks:
            yield "I could not find any relevant information in the document to answer your question."
            return

        context_str = "\n---\n".join(context_chunks)
        history_str = self._format_chat_history(chat_history)

        # Reverted to the simpler, single-call prompt for memory efficiency
        prompt = f"""
        You are a helpful assistant for DocuMentor AI.
        Your goal is to answer the user's "CURRENT QUESTION" based *only* on the provided "DOCUMENT CONTEXT".
        Use the "CHAT HISTORY" to understand conversational context. Do not use external knowledge.

        **Instructions:**
        1. First, provide a direct and clear answer to the "CURRENT QUESTION".
        2. After the answer, suggest 2-3 relevant follow-up questions, each prefixed with "SUGGESTION:".

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
        
        print("Generating streamed answer (memory-efficient mode)...")
        try:
            response_stream = await self.model.generate_content_async(prompt, stream=True)
            async for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            print(f"Error during LLM stream generation: {e}")
            yield f"An error occurred while generating the answer: {e}"

llm_instance = GeminiLLM()