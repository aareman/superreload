from __future__ import annotations

import asyncio
import logging
import sys
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from superreload.core.errors import format_exception
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
        websocket_path: str = "/superreload",
        frontend_host: str | None = None,
        frontend_port: int | None = None,
        watch_paths: list[Path] | None = None,
        force_polling: bool = False,
        poll_delay_ms: int = 300,
        verbosity: int = 1,
    ) -> None:
        self.host: str = host
        self.websocket_port: int = websocket_port
        self.websocket_path: str = websocket_path
        self.force_polling: bool = force_polling
        self.poll_delay_ms: int = poll_delay_ms
        self.verbosity: int = verbosity
        self.host = host
        self.websocket_port = websocket_port
        self.websocket_path = websocket_path
        self.force_polling = force_polling
        self.poll_delay_ms = poll_delay_ms
        self.verbosity = verbosity

        self.frontend_host: str
        self.frontend_port: int | None
        if frontend_host is None:
            self.frontend_host = host
            self.frontend_port = websocket_port
        else:
            self.frontend_host = frontend_host
            self.frontend_port = frontend_port

        self._configure_django_settings()

        self.framework = DjangoFramework()
        self.framework.setup()

        self.reloader = Reloader(framework=self.framework)

        paths = watch_paths or self.framework.get_watch_paths()

        self.watcher = FileWatcher(
            config=FileWatcherConfig(
                paths=paths,
                patterns=self.framework.get_watch_patterns(),
                ignore_patterns=self.framework.get_ignore_patterns(),
                force_polling=force_polling,
                poll_delay_ms=poll_delay_ms,
            )
        )

        self.websocket = WebSocketServer(
            host=host,
            port=websocket_port,
            path=websocket_path,
        )

        self._running = False
        self._paused = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._recently_reloaded: dict[Path, float] = {}

    @property
    def paused(self) -> bool:
        return self._paused

    def _start_debugger_monitor(self) -> None:
        """Monitor for active debugger and pause/resume reload server.

        When a debugger (pdb, ipdb, pudb, debugpy) is active, it sets
        sys.gettrace(). We pause all reload activity and yield stdin
        so the debugger has full control. Resumes when debugger exits.
        """

        def monitor() -> None:
            while self._running:
                trace_active = sys.gettrace() is not None
                if trace_active and not self._paused:
                    self._paused = True
                    logger.debug("Debugger detected, pausing superreload")
                    print(
                        "[superreload] Debugger detected — pausing reloads",
                        flush=True,
                    )
                elif not trace_active and self._paused:
                    self._paused = False
                    logger.debug("Debugger exited, resuming superreload")
                    print(
                        "[superreload] Debugger exited — resuming reloads",
                        flush=True,
                    )
                time.sleep(0.5)

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def _configure_django_settings(self) -> None:
        try:
            from django.conf import settings

            settings.SUPERRELOAD_WS_FRONTEND_HOST = self.frontend_host
            settings.SUPERRELOAD_WS_FRONTEND_PORT = self.frontend_port
            settings.SUPERRELOAD_WS_PATH = self.websocket_path
        except Exception:
            pass

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
        if self._paused:
            return
        paths = list({c.path for c in changes})
        paths = self._filter_cooldown_files(paths)

        if not paths:
            return

        for path in paths:
            logger.debug(f"File change: {path}")

        py_files = [p for p in paths if p.suffix == ".py"]
        css_files = [p for p in paths if p.suffix == ".css"]
        js_files = [p for p in paths if p.suffix == ".js"]
        html_files = [p for p in paths if p.suffix == ".html"]
        other_files = [p for p in paths if p.suffix not in (".py", ".css", ".js", ".html")]

        ctx = ReloadContext(changed_files=paths)

        if not self.framework.can_reload(ctx):
            print("[superreload] Change requires server restart (migrations/settings)", flush=True)
            return

        if py_files:
            self._mark_reloaded(py_files)
            self.framework.before_reload(ctx)
            result = await self.reloader.reload_from_paths(py_files)
            self.framework.after_reload(ctx, result)

            if result.success:
                print(f"[superreload] Reloaded: {', '.join(result.reloaded_modules)}", flush=True)
            else:
                print(f"[superreload] Reload failed: {result.errors}", flush=True)
                error_details = []
                for i, error in enumerate(result.errors):
                    module_name = (
                        result.failed_modules[i] if i < len(result.failed_modules) else None
                    )
                    error_details.append(format_exception(error, module_name).to_dict())
                    logger.error(f"Reload error in {module_name}: {error}")

                await self.websocket.notify_error(
                    "Reload failed",
                    {"errors": error_details},
                )
                return

        if css_files:
            css_names = [str(p.name) for p in css_files]
            logger.info(f"CSS hot reload: {', '.join(css_names)}")
            await self.websocket.notify_css_reload(css_names)

        if js_files:
            js_names = [str(p.name) for p in js_files]
            logger.info(f"JS hot reload: {', '.join(js_names)}")
            await self.websocket.notify_js_reload(js_names)

        if html_files:
            self.framework._clear_template_caches()
            html_names = [str(p.name) for p in html_files]
            logger.info(f"Template reload: {', '.join(html_names)}")
            await self.websocket.notify_reload(html_names)

        if py_files or other_files:
            file_names = [str(p.name) for p in py_files + other_files]
            await self.websocket.notify_reload(file_names)

    async def _run(self) -> None:
        actual_port = await self.websocket.start()
        if actual_port != self.websocket_port:
            self.websocket_port = actual_port
            self._configure_django_settings()
        ws_url = f"ws://{self.host}:{self.websocket_port}{self.websocket_path}"
        print(f"[superreload] WebSocket server started on {ws_url}", flush=True)
        print(
            f"[superreload] Watching for file changes (polling={self.force_polling})...", flush=True
        )

        async for changes in self.watcher.watch():
            if not self._running:
                break
            print(f"[superreload] Detected changes: {[str(c.path) for c in changes]}", flush=True)
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

        self._start_debugger_monitor()

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

    def trigger_reload(self) -> None:
        if self._loop and self._running:
            self._loop.call_soon_threadsafe(
                lambda: asyncio.ensure_future(
                    self.websocket.notify_reload(["manual"]), loop=self._loop
                )
            )
