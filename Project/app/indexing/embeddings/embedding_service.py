from __future__ import annotations

"""Các hàm hỗ trợ biến text thành vector embedding.

File này là trung tâm của phần "embedding" trong lane người 2. Nó chịu trách
nhiệm:
- gọi Ollama để lấy embedding thật nếu endpoint sẵn sàng
- fallback sang hashed embedding nếu môi trường local chưa hỗ trợ đầy đủ
- chuẩn hóa vector trước khi lưu vào index
"""

import hashlib
import math
import re

try:
    import httpx
except ModuleNotFoundError:
    httpx = None

from app.indexing.config import settings
from app.shared.utils import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Lớp chịu trách nhiệm encode text/query thành vector.

    Đây là nơi người 2 chốt cách tạo embedding. Các tầng khác không cần biết
    chi tiết Ollama hay fallback hoạt động ra sao, chỉ cần gọi qua class này.
    """

    async def embed_texts(self, texts: list[str]) -> tuple[list[list[float]], str]:
        """Tạo embedding cho danh sách chunk text.

        Đây là hàm chính được `IndexingService` gọi khi build hoặc rebuild index.
        Luồng xử lý:
        1. Thử gọi Ollama để lấy embedding thật.
        2. Nếu thành công, trả về danh sách vector và backend `ollama`.
        3. Nếu thất bại, fallback sang hashed embedding và trả về backend `simple`.

        Input:
        - `texts`: danh sách đoạn văn đã được chunk

        Output:
        - tuple gồm:
          - danh sách vector embedding
          - tên backend đang dùng (`ollama` hoặc `simple`)
        """

        ollama_vectors = await self._embed_texts_with_ollama(texts)
        if ollama_vectors:
            return ollama_vectors, 'ollama'

        # Keep the package runnable even when Ollama embedding endpoints are unavailable.
        logger.info('Using local hashed embeddings for index build.')
        return self._embed_texts_with_hashing(texts), 'simple'

    async def embed_query(self, question: str, embedding_backend: str) -> list[float]:
        """Tạo embedding cho một câu hỏi hoặc query đơn lẻ.

        Hàm này chủ yếu phục vụ bước truy xuất sau này. Ý tưởng là query nên
        được encode bằng cùng kiểu backend đã dùng khi build index, để vector
        của query và vector của chunk cùng nằm trong một không gian biểu diễn.

        Input:
        - `question`: câu hỏi hoặc câu truy vấn cần encode
        - `embedding_backend`: backend đã dùng lúc build index

        Output:
        - một vector đại diện cho query

        Nếu backend là `ollama` nhưng gọi thật bị lỗi, hàm trả về list rỗng để
        tầng trên có thể tự quyết định fallback tiếp theo.
        """

        if embedding_backend == 'ollama':
            ollama_vectors = await self._embed_texts_with_ollama([question])
            if ollama_vectors:
                return ollama_vectors[0]
            logger.warning('Ollama query embedding failed, using keyword-only fallback for search.')
            return []

        return self._embed_texts_with_hashing([question])[0]

    async def _embed_texts_with_ollama(self, texts: list[str]) -> list[list[float]] | None:
        """Thử lấy embedding từ Ollama cho một hoặc nhiều đoạn text.

        Hàm này hỗ trợ cả hai kiểu API phổ biến của Ollama:
        - `/api/embed` cho batch embedding ở các bản mới
        - `/api/embeddings` cho các bản cũ hơn

        Input:
        - `texts`: danh sách text cần embedding

        Output:
        - danh sách vector đã normalize nếu gọi thành công
        - `None` nếu cả hai endpoint đều thất bại
        """

        if not texts:
            return []
        if httpx is None:
            logger.warning('httpx is not installed, skipping Ollama embedding and using hashed fallback.')
            return None

        # Embedding calls must fail fast to avoid blocking /chat for many minutes.
        embed_timeout = max(8, min(20, settings.request_timeout_seconds))

        try:
            # Newer Ollama versions expose batch embedding through /api/embed.
            async with httpx.AsyncClient(timeout=embed_timeout) as client:
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

        # Legacy endpoint is one-request-per-text; keep a strict cap for large batches.
        if len(texts) > 12:
            logger.warning(
                'Skip /api/embeddings fallback for large batch size=%s to avoid long rebuild.',
                len(texts),
            )
            return None

        legacy_vectors: list[list[float]] = []
        try:
            # Fallback for older Ollama versions that still use /api/embeddings.
            async with httpx.AsyncClient(timeout=embed_timeout) as client:
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
        """Sinh vector fallback bằng kỹ thuật hashing token đơn giản.

        Đây không phải embedding ngữ nghĩa mạnh như model thật, nhưng đủ để:
        - minh họa pipeline của người 2
        - giữ cho code chạy được ở môi trường local
        - tránh phụ thuộc vào quá nhiều thư viện ngoài

        Input:
        - `texts`: danh sách text cần vector hóa

        Output:
        - danh sách vector có số chiều cố định theo `EMBEDDING_DIMENSIONS`
        """

        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * settings.embedding_dimensions
            for token in self._tokenize(text):
                # Hash tokens into a fixed-size vector so the demo works without extra libraries.
                hashed_value = hashlib.md5(token.encode('utf-8')).hexdigest()
                index = int(hashed_value, 16) % settings.embedding_dimensions
                vector[index] += 1.0
            vectors.append(self._normalize_vector(vector))
        return vectors

    def _tokenize(self, text: str) -> list[str]:
        """Tách text thành các token đơn giản theo regex.

        Hàm này chỉ giữ các token có độ dài lớn hơn 1 để giảm bớt nhiễu do các
        ký tự quá ngắn. Nó được dùng cho hashed embedding fallback.
        """

        return [token for token in re.findall(r'\w+', text.lower()) if len(token) > 1]

    def _normalize_vector(self, vector: list[float]) -> list[float]:
        """Chuẩn hóa vector về độ dài 1.

        Việc normalize giúp các vector có cùng thang đo, thuận lợi hơn cho các
        phép so sánh độ tương đồng như cosine similarity ở các tầng sau.
        """

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [round(value / norm, 6) for value in vector]
