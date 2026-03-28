from __future__ import annotations

from collections.abc import AsyncIterator

from app.rag_core.citation.citation_builder import CitationBuilder
from app.rag_core.context.context_builder import ContextBuilder
from app.rag_core.llm.ollama_client import OllamaClient
from app.rag_core.prompt.prompt_builder import PromptBuilder
from app.shared.configs import settings
from app.shared.schemas import ChatRequest, ChatResponse
from app.shared.utils import timer


class ChatService:
    def __init__(
        self,
        context_builder: ContextBuilder | None = None,
        prompt_builder: PromptBuilder | None = None,
        llm_client: OllamaClient | None = None,
        citation_builder: CitationBuilder | None = None,
    ) -> None:
        self.context_builder = context_builder or ContextBuilder()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.llm_client = llm_client or OllamaClient()
        self.citation_builder = citation_builder or CitationBuilder()

    async def ask(self, payload: ChatRequest) -> ChatResponse:
        with timer() as t:
            contexts = await self.context_builder.retrieve(payload.question, payload.top_k)
            prompt = self.prompt_builder.build(payload.question, contexts)
            answer = await self.llm_client.generate(prompt)
            citations = self.citation_builder.build(contexts, payload.include_citations)

        return ChatResponse(
            answer=answer,
            citations=citations,
            model=settings.ollama_model,
            latency_ms=t.elapsed_ms,
            conversation_id=payload.conversation_id,
        )

    async def ask_stream(self, payload: ChatRequest) -> AsyncIterator[str]:
        contexts = await self.context_builder.retrieve(payload.question, payload.top_k)
        prompt = self.prompt_builder.build(payload.question, contexts)
        async for token in self.llm_client.stream_generate(prompt):
            yield token
