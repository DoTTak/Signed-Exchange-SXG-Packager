#!/usr/bin/env python3
"""
SXG (Signed HTTP Exchange) Packager

Package a static HTML into SXG format including:
- Leaf certificate generation
- OCSP response
- cert.cbor
- .sxg file

Example:
    python3 sxg_pack.py \
      --ca-crt ./example/ca.crt \
      --ca-key ./example/ca.key \
      --html ./example/index.html \
      --sxg-domain example.com \
      --certurl-host localhost \
      --validity-days 1 \
      --out-dir ./output
"""
import subprocess
import sys

from utils import log
from sxg import SxgConfig, SxgPackager, CommandRunner
from sxg.cli import build_argument_parser
from sxg.constants import REQUIRED_COMMANDS


def main() -> None:
    """Main entry point."""
    CommandRunner.require_commands(REQUIRED_COMMANDS)

    parser = build_argument_parser()
    args = parser.parse_args()

    config = SxgConfig.from_args(args)
    config.validate_inputs()

    packager = SxgPackager(config)
    packager.package()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        log.error(f"Command failed with exit code {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        log.warning("Interrupted by user")
        sys.exit(130)
