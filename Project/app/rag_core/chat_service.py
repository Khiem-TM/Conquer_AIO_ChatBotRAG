from __future__ import annotations

import httpx

from app.shared.configs import settings
from app.shared.schemas import ChatRequest, ChatResponse, Citation
from app.shared.utils import get_logger, timer

logger = get_logger(__name__)


class ChatService:
    async def ask(self, payload: ChatRequest) -> ChatResponse:
        with timer() as t:
            answer = await self._call_ollama(payload.question)

        citations = [
            Citation(
                source_id='retrieval_stub_1',
                source_name='sample_source',
                chunk_id='chunk_001',
                score=0.0,
                snippet='This is a placeholder citation. Replace with real retrieval output.',
            )
        ]

        return ChatResponse(
            answer=answer,
            citations=citations if payload.include_citations else [],
            model=settings.ollama_model,
            latency_ms=t.elapsed_ms,
            conversation_id=payload.conversation_id,
        )

    async def _call_ollama(self, question: str) -> str:
        url = f"{settings.ollama_base_url}/api/generate"
        req = {
            'model': settings.ollama_model,
            'prompt': question,
            'stream': False,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.post(url, json=req)
                response.raise_for_status()
                data = response.json()
            return data.get('response', '').strip() or 'No response from model.'
        except Exception as exc:
            logger.exception('Failed to call Ollama: %s', exc)
            return 'Model service is unavailable. Please try again later.'
