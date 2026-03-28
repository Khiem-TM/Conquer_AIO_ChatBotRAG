"""API router for chat endpoints with history support."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from app.indexing.index_service import IndexNotReadyError
from app.rag_core.chat_service import ChatService
from app.shared.schemas import ApiResponse, ChatRequest, ChatResponse
from app.shared.storage import history_store

router = APIRouter(prefix='/api/v1', tags=['chat'])
chat_service = ChatService()


@router.post(
    '/chat',
    response_model=ChatResponse,
    summary='Chat with documents',
    description='Ask a question and get answers from ingested documents',
)
async def chat(payload: ChatRequest) -> ChatResponse:
    """
    Ask a question to the RAG chatbot.

    **Request Example:**
    ```json
    {
      "question": "What is Anscombe quartet?",
      "top_k": 5,
      "include_citations": true
    }
    ```

    **Response Example:**
    ```json
    {
      "answer": "Anscombe quartet is a set of four datasets...",
      "citations": [
        {
          "source_id": "part1_minh_vn",
          "source_name": "Part1-4_Minh_VN.md",
          "chunk_id": "part1_minh_vn_chunk_045",
          "score": 0.9345,
          "snippet": "Anscombe quartet is..."
        }
      ],
      "model": "llama3.1:8b",
      "latency_ms": 2340,
      "conversation_id": "conv_550e8400-e29b"
    }
    ```
    """
    try:
        response = await chat_service.ask(payload)
        # Save to history
        history_store.add_entry(payload.question, response.answer)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Validation error: {str(e)}',
        )
    except IndexNotReadyError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                'code': 'INDEX_NOT_READY',
                'message': str(e),
                'hint': 'Call /api/v1/ingest first, then retry chat.',
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Chat error: {str(e)}',
        )


@router.get(
    '/history',
    response_model=ApiResponse,
    summary='Get chat history',
    description='Retrieve all chat messages (latest first)',
)
async def get_history() -> ApiResponse:
    """
    Retrieve all chat history.

    **Response Example:**
    ```json
    {
      "success": true,
      "message": "OK",
      "data": {
        "messages": [
          {
            "id": "msg_550e8400-e29b",
            "question": "What is Anscombe quartet?",
            "answer": "Anscombe quartet is...",
            "timestamp": "2024-01-15T10:30:00Z"
          }
        ],
        "total": 1
      }
    }
    ```
    """
    try:
        messages = history_store.get_all()
        return ApiResponse(
            success=True,
            message='OK',
            data={'messages': messages, 'total': len(messages)},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error retrieving history: {str(e)}',
        )


@router.delete(
    '/history',
    response_model=ApiResponse,
    summary='Clear chat history',
    description='Delete all chat messages',
)
async def clear_history() -> ApiResponse:
    """
    Clear all chat history.

    **Response Example:**
    ```json
    {
      "success": true,
      "message": "History cleared",
      "data": {
        "deleted_count": 5
      }
    }
    ```
    """
    try:
        count = history_store.clear()
        return ApiResponse(
            success=True,
            message='History cleared',
            data={'deleted_count': count},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error clearing history: {str(e)}',
        )
