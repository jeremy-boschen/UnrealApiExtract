from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path

from .errors import PluginEnableError
from .models import ModuleInfo

LOGGER = logging.getLogger(__name__)


class ProjectManager:
    def __init__(self, template_root: Path, workspace_root: Path):
        self.template_root = template_root
        self.workspace_root = workspace_root

    def create_run_workspace(self, module_name: str) -> Path:
        run_root = self.workspace_root / module_name
        if run_root.exists():
            shutil.rmtree(run_root)
        shutil.copytree(self.template_root, run_root)
        LOGGER.info("Prepared workspace: %s", run_root)
        return run_root

    @staticmethod
    def enable_plugin_in_uproject(uproject_path: Path, plugin_name: str) -> None:
        data = json.loads(uproject_path.read_text(encoding="utf-8"))
        plugins = data.setdefault("Plugins", [])
        if any(entry.get("Name") == plugin_name for entry in plugins):
            for entry in plugins:
                if entry.get("Name") == plugin_name:
                    entry["Enabled"] = True
            uproject_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return
        plugins.append({"Name": plugin_name, "Enabled": True})
        try:
            uproject_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError as exc:
            raise PluginEnableError(f"Failed to enable plugin {plugin_name}: {exc}") from exc

    @staticmethod
    def inject_module_dependency(host_build_cs: Path, target_module: ModuleInfo) -> None:
        text = host_build_cs.read_text(encoding="utf-8")
        required = ["Core", "CoreUObject", "Engine", target_module.name]
        for dep in required:
            if f'"{dep}"' in text:
                continue
            marker = "PublicDependencyModuleNames.AddRange(new[] {"
            idx = text.find(marker)
            if idx != -1:
                insert_pos = idx + len(marker)
                text = text[:insert_pos] + f' "{dep}",' + text[insert_pos:]
        if "bUseUnity = false;" not in text:
            ctor_pos = text.find("{")
            if ctor_pos != -1:
                text = text[: ctor_pos + 1] + "\n        bUseUnity = false;" + text[ctor_pos + 1 :]
        host_build_cs.write_text(text, encoding="utf-8")

    @staticmethod
    def update_host_module_type_if_editor(uproject_path: Path, host_module_name: str, module_info: ModuleInfo) -> None:
        if module_info.module_type.lower() != "editor":
            return
        data = json.loads(uproject_path.read_text(encoding="utf-8"))
        for module in data.get("Modules", []):
            if module.get("Name") == host_module_name:
                module["Type"] = "Editor"
        uproject_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
