from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class TimerResult:
    elapsed_ms: int = 0


@contextmanager
def timer() -> TimerResult:
    result = TimerResult()
    start = time.perf_counter()
    try:
        yield result
    finally:
        result.elapsed_ms = int((time.perf_counter() - start) * 1000)

