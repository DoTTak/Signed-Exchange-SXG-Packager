"""Command execution utilities."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from utils import log


class CommandRunner:
    """Handles command execution with logging."""

    @staticmethod
    def run(
        cmd: Sequence[str],
        *,
        cwd: Path | None = None,
        capture: bool = False,
        silent: bool = False,
    ) -> str | None:
        """Execute a shell command with optional output capture."""
        if not silent:
            log.cmd(" ".join(cmd))

        if capture:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            return result.stdout

        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)
        return None

    @staticmethod
    def check_output(cmd: Sequence[str], *, cwd: Path | None = None) -> bytes:
        """Execute command and return raw output."""
        return subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.DEVNULL)

    @staticmethod
    def require_commands(commands: Sequence[str]) -> None:
        """Verify all required commands are available in PATH."""
        missing = [cmd for cmd in commands if shutil.which(cmd) is None]
        if missing:
            log.error(f"Commands not found in PATH: {', '.join(missing)}")
            raise SystemExit(1)
