from __future__ import annotations

from dataclasses import dataclass

from app.retrieval import HybridRetriever


@dataclass
class RetrievedChunk:
    source_id: str
    source_name: str | None
    chunk_id: str | None
    text: str
    score: float
    metadata: dict[str, str | int] | None = None
    features: dict[str, float] | None = None


class ContextBuilder:
    def __init__(
        self,
        retriever: HybridRetriever | None = None,
    ) -> None:
        self.retriever = retriever or HybridRetriever()

    async def retrieve(self, question: str, top_k: int) -> list[RetrievedChunk]:
        output = await self.retriever.retrieve(question, top_k=max(1, top_k), debug=False)
        return [
            RetrievedChunk(
                source_id=item.source_id,
                source_name=item.source_name,
                chunk_id=item.chunk_id,
                text=item.text,
                score=round(item.final_score, 6),
                metadata=dict(item.metadata or {}),
                features=dict(item.features or {}),
            )
            for item in output.chunks
        ]
