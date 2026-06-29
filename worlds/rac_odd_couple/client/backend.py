"""
Embedded local server for the Ratchet & Clank: The Odd Couple client.

Runs entirely inside the Archipelago client process - no external project,
subprocess, or virtualenv required. A stdlib HTTP server (in a background
thread) serves the frontend and the locally patched swf, plus the small REST
API the patched buttons call into; a `websockets` server (in the client's own
asyncio loop) pushes live suppress/enable state to the browser tab. The only
dependency used here beyond the standard library is `websockets`, which the
Archipelago client already requires for talking to the multiworld server.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Awaitable, Callable, Optional
from urllib.parse import parse_qs, urlparse

import websockets

logger = logging.getLogger("OddCoupleServer")

HOST = "127.0.0.1"
HTTP_PORT = 8000
WS_PORT = 8001
BASE_URL = f"http://{HOST}:{HTTP_PORT}"

ALL_SCENES = ["stereo", "taxiDriver", "gimp", "phonecall1", "scissors", "tv"]

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
PATCHED_SWF_NAME = "ap_patched_odd_couple.swf"

_CONTENT_TYPES = {
    ".html": "text/html",
    ".js": "application/javascript",
    ".css": "text/css",
}


def runtime_game_dir() -> str:
    """Writable folder where the patched swf is installed - independent of
    any external project, so this world has no runtime dependency on one."""
    import Utils
    path = Utils.user_path("rac_odd_couple")
    os.makedirs(path, exist_ok=True)
    return path


def install_patched_swf(patched_swf_path: str) -> str:
    """Copy the freshly patched swf (built by Patch.create_rom_file from the
    .apoddcouple file) into our runtime folder, under a fixed name the
    frontend always requests."""
    import shutil
    dest = os.path.join(runtime_game_dir(), PATCHED_SWF_NAME)
    shutil.copyfile(patched_swf_path, dest)
    return PATCHED_SWF_NAME


def find_installed_patched_swf() -> Optional[str]:
    """Return PATCHED_SWF_NAME if a previous run already installed it, so a
    reconnect-only launch (no .apoddcouple this time) still has a movie to
    serve instead of leaving the frontend with nothing to load."""
    if os.path.exists(os.path.join(runtime_game_dir(), PATCHED_SWF_NAME)):
        return PATCHED_SWF_NAME
    return None


class OddCoupleServer:
    """Embedded HTTP + WebSocket server bridging the browser-side SWF player
    to the Archipelago client running in the same process."""

    def __init__(self, on_scene_initiated: Callable[[str], Awaitable[None]]) -> None:
        self.on_scene_initiated = on_scene_initiated
        self.suppressed_events: set[str] = set(ALL_SCENES)
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws_clients: "set[websockets.WebSocketServerProtocol]" = set()
        self._http_server: Optional[ThreadingHTTPServer] = None
        self._http_thread: Optional[threading.Thread] = None
        self._ws_server = None

    # ---------- lifecycle ----------

    def start_http(self) -> None:
        server_ref = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: object) -> None:
                logger.debug("%s - %s", self.address_string(), fmt % args)

            def _send_json(self, status: int, payload: object) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_text(self, status: int, text: str) -> None:
                body = text.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_file(self, path: str, content_type: str) -> None:
                if not os.path.isfile(path):
                    self._send_text(404, "Not found")
                    return
                with open(path, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
                parsed = urlparse(self.path)
                path, query = parsed.path, parse_qs(parsed.query)

                if path == "/api/check":
                    scene = (query.get("scene") or [""])[0]
                    with server_ref._lock:
                        allowed = scene not in server_ref.suppressed_events
                    self._send_text(200 if allowed else 403, "ok" if allowed else "suppressed")
                    return

                if path == "/api/received":
                    scene = (query.get("scene") or [""])[0]
                    server_ref._notify_scene_initiated(scene)
                    self._send_text(200, "ok")
                    return

                if path == f"/game/{PATCHED_SWF_NAME}":
                    self._send_file(os.path.join(runtime_game_dir(), PATCHED_SWF_NAME),
                                    "application/x-shockwave-flash")
                    return

                rel = path.lstrip("/") or "index.html"
                content_type = _CONTENT_TYPES.get(os.path.splitext(rel)[1], "application/octet-stream")
                self._send_file(os.path.join(FRONTEND_DIR, rel), content_type)

            def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b"{}"
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError:
                    payload = {}
                events = set(payload.get("events", []))

                if self.path == "/api/suppress":
                    server_ref.suppress(events)
                elif self.path == "/api/enable":
                    server_ref.enable(events)
                elif self.path == "/api/set_suppressed":
                    server_ref.set_suppressed(events)
                else:
                    self._send_text(404, "Not found")
                    return
                with server_ref._lock:
                    self._send_json(200, sorted(server_ref.suppressed_events))

        self._http_server = ThreadingHTTPServer((HOST, HTTP_PORT), Handler)
        self._http_thread = threading.Thread(target=self._http_server.serve_forever, daemon=True)
        self._http_thread.start()

    async def start_ws(self) -> None:
        self._loop = asyncio.get_running_loop()

        async def handler(ws: "websockets.WebSocketServerProtocol") -> None:
            self._ws_clients.add(ws)
            try:
                with self._lock:
                    suppressed = sorted(self.suppressed_events)
                await ws.send(json.dumps({"type": "state", "suppressed": suppressed}))
                async for _raw in ws:
                    pass  # event_fired/movie_played reports from the browser are debug-only
            except websockets.exceptions.WebSocketException:
                pass
            finally:
                self._ws_clients.discard(ws)

        self._ws_server = await websockets.serve(handler, HOST, WS_PORT)

    def stop(self) -> None:
        if self._http_server:
            self._http_server.shutdown()
        if self._ws_server:
            self._ws_server.close()

    # ---------- state changes (called from the AP client's own event loop) ----------

    def set_suppressed(self, suppressed: "set[str] | list[str]") -> None:
        with self._lock:
            self.suppressed_events = set(suppressed)
        self._broadcast({"type": "set_suppressed", "events": sorted(self.suppressed_events)})

    def enable(self, events: "set[str] | list[str]") -> None:
        if not events:
            return
        with self._lock:
            self.suppressed_events -= set(events)
        self._broadcast({"type": "enable", "events": list(events)})

    def suppress(self, events: "set[str] | list[str]") -> None:
        if not events:
            return
        with self._lock:
            self.suppressed_events |= set(events)
        self._broadcast({"type": "suppress", "events": list(events)})

    # ---------- bridging between the HTTP thread and the asyncio loop ----------

    def _notify_scene_initiated(self, scene: str) -> None:
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self.on_scene_initiated(scene), self._loop)

    def _broadcast(self, message: dict) -> None:
        if self._loop is None or not self._ws_clients:
            return
        data = json.dumps(message)

        async def _send_all() -> None:
            dead = []
            for ws in list(self._ws_clients):
                try:
                    await ws.send(data)
                except websockets.exceptions.WebSocketException:
                    dead.append(ws)
            for ws in dead:
                self._ws_clients.discard(ws)

        asyncio.run_coroutine_threadsafe(_send_all(), self._loop)
