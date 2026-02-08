from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class ExtractorConfig:
    engine_root: Path
    stub_project_template: Path
    host_project_file: str
    host_module_name: str
    host_module_build_cs: str
    host_target_name: str
    editor_target_name: str
    platform: str = "Win64"
    configuration: str = "Development"
    workspace_root: Path = Path("./.work")
    output_root: Path = Path("./outputs")
    ubt_path: Path | None = None
    symbol_dump_path: Path | None = None


def load_config(path: Path) -> ExtractorConfig:
    if path.suffix.lower() == ".toml":
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    if "extractor" in data:
        data = data["extractor"]

    data.setdefault("platform", "Win64")
    data.setdefault("configuration", "Development")
    data.setdefault("workspace_root", "./.work")
    data.setdefault("output_root", "./outputs")

    path_fields = {
        "engine_root",
        "stub_project_template",
        "workspace_root",
        "output_root",
        "ubt_path",
        "symbol_dump_path",
    }
    normalized = {}
    for key, value in data.items():
        if key in path_fields and value is not None:
            normalized[key] = Path(value)
        else:
            normalized[key] = value
    return ExtractorConfig(**normalized)
