from __future__ import annotations

from app.rag_core.context.context_builder import RetrievedChunk
from app.shared.schemas import Citation


class CitationBuilder:
    def build(self, contexts: list[RetrievedChunk], include_citations: bool) -> list[Citation]:
        if not include_citations:
            return []

        citations: list[Citation] = []
        for ctx in contexts:
            citations.append(
                Citation(
                    source_id=ctx.source_id,
                    source_name=ctx.source_name,
                    chunk_id=ctx.chunk_id,
                    score=ctx.score,
                    snippet=self._shorten(ctx.text),
                )
            )
        return citations

    def _shorten(self, text: str, max_len: int = 240) -> str:
        clean = ' '.join(text.split())
        if len(clean) <= max_len:
            return clean
        return clean[: max_len - 3].rstrip() + '...'

