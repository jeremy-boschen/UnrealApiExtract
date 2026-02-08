from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from .errors import BuildFailureError, CompileDbError

LOGGER = logging.getLogger(__name__)


class BuildRunner:
    def __init__(self, ubt_path: Path):
        self.ubt_path = ubt_path

    def run_editor_build(self, target: str, platform: str, configuration: str, project_file: Path) -> None:
        cmd = [
            str(self.ubt_path),
            target,
            platform,
            configuration,
            f"-Project={project_file}",
            "-WaitMutex",
            "-NoHotReloadFromIDE",
        ]
        self._run(cmd, BuildFailureError, "Editor build failed")

    def generate_compile_db(self, target: str, platform: str, configuration: str, project_file: Path) -> Path:
        cmd = [
            str(self.ubt_path),
            "-Mode=GenerateClangDatabase",
            target,
            platform,
            configuration,
            f"-Project={project_file}",
        ]
        self._run(cmd, CompileDbError, "Compile DB generation failed")
        compile_db = project_file.parent / "compile_commands.json"
        if not compile_db.exists():
            raise CompileDbError(f"compile_commands.json not found at {compile_db}")
        return compile_db

    @staticmethod
    def _run(cmd: list[str], exc_type: type[Exception], msg: str) -> None:
        LOGGER.info("Running command: %s", " ".join(cmd))
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise exc_type(f"{msg}.\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
