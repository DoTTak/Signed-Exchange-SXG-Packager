"""Pretty logger with emoji and color support."""
from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path


class LogLevel(Enum):
    """Log levels with emoji and color support."""
    INFO = ("\u2139\ufe0f ", "\033[94m")      # Blue
    SUCCESS = ("\u2705", "\033[92m")          # Green
    WARNING = ("\u26a0\ufe0f ", "\033[93m")   # Yellow
    ERROR = ("\u274c", "\033[91m")            # Red
    CMD = ("\U0001f527", "\033[96m")          # Cyan
    KEY = ("\U0001f511", "\033[95m")          # Magenta
    CERT = ("\U0001f4dc", "\033[93m")         # Yellow
    PACKAGE = ("\U0001f4e6", "\033[92m")      # Green
    FILE = ("\U0001f4c4", "\033[97m")         # White
    STEP = ("\u25b6\ufe0f ", "\033[94m")      # Blue


class Logger:
    """Pretty logger with emoji and color support."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    def __init__(self, use_color: bool = True):
        self.use_color = use_color and sys.stdout.isatty()

    def _format(self, level: LogLevel, message: str, bold: bool = False) -> str:
        emoji, color = level.value
        if self.use_color:
            style = self.BOLD if bold else ""
            return f"{emoji} {style}{color}{message}{self.RESET}"
        return f"{emoji} {message}"

    def info(self, message: str) -> None:
        print(self._format(LogLevel.INFO, message))

    def success(self, message: str) -> None:
        print(self._format(LogLevel.SUCCESS, message, bold=True))

    def warning(self, message: str) -> None:
        print(self._format(LogLevel.WARNING, message))

    def error(self, message: str) -> None:
        print(self._format(LogLevel.ERROR, message, bold=True), file=sys.stderr)

    def cmd(self, command: str) -> None:
        if self.use_color:
            print(f"  {self.DIM}$ {command}{self.RESET}")
        else:
            print(f"  $ {command}")

    def step(self, message: str) -> None:
        print(self._format(LogLevel.STEP, message, bold=True))

    def key(self, message: str) -> None:
        print(self._format(LogLevel.KEY, message))

    def cert(self, message: str) -> None:
        print(self._format(LogLevel.CERT, message))

    def package(self, message: str) -> None:
        print(self._format(LogLevel.PACKAGE, message))

    def file(self, filepath: Path | str) -> None:
        print(self._format(LogLevel.FILE, str(filepath)))

    def header(self, title: str) -> None:
        """Print a section header."""
        width = 50
        if self.use_color:
            print(f"\n{self.BOLD}{'=' * width}{self.RESET}")
            print(f"{self.BOLD}  \U0001f680 {title}{self.RESET}")
            print(f"{self.BOLD}{'=' * width}{self.RESET}\n")
        else:
            print(f"\n{'=' * width}")
            print(f"  {title}")
            print(f"{'=' * width}\n")

    def summary(self, title: str, files: list[Path]) -> None:
        """Print a summary with file list."""
        filenames = [f.name for f in files]
        out_dir = str(files[0].parent)

        print(f"\n\U0001f389 {self.BOLD}{title}{self.RESET}" if self.use_color else f"\n\U0001f389 {title}")
        print()
        for name in filenames:
            print(f"   \U0001f4c4 {name}")
        print()
        print(f"   \U0001f4c1 {out_dir}")
        print()


# Global logger instance
log = Logger()
