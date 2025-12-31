"""SXG packager - main packaging logic."""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from utils import log

from .config import SxgConfig
from .constants import SXG_EXTENSION_OID
from .runner import CommandRunner


class SxgPackager:
    """Generates SXG packages from HTML content."""

    def __init__(self, config: SxgConfig):
        self.config = config
        self.runner = CommandRunner()

    def package(self) -> None:
        """Execute the full SXG packaging workflow."""
        log.header(f"SXG Packager - {self.config.sxg_domain}")

        self.config.out_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="sxg_pack_") as tmpdir:
            workdir = Path(tmpdir)
            self._setup_workdir(workdir)
            self._generate_sxg_key(workdir)
            self._generate_sxg_cert(workdir)
            self._generate_ocsp(workdir)
            self._generate_cert_cbor(workdir)
            self._generate_sxg(workdir)
            self._copy_outputs(workdir)

        self._print_summary()

    def _setup_workdir(self, workdir: Path) -> None:
        """Copy input files to working directory."""
        log.step("Preparing workspace...")
        (workdir / "ca.crt").write_bytes(self.config.ca_crt.read_bytes())
        (workdir / "ca.key").write_bytes(self.config.ca_key.read_bytes())
        (workdir / "content.html").write_bytes(self.config.html.read_bytes())
        log.success("Workspace ready")

    def _generate_sxg_key(self, workdir: Path) -> None:
        """Generate or copy SXG private key."""
        log.step("Setting up SXG private key...")

        if self.config.sxg_key:
            (workdir / "sxg.key").write_bytes(self.config.sxg_key.read_bytes())
            log.key(f"Using existing key: {self.config.sxg_key}")
        else:
            log.key("Generating new EC P-256 key")
            self.runner.run(
                ["openssl", "ecparam", "-name", "prime256v1", "-genkey", "-out", "sxg.key"],
                cwd=workdir,
            )
            log.success("Key generated: sxg.key")

    def _generate_sxg_cert(self, workdir: Path) -> None:
        """Generate or copy SXG leaf certificate."""
        log.step("Setting up SXG certificate...")

        if self.config.sxg_crt:
            (workdir / "sxg.crt").write_bytes(self.config.sxg_crt.read_bytes())
            log.cert(f"Using existing cert: {self.config.sxg_crt}")
            return

        # Generate CSR
        log.cert("Generating Certificate Signing Request")
        self.runner.run(
            [
                "openssl", "req", "-new", "-sha256",
                "-key", "sxg.key",
                "-out", "sxg.csr",
                "-subj", f"/CN={self.config.sxg_domain}",
            ],
            cwd=workdir,
        )

        # Write extension config
        ext_config = self._build_extension_config()
        (workdir / "sxg_ext.cnf").write_text(ext_config)

        # Sign certificate
        log.cert(f"Signing certificate for {self.config.sxg_domain}")
        self.runner.run(
            [
                "openssl", "x509", "-req",
                "-in", "sxg.csr",
                "-CA", "ca.crt",
                "-CAkey", "ca.key",
                "-out", "sxg.crt",
                "-days", str(self.config.validity_days),
                "-sha256",
                "-extfile", "sxg_ext.cnf",
            ],
            cwd=workdir,
        )
        log.success(f"Certificate signed (valid for {self.config.validity_days} days)")

    def _build_extension_config(self) -> str:
        """Build OpenSSL extension configuration for SXG certificate."""
        return (
            "basicConstraints = critical, CA:FALSE\n"
            "keyUsage = critical, digitalSignature\n"
            f"subjectAltName = DNS:{self.config.sxg_domain}\n"
            f"{SXG_EXTENSION_OID} = ASN1:NULL\n"
        )

    def _generate_ocsp(self, workdir: Path) -> None:
        """Generate OCSP request and response."""
        log.step("Generating OCSP response...")

        # Get certificate serial
        serial_output = self.runner.run(
            ["openssl", "x509", "-in", "sxg.crt", "-serial", "-noout"],
            cwd=workdir,
            capture=True,
            silent=True,
        )
        serial = serial_output.strip().split("=", 1)[1]
        log.info(f"Certificate serial: {serial}")

        # Calculate expiry
        expire_dt = datetime.now(timezone.utc) + timedelta(days=self.config.validity_days)
        expire_asn1 = self._format_asn1_time(expire_dt)

        # Write OCSP index
        index_entry = f"V\t{expire_asn1}\t\t{serial}\tunknown\t/CN={self.config.sxg_domain}\n"
        (workdir / "index.txt").write_text(index_entry)

        # Generate OCSP request
        log.info("Creating OCSP request")
        self.runner.run(
            [
                "openssl", "ocsp",
                "-issuer", "ca.crt",
                "-cert", "sxg.crt",
                "-reqout", "req.der",
                "-no_nonce",
            ],
            cwd=workdir,
        )

        # Generate OCSP response
        log.info("Creating OCSP response")
        self.runner.run(
            [
                "openssl", "ocsp",
                "-index", "index.txt",
                "-rsigner", "ca.crt",
                "-rkey", "ca.key",
                "-CA", "ca.crt",
                "-reqin", "req.der",
                "-respout", "ocsp.der",
                "-ndays", str(self.config.validity_days),
            ],
            cwd=workdir,
        )
        log.success("OCSP response generated: ocsp.der")

    @staticmethod
    def _format_asn1_time(dt: datetime) -> str:
        """Format datetime as ASN.1 UTCTime (YYMMDDHHMMSSZ)."""
        return dt.strftime("%y%m%d%H%M%SZ")

    def _generate_cert_cbor(self, workdir: Path) -> None:
        """Generate cert.cbor using gen-certurl."""
        log.step("Generating cert.cbor...")
        cert_cbor = self.runner.check_output(
            ["gen-certurl", "-pem", "sxg.crt", "-ocsp", "ocsp.der"],
            cwd=workdir,
        )
        (workdir / "cert.cbor").write_bytes(cert_cbor)
        log.success("cert.cbor generated")

    def _generate_sxg(self, workdir: Path) -> None:
        """Generate the final SXG file."""
        log.step(f"Packaging Signed Exchange: {self.config.out_sxg}")
        log.info(f"URI: {self.config.sxg_uri}")
        log.info(f"Cert URL: {self.config.cert_url}")

        self.runner.run(
            [
                "gen-signedexchange",
                "-uri", self.config.sxg_uri,
                "-content", "content.html",
                "-certificate", "sxg.crt",
                "-privateKey", "sxg.key",
                "-certUrl", self.config.cert_url,
                "-validityUrl", self.config.validity_url,
                "-o", self.config.out_sxg,
            ],
            cwd=workdir,
        )
        log.success(f"Signed Exchange created: {self.config.out_sxg}")

    def _copy_outputs(self, workdir: Path) -> None:
        """Copy generated files to output directory."""
        log.step("Copying outputs...")
        output_files = ["sxg.crt", "sxg.key", "ocsp.der", "cert.cbor", self.config.out_sxg]
        for filename in output_files:
            shutil.copy2(workdir / filename, self.config.out_dir / filename)

    def _print_summary(self) -> None:
        """Print summary of generated files."""
        output_files = [
            self.config.out_dir / "sxg.crt",
            self.config.out_dir / "sxg.key",
            self.config.out_dir / "ocsp.der",
            self.config.out_dir / "cert.cbor",
            self.config.out_dir / self.config.out_sxg,
        ]
        log.summary("SXG Package Complete!", output_files)
