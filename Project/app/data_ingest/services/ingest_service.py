from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.data_ingest.loaders.file_loader import FileLoader
from app.data_ingest.parsers.document_parser import DocumentParser, ParsedRecord
from app.data_ingest.services.import_registry import ImportRegistry
from app.shared.utils import get_logger, timer

logger = get_logger(__name__)


@dataclass
class IngestResult:
    ingested_docs: int
    ingested_chunks: int
    imported_files_total: int
    import_registry_db: str
    message: str


class IngestService:
    def __init__(
        self,
        data_input_dir: str = 'data_input',
        chunk_size: int = 900,
        chunk_overlap: int = 120,
        loader: FileLoader | None = None,
        parser: DocumentParser | None = None,
        registry: ImportRegistry | None = None,
    ) -> None:
        self.data_input_dir = Path(data_input_dir)
        self.loader = loader or FileLoader()
        self.parser = parser or DocumentParser()
        self.registry = registry or ImportRegistry()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=['\n\n', '\n', '. ', ' '],
        )

    def run(self) -> IngestResult:
        with timer() as t:
            source_files = self._scan_source_files()
            all_records: list[ParsedRecord] = []

            for file_path in source_files:
                docs = self.loader.load_from_path(file_path)
                parsed = self.parser.parse(docs, file_path)
                all_records.extend(parsed)
                self.registry.upsert_file(
                    file_path=str(file_path.resolve()),
                    file_name=file_path.name,
                    file_ext=file_path.suffix.lower(),
                    file_size=file_path.stat().st_size,
                    updated_at_ns=file_path.stat().st_mtime_ns,
                    ingested_at=datetime.now(timezone.utc).isoformat(),
                )

            chunks = self._build_chunks(all_records)

        logger.info(
            'Ingest completed: docs=%s records=%s chunks=%s latency_ms=%s',
            len(source_files),
            len(all_records),
            len(chunks),
            t.elapsed_ms,
        )

        return IngestResult(
            ingested_docs=len(source_files),
            ingested_chunks=len(chunks),
            imported_files_total=self.registry.count_files(),
            import_registry_db=str(self.registry.db_path),
            message='Ingestion completed',
        )

    def _scan_source_files(self) -> list[Path]:
        if not self.data_input_dir.exists():
            logger.warning('data_input directory not found: %s', self.data_input_dir)
            return []

        return [
            path
            for path in sorted(self.data_input_dir.rglob('*'))
            if path.is_file() and path.suffix.lower() in FileLoader.SUPPORTED_EXTENSIONS
        ]

    def _build_chunks(self, records: list[ParsedRecord]) -> list[dict]:
        chunks: list[dict] = []
        for record in records:
            split_texts = self.splitter.split_text(record.text)
            for idx, text in enumerate(split_texts, start=1):
                chunks.append(
                    {
                        'chunk_id': f"{record.metadata['doc_id']}_chunk_{idx:03d}",
                        'text': text,
                        'metadata': record.metadata,
                    }
                )
        return chunks

