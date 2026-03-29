from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

import httpx

from app.shared.configs import settings
from app.shared.utils import get_logger

logger = get_logger(__name__)


class OllamaClient:
    _client: httpx.AsyncClient | None = None

    def __init__(self) -> None:
        self._semaphore = asyncio.Semaphore(max(1, settings.ollama_max_concurrent_requests))

    async def init_pool(self) -> None:
        if self._client is None:
            limits = httpx.Limits(
                max_connections=max(1, settings.ollama_http_max_connections),
                max_keepalive_connections=max(1, settings.ollama_http_max_keepalive_connections),
            )
            read_timeout = max(30, settings.request_timeout_seconds)
            write_timeout = max(30, settings.request_timeout_seconds)
            timeout = httpx.Timeout(connect=10.0, read=read_timeout, write=write_timeout, pool=30.0)
            self._client = httpx.AsyncClient(timeout=timeout, limits=limits)

    async def close_pool(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def pull_model_if_needed(self) -> None:
        await self.init_pool()
        assert self._client is not None

        for base_url in self._candidate_urls(settings.ollama_base_url):
            try:
                tags_resp = await self._client.get(f'{base_url}/api/tags')
                tags_resp.raise_for_status()
                tags_data = tags_resp.json()
                models = [m.get('name') for m in tags_data.get('models', []) if m.get('name')]
                if settings.ollama_model in models:
                    logger.info('Ollama model already available: %s', settings.ollama_model)
                    return

                logger.warning(
                    'Configured Ollama model not found at startup: %s. Available: %s',
                    settings.ollama_model,
                    models[:5],
                )
                return
            except Exception as exc:
                logger.warning('Model tags check failed at %s: %r', base_url, exc)

    async def generate(self, prompt: str) -> str:
        await self.init_pool()

        async with self._semaphore:
            assert self._client is not None
            total_timeout = max(180, settings.request_timeout_seconds)
            # Non-stream generate can take long before returning full text.
            # Use full request budget per model to avoid premature timeout.
            per_model_timeout = total_timeout
            deadline = asyncio.get_running_loop().time() + total_timeout

            models = await self._model_candidates()
            for model in models:
                payload = self._payload(prompt, stream=False, model=model)
                for base_url in self._candidate_urls(settings.ollama_base_url):
                    remaining = deadline - asyncio.get_running_loop().time()
                    if remaining <= 0:
                        logger.warning('Ollama generation deadline exceeded before model=%s', model)
                        raise RuntimeError('Ollama generation exceeded timeout budget')
                    try:
                        generate_timeout = httpx.Timeout(
                            connect=10.0,
                            read=None,  # rely on asyncio.wait_for budget below
                            write=60.0,
                            pool=30.0,
                        )
                        response = await asyncio.wait_for(
                            self._client.post(
                                f'{base_url}/api/generate',
                                json=payload,
                                timeout=generate_timeout,
                            ),
                            timeout=min(per_model_timeout, remaining),
                        )
                        response.raise_for_status()
                        data = response.json()
                        text = str(data.get('response', '')).strip()
                        if text:
                            return text
                    except Exception as exc:
                        logger.warning('Ollama call failed at %s model=%s: %r', base_url, model, exc)

        return self._fallback(prompt)

    async def stream_generate(self, prompt: str) -> AsyncIterator[str]:
        await self.init_pool()

        async with self._semaphore:
            assert self._client is not None
            models = await self._model_candidates()
            for model in models:
                payload = self._payload(prompt, stream=True, model=model)
                for base_url in self._candidate_urls(settings.ollama_base_url):
                    try:
                        stream_read_timeout = settings.ollama_stream_read_timeout_seconds
                        stream_timeout = httpx.Timeout(
                            connect=10.0,
                            read=None if stream_read_timeout <= 0 else float(stream_read_timeout),
                            write=60.0,
                            pool=30.0,
                        )
                        async with self._client.stream(
                            'POST',
                            f'{base_url}/api/generate',
                            json=payload,
                            timeout=stream_timeout,
                        ) as response:
                            response.raise_for_status()
                            async for line in response.aiter_lines():
                                if not line:
                                    continue
                                try:
                                    data = json.loads(line)
                                except Exception:
                                    continue
                                token = str(data.get('response', ''))
                                if token:
                                    yield token
                                if data.get('done'):
                                    return
                    except Exception as exc:
                        logger.warning('Ollama stream failed at %s model=%s: %r', base_url, model, exc)

        for token in self._fallback(prompt).split():
            yield token + ' '

    async def _model_candidates(self) -> list[str]:
        assert self._client is not None
        # Keep candidate list strict and deterministic to avoid slow/unavailable
        # fallback models causing long timeouts in production.
        preferred = [settings.ollama_model]
        ordered = []
        seen = set()
        for model in preferred:
            if model not in seen:
                ordered.append(model)
                seen.add(model)

        try:
            base_url = settings.ollama_base_url.rstrip('/')
            tags_resp = await self._client.get(f"{base_url}/api/tags")
            tags_resp.raise_for_status()
            models = [m.get('name') for m in tags_resp.json().get('models', []) if m.get('name')]
            available = [m for m in ordered if m in models]
            if available:
                return available
            if models:
                return [models[0]]
        except Exception as exc:
            logger.warning('Could not fetch model tags for candidate selection: %r', exc)

        return [settings.ollama_model]

    def _payload(self, prompt: str, stream: bool, model: str) -> dict:
        return {
            'model': model,
            'prompt': prompt,
            'stream': stream,
            'keep_alive': settings.ollama_keep_alive,
            'options': {
                'num_predict': 384,
                'temperature': 0.2,
            },
        }

    def _candidate_urls(self, primary: str) -> list[str]:
        # Keep this deterministic: use configured URL only.
        # Avoid fallback hosts that can add long retries/timeouts in Docker.
        return [primary.rstrip('/')]

    def _fallback(self, prompt: str) -> str:
        short_prompt = (prompt or '').replace('\n', ' ').strip()[:180]
        return (
            'Không kết nối được Ollama. Đây là phản hồi fallback để hệ thống không bị lỗi. '
            f"Hãy bật service Ollama (model {settings.ollama_model}) rồi thử lại. "
            f'Tóm tắt prompt: {short_prompt}'
        )
