from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import ExtractionResult


class OutputWriter:
    def __init__(self, output_root: Path):
        self.output_root = output_root
        self.output_root.mkdir(parents=True, exist_ok=True)

    def write(self, result: ExtractionResult) -> tuple[Path, Path, Path]:
        module_out = self.output_root / result.module_info.name
        module_out.mkdir(parents=True, exist_ok=True)
        json_path = module_out / "api_index.json"
        txt_path = module_out / "summary.txt"
        db_path = module_out / "api_index.sqlite"

        payload = {
            "module": result.module_info.name,
            "module_type": result.module_info.module_type,
            "engine_version": result.engine_version,
            "compile_commands": str(result.compile_commands_path) if result.compile_commands_path else None,
            "symbols": [
                {
                    "module": s.module,
                    "name": s.name,
                    "symbol_type": s.symbol_type,
                    "inheritance": s.inheritance,
                    "specifiers": s.specifiers,
                    "properties": s.properties,
                    "functions": s.functions,
                    "metadata": s.metadata,
                    "module_type": s.module_type,
                    "source_file_path": s.source_file_path,
                    "line_start": s.line_start,
                    "line_end": s.line_end,
                    "editor_only": s.editor_only,
                }
                for s in result.symbols
            ],
        }
        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        lines = [
            f"Module: {result.module_info.name}",
            f"Module Type: {result.module_info.module_type}",
            f"Engine Version: {result.engine_version}",
            f"Symbol Count: {len(result.symbols)}",
            "",
            "Top symbols:",
        ]
        lines.extend(f"- {s.symbol_type} {s.name}" for s in result.symbols[:50])
        txt_path.write_text("\n".join(lines), encoding="utf-8")

        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS symbols (
                    module TEXT,
                    name TEXT,
                    symbol_type TEXT,
                    inheritance TEXT,
                    specifiers TEXT,
                    properties TEXT,
                    functions TEXT,
                    metadata TEXT,
                    module_type TEXT,
                    source_file_path TEXT,
                    line_start INTEGER,
                    line_end INTEGER,
                    editor_only INTEGER
                )
                """
            )
            conn.execute("DELETE FROM symbols")
            conn.executemany(
                "INSERT INTO symbols VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        s.module,
                        s.name,
                        s.symbol_type,
                        json.dumps(s.inheritance),
                        json.dumps(s.specifiers),
                        json.dumps(s.properties),
                        json.dumps(s.functions),
                        json.dumps(s.metadata),
                        s.module_type,
                        s.source_file_path,
                        s.line_start,
                        s.line_end,
                        1 if s.editor_only else 0,
                    )
                    for s in result.symbols
                ],
            )
            conn.commit()

        return json_path, txt_path, db_path
