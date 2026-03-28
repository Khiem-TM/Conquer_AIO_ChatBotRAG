from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.documents import Document


@dataclass
class ParsedRecord:
    text: str
    metadata: dict


class DocumentParser:
    """Normalize loaded documents into chunk-ready records."""

    def parse(self, docs: list[Document], file_path: Path) -> list[ParsedRecord]:
        records: list[ParsedRecord] = []
        for idx, doc in enumerate(docs, start=1):
            text = self._clean_text(doc.page_content)
            if not text:
                continue

            metadata = {
                'doc_id': self._build_doc_id(file_path),
                'source_name': file_path.name,
                'source_path': str(file_path),
                'file_ext': file_path.suffix.lower(),
                'page': doc.metadata.get('page'),
                'section': doc.metadata.get('section'),
                'record_index': idx,
                'ingested_at': datetime.now(timezone.utc).isoformat(),
            }
            records.append(ParsedRecord(text=text, metadata=metadata))

        return records

    def _clean_text(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines()]
        normalized = '\n'.join(line for line in lines if line)
        return normalized.strip()

    def _build_doc_id(self, file_path: Path) -> str:
        return file_path.stem.lower().replace(' ', '_')

