"""Main FastAPI application for RAG ChatBot."""

import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import chat, ingest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RAG ChatBot API",
    description="Minimal MVP backend for RAG ChatBot with FastAPI",
    version="0.1.0",
)

# Add CORS middleware (allow all origins for MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(ingest.router)


@app.get(
    "/health",
    tags=["system"],
    summary="Health check",
    description="Check if the API is running",
)
async def health_check() -> dict:
    """
    Simple health check endpoint.

    **Example Response:**
    ```json
    {
      "status": "ok",
      "timestamp": "2024-03-28T10:30:00",
      "service": "rag-chatbot-api"
    }
    ```
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "rag-chatbot-api",
    }


@app.get(
    "/",
    tags=["system"],
    summary="API root",
    description="Get API information",
)
async def root() -> dict:
    """
    API root endpoint with documentation links.

    **Example Response:**
    ```json
    {
      "message": "RAG ChatBot API",
      "version": "0.1.0",
      "docs": "/docs",
      "openapi": "/openapi.json"
    }
    ```
    """
    return {
        "message": "RAG ChatBot API",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
