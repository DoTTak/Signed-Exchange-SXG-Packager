"""Command-line interface for SXG packager."""
from __future__ import annotations

import argparse
from pathlib import Path

from .constants import (
    DEFAULT_CERT_PATH,
    DEFAULT_OUT_DIR,
    DEFAULT_OUT_SXG,
    DEFAULT_VALIDITY_DAYS,
)


def build_argument_parser() -> argparse.ArgumentParser:
    """Build and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="📦 Package a static HTML into SXG (leaf cert + OCSP + cert.cbor + .sxg).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Required arguments
    required = parser.add_argument_group("required arguments")
    required.add_argument(
        "--ca-crt", required=True, type=Path,
        help="Root CA certificate (PEM), e.g., ca.crt",
    )
    required.add_argument(
        "--ca-key", required=True, type=Path,
        help="Root CA private key (PEM), e.g., ca.key",
    )
    required.add_argument(
        "--html", required=True, type=Path,
        help="Static HTML file to package, e.g., index.html",
    )
    required.add_argument(
        "--sxg-domain", required=True,
        help="SXG domain (DNS SAN/CN), e.g., example.com",
    )
    required.add_argument(
        "--certurl-host", required=True,
        help="Host for certUrl, e.g., localhost or 127.0.0.1 (no scheme)",
    )

    # Optional arguments
    parser.add_argument(
        "--sxg-uri", default=None,
        help="URI packaged in SXG, default https://<sxg-domain>/",
    )
    parser.add_argument(
        "--certurl-path", default=DEFAULT_CERT_PATH,
        help=f"Path for cert.cbor, default {DEFAULT_CERT_PATH}",
    )
    parser.add_argument(
        "--validity-url", default=None,
        help="validityUrl for SXG, default https://<sxg-domain>/resource.validity",
    )
    parser.add_argument(
        "--out-dir", default=Path(DEFAULT_OUT_DIR), type=Path,
        help=f"Output directory, default {DEFAULT_OUT_DIR}",
    )
    parser.add_argument(
        "--out-sxg", default=DEFAULT_OUT_SXG,
        help=f"Output .sxg filename (within out-dir), default {DEFAULT_OUT_SXG}",
    )
    parser.add_argument(
        "--validity-days", type=int, default=DEFAULT_VALIDITY_DAYS,
        help=f"Leaf cert validity days, default {DEFAULT_VALIDITY_DAYS}",
    )

    # Optional: reuse provided sxg key/cert
    existing = parser.add_argument_group("existing key/cert (optional)")
    existing.add_argument(
        "--sxg-key", type=Path, default=None,
        help="Existing SXG EC private key (prime256v1)",
    )
    existing.add_argument(
        "--sxg-crt", type=Path, default=None,
        help="Existing SXG leaf certificate (PEM)",
    )

    return parser
