from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ModuleInfo:
    name: str
    module_type: str
    build_cs_path: Path
    source_root: Path
    public_dependencies: list[str] = field(default_factory=list)
    private_dependencies: list[str] = field(default_factory=list)
    include_paths: list[str] = field(default_factory=list)
    plugin_name: str | None = None
    plugin_path: Path | None = None


@dataclass(slots=True)
class SymbolRecord:
    module: str
    name: str
    symbol_type: str
    inheritance: list[str] = field(default_factory=list)
    specifiers: list[str] = field(default_factory=list)
    properties: list[dict[str, Any]] = field(default_factory=list)
    functions: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    module_type: str = "Unknown"
    source_file_path: str = ""
    line_start: int = 0
    line_end: int = 0
    editor_only: bool = False


@dataclass(slots=True)
class ExtractionResult:
    module_info: ModuleInfo
    symbols: list[SymbolRecord]
    engine_version: str
    compile_commands_path: Path | None
