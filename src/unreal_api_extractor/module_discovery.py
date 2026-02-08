from __future__ import annotations

import logging
import re
from pathlib import Path

from .models import ModuleInfo

LOGGER = logging.getLogger(__name__)
EXCLUDED_PARTS = {"Intermediate", "Binaries", "DerivedDataCache", "Saved"}


class ModuleDiscovery:
    def __init__(self, engine_root: Path, project_root: Path | None = None):
        self.engine_root = engine_root
        self.project_root = project_root

    def find_module(self, module_name: str) -> ModuleInfo | None:
        for build_cs in self._iter_build_cs_files():
            if self._module_name_from_build_cs(build_cs) != module_name:
                continue
            return self._parse_build_cs(build_cs)
        return None

    def _iter_build_cs_files(self):
        search_roots = [self.engine_root / "Engine" / "Source"]
        if self.project_root:
            search_roots.extend([
                self.project_root / "Source",
                self.project_root / "Plugins",
            ])
            search_roots.append(self.engine_root / "Engine" / "Plugins")
        seen: set[Path] = set()
        for root in search_roots:
            if not root.exists():
                continue
            for file in root.rglob("*.Build.cs"):
                if any(part in EXCLUDED_PARTS for part in file.parts):
                    continue
                if file in seen:
                    continue
                seen.add(file)
                yield file

    def _parse_build_cs(self, path: Path) -> ModuleInfo:
        text = path.read_text(encoding="utf-8", errors="ignore")
        mod_type = self._extract_assignment(text, "Type") or "Runtime"
        public = self._extract_list(text, "PublicDependencyModuleNames")
        private = self._extract_list(text, "PrivateDependencyModuleNames")
        includes = self._extract_list(text, "PublicIncludePaths") + self._extract_list(text, "PrivateIncludePaths")
        plugin_name, plugin_path = self._infer_plugin(path)
        module_name = self._module_name_from_build_cs(path)
        LOGGER.debug("Discovered module %s at %s", module_name, path)
        return ModuleInfo(
            name=module_name,
            module_type=mod_type,
            build_cs_path=path,
            source_root=path.parent,
            public_dependencies=public,
            private_dependencies=private,
            include_paths=includes,
            plugin_name=plugin_name,
            plugin_path=plugin_path,
        )

    @staticmethod
    def _extract_assignment(text: str, variable: str) -> str | None:
        pattern = re.compile(rf"\b{re.escape(variable)}\s*=\s*ModuleType\.(\w+)")
        match = pattern.search(text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_list(text: str, variable: str) -> list[str]:
        pattern = re.compile(rf"\b{re.escape(variable)}\s*\.AddRange\s*\(\s*new\s*\[\]\s*\{{(.*?)\}}\s*\)", re.S)
        match = pattern.search(text)
        if not match:
            return []
        values = re.findall(r'"([^"]+)"', match.group(1))
        return values

    @staticmethod
    def _infer_plugin(build_cs: Path) -> tuple[str | None, Path | None]:
        parts = list(build_cs.parts)
        if "Plugins" not in parts:
            return None, None
        idx = parts.index("Plugins")
        if idx + 1 >= len(parts):
            return None, None
        plugin_name = parts[idx + 1]
        plugin_path = Path(*parts[: idx + 2])
        return plugin_name, plugin_path

    @staticmethod
    def _module_name_from_build_cs(path: Path) -> str:
        name = path.name
        return name[:-9] if name.endswith(".Build.cs") else path.stem
