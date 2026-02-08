import json
from pathlib import Path

from unreal_api_extractor.models import ModuleInfo
from unreal_api_extractor.project_manager import ProjectManager


def test_enable_plugin_dedup(tmp_path: Path):
    uproject = tmp_path / "Host.uproject"
    uproject.write_text(json.dumps({"Plugins": [{"Name": "A", "Enabled": False}]}), encoding="utf-8")
    ProjectManager.enable_plugin_in_uproject(uproject, "A")
    data = json.loads(uproject.read_text(encoding="utf-8"))
    assert len(data["Plugins"]) == 1
    assert data["Plugins"][0]["Enabled"] is True


def test_inject_dependencies(tmp_path: Path):
    build_cs = tmp_path / "Host.Build.cs"
    build_cs.write_text('PublicDependencyModuleNames.AddRange(new[] { "Core" });', encoding="utf-8")
    module = ModuleInfo(name="GameplayAbilities", module_type="Runtime", build_cs_path=build_cs, source_root=tmp_path)
    ProjectManager.inject_module_dependency(build_cs, module)
    text = build_cs.read_text(encoding="utf-8")
    assert '"GameplayAbilities"' in text
    assert '"Engine"' in text
    assert '"CoreUObject"' in text
    assert "bUseUnity = false;" in text
