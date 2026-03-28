from __future__ import annotations

import httpx

from app.shared.configs import settings
from app.shared.utils import get_logger

logger = get_logger(__name__)


class OllamaClient:
    async def generate(self, prompt: str) -> str:
        candidates = self._candidate_urls(settings.ollama_base_url)
        payload = {
            'model': settings.ollama_model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'num_predict': 256,
                'temperature': 0.2,
            },
        }

        for base_url in candidates:
            try:
                async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                    response = await client.post(f'{base_url}/api/generate', json=payload)
                    response.raise_for_status()
                    data = response.json()
                return str(data.get('response', '')).strip() or 'No response from model.'
            except Exception as exc:
                logger.warning('Ollama call failed at %s: %s', base_url, exc)

        return self._fallback(prompt)

    def _candidate_urls(self, primary: str) -> list[str]:
        urls = [primary.rstrip('/')]
        for candidate in ['http://localhost:11434', 'http://127.0.0.1:11434']:
            if candidate not in urls:
                urls.append(candidate)
        return urls

    def _fallback(self, prompt: str) -> str:
        short_prompt = (prompt or '').replace('\n', ' ').strip()[:180]
        return (
            'Không kết nối được Ollama. Đây là phản hồi fallback để hệ thống không bị lỗi. '
            'Hãy bật service Ollama (model llama3.1:8b) rồi thử lại. '
            f'Tóm tắt prompt: {short_prompt}'
        )

