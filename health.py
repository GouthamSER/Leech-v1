"""Tiny TCP/HTTP health endpoint for hosts that require an open port (Koyeb, Render, ...)."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    do_HEAD = do_GET

    def log_message(self, *args):
        pass


def start_health_server(port, host="0.0.0.0"):
    srv = ThreadingHTTPServer((host, port), _Handler)
    Thread(target=srv.serve_forever, daemon=True).start()
    return srv
