from __future__ import annotations

from app.rag_core.context.context_builder import RetrievedChunk
from app.shared.configs import settings


class PromptBuilder:
    def build(self, question: str, contexts: list[RetrievedChunk], mode: str = 'document_qa') -> str:
        context_block = self._build_context_block(contexts)
        instructions = self._mode_instructions(mode)
        return (
            'Bạn là trợ lý AI cho một hệ thống RAG local-first chạy bằng Ollama. '
            'Mục tiêu là trả lời chính xác, rõ ràng, có căn cứ từ ngữ cảnh truy xuất được, '
            'và không suy diễn quá mức ngoài tài liệu.\n\n'
            f'### Chế độ\n{mode}\n\n'
            f'### Câu hỏi\n{question}\n\n'
            f'### Ngữ cảnh\n{context_block}\n\n'
            '### Quy tắc bắt buộc\n'
            '- Trả lời bằng tiếng Việt.\n'
            '- Viết trọn ý, không cắt ngang.\n'
            '- Chỉ khẳng định điều gì khi có bằng chứng trong ngữ cảnh.\n'
            '- Nếu thiếu dữ liệu, nói rõ thiếu gì hoặc phần nào chưa chắc chắn.\n'
            '- Khi viện dẫn tài liệu, ưu tiên gọi theo [1], [2], [3] tương ứng với ngữ cảnh.\n\n'
            f'### Chỉ dẫn riêng\n{instructions}\n\n'
            f'### Giới hạn ngữ cảnh mỗi chunk\n{settings.prompt_max_context_chars_per_chunk} ký tự\n'
            f'### Tổng ngân sách ngữ cảnh\n{settings.prompt_max_total_context_chars} ký tự'
        )

    def _mode_instructions(self, mode: str) -> str:
        if mode == 'reasoning_over_docs':
            return (
                '- Tách rõ: dữ kiện quan sát được, suy luận hợp lý, và kết luận.\n'
                '- Không kéo kết luận vượt quá bằng chứng.\n'
                '- Nếu có nhiều khả năng, nêu khả năng chính và độ chắc chắn tương đối.'
            )
        if mode == 'system_metadata':
            return (
                '- Ưu tiên số liệu, trạng thái hệ thống, model, backend index, thời điểm build.\n'
                '- Không dùng giọng phỏng đoán. Nếu metadata không có, nói là chưa có metadata tương ứng.'
            )
        return (
            '- Trả lời trực tiếp câu hỏi dựa trên tài liệu.\n'
            '- Sau khi trả lời ngắn gọn, có thể mở rộng thêm 1-2 ý nếu thực sự được hỗ trợ bởi ngữ cảnh.'
        )

    def _build_context_block(self, contexts: list[RetrievedChunk]) -> str:
        if not contexts:
            return 'Không có ngữ cảnh truy xuất được.'

        lines: list[str] = []
        total_chars = 0
        for idx, ctx in enumerate(contexts, start=1):
            title = ctx.source_name or ctx.source_id
            meta = ctx.metadata or {}
            page = f" | page: {meta.get('page')}" if meta.get('page') is not None else ''
            section = f" | section: {meta.get('section') or meta.get('heading')}" if meta.get('section') or meta.get('heading') else ''
            relative_path = meta.get('relative_path') or meta.get('file_path')
            path_info = f' | path: {relative_path}' if relative_path else ''
            header = f'[{idx}] Nguồn: {title} | chunk: {ctx.chunk_id} | score: {ctx.score:.4f}{page}{section}{path_info}'
            text = ctx.text.strip()
            if len(text) > settings.prompt_max_context_chars_per_chunk:
                text = text[: settings.prompt_max_context_chars_per_chunk].rstrip() + '...'
            projected = total_chars + len(header) + len(text)
            if projected > settings.prompt_max_total_context_chars and lines:
                break
            lines.append(header)
            lines.append(text)
            lines.append('')
            total_chars = projected
        return '\n'.join(lines).strip()
