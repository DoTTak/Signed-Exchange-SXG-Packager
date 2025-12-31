from flask import Flask, Response

app = Flask(__name__)

@app.route("/")
def index():
    return "Signed Exchange Demo"

@app.route("/cert.cbor")
def serve_cert():
    with open("./output/cert.cbor", "rb") as f:
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
    with open("./output/index.sxg", "rb") as f:
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
    app.run(
        host="0.0.0.0",
        port=443,
        ssl_context=("./example/server.crt", "./example/server.key"),
        debug=True
    )