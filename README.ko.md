# Signed Exchange(SXG) Packager

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.ko.md">한국어</a>
</p>

HTML 파일을 Signed HTTP Exchange (SXG) 형식으로 패키징하는 도구입니다.

## SXG란?

Signed HTTP Exchange (SXG)는 웹 콘텐츠의 원본 출처를 암호학적으로 증명하면서 제3자 캐시를 통해 배포할 수 있게 해주는 기술입니다.

> SXG의 작동 원리, 인증서 생성 과정, 상세 실습 가이드는 [sxg.ko.md](./sxg.ko.md)를 참고하세요.

## 기능

- Root CA를 사용하여 SXG 리프 인증서 자동 생성
- OCSP 응답 생성
- cert.cbor 파일 생성
- .sxg 파일 패키징
- HTTPS 테스트 서버 제공

## 필수 조건

### 시스템 요구사항

- Python 3.10+
- OpenSSL
- Go (webpackage 도구 설치용)

### webpackage 도구 설치

```bash
go install github.com/WICG/webpackage/go/signedexchange/cmd/gen-certurl@latest
go install github.com/WICG/webpackage/go/signedexchange/cmd/gen-signedexchange@latest

# 환경변수 설정
export PATH=$PATH:$(go env GOPATH)/bin
```

## 설치

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install flask
```

## 사용법

### SXG 패키지 생성

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

### 명령줄 옵션

#### 필수 옵션

| 옵션 | 설명 |
|------|------|
| `--ca-crt` | Root CA 인증서 (PEM) |
| `--ca-key` | Root CA 개인키 (PEM) |
| `--html` | 패키징할 HTML 파일 |
| `--sxg-domain` | SXG 도메인 (예: example.com) |
| `--certurl-host` | cert.cbor 호스트 (예: localhost) |

#### 선택 옵션

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--sxg-uri` | `https://<sxg-domain>/` | SXG URI |
| `--certurl-path` | `/cert.cbor` | cert.cbor 경로 |
| `--validity-url` | `https://<sxg-domain>/resource.validity` | validityUrl |
| `--out-dir` | `./output` | 출력 디렉토리 |
| `--out-sxg` | `index.sxg` | 출력 파일명 |
| `--validity-days` | `1` | 인증서 유효 기간 (일) |
| `--sxg-key` | - | 기존 SXG 개인키 (재사용 시) |
| `--sxg-crt` | - | 기존 SXG 인증서 (재사용 시) |

### HTTPS 테스트 서버 실행

```bash
sudo python3 https_server.py
```

**엔드포인트:**
- `https://localhost/` - 기본 페이지
- `https://localhost/cert.cbor` - 인증서 체인
- `https://localhost/sxg` - SXG 파일

## 프로젝트 구조

```
Signed-Exchange-Demo/
├── sxg-pack.py          # 메인 진입점
├── https_server.py      # HTTPS 테스트 서버
├── sxg-demo.sh          # 데모 스크립트 (bash)
├── sxg/
│   ├── cli.py           # CLI 파서
│   ├── config.py        # 설정 클래스
│   ├── constants.py     # 상수
│   ├── packager.py      # 패키징 로직
│   └── runner.py        # 명령 실행 유틸리티
├── utils/
│   └── logger.py        # 로깅
├── example/             # 예제 파일
│   ├── ca.crt / ca.key
│   ├── server.crt / server.key
│   └── index.html
└── output/              # 생성 파일 출력
```

## 출력 파일

| 파일 | 설명 |
|------|------|
| `sxg.crt` | SXG 리프 인증서 |
| `sxg.key` | SXG 개인키 |
| `ocsp.der` | OCSP 응답 |
| `cert.cbor` | CBOR 인증서 체인 |
| `index.sxg` | Signed Exchange 파일 |

## 테스트

1. Root CA (`example/ca.crt`)를 시스템에 신뢰하도록 등록
2. HTTPS 서버 실행: `sudo python3 https_server.py`
3. 브라우저에서 `https://localhost/sxg` 접속

## 참고 자료
- [Signed HTTP Exchanges Draft](https://wicg.github.io/webpackage/draft-yasskin-http-origin-signed-responses.html)
- [Google SXG 가이드](https://developers.google.com/search/docs/appearance/signed-exchange)
- [webpackage 도구](https://github.com/WICG/webpackage)

## 라이선스

MIT License
