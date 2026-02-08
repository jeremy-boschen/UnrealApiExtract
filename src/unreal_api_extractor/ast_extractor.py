from __future__ import annotations

import json
import re
from pathlib import Path

from .models import ModuleInfo, SymbolRecord


class AstExtractor:
    """Best-effort extraction for non-reflected C++ symbols from compile_commands."""

    def extract(self, compile_db_path: Path, module_info: ModuleInfo) -> list[SymbolRecord]:
        db = json.loads(compile_db_path.read_text(encoding="utf-8"))
        symbols: list[SymbolRecord] = []
        for unit in db:
            file_path = Path(unit.get("file", ""))
            if module_info.name.lower() not in file_path.as_posix().lower():
                continue
            if not file_path.exists() or file_path.suffix not in {".h", ".hpp", ".cpp"}:
                continue
            symbols.extend(self._parse_translation_unit(file_path, module_info))
        return symbols

    def _parse_translation_unit(self, file_path: Path, module_info: ModuleInfo) -> list[SymbolRecord]:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        records: list[SymbolRecord] = []
        for idx, line in enumerate(text.splitlines(), start=1):
            ns = re.search(r"^\s*namespace\s+(\w+)", line)
            clz = re.search(r"^\s*class\s+(\w+)", line)
            fn = re.search(r"^\s*(?:inline\s+)?(?:[\w:<>]+)\s+(\w+)\s*\([^;]*\)\s*\{", line)
            if ns:
                records.append(SymbolRecord(module=module_info.name, name=ns.group(1), symbol_type="namespace", module_type=module_info.module_type, source_file_path=str(file_path), line_start=idx, line_end=idx))
            if clz and "UCLASS" not in line:
                records.append(SymbolRecord(module=module_info.name, name=clz.group(1), symbol_type="class", module_type=module_info.module_type, source_file_path=str(file_path), line_start=idx, line_end=idx))
            if fn:
                records.append(SymbolRecord(module=module_info.name, name=fn.group(1), symbol_type="function", module_type=module_info.module_type, source_file_path=str(file_path), line_start=idx, line_end=idx))
        return records
