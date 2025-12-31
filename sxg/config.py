"""SXG configuration dataclass."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from utils import log


@dataclass
class SxgConfig:
    """Configuration for SXG generation."""
    ca_crt: Path
    ca_key: Path
    html: Path
    sxg_domain: str
    sxg_uri: str
    validity_url: str
    cert_url: str
    out_dir: Path
    out_sxg: str
    validity_days: int
    sxg_key: Path | None = None
    sxg_crt: Path | None = None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> SxgConfig:
        """Create config from parsed arguments."""
        sxg_uri = args.sxg_uri or f"https://{args.sxg_domain}/"
        validity_url = args.validity_url or f"https://{args.sxg_domain}/resource.validity"
        cert_url = f"https://{args.certurl_host}{args.certurl_path}"

        return cls(
            ca_crt=args.ca_crt.resolve(),
            ca_key=args.ca_key.resolve(),
            html=args.html.resolve(),
            sxg_domain=args.sxg_domain,
            sxg_uri=sxg_uri,
            validity_url=validity_url,
            cert_url=cert_url,
            out_dir=args.out_dir.resolve(),
            out_sxg=args.out_sxg,
            validity_days=args.validity_days,
            sxg_key=args.sxg_key,
            sxg_crt=args.sxg_crt,
        )

    def validate_inputs(self) -> None:
        """Validate that all required input files exist."""
        missing = [
            path for path in (self.ca_crt, self.ca_key, self.html)
            if not path.exists()
        ]
        if missing:
            log.error(f"Files not found: {', '.join(str(p) for p in missing)}")
            raise SystemExit(1)
