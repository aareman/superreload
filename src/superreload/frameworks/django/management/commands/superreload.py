from __future__ import annotations

import select
import sys
import threading
from typing import Any

from django.core.management import execute_from_command_line
from django.core.management.base import BaseCommand

from superreload.frameworks.django.reload_server import DjangoReloadServer


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

    def handle(self, *_args: Any, **options: Any) -> None:
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
        )

        ws_url = f"ws://{options['ws_host']}:{options['ws_port']}{ws_path}"
        self.stdout.write(self.style.SUCCESS(f"Starting superreload on {ws_url}"))
        self.stdout.write(self.style.NOTICE("Press 'r' + Enter to trigger manual reload"))
        if options["force_polling"]:
            self.stdout.write(self.style.WARNING("Using polling mode for file watching"))

        reload_server.start(background=True)
        _start_keyboard_listener(reload_server, self.stdout)

        self._run_django_server(options["addrport"])

    def _run_django_server(self, addrport: str) -> None:
        argv = [sys.argv[0], "runserver", addrport, "--noreload"]
        execute_from_command_line(argv)
