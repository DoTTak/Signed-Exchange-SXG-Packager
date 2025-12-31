#!/bin/bash
set -euo pipefail

log_step() { echo -e "\n=============================================\n[STEP] $*\n============================================="; }
log_info() { echo "[INFO] $*"; }
log_cmd()  { echo "[CMD ] $*"; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[ERROR] '$1' not found in PATH." >&2
    exit 127
  }
}

for c in openssl gen-certurl gen-signedexchange; do
  require_cmd "$c"
done

log_step "변수 설정 및 초기화"
DNS_NAME="localhost"
IP_ADDR="127.0.0.1"
CA_NAME="Signed Exchange Demo"
SXG_DOMAIN="example.com"
VALIDITY_DAYS=1

if date -u -d "+${VALIDITY_DAYS} day" >/dev/null 2>&1; then
  EXPIRE_DATE=$(date -u -d "+${VALIDITY_DAYS} day" +"%y%m%d%H%M%SZ")
else
  EXPIRE_DATE=$(date -u -v+"${VALIDITY_DAYS}"d +"%y%m%d%H%M%SZ")
fi

CERT_DIR="./certs"
log_info "인증서 디렉터리 초기화: ${CERT_DIR}"
rm -rf "${CERT_DIR}"
mkdir -p "${CERT_DIR}"
cd "${CERT_DIR}"

log_step "Root CA 생성"
cat > ca.cnf <<EOF
[ req ]
default_bits       = 4096
prompt             = no
default_md         = sha256
distinguished_name = dn
x509_extensions    = ca_ext

[ dn ]
CN = ${CA_NAME} - Root CA

[ ca_ext ]
basicConstraints = critical, CA:TRUE, pathlen:0
keyUsage = critical, keyCertSign, cRLSign
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always
EOF

log_cmd "openssl genrsa -out ca.key 4096"
openssl genrsa -out ca.key 4096

log_cmd "openssl req -x509 -new -key ca.key -out ca.crt"
openssl req -x509 -new \
  -key ca.key \
  -out ca.crt \
  -days "${VALIDITY_DAYS}" \
  -sha256 \
  -config ca.cnf \
  -extensions ca_ext

log_step "HTTPS 서버 인증서 생성"
cat > server.cnf <<EOF
[ req ]
default_bits       = 2048
prompt             = no
default_md         = sha256
distinguished_name = dn
req_extensions     = server_ext

[ dn ]
CN = ${CA_NAME} - Server Cert

[ server_ext ]
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = ${DNS_NAME}
IP.1  = ${IP_ADDR}
EOF

log_cmd "openssl genrsa -out server.key 2048"
openssl genrsa -out server.key 2048

log_cmd "openssl req -new -key server.key -out server.csr"
openssl req -new -key server.key -out server.csr -config server.cnf

log_cmd "openssl x509 -req -in server.csr -out server.crt"
openssl x509 -req \
  -in server.csr \
  -CA ca.crt -CAkey ca.key \
  -out server.crt \
  -days "${VALIDITY_DAYS}" \
  -sha256 \
  -extfile server.cnf \
  -extensions server_ext

log_step "리소스 준비"
log_info "index.html 생성"
echo "<h1>Hello SXG !!</h1>" > index.html

log_step "SXG 인증서 생성"
log_cmd "openssl ecparam -name prime256v1 -genkey -out sxg.key"
openssl ecparam -name prime256v1 -genkey -out sxg.key

log_cmd "openssl req -new -sha256 -key sxg.key -out sxg.csr"
openssl req -new -sha256 \
  -key sxg.key \
  -out sxg.csr \
  -subj "/CN=${SXG_DOMAIN}"

cat > sxg_ext.cnf <<EOF
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature
subjectAltName = DNS:${SXG_DOMAIN}
1.3.6.1.4.1.11129.2.1.22 = ASN1:NULL
EOF

log_cmd "openssl x509 -req -in sxg.csr -out sxg.crt"
openssl x509 -req \
  -in sxg.csr \
  -CA ca.crt -CAkey ca.key \
  -out sxg.crt \
  -days "${VALIDITY_DAYS}" \
  -sha256 \
  -extfile sxg_ext.cnf

log_step "OCSP 응답 생성"
log_info "SXG 인증서 시리얼 조회"
SERIAL=$(openssl x509 -in sxg.crt -serial -noout | cut -d= -f2)

log_info "OCSP index.txt 생성"
echo -e "V\t${EXPIRE_DATE}\t\t${SERIAL}\tunknown\t/CN=${SXG_DOMAIN}" > index.txt

log_cmd "openssl ocsp -issuer ca.crt -cert sxg.crt -reqout req.der"
openssl ocsp \
  -issuer ca.crt \
  -cert sxg.crt \
  -reqout req.der \
  -no_nonce

log_cmd "openssl ocsp -respout ocsp.der"
openssl ocsp \
  -index index.txt \
  -rsigner ca.crt \
  -rkey ca.key \
  -CA ca.crt \
  -reqin req.der \
  -respout ocsp.der \
  -ndays "${VALIDITY_DAYS}"

log_step "cert.cbor 생성"
log_cmd "gen-certurl -pem sxg.crt -ocsp ocsp.der"
gen-certurl -pem sxg.crt -ocsp ocsp.der > cert.cbor

log_step "Signed Exchange 생성"
log_cmd "gen-signedexchange -o index.sxg"
gen-signedexchange \
  -uri "https://${SXG_DOMAIN}/" \
  -content index.html \
  -certificate sxg.crt \
  -privateKey sxg.key \
  -certUrl "https://${DNS_NAME}/cert.cbor" \
  -validityUrl "https://${SXG_DOMAIN}/resource.validity" \
  -o index.sxg

log_info "완료: index.sxg 생성됨"
