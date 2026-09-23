"""HTTP server for canon federation — exposes local canon to peers."""
import http.server
import json
import socketserver
import threading
from typing import Dict

from .protocol import CanonFederation, Peer


class FederationHTTPHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for the federation server."""

    fed: CanonFederation = None  # Class-level, set before server starts

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/info"):
            self._send_json({"info": self.fed.stats()})
        elif self.path == "/canon/list":
            self._send_json({"canon": list(self.fed.state.canon.keys())})
        elif self.path.startswith("/canon/"):
            canon_id = self.path[len("/canon/"):]
            if canon_id in self.fed.state.canon:
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown")
                self.end_headers()
                self.wfile.write(self.fed.state.canon[canon_id].encode())
            else:
                self.send_error(404, "canon not found")
        elif self.path == "/peers":
            self._send_json({"peers": [p.to_dict() for p in self.fed.list_peers()]})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/submit":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            try:
                data = json.loads(body)
                canon_id = data.get("id")
                lore = data.get("lore", "")
                if not canon_id or not lore:
                    self.send_error(400, "id and lore required")
                    return
                self.fed.add_local_canon(canon_id, lore)
                self._send_json({"admitted": True, "id": canon_id, "n_canon": len(self.fed.state.canon)})
            except Exception as e:
                self.send_error(400, str(e))
        elif self.path.startswith("/peers/add"):
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            try:
                data = json.loads(body)
                peer = self.fed.add_peer(data["name"], data["url"])
                self._send_json({"added": peer.to_dict()})
            except Exception as e:
                self.send_error(400, str(e))
        else:
            self.send_error(404)

    def _send_json(self, data):
        body = json.dumps(data, indent=1).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # silence


def start_server(fed: CanonFederation, port: int = 8767) -> threading.Thread:
    """Start the federation server in a background thread."""
    FederationHTTPHandler.fed = fed

    class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    server = ThreadedServer(("", port), FederationHTTPHandler)

    def serve():
        server.serve_forever()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return thread, server
