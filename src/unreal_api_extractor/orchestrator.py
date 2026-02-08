from __future__ import annotations

import json
from pathlib import Path

from .ast_extractor import AstExtractor
from .build_runner import BuildRunner
from .cache import CacheManager
from .config import ExtractorConfig
from .errors import ModuleNotFoundError
from .models import ExtractionResult, SymbolRecord
from .module_discovery import ModuleDiscovery
from .output_writer import OutputWriter
from .project_manager import ProjectManager
from .reflection_extractor import ReflectionExtractor
from .symbol_extractor import SymbolFileExtractor


class ExtractionOrchestrator:
    def __init__(self, config: ExtractorConfig):
        self.config = config
        ubt_path = config.ubt_path or config.engine_root / "Engine" / "Binaries" / "DotNET" / "UnrealBuildTool" / "UnrealBuildTool.exe"
        self.build_runner = BuildRunner(ubt_path)

    def run(self, module_name: str) -> tuple[Path, Path, Path]:
        project_manager = ProjectManager(self.config.stub_project_template, self.config.workspace_root)
        workspace = project_manager.create_run_workspace(module_name)

        project_root = workspace
        uproject_path = project_root / self.config.host_project_file
        host_build_cs = project_root / self.config.host_module_build_cs

        discovery = ModuleDiscovery(self.config.engine_root, project_root)
        module_info = discovery.find_module(module_name)
        if not module_info:
            raise ModuleNotFoundError(f"Module {module_name} not found in Engine/Source, Source, or Plugins")

        if module_info.plugin_name:
            project_manager.enable_plugin_in_uproject(uproject_path, module_info.plugin_name)
        project_manager.inject_module_dependency(host_build_cs, module_info)
        project_manager.update_host_module_type_if_editor(uproject_path, self.config.host_module_name, module_info)

        engine_version = self._read_engine_version(self.config.engine_root)
        cache = CacheManager(self.config.workspace_root / ".cache" / "index_cache.json")
        fp = cache.fingerprint([module_info.build_cs_path, host_build_cs, uproject_path], extra=engine_version)
        cache_key = f"{engine_version}:{module_name}"

        compile_db: Path | None = None
        if cache.should_rebuild(cache_key, fp):
            self.build_runner.run_editor_build(self.config.editor_target_name, self.config.platform, self.config.configuration, uproject_path)
            compile_db = self.build_runner.generate_compile_db(self.config.host_target_name, self.config.platform, self.config.configuration, uproject_path)
            cache.update(cache_key, fp)
        else:
            potential = uproject_path.parent / "compile_commands.json"
            compile_db = potential if potential.exists() else None

        reflection = ReflectionExtractor().extract(module_info, project_root)
        ast_symbols = AstExtractor().extract(compile_db, module_info) if compile_db else []
        symbol_file_symbols = self._extract_symbol_file(module_info)

        all_symbols = self._dedup_symbols(reflection + ast_symbols + symbol_file_symbols)

        result = ExtractionResult(module_info=module_info, symbols=all_symbols, engine_version=engine_version, compile_commands_path=compile_db)
        return OutputWriter(self.config.output_root).write(result)

    def _extract_symbol_file(self, module_info) -> list[SymbolRecord]:
        symbol_file = self.config.symbol_dump_path
        if not symbol_file:
            return []
        if not symbol_file.exists():
            return []
        return SymbolFileExtractor().extract(symbol_file, module_info)

    @staticmethod
    def _dedup_symbols(symbols: list[SymbolRecord]) -> list[SymbolRecord]:
        merged: dict[tuple[str, str], SymbolRecord] = {}
        for symbol in symbols:
            key = (symbol.name, symbol.symbol_type)
            if key not in merged:
                merged[key] = symbol
                continue
            existing = merged[key]
            # Prefer UHT/reflection enriched metadata over plain entries.
            if existing.metadata.get("source") != "uht" and symbol.metadata.get("source") == "uht":
                merged[key] = symbol
        return list(merged.values())

    @staticmethod
    def _read_engine_version(engine_root: Path) -> str:
        build_version = engine_root / "Engine" / "Build" / "Build.version"
        if not build_version.exists():
            return "unknown"
        data = json.loads(build_version.read_text(encoding="utf-8"))
        return f"{data.get('MajorVersion', 0)}.{data.get('MinorVersion', 0)}.{data.get('PatchVersion', 0)}"
