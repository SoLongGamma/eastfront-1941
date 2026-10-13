#!/usr/bin/env python3
"""live/site 정적 서버 (127.0.0.1 전용, 디렉터리 목록 금지, 캐시 짧게). 터널(cloudflared)이 이 포트를 공개한다."""
import http.server, os, sys
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")
PORT = int(os.environ.get("EF_PORT", "8941"))


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=SITE, **k)

    def list_directory(self, path):
        self.send_error(404); return None

    def end_headers(self):
        p = self.path.split("?")[0]
        self.send_header("Cache-Control", "no-cache, max-age=0" if p.endswith((".html", ".json", "/")) else "public, max-age=60")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
