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
            "--superreload-port",
            type=int,
            default=9877,
            help="WebSocket port for superreload (default: 9877)",
        )
        parser.add_argument(
            "--no-superreload",
            action="store_true",
            default=False,
            help="Disable superreload",
        )
        parser.add_argument(
            "addrport",
            nargs="?",
            default="8000",
            help="Optional port number or ipaddr:port",
        )

    def handle(self, *_args: Any, **options: Any) -> None:
        if options.get("no_superreload"):
            self.stdout.write("Running without superreload")
            self._run_django_server(options["addrport"])
            return

        reload_server = DjangoReloadServer(
            websocket_port=options["superreload_port"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting superreload on ws://localhost:{options['superreload_port']}"
            )
        )

        reload_server.start(background=True)

        self._run_django_server(options["addrport"])

    def _run_django_server(self, addrport: str) -> None:
        argv = [sys.argv[0], "runserver", addrport, "--noreload"]
        execute_from_command_line(argv)
