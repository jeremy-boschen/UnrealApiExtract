from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .logging_utils import configure_logging
from .orchestrator import ExtractionOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unreal Engine API extraction for LLM grounding")
    parser.add_argument("module_name", help="Target Unreal module name")
    parser.add_argument("--config", required=True, type=Path, help="Path to JSON/TOML extractor config")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--symbol-dump", type=Path, help="Optional path to symbol dump (.txt/.json) for signature/type extraction")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    configure_logging(args.verbose)
    config = load_config(args.config)
    if args.symbol_dump:
        config.symbol_dump_path = args.symbol_dump
    json_path, txt_path, db_path = ExtractionOrchestrator(config).run(args.module_name)
    print(f"API JSON: {json_path}")
    print(f"Summary: {txt_path}")
    print(f"SQLite: {db_path}")


if __name__ == "__main__":
    main()
