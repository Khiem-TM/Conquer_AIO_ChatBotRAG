from __future__ import annotations

from app.rag_core.context.context_builder import RetrievedChunk


class PromptBuilder:
    def build(self, question: str, contexts: list[RetrievedChunk]) -> str:
        context_block = self._build_context_block(contexts)
        return (
            'Bạn là trợ lý AI cho hệ thống RAG. '\
            'Hãy trả lời ngắn gọn, đúng trọng tâm, bám sát ngữ cảnh được cung cấp. '\
            'Nếu ngữ cảnh không đủ, hãy nói rõ mức độ không chắc chắn.\n\n'
            f'### Câu hỏi\n{question}\n\n'
            f'### Ngữ cảnh\n{context_block}\n\n'
            '### Yêu cầu trả lời\n'
            '- Trả lời bằng tiếng Việt.\n'
            '- Ưu tiên thông tin có trong ngữ cảnh.\n'
            '- Không bịa thêm thông tin ngoài ngữ cảnh.'
        )

    def _build_context_block(self, contexts: list[RetrievedChunk]) -> str:
        if not contexts:
            return 'Không có ngữ cảnh truy xuất được.'

        lines: list[str] = []
        for idx, ctx in enumerate(contexts, start=1):
            title = ctx.source_name or ctx.source_id
            lines.append(f'[{idx}] Nguồn: {title} | chunk: {ctx.chunk_id} | score: {ctx.score:.4f}')
            lines.append(ctx.text)
            lines.append('')
        return '\n'.join(lines).strip()

