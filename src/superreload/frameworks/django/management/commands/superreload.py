from __future__ import annotations

import logging
import select
import sys
import threading
from typing import Any

from django.core.management import execute_from_command_line
from django.core.management.base import BaseCommand

from superreload.frameworks.django.reload_server import DjangoReloadServer

DJANGO_VERBOSITY_MINIMAL = 0
DJANGO_VERBOSITY_NORMAL = 1
DJANGO_VERBOSITY_VERBOSE = 2
DJANGO_VERBOSITY_DEBUG = 3


def _start_keyboard_listener(reload_server: DjangoReloadServer, stdout: Any) -> None:
    def keyboard_thread() -> None:
        stdin = sys.stdin

        if not stdin.isatty():
            return

        while True:
            try:
                readable, _, _ = select.select([stdin], [], [], 0.5)
                if readable:
                    char = stdin.read(1)
                    if char.lower() == "r":
                        stdout.write("Manual reload triggered\n")
                        reload_server.trigger_reload()
            except Exception:
                break

    thread = threading.Thread(target=keyboard_thread, daemon=True)
    thread.start()


class Command(BaseCommand):  # type: ignore[misc]
    help = "Run Django development server with superreload hot reloading"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "addrport",
            nargs="?",
            default="8000",
            help="Optional port number or ipaddr:port for Django server",
        )
        parser.add_argument(
            "--ws-host",
            type=str,
            default="localhost",
            help="WebSocket server host (default: localhost)",
        )
        parser.add_argument(
            "--ws-port",
            type=int,
            default=9877,
            help="WebSocket server port (default: 9877)",
        )
        parser.add_argument(
            "--ws-path",
            type=str,
            default="/superreload",
            help="WebSocket URL path (default: /superreload)",
        )
        parser.add_argument(
            "--no-reload",
            action="store_true",
            default=False,
            help="Disable hot reloading",
        )
        parser.add_argument(
            "--force-polling",
            action="store_true",
            default=False,
            help="Use polling instead of filesystem notifications (required for Docker)",
        )
        parser.add_argument(
            "--poll-delay",
            type=int,
            default=300,
            help="Delay between polls in milliseconds when using --force-polling (default: 300)",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            default=False,
            help="Enable debug output (equivalent to --verbosity 3)",
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        verbosity = options.get("verbosity", DJANGO_VERBOSITY_NORMAL)
        if options.get("debug"):
            verbosity = DJANGO_VERBOSITY_DEBUG

        self._configure_logging(verbosity)

        if options.get("no_reload"):
            self.stdout.write("Running without hot reloading")
            self._run_django_server(options["addrport"])
            return

        ws_path = options["ws_path"]
        if not ws_path.startswith("/"):
            ws_path = "/" + ws_path

        reload_server = DjangoReloadServer(
            host=options["ws_host"],
            websocket_port=options["ws_port"],
            websocket_path=ws_path,
            force_polling=options["force_polling"],
            poll_delay_ms=options["poll_delay"],
            verbosity=verbosity,
        )

        self.stdout.write(self.style.NOTICE("Press 'r' + Enter to trigger manual reload"))
        if options["force_polling"]:
            self.stdout.write(self.style.WARNING("Using polling mode for file watching"))

        if verbosity >= DJANGO_VERBOSITY_VERBOSE:
            self._print_verbose_config(reload_server)

        reload_server.start(background=True)
        _start_keyboard_listener(reload_server, self.stdout)

        self._run_django_server(options["addrport"])

    def _configure_logging(self, verbosity: int) -> None:
        superreload_logger = logging.getLogger("superreload")

        if verbosity >= DJANGO_VERBOSITY_DEBUG:
            superreload_logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(logging.Formatter("[superreload] %(levelname)s: %(message)s"))
            superreload_logger.addHandler(handler)
        elif verbosity >= DJANGO_VERBOSITY_VERBOSE:
            superreload_logger.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter("[superreload] %(message)s"))
            superreload_logger.addHandler(handler)

    def _print_verbose_config(self, reload_server: DjangoReloadServer) -> None:
        self.stdout.write("\n[superreload] Configuration:")
        self.stdout.write("  Watch paths:")
        for path in reload_server.watcher.config.paths:
            self.stdout.write(f"    - {path}")
        self.stdout.write(f"  Watch patterns: {', '.join(reload_server.watcher.config.patterns)}")
        self.stdout.write(
            f"  Ignore patterns: {', '.join(reload_server.watcher.config.ignore_patterns)}"
        )
        self.stdout.write(f"  Force polling: {reload_server.force_polling}")
        if reload_server.force_polling:
            self.stdout.write(f"  Poll delay: {reload_server.poll_delay_ms}ms")

        try:
            from django.apps import apps

            app_names = [app.name for app in apps.get_app_configs()]
            self.stdout.write(f"  Django apps: {', '.join(app_names)}")
        except Exception:
            pass
        self.stdout.write("")

    def _run_django_server(self, addrport: str) -> None:
        argv = [sys.argv[0], "runserver", addrport, "--noreload"]
        execute_from_command_line(argv)
