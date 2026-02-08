from pathlib import Path

from unreal_api_extractor.models import ModuleInfo
from unreal_api_extractor.symbol_extractor import SymbolFileExtractor


def _module(tmp_path: Path) -> ModuleInfo:
    build_cs = tmp_path / "Foo.Build.cs"
    build_cs.write_text("", encoding="utf-8")
    return ModuleInfo(name="Foo", module_type="Runtime", build_cs_path=build_cs, source_root=tmp_path)


def test_extract_text_symbol_dump(tmp_path: Path):
    dump = tmp_path / "symbols.txt"
    dump.write_text(
        """
class UE::Gameplay::FAbilitySystem
void UE::Gameplay::FAbilitySystem::ActivateAbility(int32 Id)
""",
        encoding="utf-8",
    )
    symbols = SymbolFileExtractor().extract(dump, _module(tmp_path))
    names = {(s.name, s.symbol_type) for s in symbols}
    assert ("UE::Gameplay::FAbilitySystem", "class") in names
    assert ("UE::Gameplay::FAbilitySystem::ActivateAbility", "function") in names


def test_extract_json_symbol_dump(tmp_path: Path):
    dump = tmp_path / "symbols.json"
    dump.write_text(
        '{"symbols": [{"name": "UE::Gameplay::FAbilitySystem::Cancel", "kind": "function", "signature": "void UE::Gameplay::FAbilitySystem::Cancel()"}]}',
        encoding="utf-8",
    )
    symbols = SymbolFileExtractor().extract(dump, _module(tmp_path))
    assert len(symbols) == 1
    assert symbols[0].metadata["signature"] == "void UE::Gameplay::FAbilitySystem::Cancel()"
