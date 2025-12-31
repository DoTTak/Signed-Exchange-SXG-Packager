<p align="center">
  <a href="./sxg.en.md">English</a> | <a href="./sxg.ko.md">한국어</a>
</p>

# 1. SXG(Signed Exchange) 란?

## 1.1 정의

Signed Exchange(SXG) 는 제3자(예: CDN)가 웹 리소스를 전달하면서도 콘텐츠의 무결성과 출처를 유지할 수 있게 하는 표준 기술입니다.

A 서버([a.com](http://a.com))가 SXG 파일(index.sxg)을 생성하여 제3자인 B 서버([b.com](http://b.com))에 배포한 경우, 사용자가 [b.com/index.sxg](http://b.com/index.sxg) 를 요청하더라도 브라우저는 원본 도메인([a.com](http://a.com))에서 온 것처럼 처리합니다.

따라서, SXG는 리소스가 어떤 경로로 전달되든 원본 출처를 인증할 수 있는 전달 메커니즘입니다.

## 1.2 핵심 기능

- 제3자(CDN·검색엔진)가 콘텐츠를 전달해도 원본 출처(origin) 유지
- 변조 방지 및 신뢰 검증
- 사전 로딩(prefetch) 지원으로 초기 로딩 성능 개선

## 1.3 범위

- 정적 HTML 중심
- SXG는 Chromium 기반 브라우저(Chrome 73, Edge 79, Opera 64 이상 버전)에서 지원

# 2. 작동방식

![image-001](./images/image-001.png)
- 출처: https://developer.chrome.com/blog/signed-exchanges?hl=ko

SXG는 다음과 같은 단계로 작동합니다.

1. 원본 서버(`a.com`)가 HTTP 응답(헤더 + 본문)을 생성하고, 이를 X.509 인증서로 서명합니다.
2. 서명된 교환 파일(.sxg)이 생성되어 외부 서버(`b.com`, e.g. CDN or 캐시)에 배포됩니다.
3. 사용자가 리소스를 요청하면, 외부 서버(`b.com`)가 SXG 파일을 전달합니다.
4. 브라우저는 서명을 검증하여 콘텐츠가 원본 출처에서 왔고 변조되지 않았음을 확인한 후, 원본 URL(`a.com`)을 주소창에 표시합니다.

즉, 콘텐츠의 출처와 배포 주체가 분리되어 특정 서버, 연결, 호스팅 서비스에 의존하지 않고도 콘텐츠를 웹에 게시할 수 있습니다.

# 3. 실습

> **⚠️ 주의사항**
> 
> - **SXG는 기본적으로 HTTPS 웹 서버에서 작동합니다. 아래 실습에서는 HTTPS 웹 서버 설정을 위한 사설 인증서 생성 과정을 다룹니다. 사설 인증서를 생성한 후에는 브라우저가 인증서를 신뢰할 수 있도록 시스템 인증서 저장소에 CA 인증서를 추가하고 '신뢰' 설정을 해야 합니다.**
> - **로컬 테스트를 위해 도메인은 localhost 를 사용합니다.**
> 

## 3.1 도구 설치: gen-certurl, gen-signedexchange

SXG를 구현하기 위해 `gen-signedexchange`, `gen-certurl` 도구를 설치합니다. 해당 도구는 Go 환경이므로, Go 언어가 설치되어 있어야 합니다.

> ref. https://github.com/WICG/webpackage/tree/main/go/signedexchange#creating-our-first-signed-exchange
> 

```bash
# signed-exchange 도구 설치
go install github.com/WICG/webpackage/go/signedexchange/cmd/gen-certurl@latest
go install github.com/WICG/webpackage/go/signedexchange/cmd/gen-signedexchange@latest

# 환경변수 설정
export PATH=$PATH:$(go env GOPATH)/bin
```

## 3.2 인증서 생성

SXG를 서빙하려면 HTTPS 웹 서버가 필요합니다. 다만, 현재는 실습 환경이므로 사설 Root CA(Certificate Authority) 인증서와 서버 인증서를 생성하여 사용합니다.

### 3.2.1 Root CA 인증서 생성: ca.crt, ca.key

Root CA 생성을 위해 OpenSSL 설정 파일 `ca.cnf` 를 작성합니다.

> `CA:TRUE` 는 해당 인증서가 CA 역할을 수행할 수 있음을 명시하는 확장 필드로, 하위 인증서(서버 인증서 등)를 서명할 수 있는 권한을 부여합니다.
> 

📄 ca.cnf

```bash
[ req ]
default_bits       = 4096
prompt             = no
default_md         = sha256
distinguished_name = dn
x509_extensions    = ca_ext

[ dn ]
CN = Signed Exchange Demo - Root CA

[ ca_ext ]
basicConstraints = critical, CA:TRUE, pathlen:0
keyUsage = critical, keyCertSign, cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always
```

작성된 `ca.cnf` 를 통해 Root CA의 개인 키(`ca.key`)와 인증서(`ca.crt`)를 생성합니다.

```bash
# Root CA 개인키 생성: ca.key
openssl genrsa -out ca.key 4096

# Root CA 인증서 생성: ca.crt
openssl req -x509 -new \
  -key ca.key \
  -out ca.crt \
  -days 1 -sha256 \
  -config ca.cnf \
  -extensions ca_ext
```

![image-002](./images/image-002.png)

### 3.2.2 서버 인증서 생성: server.crt, server.csr, server.key

서버 인증서 생성을 위해 다음의 내용을 `server.cnf` 로 저장합니다.

> `alt_names` 섹션은 인증서가 유효한 주체 대체 이름(SAN)을 정의합니다. 현재 실습은 로컬 환경이므로 `localhost` 도메인과 로컬 IP 주소 `127.0.0.1`을 지정합니다.
> 

📄 server.cnf

```bash
[ req ]
default_bits       = 2048
prompt             = no
default_md         = sha256
distinguished_name = dn
req_extensions     = server_ext

[ dn ]
CN = Signed Exchange Demo - Server CA

[ server_ext ]
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = localhost
IP.1  = 127.0.0.1
```

서버 인증서의 개인 키(`server.key`)와 인증서 서명 요청(`server.csr`)을 생성한 후, Root CA(`ca.key`, `ca.crt`)로 서명하여 서버 인증서(`server.crt`)를 발급합니다.

> CSR(Certificate Signing Request) 파일은 인증 기관(CA)에게 인증서 발급을 요청하기 위한 파일입니다. 서버의 공개 키와 기본 정보가 들어있으며, CA가 이를 확인하고 서명하여 인증서(.crt)를 만들어줍니다.
> 

```bash
# 서버 개인키 생성: server.key
openssl genrsa -out server.key 2048

# 인증서 서명 요청(CSR) 생성: server.csr
openssl req -new \
  -key server.key \
  -out server.csr \
  -config server.cnf

# Root CA로 서버 인증서 서명: server.crt
openssl x509 -req \
  -in server.csr \
  -CA ca.crt -CAkey ca.key \
  -CAcreateserial \
  -out server.crt \
  -days 1 -sha256 \
  -extfile server.cnf -extensions server_ext
```

![image-003](./images/image-003.png)

## 3.3 Signed Exchange 패키징

### 3.3.1 리소스 준비

SXG로 패키징할 정적 HTML 파일을 준비합니다.

```bash
echo "<h1>Hello SXG \!\!</h1>" > index.html
```

![image-004](./images/image-004.png)

### 3.3.2 SXG 인증서 생성: sxg.key, sxg.csr, sxg.crt

Signed Exchange에 사용할 개인키(`sxg.key`)와 인증서 서명 요청(`sxg.csr`)을 생성하고 Root CA(`ca.key`, `ca.crt`)로 서명하여 SXG 패키징용 인증서(`sxg.crt`)를 발급합니다.

> 아래 코드에 작성된 `example.com` 오리진은 Signed Exchange에 포함되는 URL의 오리진으로, 브라우저가 해당 SXG가 `example.com` 에 의해 서명되었음을 검증하는 기준입니다.
> 
> 
> `1.3.6.1.4.1.11129.2.1.22 = ASN1:NULL`는 Google이 정의한 SXG 전용 X.509 확장입니다. 해당 확장(`CanSignHttpExchanges`)에 의해 인증서가 SXG를 서명할 권한이 있음을 명시적으로 선언합니다.
> 

```bash
# SXG 개인키 생성: sxg.key
openssl ecparam -out sxg.key -name prime256v1 -genkey

# 인증서 서명 요청(CSR) 생성: sxg.csr
openssl req -new -sha256 -key sxg.key -out sxg.csr \
  -subj "/CN=example.com"

# Root CA로 SXG 인증서 서명: sxg.crt
openssl x509 -req -in sxg.csr -out sxg.crt \
    -CA ca.crt -CAkey ca.key \
    -extfile <(echo -e "1.3.6.1.4.1.11129.2.1.22 = ASN1:NULL\nsubjectAltName=DNS:example.com")
```

![image-005](./images/image-005.png)

### 3.3.3 **OCSP 응답 생성: ocsp.der**

Signed Exchange는 패키징 시점의 인증서 상태를 기준으로 검증됩니다. 이는 브라우저가 SXG 검증 과정에서 실시간 OCSP 조회를 수행하지 않기 때문이며, 대신 유효한 OCSP 응답이 Signed Exchange에 포함되어 있어야 합니다.

먼저 OCSP 응답을 생성하기 위해 CA가 발급한 인증서의 상태를 기록하는 OCSP 상태 관리 index 파일(`index.txt`)을 생성합니다.

> **OCSP 상태 관리 idnex란?**
> 
> CA가 발급한 인증서의 상태(유효·폐기·만료)를 추적하는 데이터베이스 파일입니다.<br>
> 구조: `[상태 코드]\t[만료시간]\t[폐기시간]\t[인증서 시리얼]\t[파일명 필드]\t[인증서 Subject DN]`
> - 상태 코드: `V`(유효), `R`(폐기), `E`(만료)
> - 유효한 인증서는 폐기시간이 없으므로 빈 칸(`\t\t`)으로 표시

```bash
# 변수 설정
VALIDITY_DAYS=1
if date -u -d "+${VALIDITY_DAYS} day" >/dev/null 2>&1; then
  EXPIRE_DATE=$(date -u -d "+${VALIDITY_DAYS} day" +"%y%m%d%H%M%SZ")
else
  EXPIRE_DATE=$(date -u -v+"${VALIDITY_DAYS}"d +"%y%m%d%H%M%SZ")
fi
# OCSP는 시리얼 번호 기준으로 인증서를 식별
SERIAL=$(openssl x509 -in sxg.crt -serial -noout | cut -d= -f2)

# OCSP 상태 관리 index 생성: index.txt
echo -e "V\t$EXPIRE_DATE\t\t$SERIAL\tunknown\t/CN=example.com" > index.txt
```

![image-006](./images/image-006.png)

그 다음 OCSP 상태 관리 index(`index.txt`)를 기준으로 인증서 상태를 판단하여 OCSP 응답을 생성합니다. 이는 OpenSSL OCSP Responder를 이용합니다.

> **OpenSSL OCSP Responder란?**
> 
> CA를 대신해 인증서의 현재 상태를 조회·응답하는 구성요소로, OCSP 요청을 수신하면 CA의 인증서 상태 관리 index 파일을 참조하여 해당 인증서의 유효 여부를 판단하고, 그 결과를 OCSP 응답 메시지로 생성·서명합니다.<br>
> SXG에서는 실시간 OCSP 조회를 수행하지 않으므로, OpenSSL OCSP Responder는 패키징 시점에 정적 OCSP 응답을 생성하는 역할로 사용됩니다.
> 

~~아래 두 가지 방법 중 한 가지를 선택하세요.~~(선택 1 방법을 권장합니다.)

- 선택 1) [권장] OCSP 요청·응답 생성(정적 OCSP 응답 생성)
    
    ```bash
    # OCSP 요청 생성: req.der
    openssl ocsp -issuer ca.crt -cert sxg.crt -reqout req.der -no_nonce
    
    # OCSP 응답 생성: ocsp.der
    openssl ocsp -index index.txt -rsigner ca.crt -rkey ca.key -CA ca.crt \
        -reqin req.der -respout ocsp.der -ndays 3
    ```
    
    ![image-007](./images/image-007.png)
    
- ~~선택 2) 로컬 OCSP Responder 구동을 통한 OCSP 응답 생성~~
    
    ```bash
    # OCSP Responder 백그라운드 실행: 포트 2560
    openssl ocsp -index index.txt -port 2560 \
      -rsigner ca.crt -rkey ca.key -issuer ca.crt \
      -CA ca.crt &
    OCSP_PID=$!
    
    # 서버 뜰 시간 잠깐 대기
    sleep 1
    
    # OCSP 응답 생성: ocsp.der
    openssl ocsp -issuer ca.crt -cert sxg.crt \
      -url http://127.0.0.1:2560 -respout ocsp.der \
      -CAfile ca.crt
    
    # Responder 종료
    kill $OCSP_PID
    ```
    
    ![image-008](./images/image-008.png)
    

