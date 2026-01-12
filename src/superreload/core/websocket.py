from __future__ import annotations

import asyncio
import json
import logging
import socket
from dataclasses import dataclass, field
from typing import Any, Callable

try:
    import websockets
    from websockets import serve as ws_serve

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    websockets = None  # type: ignore[assignment]
    ws_serve = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)


def is_port_available(host: str, port: int) -> bool:
    """Check if a port is available for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(host: str, start_port: int, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port.

    Args:
        host: The host to bind to.
        start_port: The port to start searching from.
        max_attempts: Maximum number of ports to try.

    Returns:
        An available port number.

    Raises:
        RuntimeError: If no available port is found within max_attempts.
    """
    for offset in range(max_attempts):
        port = start_port + offset
        if is_port_available(host, port):
            return port
    raise RuntimeError(
        f"Could not find available port in range {start_port}-{start_port + max_attempts - 1}"
    )


@dataclass
class WebSocketMessage:
    type: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({"type": self.type, "data": self.data})

    @classmethod
    def from_json(cls, raw: str) -> WebSocketMessage:
        parsed = json.loads(raw)
        return cls(type=parsed.get("type", "unknown"), data=parsed.get("data", {}))


class WebSocketServer:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 9877,
        path: str = "/superreload",
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[[], None] | None = None,
    ) -> None:
        if not HAS_WEBSOCKETS:
            raise ImportError("websockets is required. Install with: pip install superreload")
        self.host = host
        self.port = port
        self.path = path.rstrip("/") if path != "/" else path
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self._clients: set[Any] = set()
        self._server: Any = None
        self._running = False

    async def _handler(self, websocket: Any) -> None:
        request = getattr(websocket, "request", None)
        if request is not None:
            request_path: str = getattr(request, "path", "/")
            normalized_path = request_path.rstrip("/") if request_path != "/" else request_path
            if normalized_path != self.path:
                await websocket.close(1008, "Invalid path")
                return

        self._clients.add(websocket)
        logger.debug(f"Client connected. Total clients: {len(self._clients)}")

        if self.on_connect:
            self.on_connect()

        try:
            await websocket.send(
                WebSocketMessage(type="connected", data={"status": "ok"}).to_json()
            )
            async for message in websocket:
                try:
                    msg = WebSocketMessage.from_json(str(message))
                    logger.debug(f"Received message: {msg.type}")
                    if msg.type == "force_reload":
                        logger.info("Manual reload requested from browser")
                        await self.notify_reload(["manual"])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")
        except Exception as e:
            logger.debug(f"WebSocket error: {e}")
        finally:
            self._clients.discard(websocket)
            logger.debug(f"Client disconnected. Total clients: {len(self._clients)}")
            if self.on_disconnect:
                self.on_disconnect()

    async def broadcast(self, message: WebSocketMessage) -> None:
        if not self._clients:
            return

        await asyncio.gather(
            *[client.send(message.to_json()) for client in self._clients],
            return_exceptions=True,
        )

    async def notify_reload(self, files: list[str] | None = None) -> None:
        await self.broadcast(
            WebSocketMessage(
                type="reload",
                data={"files": files or [], "timestamp": asyncio.get_event_loop().time()},
            )
        )

    async def notify_css_reload(self, files: list[str]) -> None:
        await self.broadcast(
            WebSocketMessage(
                type="css_reload",
                data={"files": files, "timestamp": asyncio.get_event_loop().time()},
            )
        )

    async def notify_js_reload(self, files: list[str]) -> None:
        await self.broadcast(
            WebSocketMessage(
                type="js_reload",
                data={"files": files, "timestamp": asyncio.get_event_loop().time()},
            )
        )

    async def notify_error(self, error: str, details: dict[str, Any] | None = None) -> None:
        await self.broadcast(
            WebSocketMessage(
                type="error",
                data={"message": error, "details": details or {}},
            )
        )

    async def start(self) -> int:
        """Start the WebSocket server, auto-selecting port if needed.

        Returns:
            The actual port the server is running on.
        """
        if self._running:
            return self.port

        if ws_serve is None:
            raise ImportError("websockets is required")

        if not is_port_available(self.host, self.port):
            old_port = self.port
            self.port = find_available_port(self.host, self.port + 1)
            logger.info(f"Port {old_port} in use, using {self.port} instead")

        self._running = True
        self._server = await ws_serve(
            self._handler,
            self.host,
            self.port,
        )
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}{self.path}")
        return self.port

    async def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("WebSocket server stopped")

    @property
    def client_count(self) -> int:
        return len(self._clients)

    @property
    def is_running(self) -> bool:
        return self._running
