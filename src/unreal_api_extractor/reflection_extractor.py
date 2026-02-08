from __future__ import annotations

import logging
import re
from pathlib import Path

from .errors import UhtOutputMissingError
from .models import ModuleInfo, SymbolRecord
from .normalizer import normalize_unreal_macro

LOGGER = logging.getLogger(__name__)
EXCLUDED = {"Intermediate", "Binaries", "DerivedDataCache", "Saved"}


class ReflectionExtractor:
    def extract(self, module_info: ModuleInfo, project_root: Path) -> list[SymbolRecord]:
        symbols = self._extract_from_headers(module_info)
        generated = self._extract_from_uht(project_root, module_info)
        merged = {(s.name, s.symbol_type): s for s in symbols}
        for symbol in generated:
            merged[(symbol.name, symbol.symbol_type)] = symbol
        return list(merged.values())

    def _extract_from_headers(self, module_info: ModuleInfo) -> list[SymbolRecord]:
        found: list[SymbolRecord] = []
        for header in module_info.source_root.rglob("*.h"):
            if any(part in EXCLUDED for part in header.parts):
                continue
            found.extend(self._parse_header(header, module_info))
        return found

    def _extract_from_uht(self, project_root: Path, module_info: ModuleInfo) -> list[SymbolRecord]:
        uht_roots = list(project_root.glob("Intermediate/Build/**/UHT"))
        if not uht_roots:
            raise UhtOutputMissingError("No UHT directory found under Intermediate/Build")
        found: list[SymbolRecord] = []
        for root in uht_roots:
            for file in root.rglob("*.generated.h"):
                if module_info.name.lower() not in file.as_posix().lower():
                    continue
                found.extend(self._parse_header(file, module_info, prefer_generated=True))
        return found

    def _parse_header(self, header: Path, module_info: ModuleInfo, prefer_generated: bool = False) -> list[SymbolRecord]:
        text = header.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        symbols: list[SymbolRecord] = []
        pending_macro: str | None = None
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if any(stripped.startswith(macro) for macro in ["UCLASS", "USTRUCT", "UENUM", "UINTERFACE"]):
                pending_macro = normalize_unreal_macro(stripped)
                continue
            if pending_macro and re.search(r"\b(class|struct|enum)\s+\w+", stripped):
                symbol_match = re.search(r"\b(class|struct|enum)\s+(\w+)(?:\s*:\s*public\s*([\w:]+))?", stripped)
                if symbol_match:
                    symbol_type, name, inherit = symbol_match.groups()
                    symbols.append(
                        SymbolRecord(
                            module=module_info.name,
                            name=name,
                            symbol_type=symbol_type,
                            inheritance=[inherit] if inherit else [],
                            specifiers=[pending_macro],
                            module_type=module_info.module_type,
                            source_file_path=str(header),
                            line_start=line_no,
                            line_end=line_no,
                            metadata={"source": "uht" if prefer_generated else "header"},
                            editor_only=module_info.module_type.lower() == "editor",
                        )
                    )
                pending_macro = None
                continue
            prop = re.search(r"UPROPERTY\((.*?)\)", stripped)
            func = re.search(r"UFUNCTION\((.*?)\)", stripped)
            if symbols and prop:
                symbols[-1].properties.append({"specifiers": prop.group(1).strip(), "line": line_no})
            if symbols and func:
                symbols[-1].functions.append({"specifiers": func.group(1).strip(), "line": line_no})
        LOGGER.debug("Parsed %s symbols from %s", len(symbols), header)
        return symbols