### 3.3.4 SXG 인증서 메타데이터 생성: cert.cbor

생성된 OCSP 응답(`ocsp.der`)을 SXG 인증서와 결합하고 CBOR 형식의 인증서 메타데이터 파일(`cert.cbor`)을 생성합니다.

> 생성된 `cert.cbor` 은 브라우저가 SXG 검증 시 인증서 체인, 인증서 상태(OCSP)를 함께 검증하기 위해 사용됩니다.
> 

```bash
gen-certurl -pem sxg.crt -ocsp ocsp.der > cert.cbor
```

![image-009](./images/image-009.png)

### 3.3.5 Signed Exchage(SXG) 생성: index.sxg

앞서 작성한 리소스(`index.html`)를 Signed Exchange(SXG) 형식으로 패키징합니다.

> 옵션 설명
> 
> `-uri` SXG가 주장하는 콘텐츠의 URL 오리진<br>
> `-content` 서명할 실제 콘텐츠<br>
> `-certificate` SXG 서명에 사용될 인증서<br>
> `-privateKey` 인증서에 대응하는 개인키<br>
> `-certUrl` 인증서 메타데이터(cert.cbor)가 제공되는 URL<br>
> `-validityUrl` SXG 유효성 재검증을 위한 validity 리소스<br>
> `-o` 생성될 SXG 파일<br>
> 

