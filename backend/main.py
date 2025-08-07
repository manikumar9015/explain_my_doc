# backend/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import all necessary modules
from .parsers import pdf_parser, docx_parser, txt_parser
from .core.chunker import chunk_text
from .core.embedder import embedder_instance
from .vector_store.chroma import vector_store_instance
from .core.llm import llm_instance
from .core.scheduler import scheduler, session_manager
from fastapi.responses import JSONResponse, StreamingResponse

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ExplainMyDoc.ai API",
    description="API for temporary, session-based document analysis.",
    version="3.0.2-ephemeral", # I've bumped the version number
)

# --- CORRECTED MIDDLEWARE CONFIGURATION ---
# The 'origins' variable is now defined correctly in the code.
origins = [
    "http://localhost:5173", # The default URL for the Vite React dev server
    "http://localhost:3000", # A common alternative for React dev servers
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)

# --- THEN, define the lifecycle events using the 'app' object ---
@app.on_event("startup")
async def startup_event():
    """Tasks to run when the application starts."""
    # Add the cleanup job to the scheduler to run every 10 minutes
    scheduler.add_job(session_manager.cleanup_expired_sessions, 'interval', minutes=10)
    scheduler.start()
    print("Scheduler started and cleanup job scheduled.")

@app.on_event("shutdown")
async def shutdown_event():
    """Tasks to run when the application shuts down."""
    scheduler.shutdown()
    print("Scheduler shut down.")

# --- Pydantic models for request bodies ---
class QueryRequest(BaseModel):
    session_id: str
    question: str

# --- API Endpoints ---
@app.get("/", tags=["Health Check"])
def read_root():
    """A simple endpoint to check if the server is running."""
    return {"status": "ok"}

@app.post("/process/", tags=["Document Processing"])
async def process_document(file: UploadFile = File(...)):
    """
    Processes a new document, creating a temporary session and a unique data collection.
    Returns a session_id that must be used for all subsequent queries.
    """
    # Task 1: Create a unique session and collection
    try:
        session_id = vector_store_instance.create_collection()
        session_manager.register_session(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create a new session: {e}")

    # Task 2: Parse the document
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
        # Clean up the created collection if the file is invalid
        vector_store_instance.delete_collection(session_id)
        raise HTTPException(status_code=400, detail=f"Unsupported file type: '{content_type}'.")

    if "Error:" in extracted_text:
        vector_store_instance.delete_collection(session_id)
        raise HTTPException(status_code=500, detail=extracted_text)
    
    if not extracted_text.strip():
        vector_store_instance.delete_collection(session_id)
        raise HTTPException(status_code=400, detail="Document is empty or contains no readable text.")

    # Task 3: Chunk and Embed
    text_chunks = chunk_text(extracted_text)
    chunk_embeddings = await embedder_instance.embed_documents(text_chunks)

    # Task 4: Store in the new, unique collection
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
        content={
            "message": "Document processed successfully. Use the session_id to ask questions.",
            "session_id": session_id
        }
    )

@app.post("/query/", tags=["Question Answering"])
async def query_document(request: QueryRequest):
    """
    Accepts a user's question, finds context, and STREAMS back the answer.
    """
    session_id = request.session_id
    question = request.question

    # Steps 1 and 2 (embedding and querying) are the same
    try:
        query_embedding = await embedder_instance.embed_documents([question])
        context_chunks = vector_store_instance.query(
            collection_name=session_id,
            query_embedding=query_embedding[0]
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found or query error: {e}")

    # Step 3: Generate the answer using the new streaming function
    try:
        # This returns an async generator, not a final string
        answer_generator = llm_instance.generate_answer_stream(
            question=question,
            context_chunks=context_chunks
        )
        # Use FastAPI's StreamingResponse to send the data chunk-by-chunk
        return StreamingResponse(answer_generator, media_type="text/plain")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating final answer with LLM: {e}")