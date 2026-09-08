# -*- coding: utf-8 -*-
# VoiceNote local server — serves the web app AND proxies /v1/* to llama-server :8080.
#   HTTPS :8443  -> มือถือ/คนนอก (secure context = mic ทำงาน)
#   HTTP  :8444  -> localhost เท่านั้น (ให้ cloudflared tunnel เข้าถึงได้)
# Public access: cloudflared quick tunnel -> https://<random>.trycloudflare.com
# Security: ตั้ง env VN_SECRET=... แล้ว /v1/* ต้องส่ง ?token=<secret> (หน้าเว็บใส่ใน ⚙)
import http.server, ssl, os, sys, urllib.request
from urllib.parse import urlparse, parse_qs

PORT = 8443
ROOT = os.path.dirname(os.path.abspath(__file__))
UPSTREAM = "http://127.0.0.1:8080"
SECRET = os.environ.get("VN_SECRET", "")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    # ---- guard: ปิดกั้น /v1/* ด้วย token (ถ้าตั้ง VN_SECRET) ----
    def _denied(self):
        self.send_response(403)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"forbidden: bad or missing token")

    def _token_ok(self):
        if not SECRET:
            return True
        tok = parse_qs(urlparse(self.path).query).get("token", [""])[0]
        return tok == SECRET

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
            if not self._token_ok():
                return self._denied()
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
            if not self._token_ok():
                return self._denied()
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

    # HTTP (localhost only) — origin ของ cloudflared tunnel
    local_httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 8444), Handler)
    import threading
    threading.Thread(target=local_httpd.serve_forever, daemon=True).start()

    print("VoiceNote local HTTPS on port %d (serves app + proxies /v1 -> :8080)" % PORT)
    print("HTTP origin for cloudflared: http://127.0.0.1:8444")
    print("Token guard:", "ON" if SECRET else "OFF (set VN_SECRET to enable)")
    sys.stdout.flush()
    httpd.serve_forever()
