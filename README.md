# Signed Exchange(SXG) Packager

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.ko.md">한국어</a>
</p>

A tool for packaging HTML files into Signed HTTP Exchange (SXG) format.

## What is SXG?

Signed HTTP Exchange (SXG) is a technology that cryptographically proves the origin of web content while allowing distribution through third-party caches.

> For detailed information on how SXG works, certificate generation, and hands-on tutorials, see [sxg.en.md](./sxg.en.md).

## Features

- Automatic SXG leaf certificate generation using Root CA
- OCSP response generation
- cert.cbor file generation
- .sxg file packaging
- HTTPS test server included

## Prerequisites

### System Requirements

- Python 3.10+
- OpenSSL
- Go (for webpackage tools installation)

### Installing webpackage Tools

```bash
go install github.com/WICG/webpackage/go/signedexchange/cmd/gen-certurl@latest
go install github.com/WICG/webpackage/go/signedexchange/cmd/gen-signedexchange@latest

# Add to PATH
export PATH=$PATH:$(go env GOPATH)/bin
```

## Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install flask
```

## Usage

### Generate SXG Package

```bash
python3 sxg-pack.py \
  --ca-crt ./example/ca.crt \
  --ca-key ./example/ca.key \
  --html ./example/index.html \
  --sxg-domain example.com \
  --certurl-host localhost \
  --validity-days 1 \
  --out-dir ./output
```

### Command Line Options

#### Required Options

| Option | Description |
|--------|-------------|
| `--ca-crt` | Root CA certificate (PEM) |
| `--ca-key` | Root CA private key (PEM) |
| `--html` | HTML file to package |
| `--sxg-domain` | SXG domain (e.g., example.com) |
| `--certurl-host` | cert.cbor host (e.g., localhost) |

#### Optional Options

| Option | Default | Description |
|--------|---------|-------------|
| `--sxg-uri` | `https://<sxg-domain>/` | SXG URI |
| `--certurl-path` | `/cert.cbor` | cert.cbor path |
| `--validity-url` | `https://<sxg-domain>/resource.validity` | validityUrl |
| `--out-dir` | `./output` | Output directory |
| `--out-sxg` | `index.sxg` | Output filename |
| `--validity-days` | `1` | Certificate validity (days) |
| `--sxg-key` | - | Existing SXG private key (for reuse) |
| `--sxg-crt` | - | Existing SXG certificate (for reuse) |

### Run HTTPS Test Server

```bash
sudo python3 https_server.py
```

**Endpoints:**
- `https://localhost/` - Default page
- `https://localhost/cert.cbor` - Certificate chain
- `https://localhost/sxg` - SXG file

## Project Structure

```
Signed-Exchange-Demo/
├── sxg-pack.py          # Main entry point
├── https_server.py      # HTTPS test server
├── sxg-demo.sh          # Demo script (bash)
├── sxg/
│   ├── cli.py           # CLI parser
│   ├── config.py        # Configuration class
│   ├── constants.py     # Constants
│   ├── packager.py      # Packaging logic
│   └── runner.py        # Command runner utility
├── utils/
│   └── logger.py        # Logging
├── example/             # Example files
│   ├── ca.crt / ca.key
│   ├── server.crt / server.key
│   └── index.html
└── output/              # Generated files output
```

## Output Files

| File | Description |
|------|-------------|
| `sxg.crt` | SXG leaf certificate |
| `sxg.key` | SXG private key |
| `ocsp.der` | OCSP response |
| `cert.cbor` | CBOR certificate chain |
| `index.sxg` | Signed Exchange file |

## Testing

1. Add Root CA (`example/ca.crt`) to system trust store
2. Run HTTPS server: `sudo python3 https_server.py`
3. Access `https://localhost/sxg` in browser

## References
- [Signed HTTP Exchanges Draft](https://wicg.github.io/webpackage/draft-yasskin-http-origin-signed-responses.html)
- [Google SXG Guide](https://developers.google.com/search/docs/appearance/signed-exchange)
- [webpackage Tools](https://github.com/WICG/webpackage)

## License

MIT License
