from pathlib import Path

from unreal_api_extractor.module_discovery import ModuleDiscovery


def test_parse_build_cs(tmp_path: Path):
    build = tmp_path / "Engine" / "Source" / "Runtime" / "Foo" / "Foo.Build.cs"
    build.parent.mkdir(parents=True)
    build.write_text(
        '''
public class Foo : ModuleRules {
  public Foo(ReadOnlyTargetRules Target) : base(Target) {
    Type = ModuleType.Editor;
    PublicDependencyModuleNames.AddRange(new[] { "Core", "Engine" });
    PrivateDependencyModuleNames.AddRange(new[] { "Slate" });
  }
}
''',
        encoding="utf-8",
    )
    discovery = ModuleDiscovery(tmp_path)
    info = discovery.find_module("Foo")
    assert info is not None
    assert info.module_type == "Editor"
    assert "Core" in info.public_dependencies
    assert "Slate" in info.private_dependencies
