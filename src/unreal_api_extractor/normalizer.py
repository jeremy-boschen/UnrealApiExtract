from __future__ import annotations

import re


MACROS = ["UCLASS", "USTRUCT", "UENUM", "UINTERFACE", "UPROPERTY", "UFUNCTION"]


def normalize_unreal_macro(macro_call: str) -> str:
    for macro in MACROS:
        pattern = re.compile(rf"\b{macro}\s*\((.*?)\)")
        match = pattern.search(macro_call)
        if match:
            return f"[[ue::{macro}({match.group(1).strip()})]]"
        if macro_call.strip() == macro:
            return f"[[ue::{macro}]]"
    return macro_call
