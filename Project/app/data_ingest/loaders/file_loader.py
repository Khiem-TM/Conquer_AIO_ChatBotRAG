from __future__ import annotations

from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document


class FileLoader:
    """Load raw documents from supported file types."""

    SUPPORTED_EXTENSIONS = {'.docx', '.txt', '.pdf', '.md'}

    def load_from_path(self, file_path: Path) -> list[Document]:
        ext = file_path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return []

        loader = self._build_loader(file_path, ext)
        docs = loader.load()

        for doc in docs:
            doc.metadata['source_path'] = str(file_path)
            doc.metadata['source_name'] = file_path.name
            doc.metadata['file_ext'] = ext

        return docs

    def _build_loader(self, file_path: Path, ext: str):
        if ext == '.docx':
            return Docx2txtLoader(str(file_path))
        if ext == '.pdf':
            return PyPDFLoader(str(file_path))
        return TextLoader(str(file_path), encoding='utf-8', autodetect_encoding=True)

