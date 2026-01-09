from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="superreload",
        description="True hot reload for Django and Python web frameworks",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    run_parser = subparsers.add_parser("run", help="Run with hot reloading")
    run_parser.add_argument(
        "framework",
        choices=["django", "flask"],
        help="Web framework to use",
    )
    run_parser.add_argument(
        "--port",
        type=int,
        default=9877,
        help="WebSocket port for browser refresh (default: 9877)",
    )
    run_parser.add_argument(
        "args",
        nargs="*",
        help="Additional arguments to pass to the framework",
    )

    subparsers.add_parser("version", help="Show version")

    args = parser.parse_args()

    if args.command == "version":
        from superreload import __version__

        print(f"superreload {__version__}")
        return 0

    if args.command == "run":
        if args.framework == "django":
            return run_django(args)
        elif args.framework == "flask":
            print("Flask support coming soon!")
            return 1

    parser.print_help()
    return 0


def run_django(args: argparse.Namespace) -> int:
    try:
        from superreload.frameworks.django import DjangoReloadServer
    except ImportError:
        print("Django is not installed. Install with: pip install superreload[django]")
        return 1

    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        import django

        django.setup()
    except Exception as e:
        print(f"Failed to setup Django: {e}")
        return 1

    server = DjangoReloadServer(websocket_port=args.port)
    print(f"Starting superreload on ws://localhost:{args.port}")

    try:
        server.start(background=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
