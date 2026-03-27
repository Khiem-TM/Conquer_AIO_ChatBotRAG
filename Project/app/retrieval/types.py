from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class IndexedChunk:
    chunk_id: str
    source_id: str
    source_name: str
    text: str
    vector: list[float]
    metadata: dict[str, str | int] = field(default_factory=dict)

