# backend/main.py

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
from .core.vector_store.chroma import vector_store_instance
from .core.llm import llm_instance
from .core.scheduler import scheduler, session_manager

app = FastAPI(
    title="DocuMentor AI API",
    description="API with summarization, export, and agentic features.",
    version="4.1.0-stable",
)

# --- CORRECTED CORS POLICY FOR VERCEL PREVIEWS ---
allow_origin_regex = r"https://.*\.vercel\.app"
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=allow_origin_regex, # Use the regex for Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Source-Chunks"],
)
# --- END OF CORS FIX ---

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
    
    if content_type == 'application/pdf': extracted_text = pdf_parser.parse_pdf(file)
    elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or filename.endswith('.docx'): extracted_text = docx_parser.parse_docx(file)
    elif content_type == 'text/plain' or filename.endswith('.txt'): extracted_text = txt_parser.parse_txt(file)
    else: vector_store_instance.delete_collection(session_id); raise HTTPException(status_code=400, detail=f"Unsupported file type.")
    
    if "Error:" in extracted_text: vector_store_instance.delete_collection(session_id); raise HTTPException(status_code=500, detail=extracted_text)
    if not extracted_text.strip(): vector_store_instance.delete_collection(session_id); raise HTTPException(status_code=400, detail="Document is empty.")

    text_chunks = chunk_text(extracted_text)
    batch_size = 100
    total_chunks = len(text_chunks)
    print(f"Starting to process {total_chunks} chunks in batches of {batch_size}...")
    for i in range(0, total_chunks, batch_size):
        batch_chunks = text_chunks[i:i + batch_size]
        try:
            chunk_embeddings = await embedder_instance.embed_documents(batch_chunks)
            metadatas = [{"source": filename} for _ in batch_chunks]
            vector_store_instance.add_documents(
                collection_name=session_id, chunks=batch_chunks, embeddings=chunk_embeddings, metadatas=metadatas
            )
            print(f"Processed batch {i // batch_size + 1}/{(total_chunks + batch_size - 1) // batch_size}")
        except Exception as e:
            vector_store_instance.delete_collection(session_id)
            raise HTTPException(status_code=500, detail=f"Failed to process batch {i}: {e}")

    return JSONResponse(
        status_code=200, content={"message": "Document processed successfully in batches.", "session_id": session_id}
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
    chat_history = [msg.dict() for msg in request.chat_history]
    if not chat_history or len(chat_history) <= 1:
        raise HTTPException(status_code=400, detail="Cannot export an empty conversation.")
    try:
        markdown_content = await llm_instance.summarize_conversation(chat_history)
        if "Error:" in markdown_content:
            raise HTTPException(status_code=500, detail=markdown_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {e}")
    
    reports_dir = "generated_reports"
    os.makedirs(reports_dir, exist_ok=True)
    pdf_filename = f"{uuid.uuid4()}.pdf"
    pdf_filepath = os.path.join(reports_dir, pdf_filename)

    try:
        pdf = MarkdownPdf(toc_level=2)
        pdf.add_section(Section(markdown_content, toc=True))
        pdf.save(pdf_filepath)
        background_tasks.add_task(os.remove, pdf_filepath)
        return FileResponse(
            path=pdf_filepath, filename="DocuMentor_Summary.pdf", media_type='application/pdf'
        )
    except Exception as e:
        print(f"!!! PDF GENERATION FAILED !!!: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to convert Markdown to PDF: {str(e)}")