from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

from app.indexing.index_service import IndexNotReadyError, IndexingService
from app.rag_core.citation.citation_builder import CitationBuilder
from app.rag_core.context.context_builder import ContextBuilder, RetrievedChunk
from app.retrieval import HybridRetriever
from app.rag_core.llm.ollama_client import OllamaClient
from app.rag_core.prompt.prompt_builder import PromptBuilder
from app.shared.configs import settings
from app.shared.schemas import ChatRequest, ChatResponse
from app.shared.utils import timer


@dataclass
class PreparedAnswer:
    mode: str
    question: str
    prompt: str
    contexts: list[RetrievedChunk]
    citations_enabled: bool
    metadata: dict[str, object]
    confidence: str


class ChatService:
    def __init__(
        self,
        context_builder: ContextBuilder | None = None,
        prompt_builder: PromptBuilder | None = None,
        llm_client: OllamaClient | None = None,
        citation_builder: CitationBuilder | None = None,
        indexing_service: IndexingService | None = None,
    ) -> None:
        self.indexing_service = indexing_service or IndexingService()
        self.context_builder = context_builder or ContextBuilder(
            retriever=HybridRetriever(indexing_service=self.indexing_service)
        )
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.llm_client = llm_client or OllamaClient()
        self.citation_builder = citation_builder or CitationBuilder()

    async def prepare(self, payload: ChatRequest) -> PreparedAnswer:
        mode, intent_confidence = self._detect_mode(payload.question)
        if mode == 'system_metadata':
            metadata = await self._collect_system_metadata()
            contexts = self._metadata_contexts(metadata)
            prompt = self.prompt_builder.build(payload.question, contexts, mode=mode)
            confidence = 'high'
        else:
            contexts = await self.context_builder.retrieve(payload.question, payload.top_k)
            if not contexts and self._is_global_summary_request(payload.question):
                contexts = await self._collect_global_summary_contexts(max_sources=max(3, payload.top_k))
                if contexts:
                    mode = 'reasoning_over_docs'
                    intent_confidence = max(intent_confidence, 0.82)
            metadata = {'retrieved_contexts': len(contexts), 'intent_confidence': intent_confidence}
            prompt = self.prompt_builder.build(payload.question, contexts, mode=mode)
            confidence = 'high' if len(contexts) >= 3 else 'medium' if contexts else 'low'
        return PreparedAnswer(
            mode=mode,
            question=payload.question,
            prompt=prompt,
            contexts=contexts,
            citations_enabled=payload.include_citations,
            metadata=metadata,
            confidence=confidence,
        )

    async def ask(self, payload: ChatRequest) -> ChatResponse:
        with timer() as t:
            prepared = await self.prepare(payload)
            if prepared.mode == 'system_metadata':
                answer = self._render_system_metadata_answer(prepared.metadata)
            else:
                answer = await self.llm_client.generate(prepared.prompt)
            answer = self._finalize_answer(answer, prepared.mode)
            citations = self.citation_builder.build(prepared.contexts, prepared.citations_enabled)

        return ChatResponse(
            answer=answer,
            citations=citations,
            model=settings.ollama_model,
            latency_ms=t.elapsed_ms,
            conversation_id=payload.conversation_id,
            mode=prepared.mode,
            confidence=prepared.confidence,
            metadata=prepared.metadata,
        )

    async def ask_stream(self, payload: ChatRequest) -> AsyncIterator[str]:
        prepared = await self.prepare(payload)
        if prepared.mode == 'system_metadata':
            yield self._render_system_metadata_answer(prepared.metadata)
            return
        async for token in self.llm_client.stream_generate(prepared.prompt):
            yield token

    def _detect_mode(self, question: str) -> tuple[str, float]:
        q = question.lower().strip()

        # --- system_metadata signals ---
        # High-confidence triggers: user asks about the RAG system itself
        system_strong = {
            'metadata', 'system', 'hệ thống', 'he thong',
            'embedding model', 'embedding backend',
            'index status', 'index backend', 'index metadata',
            'ingest status', 'ingest history', 'lịch sử ingest', 'lich su ingest',
            'bao nhiêu chunk', 'bao nhieu chunk',
            'bao nhiêu tài liệu', 'bao nhieu tai lieu',
            'bao nhiêu document', 'how many document',
            'trạng thái hệ thống', 'trang thai he thong',
            'số lượng chunk', 'so luong chunk',
            'số lượng tài liệu', 'so luong tai lieu',
            'database backend', 'vector store',
            'chunker version', 'schema version',
        }
        # Ambiguous triggers: only count when paired with another system signal
        system_weak = {
            'model', 'backend', 'database', 'db',
            'trạng thái', 'trang thai',
            'số lượng', 'so luong',
        }

        strong_hits = sum(1 for term in system_strong if term in q)
        weak_hits = sum(1 for term in system_weak if term in q)

        # Require at least 1 strong signal, or 2 weak signals, to route as system_metadata.
        # Explicitly guard against "bao nhiêu tài liệu nói về X" being mis-classified.
        _doc_content_phrases = {'nói về', 'noi ve', 'đề cập', 'de cap', 'giải thích', 'giai thich', 'liên quan', 'lien quan'}
        is_about_doc_content = any(phrase in q for phrase in _doc_content_phrases)

        if not is_about_doc_content and (strong_hits >= 1 or weak_hits >= 2):
            confidence = min(1.0, 0.60 + 0.12 * (strong_hits + 0.5 * weak_hits))
            return 'system_metadata', confidence

        # --- reasoning_over_docs signals ---
        reasoning_terms = {
            'so sánh', 'so sanh', 'compare',
            'đánh giá', 'danh gia', 'evaluate', 'assess',
            'nguyên nhân', 'nguyen nhan', 'cause', 'reason',
            'kết luận', 'ket luan', 'conclude', 'conclusion',
            'phân tích', 'phan tich', 'analyze', 'analyse',
            'ưu nhược điểm', 'uu nhuoc diem', 'pros and cons', 'advantages',
            'tổng kết', 'tong ket', 'tóm tắt', 'tom tat', 'summarize', 'summary',
            'suy luận', 'suy luan', 'infer', 'inference',
        }
        reasoning_score = sum(1 for term in reasoning_terms if term in q)
        if reasoning_score >= 1:
            return 'reasoning_over_docs', min(1.0, 0.55 + 0.12 * reasoning_score)

        return 'document_qa', 0.65

    def _is_global_summary_request(self, question: str) -> bool:
        q = question.lower().strip()
        summary_terms = {
            'tóm tắt tài liệu', 'tom tat tai lieu',
            'tóm tắt các tài liệu', 'tom tat cac tai lieu',
            'tóm tắt tất cả tài liệu', 'tom tat tat ca tai lieu',
            'tổng kết tài liệu', 'tong ket tai lieu',
            'summary of documents', 'summarize the documents', 'summarize all documents',
        }
        return any(term in q for term in summary_terms)

    async def _collect_global_summary_contexts(self, max_sources: int = 5) -> list[RetrievedChunk]:
        try:
            snapshot = await self.indexing_service.get_index_snapshot()
        except IndexNotReadyError:
            return []

        chunks = list(snapshot.get('chunks', []))
        if not chunks:
            return []

        selected: list[RetrievedChunk] = []
        seen_sources: set[str] = set()

        for item in chunks:
            source_id = str(item.get('source_id', ''))
            if source_id in seen_sources:
                continue
            seen_sources.add(source_id)
            selected.append(
                RetrievedChunk(
                    source_id=source_id,
                    source_name=str(item.get('source_name') or source_id),
                    chunk_id=str(item.get('chunk_id', '')) or None,
                    text=str(item.get('text', '')),
                    score=1.0,
                    metadata=dict(item.get('metadata', {}) or {}),
                )
            )
            if len(selected) >= max(1, max_sources):
                break

        return selected

    async def _collect_system_metadata(self) -> dict[str, object]:
        snapshot = None
        try:
            snapshot = await self.indexing_service.get_index_snapshot()
        except IndexNotReadyError:
            snapshot = None

        data_input_dir = Path(settings.index_data_input_dir)
        files = []
        if data_input_dir.exists():
            files = sorted(
                p.relative_to(data_input_dir).as_posix()
                for p in data_input_dir.rglob('*')
                if p.is_file() and not p.name.startswith('.')
            )
        docs_count = len(files)
        chunk_count = len(snapshot.get('chunks', [])) if snapshot else 0
        indexed_sources = len(snapshot.get('sources', {})) if snapshot else 0
        manifest = dict(snapshot.get('manifest', {})) if snapshot else {}
        return {
            'document_count': docs_count,
            'chunk_count': chunk_count,
            'indexed_source_count': indexed_sources,
            'documents': files,
            'index_ready': bool(snapshot),
            'index_built_at': snapshot.get('built_at') if snapshot else None,
            'embedding_model': snapshot.get('embedding_model') if snapshot else settings.embedding_model,
            'embedding_backend': snapshot.get('embedding_backend') if snapshot else 'pending',
            'generation_model': settings.ollama_model,
            'reranker_model': settings.ollama_reranker_model,
            'vector_backend': settings.index_store_backend,
            'chunker_version': snapshot.get('chunker_version') if snapshot else settings.index_chunker_version,
            'schema_version': snapshot.get('schema_version') if snapshot else settings.index_schema_version,
            'manifest': manifest,
        }

    def _metadata_contexts(self, metadata: dict[str, object]) -> list[RetrievedChunk]:
        docs = metadata.get('documents') or []
        manifest = metadata.get('manifest') or {}
        summary = (
            f"Database local hiện có {metadata.get('document_count', 0)} tài liệu gốc, "
            f"{metadata.get('chunk_count', 0)} chunks, {metadata.get('indexed_source_count', 0)} nguồn đã index. "
            f"Generation model: {metadata.get('generation_model')}. Embedding model: {metadata.get('embedding_model')}. "
            f"Index backend: {metadata.get('vector_backend')}. Chunker: {metadata.get('chunker_version')}. "
            f"Built at: {metadata.get('index_built_at')}. Manifest: {manifest}."
        )
        contexts = [
            RetrievedChunk(
                source_id='system_metadata',
                source_name='System metadata',
                chunk_id='system_metadata_chunk_001',
                text=summary,
                score=1.0,
                metadata={},
            )
        ]
        if docs:
            contexts.append(
                RetrievedChunk(
                    source_id='system_documents',
                    source_name='Document registry',
                    chunk_id='system_documents_chunk_001',
                    text='Các tài liệu hiện có: ' + ', '.join(str(item) for item in docs[:50]),
                    score=0.95,
                    metadata={},
                )
            )
        return contexts

    def _finalize_answer(self, answer: str, mode: str) -> str:
        text = ' '.join((answer or '').split()).strip()
        if not text:
            return 'Tôi chưa tạo được câu trả lời từ dữ liệu hiện có.'
        if text[-1] not in '.!?…':
            text += '.'
        if mode == 'system_metadata' and 'database' not in text.lower() and 'tài liệu' not in text.lower():
            text = 'Dựa trên metadata hệ thống hiện có: ' + text
        return text

    def _render_system_metadata_answer(self, metadata: dict[str, object]) -> str:
        docs = int(metadata.get('document_count', 0) or 0)
        chunks = int(metadata.get('chunk_count', 0) or 0)
        sources = int(metadata.get('indexed_source_count', 0) or 0)
        model = metadata.get('generation_model')
        embed = metadata.get('embedding_model')
        built_at = metadata.get('index_built_at') or 'chưa có'
        chunker_version = metadata.get('chunker_version') or settings.index_chunker_version
        answer = (
            f"Hiện hệ thống local có {docs} tài liệu gốc, {chunks} chunks đã index và {sources} nguồn trong index. "
            f"Model sinh câu trả lời đang cấu hình là {model}, model embedding là {embed}, chunker version là {chunker_version}. "
            f"Thời điểm build index gần nhất: {built_at}."
        )
        file_names = metadata.get('documents') or []
        if file_names:
            doc_text = ', '.join(str(name) for name in file_names[:8])
            if len(file_names) > 8:
                doc_text += f', và {len(file_names) - 8} tài liệu khác'
            answer += f' Các tài liệu hiện có gồm: {doc_text}.'
        manifest = metadata.get('manifest') or {}
        if manifest:
            answer += f' Manifest local: {manifest}.'
        return answer
