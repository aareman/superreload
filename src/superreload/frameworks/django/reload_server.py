from __future__ import annotations

import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from superreload.core.framework import ReloadContext
from superreload.core.reloader import Reloader
from superreload.core.watcher import FileChange, FileWatcher, FileWatcherConfig
from superreload.core.websocket import WebSocketServer
from superreload.frameworks.django.framework import DjangoFramework

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

RELOAD_COOLDOWN_SECONDS = 1.0


class DjangoReloadServer:
    def __init__(
        self,
        host: str = "localhost",
        websocket_port: int = 9877,
        watch_paths: list[Path] | None = None,
    ) -> None:
        self.host = host
        self.websocket_port = websocket_port

        self.framework = DjangoFramework()
        self.framework.setup()

        self.reloader = Reloader(framework=self.framework)

        paths = watch_paths or self.framework.get_watch_paths()

        self.watcher = FileWatcher(
            config=FileWatcherConfig(
                paths=paths,
                patterns=self.framework.get_watch_patterns(),
                ignore_patterns=self.framework.get_ignore_patterns(),
            )
        )

        self.websocket = WebSocketServer(
            host=host,
            port=websocket_port,
        )

        self._running = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._recently_reloaded: dict[Path, float] = {}

    def _filter_cooldown_files(self, paths: list[Path]) -> list[Path]:
        now = time.time()
        filtered = []
        for path in paths:
            last_reload = self._recently_reloaded.get(path)
            if last_reload is None or (now - last_reload) > RELOAD_COOLDOWN_SECONDS:
                filtered.append(path)
            else:
                logger.debug(f"Ignoring {path} (in cooldown)")
        return filtered

    def _mark_reloaded(self, paths: list[Path]) -> None:
        now = time.time()
        for path in paths:
            self._recently_reloaded[path] = now
        self._cleanup_old_entries()

    def _cleanup_old_entries(self) -> None:
        now = time.time()
        expired = [p for p, t in self._recently_reloaded.items() if (now - t) > 10.0]
        for p in expired:
            del self._recently_reloaded[p]

    async def _handle_file_changes(self, changes: list[FileChange]) -> None:
        paths = list({c.path for c in changes})
        paths = self._filter_cooldown_files(paths)

        if not paths:
            return

        for path in paths:
            logger.debug(f"File change: {path}")

        py_files = [p for p in paths if p.suffix == ".py"]

        ctx = ReloadContext(changed_files=paths)

        if not self.framework.can_reload(ctx):
            logger.info("Change requires server restart (migrations/settings)")
            return

        if py_files:
            self._mark_reloaded(py_files)
            self.framework.before_reload(ctx)
            result = await self.reloader.reload_from_paths(py_files)
            self.framework.after_reload(ctx, result)

            if result.success:
                logger.info(f"Reloaded: {', '.join(result.reloaded_modules)}")
            else:
                for error in result.errors:
                    logger.error(f"Reload error: {error}")
                await self.websocket.notify_error(
                    "Reload failed",
                    {"errors": [str(e) for e in result.errors]},
                )
                return

        file_names = [str(p.name) for p in paths]
        await self.websocket.notify_reload(file_names)

    async def _run(self) -> None:
        await self.websocket.start()
        logger.info(f"SuperReload server started on ws://{self.host}:{self.websocket_port}")

        async for changes in self.watcher.watch():
            if not self._running:
                break
            await self._handle_file_changes(changes)

    def _run_in_thread(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._running = True
        try:
            self._loop.run_until_complete(self._run())
        except Exception as e:
            logger.error(f"SuperReload server error: {e}")
        finally:
            self._loop.close()

    def start(self, background: bool = True) -> None:
        if self._running:
            return

        if background:
            self._thread = threading.Thread(target=self._run_in_thread, daemon=True)
            self._thread.start()
        else:
            self._running = True
            asyncio.run(self._run())

    def stop(self) -> None:
        self._running = False
        self.watcher.stop()
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
