from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import base64
import os
import uuid
from markdown_pdf import MarkdownPdf, Section
from fastapi import BackgroundTasks

from .parsers import pdf_parser, docx_parser, txt_parser
from .core.chunker import chunk_text
from .core.embedder import embedder_instance
from .vector_store.chroma import vector_store_instance
from .core.llm import llm_instance
from .core.scheduler import scheduler, session_manager

app = FastAPI(
    title="DocuMentor AI API",
    description="API with summarization, export, and agentic features.",
    version="4.0.0-export",
)

origins = ["http://localhost:5173", "http://localhost:3000", "https://explain-my-doc.vercel.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Source-Chunks"],
)

@app.on_event("startup")
async def startup_event():
    scheduler.add_job(session_manager.cleanup_expired_sessions, 'interval', minutes=10)
    scheduler.start()
    print("Scheduler started and cleanup job scheduled.")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler shut down.")

class ChatMessage(BaseModel):
    sender: str
    text: str

class QueryRequest(BaseModel):
    session_id: str
    question: str
    chat_history: List[ChatMessage] = []

class ExportRequest(BaseModel):
    chat_history: List[ChatMessage] = []

@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok"}

@app.post("/process/", tags=["Document Processing"])
async def process_document(file: UploadFile = File(...)):
    try:
        session_id = vector_store_instance.create_collection()
        session_manager.register_session(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create a new session: {e}")
    
    content_type = file.content_type
    filename = file.filename
    extracted_text = ""
    
    # ... (the file parsing logic is the same)
    if content_type == 'application/pdf': extracted_text = pdf_parser.parse_pdf(file)
    # ... (etc. for docx, txt)
    else: vector_store_instance.delete_collection(session_id); raise HTTPException(status_code=400, detail=f"Unsupported file type.")
    
    if "Error:" in extracted_text: vector_store_instance.delete_collection(session_id); raise HTTPException(status_code=500, detail=extracted_text)
    if not extracted_text.strip(): vector_store_instance.delete_collection(session_id); raise HTTPException(status_code=400, detail="Document is empty.")

    text_chunks = chunk_text(extracted_text)
    
    # --- NEW BATCH PROCESSING LOGIC ---
    batch_size = 100 # Process 100 chunks at a time
    total_chunks = len(text_chunks)
    
    print(f"Starting to process {total_chunks} chunks in batches of {batch_size}...")

    for i in range(0, total_chunks, batch_size):
        batch_chunks = text_chunks[i:i + batch_size]
        
        try:
            # Generate embeddings for the current small batch
            chunk_embeddings = await embedder_instance.embed_documents(batch_chunks)
            
            # Prepare metadata for the current batch
            metadatas = [{"source": filename} for _ in batch_chunks]
            
            # Add the current batch to the vector store
            vector_store_instance.add_documents(
                collection_name=session_id, 
                chunks=batch_chunks, 
                embeddings=chunk_embeddings, 
                metadatas=metadatas
            )
            print(f"Processed batch {i // batch_size + 1}/{(total_chunks + batch_size - 1) // batch_size}")

        except Exception as e:
            # Clean up if any batch fails
            vector_store_instance.delete_collection(session_id)
            raise HTTPException(status_code=500, detail=f"Failed to process batch {i}: {e}")
    # --- END OF NEW LOGIC ---

    return JSONResponse(
        status_code=200, 
        content={"message": "Document processed successfully in batches.", "session_id": session_id}
    )

@app.post("/query/", tags=["Question Answering"])
async def query_document(request: QueryRequest):
    session_id = request.session_id
    question = request.question
    chat_history = [msg.dict() for msg in request.chat_history]

    try:
        query_embedding = await embedder_instance.embed_documents([question])
        context_chunks = vector_store_instance.query(
            collection_name=session_id,
            query_embedding=query_embedding[0]
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found or query error: {e}")

    sources_json = json.dumps(context_chunks)
    sources_b64 = base64.b64encode(sources_json.encode('utf-8')).decode('utf-8')
    custom_headers = { "X-Source-Chunks": sources_b64 }

    try:
        answer_generator = llm_instance.generate_answer_stream(
            question=question,
            context_chunks=context_chunks,
            chat_history=chat_history
        )
        return StreamingResponse(answer_generator, media_type="text/plain", headers=custom_headers)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating final answer with LLM: {e}")

@app.post("/export/pdf", tags=["Exporting"])
async def export_conversation_to_pdf(request: ExportRequest, background_tasks: BackgroundTasks):
    """
    Generates a summary PDF and returns it for download.
    This version avoids tempfile and uses background tasks for cleanup.
    """
    chat_history = [msg.dict() for msg in request.chat_history]
    if not chat_history or len(chat_history) <= 1:
        raise HTTPException(status_code=400, detail="Cannot export an empty conversation.")

    # Step 1: Generate the summary (no change here)
    try:
        markdown_content = await llm_instance.summarize_conversation(chat_history)
        if "Error:" in markdown_content:
            raise HTTPException(status_code=500, detail=markdown_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {e}")

    # --- NEW ROBUST PDF GENERATION LOGIC ---
    
    # Define a reports directory and ensure it exists
    reports_dir = "generated_reports"
    os.makedirs(reports_dir, exist_ok=True)
    
    # Create a unique filename for the PDF
    pdf_filename = f"{uuid.uuid4()}.pdf"
    pdf_filepath = os.path.join(reports_dir, pdf_filename)

    try:
        # Step 2: Convert Markdown to PDF in our new directory
        print(f"Attempting to save PDF to: {pdf_filepath}")
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(markdown_content, toc=True))
        pdf.save(pdf_filepath)
        print("PDF saved successfully.")

        # Step 3: Add a background task to delete the file after sending it
        # This prevents cluttering our server with old reports.
        background_tasks.add_task(os.remove, pdf_filepath)

        # Step 4: Return the generated file for download
        return FileResponse(
            path=pdf_filepath, 
            filename="DocuMentor_Summary.pdf", 
            media_type='application/pdf'
        )
    except Exception as e:
        # This will now give us a more specific error in the terminal
        print(f"!!! PDF GENERATION FAILED !!!: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to convert Markdown to PDF: {str(e)}")