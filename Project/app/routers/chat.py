"""API router for chat endpoints with history support."""
from __future__ import annotations

import asyncio
import contextlib
import json
import time
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.indexing.index_service import IndexNotReadyError
from app.shared.schemas import ApiResponse, ChatRequest, ChatResponse
from app.shared.security import check_rate_limit, require_local_api_key
from app.shared.service_container import get_chat_service
from app.shared.storage import history_store
from app.shared.utils import get_logger

router = APIRouter(prefix='/api/v1', tags=['chat'])
logger = get_logger(__name__)
SSE_PING_INTERVAL_SECONDS = 12


@router.post('/chat', response_model=ChatResponse, dependencies=[Depends(require_local_api_key)])
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    try:
        check_rate_limit(request.client.host if request.client else 'local')
        response = await get_chat_service().ask(payload)
        history_store.add_entry(payload.question, response.answer)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Validation error: {str(e)}')
    except IndexNotReadyError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={'code': 'INDEX_NOT_READY', 'message': str(e), 'hint': 'Call /api/v1/ingest first, then retry chat.'})
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Chat error: {str(e)}')


@router.post('/chat/stream', dependencies=[Depends(require_local_api_key)])
async def chat_stream(payload: ChatRequest, request: Request) -> StreamingResponse:
    check_rate_limit(request.client.host if request.client else 'local')
    chat_service = get_chat_service()

    async def event_generator():
        request_started = time.perf_counter()
        retrieval_ready_ms: float | None = None
        first_token_ms: float | None = None
        queue: asyncio.Queue[dict | None] = asyncio.Queue()

        yield f"data: {json.dumps({'meta': {'status': 'started'}}, ensure_ascii=False)}\n\n"
        try:
            prepared = await chat_service.prepare(payload)
            citations = chat_service.citation_builder.build(prepared.contexts, payload.include_citations)
        except IndexNotReadyError as e:
            yield f"data: {json.dumps({'error': {'code': 'INDEX_NOT_READY', 'message': str(e), 'hint': 'Hãy tải tài liệu lên ở tab Tài liệu rồi ingest lại trước khi chat.'}}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'meta': {'status': 'completed'}}, ensure_ascii=False)}\n\n"
            return
        except Exception as e:
            yield f"data: {json.dumps({'error': {'code': 'PREPARE_ERROR', 'message': f'Chat stream error: {str(e)}'}}, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'meta': {'status': 'completed'}}, ensure_ascii=False)}\n\n"
            return

        async def producer() -> None:
            nonlocal retrieval_ready_ms
            try:
                chunks: list[str] = []
                async for token in chat_service.llm_client.stream_generate(prepared.prompt):
                    if retrieval_ready_ms is None:
                        retrieval_ready_ms = (time.perf_counter() - request_started) * 1000
                    chunks.append(token)
                    await queue.put({'token': token})
                full_answer = chat_service._finalize_answer(''.join(chunks), prepared.mode)
                history_store.add_entry(payload.question, full_answer)
                await queue.put({'result': {'answer': full_answer, 'mode': prepared.mode, 'confidence': prepared.confidence, 'metadata': prepared.metadata, 'citations': [c.model_dump() for c in citations]}})
                await queue.put({'done': True})
            except IndexNotReadyError as e:
                await queue.put({'error': {'code': 'INDEX_NOT_READY', 'message': str(e), 'hint': 'Call /api/v1/ingest first, then retry chat.'}})
            except Exception as e:
                await queue.put({'error': {'code': 'STREAM_ERROR', 'message': f'Chat stream error: {str(e)}'}})
            finally:
                await queue.put(None)

        producer_task = asyncio.create_task(producer())
        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=SSE_PING_INTERVAL_SECONDS)
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'ping': {'ts': int(time.time())}}, ensure_ascii=False)}\n\n"
                    continue
                if item is None:
                    break
                if 'token' in item and first_token_ms is None:
                    first_token_ms = (time.perf_counter() - request_started) * 1000
                    if retrieval_ready_ms is None:
                        retrieval_ready_ms = first_token_ms
                    yield f"data: {json.dumps({'meta': {'status': 'first_token', 'retrieval_ms': round(retrieval_ready_ms, 2), 'first_token_ms': round(first_token_ms, 2)}}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                if item.get('done') or item.get('error'):
                    break
        finally:
            if not producer_task.done():
                producer_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await producer_task
        full_completion_ms = (time.perf_counter() - request_started) * 1000
        logger.info('chat.stream completed | retrieval_ms=%s first_token_ms=%s full_completion_ms=%.2f', round(retrieval_ready_ms, 2) if retrieval_ready_ms is not None else None, round(first_token_ms, 2) if first_token_ms is not None else None, full_completion_ms)
        yield f"data: {json.dumps({'meta': {'status': 'completed', 'full_completion_ms': round(full_completion_ms, 2)}}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'X-Accel-Buffering': 'no'})


@router.get('/history', response_model=ApiResponse, dependencies=[Depends(require_local_api_key)])
async def get_history() -> ApiResponse:
    messages = history_store.get_all()
    return ApiResponse(success=True, message='OK', data={'messages': messages, 'total': len(messages)})


@router.delete('/history', response_model=ApiResponse, dependencies=[Depends(require_local_api_key)])
async def clear_history() -> ApiResponse:
    count = history_store.clear()
    return ApiResponse(success=True, message='History cleared', data={'deleted_count': count})
