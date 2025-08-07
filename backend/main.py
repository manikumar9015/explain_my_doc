# backend/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import base64

# Import all necessary modules
from .parsers import pdf_parser, docx_parser, txt_parser
from .core.chunker import chunk_text
from .core.embedder import embedder_instance
from .vector_store.chroma import vector_store_instance
from .core.llm import llm_instance
from .core.scheduler import scheduler, session_manager

# Initialize the FastAPI app
app = FastAPI(
    title="ExplainMyDoc.ai API",
    description="API for temporary, session-based document analysis.",
    version="3.1.0-streaming-sources",
)

# CORS Middleware Configuration
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Source-Chunks"], # Expose the custom header to the browser
)

# FastAPI App Lifecycle Events
@app.on_event("startup")
async def startup_event():
    scheduler.add_job(session_manager.cleanup_expired_sessions, 'interval', minutes=10)
    scheduler.start()
    print("Scheduler started and cleanup job scheduled.")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler shut down.")

# Pydantic models for request bodies
class QueryRequest(BaseModel):
    session_id: str
    question: str

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
    
    if content_type == 'application/pdf':
        extracted_text = pdf_parser.parse_pdf(file)
    elif content_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' or filename.endswith('.docx'):
        extracted_text = docx_parser.parse_docx(file)
    elif content_type == 'text/plain' or filename.endswith('.txt'):
        extracted_text = txt_parser.parse_txt(file)
    else:
        vector_store_instance.delete_collection(session_id)
        raise HTTPException(status_code=400, detail=f"Unsupported file type: '{content_type}'.")

    if "Error:" in extracted_text:
        vector_store_instance.delete_collection(session_id)
        raise HTTPException(status_code=500, detail=extracted_text)
    
    if not extracted_text.strip():
        vector_store_instance.delete_collection(session_id)
        raise HTTPException(status_code=400, detail="Document is empty or contains no readable text.")

    text_chunks = chunk_text(extracted_text)
    chunk_embeddings = await embedder_instance.embed_documents(text_chunks)

    try:
        metadatas = [{"source": filename} for _ in text_chunks]
        vector_store_instance.add_documents(
            collection_name=session_id,
            chunks=text_chunks,
            embeddings=chunk_embeddings,
            metadatas=metadatas
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store document in session {session_id}: {e}")

    return JSONResponse(
        status_code=200,
        content={ "message": "Document processed successfully.", "session_id": session_id }
    )

@app.post("/query/", tags=["Question Answering"])
async def query_document(request: QueryRequest):
    session_id = request.session_id
    question = request.question

    try:
        query_embedding = await embedder_instance.embed_documents([question])
        context_chunks = vector_store_instance.query(
            collection_name=session_id,
            query_embedding=query_embedding[0]
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found or query error: {e}")

    # Prepare custom headers with source chunks
    sources_json = json.dumps(context_chunks)
    sources_b64 = base64.b64encode(sources_json.encode('utf-8')).decode('utf-8')
    custom_headers = { "X-Source-Chunks": sources_b64 }

    try:
        answer_generator = llm_instance.generate_answer_stream(
            question=question,
            context_chunks=context_chunks
        )
        return StreamingResponse(answer_generator, media_type="text/plain", headers=custom_headers)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating final answer with LLM: {e}")