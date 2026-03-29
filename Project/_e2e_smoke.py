import json
import threading
import time
from typing import Any

import requests

BASE = 'http://127.0.0.1:8000'
EARLY_EVENT_TIMEOUT = 90
FULL_TIMEOUT = 600


def hit(name: str, method: str, path: str, timeout: int = 60, **kwargs: Any) -> dict[str, Any]:
    t0 = time.time()
    out: dict[str, Any] = {'name': name, 'ok': False, 'status': None, 'latency_s': None}
    try:
        r = requests.request(method, BASE + path, timeout=timeout, **kwargs)
        out['status'] = r.status_code
        out['ok'] = 200 <= r.status_code < 300
        out['latency_s'] = round(time.time() - t0, 3)
        out['body_preview'] = (r.text or '')[:300]
    except Exception as e:
        out['error'] = repr(e)
        out['latency_s'] = round(time.time() - t0, 3)
    return out


def stream_chat_early(name: str, question: str) -> dict[str, Any]:
    t0 = time.time()
    out: dict[str, Any] = {'name': name, 'ok': False, 'status': None, 'latency_s': None}
    payload = {'question': question, 'top_k': 3, 'include_citations': True}
    try:
        with requests.post(BASE + '/api/v1/chat/stream', json=payload, timeout=(10, FULL_TIMEOUT), stream=True) as r:
            out['status'] = r.status_code
            out['first_events'] = []
            early_deadline = time.time() + EARLY_EVENT_TIMEOUT

            for line in r.iter_lines(decode_unicode=True):
                if time.time() > early_deadline:
                    break
                if not line:
                    continue
                out['first_events'].append(line)
                if line.startswith('data:'):
                    payload_text = line[5:].strip()
                    if any(k in payload_text for k in ('"meta"', '"ping"', '"token"', '"done"')):
                        out['ok'] = r.status_code == 200
                        out['first_signal'] = payload_text[:180]
                        break
                if len(out['first_events']) >= 8:
                    break

            out['latency_s'] = round(time.time() - t0, 3)
            if not out['ok'] and r.status_code == 200:
                out['error'] = f'No early stream signal within {EARLY_EVENT_TIMEOUT}s'
    except Exception as e:
        out['error'] = repr(e)
        out['latency_s'] = round(time.time() - t0, 3)
    return out


def burst_chat_stream(n: int = 3) -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    def worker(i: int) -> None:
        res = stream_chat_early(f'chat_burst_{i}', f'burst test {i}: tóm tắt dữ liệu có gì?')
        results.append(res)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(1, n + 1)]
    t0 = time.time()
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    return {
        'name': 'chat_burst',
        'ok': all(r.get('ok') for r in results),
        'latency_s': round(time.time() - t0, 3),
        'results': sorted(results, key=lambda x: x['name']),
    }


def main() -> None:
    report = {
        'health': hit('health', 'GET', '/health', timeout=20),
        'ingest': hit('ingest', 'POST', '/api/v1/ingest', timeout=120),
        'chat': stream_chat_early('chat', 'Tóm tắt các tài liệu hiện có'),
        'chat_stream': stream_chat_early('chat_stream', 'Hãy trả lời ngắn gọn: dữ liệu hiện có nói về gì?'),
        'chat_burst': burst_chat_stream(3),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

