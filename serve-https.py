# -*- coding: utf-8 -*-
# VoiceNote local HTTPS server — serves the web app AND proxies /v1/* to llama-server :8080.
# One origin (https://<LAN-IP>:8443) = mic works (secure context) + same-origin LLM API (no CORS/mixed-content).
import http.server, ssl, os, sys, urllib.request

PORT = 8443
ROOT = os.path.dirname(os.path.abspath(__file__))
UPSTREAM = "http://127.0.0.1:8080"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    # ---- proxy /v1/* -> llama-server :8080 (same-origin LLM API) ----
    def _proxy(self, method):
        body = None
        if method in ("POST", "PUT"):
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n) if n else b""
        req = urllib.request.Request(UPSTREAM + self.path, data=body, method=method)
        for h in ("Content-Type", "Authorization"):
            if self.headers.get(h):
                req.add_header(h, self.headers[h])
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                data = r.read()
                self.send_response(r.status)
                self.send_header("Content-Type", r.headers.get("Content-Type", "application/json"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except Exception as e:
            msg = ("proxy error: %s" % e).encode()
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(msg)

    def do_POST(self):
        if self.path.startswith("/v1/"):
            return self._proxy("POST")
        self.send_error(405)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        if self.path.startswith("/v1/"):
            return self._proxy("GET")
        super().do_GET()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    cert_dir = ROOT
    key, crt = os.path.join(cert_dir, "local.key"), os.path.join(cert_dir, "local.crt")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(crt, key)
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    print("VoiceNote local HTTPS on port %d (serves app + proxies /v1 -> :8080)" % PORT)
    sys.stdout.flush()
    httpd.serve_forever()
