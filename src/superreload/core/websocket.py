from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

try:
    import websockets
    from websockets import ServerConnection
    from websockets import serve as ws_serve

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    websockets = None  # type: ignore[assignment]
    ServerConnection = None  # type: ignore[misc, assignment]
    ws_serve = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


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
        on_connect: Callable[[], None] | None = None,
        on_disconnect: Callable[[], None] | None = None,
    ) -> None:
        if not HAS_WEBSOCKETS:
            raise ImportError("websockets is required. Install with: pip install superreload")
        self.host = host
        self.port = port
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self._clients: set[Any] = set()
        self._server: Any = None
        self._running = False

    async def _handler(self, websocket: Any) -> None:
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

    async def notify_error(self, error: str, details: dict[str, Any] | None = None) -> None:
        await self.broadcast(
            WebSocketMessage(
                type="error",
                data={"message": error, "details": details or {}},
            )
        )

    async def start(self) -> None:
        if self._running:
            return

        if ws_serve is None:
            raise ImportError("websockets is required")

        self._running = True
        self._server = await ws_serve(
            self._handler,
            self.host,
            self.port,
        )
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

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
