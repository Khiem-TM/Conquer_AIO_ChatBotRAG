from __future__ import annotations

"""CLI nhỏ để chạy và demo phần indexing một cách độc lập.

Nhờ file này, người 2 có thể test `status`, `rebuild`, `sync`, `snapshot`,
`delete-source` mà không cần chạm vào API hay logic của người 4/người 5.
"""

import argparse
import asyncio
import json

from app.indexing import IndexingService


async def _run_command(args: argparse.Namespace) -> dict:
    """Điều phối lệnh CLI sang `IndexingService`.

    Input:
    - `args`: kết quả parse từ command line

    Output:
    - dictionary có thể in ra JSON để người dùng xem ngay trên terminal
    """

    service = IndexingService()

    if args.command == 'status':
        return (await service.get_status()).model_dump()
    if args.command == 'rebuild':
        return (await service.rebuild_index()).model_dump()
    if args.command == 'sync':
        return (await service.sync_index()).model_dump()
    if args.command == 'snapshot':
        return await service.get_index_snapshot()
    if args.command == 'delete-source':
        return (await service.delete_source(args.source_id)).model_dump()

    raise ValueError(f'Unsupported command: {args.command}')


def build_parser() -> argparse.ArgumentParser:
    """Khai báo các lệnh CLI mà người 2 hỗ trợ.

    Các lệnh hiện có:
    - `status`: xem trạng thái index
    - `rebuild`: build lại toàn bộ index
    - `sync`: đồng bộ index theo thay đổi mới
    - `snapshot`: in toàn bộ snapshot index
    - `delete-source`: xóa một source theo id
    """

    parser = argparse.ArgumentParser(description='Indexing CLI for person 2.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('status')
    subparsers.add_parser('rebuild')
    subparsers.add_parser('sync')
    subparsers.add_parser('snapshot')

    delete_parser = subparsers.add_parser('delete-source')
    delete_parser.add_argument('source_id')

    return parser


def main() -> None:
    """Điểm vào chính khi chạy `python -m app.indexing.cli ...`.

    Hàm này:
    1. parse command line
    2. chạy command async tương ứng
    3. in kết quả ra JSON để dễ đọc và dễ debug
    """

    parser = build_parser()
    args = parser.parse_args()
    result = asyncio.run(_run_command(args))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
