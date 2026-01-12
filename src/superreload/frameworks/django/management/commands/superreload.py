from __future__ import annotations

import sys
from typing import Any

from django.core.management import execute_from_command_line
from django.core.management.base import BaseCommand

from superreload.frameworks.django.reload_server import DjangoReloadServer


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
            "--no-reload",
            action="store_true",
            default=False,
            help="Disable hot reloading",
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        if options.get("no_reload"):
            self.stdout.write("Running without hot reloading")
            self._run_django_server(options["addrport"])
            return

        reload_server = DjangoReloadServer(
            host=options["ws_host"],
            websocket_port=options["ws_port"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting superreload on ws://{options['ws_host']}:{options['ws_port']}"
            )
        )

        reload_server.start(background=True)

        self._run_django_server(options["addrport"])

    def _run_django_server(self, addrport: str) -> None:
        argv = [sys.argv[0], "runserver", addrport, "--noreload"]
        execute_from_command_line(argv)
