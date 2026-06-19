"""
RAG Knowledge Base API
Entry point for the FastAPI application.
"""

import logging
import time
import os
import shutil

from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Body, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import pdfplumber
from datetime import timedelta

from app.auth import get_current_user, create_access_token, verify_password, TEST_USER, ACCESS_TOKEN_EXPIRE_MINUTES

from services.vector_store import VectorDatabase
from services.embedder import TextEmbedder
from services.text_chunker import chunk_text
from services.llm_service import LLMService

# ---------------------------------------------------------------------------
# Environment & Logging
# ---------------------------------------------------------------------------
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App Configuration
# ---------------------------------------------------------------------------
APP_NAME = os.getenv("APP_NAME", "RAG Knowledge Base API")
APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# ---------------------------------------------------------------------------
# Global Services
# ---------------------------------------------------------------------------
vector_db = VectorDatabase(embedding_dimension=768, persist_dir="data/vector_store")
embedder = TextEmbedder(model_name="models/gemini-embedding-001")
llm_service = LLMService(vector_db=vector_db, embedder=embedder)

# ---------------------------------------------------------------------------
# FastAPI Instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "A Retrieval-Augmented Generation (RAG) knowledge base API built with FastAPI. "
        "Provides document ingestion, vector search, and AI-powered Q&A endpoints."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

# 1. CORS — allow configurable origins (default: all in dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Trusted Hosts — guards against HTTP Host header attacks
if ALLOWED_HOSTS != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)


# 3. Request Logging — logs method, path, status code, and latency
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s → %s  (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ---------------------------------------------------------------------------
# Startup / Shutdown Events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 %s v%s starting up in [%s] mode", APP_NAME, APP_VERSION, ENVIRONMENT)
    # Try to load existing vectors on startup
    if vector_db.load_from_disk():
        logger.info(f"Loaded existing vector database with {vector_db.get_total_items()} items.")
    else:
        logger.info("No existing vector database found. Starting fresh.")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 %s shutting down", APP_NAME)
    vector_db.save_to_disk()
    logger.info("Vector database saved to disk.")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Root"], summary="API root")
async def root():
    """Returns a welcome message and basic API information."""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health_check():
    """
    Liveness / readiness probe.

    Returns HTTP 200 with a JSON payload containing service status,
    version, and current environment.  Suitable for use with Docker
    HEALTHCHECK, Kubernetes liveness probes, or any uptime monitor.
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "service": APP_NAME,
            "version": APP_VERSION,
            "environment": ENVIRONMENT,
        },
    )


@app.post("/login", tags=["Auth"], summary="Login to get JWT token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Check if the user exists and password is correct
    if form_data.username != TEST_USER["username"] or not verify_password(form_data.password, TEST_USER["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/upload", tags=["Upload"], summary="Upload and process a PDF file")
async def upload_pdf(
    file: UploadFile = File(...)
):
    """
    Accepts a PDF file, extracts text, chunks it, generates embeddings, 
    and saves to the vector database.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Resolve project root (rag-knowledge-base) relative to this file (app/main.py)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_data_dir = os.path.join(base_dir, "data", "raw")
    
    os.makedirs(raw_data_dir, exist_ok=True)
    file_path = os.path.join(raw_data_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        file.file.close()

    # Process the PDF
    try:
        chunks_to_embed = []
        metadata_list = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    # Break the page text into smaller chunks
                    page_chunks = chunk_text(text, chunk_size=1000, overlap=200)
                    for chunk in page_chunks:
                        chunks_to_embed.append(chunk)
                        metadata_list.append({
                            "text": chunk,
                            "filename": file.filename,
                            "page_number": page_num
                        })
        
        # Generate embeddings
        if not chunks_to_embed:
            raise HTTPException(status_code=400, detail="Could not extract any text from the provided PDF file.")
            
        embeddings = embedder.turn_chunks_into_embeddings(chunks_to_embed)
        # Add to database
        vector_db.add_embeddings(embeddings, metadata_list)
        # Save right away so we don't lose data if the server crashes
        vector_db.save_to_disk()
            
    except HTTPException:
        # Re-raise HTTP exceptions so they return proper status codes to the client
        raise
    except Exception as e:
        import traceback
        err_msg = repr(e) + "\n" + traceback.format_exc()
        logger.error(f"Failed to process PDF {file.filename}: {err_msg}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {err_msg}")
        
    return {
        "message": "File processed and added to knowledge base successfully",
        "filename": file.filename,
        "chunks_added": len(chunks_to_embed),
        "total_knowledge_base_size": vector_db.get_total_items()
    }


@app.post("/ask", tags=["Q&A"], summary="Ask a question")
async def ask_question(
    query: str = Body(..., embed=True),
    session_id: str = Body("default", embed=True)
):
    """
    Ask a question against the knowledge base.
    Uses RAG (Retrieval-Augmented Generation) to find relevant context
    and generate an answer using the LLM.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    try:
        result = llm_service.ask_question(query=query, session_id=session_id)
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to process query: {error_msg}")
        if "LLM_API_UNAVAILABLE" in error_msg:
            raise HTTPException(status_code=503, detail="The AI service is currently unavailable. Please try again later.")
        elif "LLM_API_QUOTA" in error_msg:
            raise HTTPException(status_code=429, detail="The AI service quota has been exceeded. Please try again later.")
        raise HTTPException(status_code=500, detail=f"Error generating answer: {error_msg}")

from fastapi.responses import StreamingResponse

@app.post("/ask/stream", tags=["Q&A"], summary="Ask a question and stream response")
async def ask_question_stream_endpoint(
    query: str = Body(..., embed=True),
    session_id: str = Body("default", embed=True)
):
    """
    Ask a question against the knowledge base and stream the answer token by token.
    Uses Server-Sent Events (SSE) format.
    """
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    return StreamingResponse(
        llm_service.ask_question_stream(query=query, session_id=session_id),
        media_type="text/event-stream"
    )