```bash

gen-signedexchange \
  -uri https://example.com/ \
  -content index.html \
  -certificate sxg.crt \
  -privateKey sxg.key \
  -certUrl https://localhost/cert.cbor \
  -validityUrl https://example.com/resource.validity \
  -o index.sxg
```

![image-010](./images/image-010.png)

## 3.4 SXG 시연

### 3.4.1 WAS(flask) 실행

아래의 Flask 웹 어플리케이션 코드를 `server.py` 로 작성하고,

📄 server.py

```python
from flask import Flask, Response

app = Flask(__name__)

@app.route("/")
def index():
    return "Signed Exchange Demo"

@app.route("/cert.cbor")
def serve_cert():
    with open("./cert.cbor", "rb") as f:
        data = f.read()

    return Response(
        data,
        mimetype="application/cert-chain+cbor",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        }
    )

@app.route("/sxg")
def serve_sxg():
    with open("./index.sxg", "rb") as f:
        data = f.read()

    return Response(
        data,
        mimetype="application/signed-exchange;v=b3",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=443,
        ssl_context=("./server.crt", "./server.key"),
        debug=True
    )
```

아래의 명령어로 실행합니다.

```bash
python server.py
```

![image-011](./images/image-011.png)

### 3.4.2 사설 Root CA 인증서 신뢰

