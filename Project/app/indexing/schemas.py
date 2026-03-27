from __future__ import annotations

"""Các schema nội bộ dành riêng cho package indexing.

Mục tiêu của file này là chuẩn hóa dữ liệu trả về của người 2 khi:
- kiểm tra trạng thái index
- rebuild hoặc sync index
- xóa một source khỏi index

Việc tách schema riêng giúp phần indexing có thể hoạt động độc lập và không làm
ảnh hưởng tới contract API chung của người khác.
"""

from pydantic import BaseModel, Field


class IndexStatus(BaseModel):
    """Mô tả trạng thái hiện tại của local index.

    Schema này thường được dùng khi teammate hoặc CLI muốn biết:
    - index đã sẵn sàng hay chưa
    - đang dùng backend embedding nào
    - có bao nhiêu source và bao nhiêu chunk
    - thời điểm build gần nhất
    """

    ready: bool = False
    embedding_backend: str = 'pending'
    embedding_model: str
    total_sources: int = 0
    total_chunks: int = 0
    built_at: str | None = None


class IndexOperationResult(IndexStatus):
    """Mở rộng `IndexStatus` cho các thao tác có thay đổi dữ liệu.

    Ngoài thông tin trạng thái chung, schema này bổ sung:
    - thông báo thao tác vừa thực hiện
    - latency của thao tác
    - danh sách source được cập nhật
    - danh sách source bị xóa

    Nó phù hợp cho các lệnh như `rebuild`, `sync`, `delete-source`.
    """

    message: str = 'Index updated'
    latency_ms: int = 0
    updated_sources: list[str] = Field(default_factory=list)
    deleted_sources: list[str] = Field(default_factory=list)
