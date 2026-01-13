# ruff: noqa: UP006, UP035, UP045
# Using Optional/List instead of | union syntax for Python 3.9 compatibility.
# Typer uses get_type_hints() at runtime which evaluates annotations.
from __future__ import annotations

from pathlib import Path
from typing import Annotated, List, Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="superreload",
    help="True hot reload for Python scripts and web frameworks",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()
err_console = Console(stderr=True)


def _log(message: str) -> None:
    """Print styled superreload message."""
    console.print(f"[bold cyan]\\[superreload][/bold cyan] {message}")


def _error(message: str) -> None:
    """Print styled error message."""
    err_console.print(f"[bold red]\\[superreload][/bold red] {message}")


def _warning(message: str) -> None:
    """Print styled warning message."""
    console.print(f"[bold yellow]\\[superreload][/bold yellow] {message}")


def _version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        from superreload import __version__

        console.print(f"superreload [bold]{__version__}[/bold]")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    """True hot reload for Python scripts and web frameworks."""
    pass


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def run(
    ctx: typer.Context,
    script: Annotated[Path, typer.Argument(help="Python script to run")],
    watch: Annotated[
        Optional[List[Path]],
        typer.Option("--watch", "-w", help="Additional directories to watch (can be repeated)"),
    ] = None,
    gitignore: Annotated[
        bool,
        typer.Option("--gitignore", help="Use .gitignore patterns to exclude files"),
    ] = False,
    full_reload: Annotated[
        bool,
        typer.Option(
            "--full-reload", help="Restart script on any change (instead of hot reloading)"
        ),
    ] = False,
    ignore: Annotated[
        Optional[List[str]],
        typer.Option("--ignore", "-i", help="Patterns to ignore (can be repeated)"),
    ] = None,
    simple: Annotated[
        bool,
        typer.Option("--simple", help="Use simple mode (re-execute on change) instead of jurigged"),
    ] = False,
) -> None:
    """Run a Python script with hot reloading.

    Use -- to separate script arguments:

        superreload run script.py -- --port 8080 --debug
    """
    script_args = ctx.args
    _run_script_command(script, script_args, watch, gitignore, full_reload, ignore, simple)


@app.command(deprecated=True)
def django(
    port: Annotated[
        int,
        typer.Option("--port", help="WebSocket port for browser refresh"),
    ] = 9877,
) -> None:
    """Run Django with hot reloading.

    [bold yellow]DEPRECATED:[/bold yellow] Use 'python manage.py superreload' instead.
    """
    _run_django_command(port)


def _run_script_command(
    script: Path,
    script_args: list[str],
    watch: Optional[List[Path]],
    gitignore: bool,
    full_reload: bool,
    ignore: Optional[List[str]],
    simple: bool,
) -> None:
    """Run a Python script with hot reloading."""
    from superreload.core.script_runner import ScriptRunner, ScriptRunnerConfig

    script_path = script.resolve()
    if not script_path.exists():
        _error(f"Script not found: {script}")
        raise typer.Exit(code=1)

    if script_path.suffix != ".py":
        _error(f"Not a Python file: {script}")
        raise typer.Exit(code=1)

    # Build watch paths
    watch_paths: list[Path] = []
    if watch:
        for p in watch:
            path = p.resolve()
            if path.exists():
                watch_paths.append(path)
            else:
                _warning(f"Watch path does not exist: {p}")

    # Build ignore patterns
    ignore_patterns: list[str] = list(ignore) if ignore else []

    config = ScriptRunnerConfig(
        script_path=script_path,
        script_args=script_args,
        watch_paths=watch_paths,
        use_gitignore=gitignore,
        full_reload=full_reload,
        ignore_patterns=ignore_patterns,
        simple_mode=simple,
    )

    runner = ScriptRunner(config)

    try:
        exit_code = runner.run()
        raise typer.Exit(code=exit_code)
    except KeyboardInterrupt:
        _log("Shutting down...")
        runner.stop()
        raise typer.Exit(code=0) from None


def _run_django_command(port: int) -> None:
    """Run Django with hot reloading."""
    try:
        from superreload.frameworks.django import DjangoReloadServer
    except ImportError:
        _error("Django is not installed. Install with: pip install superreload[django]")
        raise typer.Exit(code=1) from None

    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        import django

        django.setup()
    except Exception as e:
        _error(f"Failed to setup Django: {e}")
        raise typer.Exit(code=1) from None

    server = DjangoReloadServer(websocket_port=port)
    _log(f"Starting superreload on ws://localhost:{port}")

    try:
        server.start(background=False)
    except KeyboardInterrupt:
        _log("Shutting down...")
        server.stop()

    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
