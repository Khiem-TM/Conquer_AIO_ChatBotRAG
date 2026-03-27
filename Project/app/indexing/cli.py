from __future__ import annotations

import argparse
import asyncio
import json

from app.indexing import IndexingService


async def _run_command(args: argparse.Namespace) -> dict:
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
    parser = build_parser()
    args = parser.parse_args()
    result = asyncio.run(_run_command(args))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
