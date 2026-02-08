from __future__ import annotations

import hashlib
import json
from pathlib import Path


class CacheManager:
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        if cache_file.exists():
            self.data = json.loads(cache_file.read_text(encoding="utf-8"))
        else:
            self.data = {}

    @staticmethod
    def fingerprint(paths: list[Path], extra: str = "") -> str:
        h = hashlib.sha256(extra.encode("utf-8"))
        for path in sorted(paths):
            if not path.exists():
                continue
            stat = path.stat()
            h.update(str(path).encode("utf-8"))
            h.update(str(stat.st_mtime_ns).encode("utf-8"))
            h.update(str(stat.st_size).encode("utf-8"))
        return h.hexdigest()

    def should_rebuild(self, key: str, fingerprint: str) -> bool:
        return self.data.get(key) != fingerprint

    def update(self, key: str, fingerprint: str) -> None:
        self.data[key] = fingerprint
        self.cache_file.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
