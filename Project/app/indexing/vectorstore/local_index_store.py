from __future__ import annotations

"""Local JSON-backed store dùng để lưu và quản lý index của người 2.

File này không cố gắng trở thành một vector database hoàn chỉnh. Vai trò chính
của nó là:
- đọc dữ liệu đầu vào từ thư mục local
- chuẩn bị chunk records để đi embedding
- lưu snapshot index ra JSON
- chuẩn hóa metadata để người 3 có thể nhận lại dễ dàng
"""

import json
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.indexing.config import settings
from app.indexing.schemas import IndexOperationResult, IndexStatus
from app.shared.utils import get_logger

logger = get_logger(__name__)


class LocalIndexStore:
    """Store local tối giản để lưu snapshot index ở dạng JSON.

    Class này tập trung vào thao tác dữ liệu và metadata của index, không tự xử
    lý embedding và cũng không tham gia vào logic prompt/chat.
    """

    def __init__(self) -> None:
        """Khởi tạo store cục bộ cho index.

        `self._index_data` được dùng như cache trong bộ nhớ để tránh phải đọc
        lại file JSON nhiều lần trong cùng một tiến trình.

        `self._project_dir` giúp resolve các đường dẫn tương đối như
        `data_input` hoặc `data/index_store.json` từ đúng gốc thư mục `Project`.
        """

        self._index_data: dict[str, Any] | None = None
        self._project_dir = Path(__file__).resolve().parents[3]

    def load_index_data(self) -> dict[str, Any] | None:
        """Đọc dữ liệu index hiện tại từ file JSON.

        Luồng xử lý:
        1. Nếu đã có cache trong bộ nhớ thì trả về luôn.
        2. Nếu file index chưa tồn tại thì trả về `None`.
        3. Nếu file có tồn tại thì đọc JSON và lưu lại vào cache.

        Output:
        - `dict` chứa toàn bộ snapshot index
        - `None` nếu index chưa được tạo
        """

        if self._index_data is not None:
            return self._index_data

        storage_path = self.get_storage_path()
        if not storage_path.exists():
            return None

        self._index_data = json.loads(storage_path.read_text(encoding='utf-8'))
        return self._index_data

    def write_index_data(self, index_data: dict[str, Any]) -> None:
        """Ghi toàn bộ snapshot index xuống file JSON.

        Input:
        - `index_data`: dictionary chứa sources, chunks, embedding backend,
          embedding model và thời điểm build

        Hàm này cũng cập nhật lại cache trong bộ nhớ để các lời gọi sau không
        cần đọc file lại ngay lập tức.
        """

        storage_path = self.get_storage_path()
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_text(json.dumps(index_data, ensure_ascii=False, indent=2), encoding='utf-8')
        self._index_data = index_data

    def scan_source_files(self) -> list[Path]:
        """Quét thư mục input và lấy danh sách file nguồn hợp lệ.

        Hiện tại store hỗ trợ `.md`, `.txt`, `.docx`, `.pdf`.
        File tạm kiểu `~$...` sẽ bị bỏ qua để tránh index nhầm các file lock do
        editor tạo ra.

        Output:
        - danh sách `Path` đã được sắp xếp
        """

        data_input_dir = self.get_data_input_dir()
        if not data_input_dir.exists():
            logger.warning('data_input directory does not exist: %s', data_input_dir)
            return []

        supported_extensions = {'.md', '.txt', '.docx', '.pdf'}
        return [
            file_path
            for file_path in sorted(data_input_dir.rglob('*'))
            if file_path.is_file()
            and file_path.suffix.lower() in supported_extensions
            and not file_path.name.startswith('~$')
        ]

    def prepare_chunk_records(self, source_files: list[Path]) -> tuple[list[dict[str, Any]], list[str]]:
        """Biến danh sách file nguồn thành các chunk record sẵn sàng để embedding.

        Input:
        - `source_files`: danh sách file sẽ được đưa vào index

        Output:
        - `raw_chunks`: danh sách object chunk kèm metadata cơ bản
        - `texts`: danh sách text tương ứng để đưa sang `EmbeddingService`

        Đây là bước trung gian rất quan trọng vì nó tách rõ:
        - store lo việc đọc file, chia chunk, tạo metadata
        - embedding service chỉ lo biến text thành vector
        """

        raw_chunks: list[dict[str, Any]] = []
        texts: list[str] = []

        for file_path in source_files:
            text = self.read_source_text(file_path)
            if not text:
                continue

            chunks = self.split_text(text)
            source_id = self.build_source_id(file_path)
            for index, chunk_text in enumerate(chunks, start=1):
                cleaned_text = chunk_text.strip()
                if not cleaned_text:
                    continue

                raw_chunks.append(
                    {
                        'source_id': source_id,
                        'source_name': file_path.name,
                        'chunk_id': f'{source_id}_chunk_{index:03d}',
                        'text': cleaned_text,
                    }
                )
                texts.append(cleaned_text)

        return raw_chunks, texts

    def build_sources_payload(self, source_files: list[Path]) -> dict[str, dict[str, Any]]:
        """Tạo metadata cấp source cho toàn bộ file đầu vào.

        Output của hàm này được lưu vào trường `sources` trong snapshot index.
        Nó giúp các tầng sau biết:
        - source này đến từ file nào
        - tên file là gì
        - thời điểm file được sửa gần nhất
        """

        return {
            self.build_source_id(file_path): {
                'source_name': file_path.name,
                'file_path': str(file_path),
                'updated_at_ns': file_path.stat().st_mtime_ns,
            }
            for file_path in source_files
        }

    def build_status_response(self, index_data: dict[str, Any] | None) -> IndexStatus:
        """Chuyển snapshot index thành schema trạng thái gọn nhẹ.

        Hàm này phù hợp cho các lệnh kiểm tra nhanh như `status`, khi người dùng
        chỉ cần biết index có tồn tại, đang dùng model nào, và có bao nhiêu
        source/chunk.
        """

        if not index_data:
            return IndexStatus(embedding_model=settings.embedding_model)

        return IndexStatus(
            ready=bool(index_data.get('chunks')),
            embedding_backend=index_data.get('embedding_backend', 'pending'),
            embedding_model=index_data.get('embedding_model', settings.embedding_model),
            total_sources=len(index_data.get('sources', {})),
            total_chunks=len(index_data.get('chunks', [])),
            built_at=index_data.get('built_at'),
        )

    def build_operation_response(
        self,
        index_data: dict[str, Any],
        message: str,
        latency_ms: int,
        updated_sources: list[str],
        deleted_sources: list[str],
    ) -> IndexOperationResult:
        """Tạo response đầy đủ cho một thao tác có thay đổi trên index.

        Input:
        - `index_data`: snapshot sau khi thao tác hoàn tất
        - `message`: mô tả ngắn về thao tác vừa diễn ra
        - `latency_ms`: thời gian thực thi
        - `updated_sources`: danh sách source được thêm/cập nhật
        - `deleted_sources`: danh sách source bị xóa

        Output:
        - `IndexOperationResult`
        """

        status_response = self.build_status_response(index_data)
        return IndexOperationResult(
            ready=status_response.ready,
            embedding_backend=status_response.embedding_backend,
            embedding_model=status_response.embedding_model,
            total_sources=status_response.total_sources,
            total_chunks=status_response.total_chunks,
            built_at=status_response.built_at,
            message=message,
            latency_ms=latency_ms,
            updated_sources=updated_sources,
            deleted_sources=deleted_sources,
        )

    def empty_index_data(self) -> dict[str, Any]:
        """Tạo snapshot rỗng cho trường hợp index chưa tồn tại.

        Snapshot rỗng này hữu ích khi:
        - vừa khởi tạo project
        - chưa từng build index
        - cần fallback an toàn cho thao tác delete/status
        """

        return {
            'embedding_backend': 'pending',
            'embedding_model': settings.embedding_model,
            'built_at': None,
            'sources': {},
            'chunks': [],
        }

    def build_source_id(self, file_path: Path) -> str:
        """Sinh `source_id` ổn định từ đường dẫn file.

        `source_id` được tạo dựa trên path tương đối so với thư mục input.
        Dấu `/` được thay bằng `__` để id dễ dùng hơn trong JSON và CLI.
        """

        relative_path = file_path.relative_to(self.get_data_input_dir()).as_posix()
        return relative_path.replace('/', '__')

    def read_source_text(self, file_path: Path) -> str:
        """Đọc nội dung text từ một file nguồn.

        Hỗ trợ:
        - `.md`, `.txt`: đọc utf-8
        - `.docx`: trích text từ `word/document.xml`
        - `.pdf`: trích text bằng `pypdf`
        """

        suffix = file_path.suffix.lower()
        if suffix == '.docx':
            return self._read_docx_text(file_path)
        if suffix == '.pdf':
            return self._read_pdf_text(file_path)

        try:
            return file_path.read_text(encoding='utf-8').strip()
        except UnicodeDecodeError:
            return file_path.read_text(encoding='utf-8', errors='ignore').strip()

    def _read_docx_text(self, file_path: Path) -> str:
        try:
            with zipfile.ZipFile(file_path) as archive:
                xml_bytes = archive.read('word/document.xml')
        except Exception as exc:
            logger.warning('Failed to read DOCX source %s: %s', file_path, exc)
            return ''

        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as exc:
            logger.warning('Failed to parse DOCX XML %s: %s', file_path, exc)
            return ''

        text_nodes: list[str] = []
        for node in root.iter():
            if node.tag.endswith('}t') and node.text:
                text_nodes.append(node.text)

        return '\n'.join(text_nodes).strip()

    def _read_pdf_text(self, file_path: Path) -> str:
        try:
            from pypdf import PdfReader
        except ModuleNotFoundError:
            logger.warning('pypdf is not installed; skip PDF source %s', file_path)
            return ''

        try:
            reader = PdfReader(str(file_path))
            page_texts = [(page.extract_text() or '').strip() for page in reader.pages]
            return '\n\n'.join(text for text in page_texts if text).strip()
        except Exception as exc:
            logger.warning('Failed to read PDF source %s: %s', file_path, exc)
            return ''

    def split_text(self, text: str) -> list[str]:
        """Chia văn bản thành các chunk tương đối dễ hiểu.

        Chiến lược hiện tại:
        1. Ưu tiên tách theo các block/ngắt đoạn tự nhiên.
        2. Gộp các block nhỏ lại nếu tổng độ dài vẫn trong giới hạn.
        3. Nếu một block quá dài, chuyển sang `split_long_block()`.

        Mục tiêu là giữ được ý nghĩa của đoạn văn tốt hơn so với việc cắt máy
        móc hoàn toàn theo số ký tự ngay từ đầu.
        """

        blocks = [block.strip() for block in re.split(r'\n\s*\n', text) if block.strip()]
        chunks: list[str] = []
        current_chunk = ''

        for block in blocks:
            # Prefer paragraph-aware grouping before falling back to fixed-size slicing.
            next_chunk = f'{current_chunk}\n\n{block}'.strip() if current_chunk else block
            if len(next_chunk) <= settings.index_chunk_size:
                current_chunk = next_chunk
                continue

            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ''

            if len(block) <= settings.index_chunk_size:
                current_chunk = block
                continue

            chunks.extend(self.split_long_block(block))

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def split_long_block(self, text: str) -> list[str]:
        """Cắt một block dài thành nhiều phần có overlap.

        Hàm này chỉ được gọi khi một block riêng lẻ vẫn dài hơn giới hạn chunk.
        Overlap giúp giữ lại một phần ngữ cảnh ở đầu/cuối các chunk liên tiếp,
        giảm nguy cơ mất ý khi retrieval hoặc rerank đọc từng chunk riêng.
        """

        chunks: list[str] = []
        start = 0
        chunk_size = max(100, settings.index_chunk_size)
        overlap = max(0, min(settings.index_chunk_overlap, chunk_size // 2))

        while start < len(text):
            # Overlap keeps some context when a single paragraph is longer than chunk_size.
            end = min(len(text), start + chunk_size)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start = max(start + 1, end - overlap)

        return chunks

    def get_data_input_dir(self) -> Path:
        """Trả về đường dẫn tuyệt đối tới thư mục input của người 2."""

        return self.resolve_path(settings.data_input_dir)

    def get_storage_path(self) -> Path:
        """Trả về đường dẫn tuyệt đối tới file JSON lưu snapshot index."""

        return self.resolve_path(settings.index_storage_path)

    def utc_now(self) -> str:
        """Sinh timestamp UTC dạng ISO string để ghi vào snapshot."""

        return datetime.now(timezone.utc).isoformat()

    def resolve_path(self, value: str) -> Path:
        """Chuẩn hóa một path tương đối hoặc tuyệt đối.

        Nếu `value` đã là absolute path thì giữ nguyên.
        Nếu là relative path thì nối với thư mục gốc `Project` để việc chạy CLI
        hay import module từ nhiều nơi khác nhau vẫn cho ra cùng một đường dẫn.
        """

        path = Path(value)
        if path.is_absolute():
            return path
        return (self._project_dir / path).resolve()
