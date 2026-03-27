from __future__ import annotations

import hashlib
import math
import re

import httpx

from app.indexing.config import settings
from app.shared.utils import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    async def embed_texts(self, texts: list[str]) -> tuple[list[list[float]], str]:
        ollama_vectors = await self._embed_texts_with_ollama(texts)
        if ollama_vectors:
            return ollama_vectors, 'ollama'

        logger.info('Using local hashed embeddings for index build.')
        return self._embed_texts_with_hashing(texts), 'simple'

    async def embed_query(self, question: str, embedding_backend: str) -> list[float]:
        if embedding_backend == 'ollama':
            ollama_vectors = await self._embed_texts_with_ollama([question])
            if ollama_vectors:
                return ollama_vectors[0]
            logger.warning('Ollama query embedding failed, using keyword-only fallback for search.')
            return []

        return self._embed_texts_with_hashing([question])[0]

    async def _embed_texts_with_ollama(self, texts: list[str]) -> list[list[float]] | None:
        if not texts:
            return []

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.post(
                    f'{settings.ollama_base_url}/api/embed',
                    json={'model': settings.embedding_model, 'input': texts},
                )
                response.raise_for_status()
                data = response.json()
            embeddings = data.get('embeddings', [])
            if embeddings and len(embeddings) == len(texts):
                return [self._normalize_vector(list(map(float, embedding))) for embedding in embeddings]
        except Exception as exc:
            logger.warning('Ollama /api/embed is unavailable: %s', exc)

        legacy_vectors: list[list[float]] = []
        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                for text in texts:
                    response = await client.post(
                        f'{settings.ollama_base_url}/api/embeddings',
                        json={'model': settings.embedding_model, 'prompt': text},
                    )
                    response.raise_for_status()
                    data = response.json()
                    embedding = data.get('embedding')
                    if not embedding:
                        return None
                    legacy_vectors.append(self._normalize_vector(list(map(float, embedding))))
            return legacy_vectors if len(legacy_vectors) == len(texts) else None
        except Exception as exc:
            logger.warning('Ollama /api/embeddings is unavailable: %s', exc)
            return None

    def _embed_texts_with_hashing(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * settings.embedding_dimensions
            for token in self._tokenize(text):
                hashed_value = hashlib.md5(token.encode('utf-8')).hexdigest()
                index = int(hashed_value, 16) % settings.embedding_dimensions
                vector[index] += 1.0
            vectors.append(self._normalize_vector(vector))
        return vectors

    def _tokenize(self, text: str) -> list[str]:
        return [token for token in re.findall(r'\w+', text.lower()) if len(token) > 1]

    def _normalize_vector(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [round(value / norm, 6) for value in vector]