크롬 브라우저로 https://localhost 로 이동합니다. 이때, 아래와 같이 `ERR_CERT_AUTHORITY_INVALID` 가 발생한 경우 Root CA 인증서 `ca.crt` 를 브라우저에 신뢰할 수 있는 인증서로 추가해야 합니다.

> 실습 환경에서는 사설 CA를 이용하고 있으므로 앞서 생성한 Root CA 인증서를 브라우저에 신뢰할 수 있는 인증서로 추가해야 정상적으로 SXG 검증이 가능합니다.
> 

![image-012](./images/image-012.png)

Chrome 설정에서 '개인 정보 보호 및 보안' → '보안' → ‘인증서 관리’(chrome://certificate-manager/) → ‘인증서 관리’ 에서 Root CA 인증서 `ca.crt` 를 추가하고 ‘신뢰’ 항목에 ‘이 인증서 사용 시’를 ‘항상 신뢰’로 변경합니다.

![image-013](./images/image-013.png)

이후 다시 https://localhost에 접속하면 페이지가 정상적으로 표시됩니다.

![image-014](./images/image-014.png)

### 3.4.3 SXG 요청

이제 SXG 파일을 서빙하는 엔드포인트 https://localhost/sxg 에 접속하면, `gen-signedexchange` 명령어의 `uri` 옵션에 지정한 URL이 브라우저 주소창에 표시됩니다.

![image-015](./images/image-015.png)

따라서, 사용자가 https://localhost/sxg 로 접속하여 SXG 파일을 요청하면, 실제로는 localhost 서버에서 파일을 받지만 브라우저 주소창에는 `https://example.com/`이 표시됩니다. 이는 SXG의 핵심 특징으로, 제3자(localhost)가 콘텐츠를 제공하더라도 원본 출처([example.com](http://example.com))의 신원을 유지할 수 있음을 보여줍니다.

---

# References

- [How to set up Signed Exchanges using Web Packager  |  Articles  |  web.dev](https://web.dev/articles/signed-exchanges-webpackager)
- [Signed Exchanges (SXGs)  |  Articles  |  web.dev](https://web.dev/articles/signed-exchanges)
- [서명된 HTTP 교환  |  Blog  |  Chrome for Developers](https://developer.chrome.com/blog/signed-exchanges?hl=ko)
- [webpackage/go/signedexchange at main · WICG/webpackage](https://github.com/WICG/webpackage/tree/main/go/signedexchange#creating-our-first-signed-exchange)
- [How to Use Signed HTTP Exchanges (SXG) to Steal User Cookie — With Challenge Example](https://medium.com/@0x3en70rs/how-to-use-signed-http-exchanges-sxg-to-steal-user-cookie-with-challenge-example-19b313974257)
- [SECCON CTF 14(2025) Quals Writeup - Qiita](https://qiita.com/Liesegang/items/9b52589c57fd7da5dd67)