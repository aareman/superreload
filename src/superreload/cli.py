from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="superreload",
        description="True hot reload for Python scripts and web frameworks",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run script subcommand
    run_parser = subparsers.add_parser(
        "run",
        help="Run a Python script with hot reloading",
        description="Run a Python script with automatic hot reloading on file changes",
    )
    run_parser.add_argument(
        "script",
        type=str,
        help="Python script to run",
    )
    run_parser.add_argument(
        "--watch",
        "-w",
        action="append",
        dest="watch_paths",
        metavar="PATH",
        help="Additional directories to watch (can be repeated)",
    )
    run_parser.add_argument(
        "--gitignore",
        action="store_true",
        help="Use .gitignore patterns to exclude files",
    )
    run_parser.add_argument(
        "--full-reload",
        action="store_true",
        help="Restart script on any change (instead of hot reloading modules)",
    )
    run_parser.add_argument(
        "--ignore",
        "-i",
        action="append",
        dest="ignore_patterns",
        metavar="PATTERN",
        help="Patterns to ignore (can be repeated)",
    )
    run_parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple mode (re-execute on change) instead of jurigged",
    )
    run_parser.add_argument(
        "script_args",
        nargs="*",
        metavar="ARGS",
        help="Arguments to pass to the script (use -- to separate)",
    )

    # Django subcommand (legacy)
    django_parser = subparsers.add_parser(
        "django",
        help="Run Django with hot reloading (use 'python manage.py superreload' instead)",
    )
    django_parser.add_argument(
        "--port",
        type=int,
        default=9877,
        help="WebSocket port for browser refresh (default: 9877)",
    )
    django_parser.add_argument(
        "args",
        nargs="*",
        help="Additional arguments to pass to Django",
    )

    # Version subcommand
    subparsers.add_parser("version", help="Show version")

    # Parse args, handling -- separator for script args
    args, remaining = parser.parse_known_args()

    if args.command == "version":
        from superreload import __version__

        print(f"superreload {__version__}")
        return 0

    if args.command == "run":
        # Merge remaining args (after --) with script_args
        script_args = (args.script_args or []) + remaining
        return run_script(args, script_args)

    if args.command == "django":
        return run_django(args)

    parser.print_help()
    return 0


def run_script(args: argparse.Namespace, script_args: list[str]) -> int:
    """Run a Python script with hot reloading."""
    from superreload.core.script_runner import ScriptRunner, ScriptRunnerConfig

    script_path = Path(args.script).resolve()
    if not script_path.exists():
        print(f"Error: Script not found: {args.script}")
        return 1

    if script_path.suffix != ".py":
        print(f"Error: Not a Python file: {args.script}")
        return 1

    # Build watch paths
    watch_paths: list[Path] = []
    if args.watch_paths:
        for p in args.watch_paths:
            path = Path(p).resolve()
            if path.exists():
                watch_paths.append(path)
            else:
                print(f"Warning: Watch path does not exist: {p}")

    # Build ignore patterns
    ignore_patterns: list[str] = []
    if args.ignore_patterns:
        ignore_patterns.extend(args.ignore_patterns)

    config = ScriptRunnerConfig(
        script_path=script_path,
        script_args=script_args,
        watch_paths=watch_paths,
        use_gitignore=args.gitignore,
        full_reload=args.full_reload,
        ignore_patterns=ignore_patterns,
        simple_mode=args.simple,
    )

    runner = ScriptRunner(config)

    try:
        return runner.run()
    except KeyboardInterrupt:
        print("\n[superreload] Shutting down...")
        runner.stop()
        return 0


def run_django(args: argparse.Namespace) -> int:
    """Run Django with hot reloading."""
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
