from __future__ import annotations

import json
import re
from pathlib import Path

from .models import ModuleInfo, SymbolRecord


class SymbolFileExtractor:
    """Extract C++ API signatures/types from symbol dump files.

    Supported inputs:
    - JSON: {"symbols": [{"name": "Foo::Bar", "kind": "function", "signature": "void Foo::Bar(int)"}, ...]}
    - Text: lines containing C++-like declarations/signatures, e.g.
        void UE::FThing::DoWork(int32 Value)
        class UE::FThing
        struct UE::FData
    """

    FUNC_RE = re.compile(
        r"^(?P<ret>[\w:\<\>\*&\s~]+?)\s+(?P<name>[\w:~]+)\s*\((?P<args>.*)\)\s*$"
    )
    TYPE_RE = re.compile(r"^(?P<kind>class|struct|enum)\s+(?P<name>[\w:]+)\s*$")

    def extract(self, symbol_file: Path, module_info: ModuleInfo) -> list[SymbolRecord]:
        if symbol_file.suffix.lower() == ".json":
            return self._extract_json(symbol_file, module_info)
        return self._extract_text(symbol_file, module_info)

    def _extract_json(self, symbol_file: Path, module_info: ModuleInfo) -> list[SymbolRecord]:
        payload = json.loads(symbol_file.read_text(encoding="utf-8"))
        raw = payload.get("symbols", payload if isinstance(payload, list) else [])
        records: list[SymbolRecord] = []
        for item in raw:
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            kind = str(item.get("kind", "symbol")).strip().lower()
            sig = str(item.get("signature", "")).strip()
            records.append(
                SymbolRecord(
                    module=module_info.name,
                    name=name,
                    symbol_type=kind,
                    module_type=module_info.module_type,
                    source_file_path=str(symbol_file),
                    metadata={"source": "symbol_file", "signature": sig} if sig else {"source": "symbol_file"},
                )
            )
        return records

    def _extract_text(self, symbol_file: Path, module_info: ModuleInfo) -> list[SymbolRecord]:
        records: list[SymbolRecord] = []
        for line_no, line in enumerate(symbol_file.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            stripped = line.strip().rstrip(";")
            if not stripped:
                continue
            tmatch = self.TYPE_RE.match(stripped)
            if tmatch:
                records.append(
                    SymbolRecord(
                        module=module_info.name,
                        name=tmatch.group("name"),
                        symbol_type=tmatch.group("kind"),
                        module_type=module_info.module_type,
                        source_file_path=str(symbol_file),
                        line_start=line_no,
                        line_end=line_no,
                        metadata={"source": "symbol_file"},
                    )
                )
                continue

            fmatch = self.FUNC_RE.match(stripped)
            if fmatch and "::" in fmatch.group("name"):
                records.append(
                    SymbolRecord(
                        module=module_info.name,
                        name=fmatch.group("name"),
                        symbol_type="function",
                        module_type=module_info.module_type,
                        source_file_path=str(symbol_file),
                        line_start=line_no,
                        line_end=line_no,
                        metadata={
                            "source": "symbol_file",
                            "signature": stripped,
                            "return_type": fmatch.group("ret").strip(),
                            "arguments": fmatch.group("args").strip(),
                        },
                    )
                )
        return records
