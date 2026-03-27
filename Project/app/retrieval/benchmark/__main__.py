from __future__ import annotations

import argparse
from dataclasses import asdict
import json

from app.retrieval.benchmark import run_benchmark


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run retrieval benchmark')
    parser.add_argument('--samples', type=str, default=None, help='Path to benchmark samples JSON')
    parser.add_argument('--top-k', type=int, default=None, help='Top-k retrieval to evaluate')
    parser.add_argument('--output', type=str, default=None, help='Output path for benchmark report JSON')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_benchmark(samples_path=args.samples, top_k=args.top_k, output_path=args.output)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
