from __future__ import annotations

import ast
import os
import sys
import threading
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from superreload.core.gitignore import collect_gitignore_patterns
from superreload.core.watcher import FileChange, FileWatcher, FileWatcherConfig

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class ScriptRunnerConfig:
    script_path: Path
    script_args: list[str] = field(default_factory=list)
    watch_paths: list[Path] = field(default_factory=list)
    use_gitignore: bool = False
    full_reload: bool = False
    ignore_patterns: list[str] = field(default_factory=list)
    simple_mode: bool = False  # Use reloading-style instead of jurigged


class ScriptRunner:
    """Run a Python script with hot reloading.

    Default mode: Uses jurigged for surgical code object patching.
    Simple mode (--simple): Re-parses and re-executes on file changes.
    """

    def __init__(
        self,
        config: ScriptRunnerConfig,
        on_reload: Callable[[], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self.config = config
        self.on_reload = on_reload
        self.on_error = on_error
        self._running = False
        self._reload_event = threading.Event()
        self._lock = threading.Lock()

    def _get_watch_paths(self) -> list[Path]:
        paths = [self.config.script_path.parent]
        paths.extend(self.config.watch_paths)
        return [p.resolve() for p in paths]

    def _get_ignore_patterns(self) -> list[str]:
        patterns = list(self.config.ignore_patterns)
        if self.config.use_gitignore:
            watch_paths = self._get_watch_paths()
            gitignore_patterns = collect_gitignore_patterns(watch_paths)
            patterns.extend(gitignore_patterns)
        return patterns

    def _is_main_script(self, path: Path) -> bool:
        return path.resolve() == self.config.script_path.resolve()

    def run(self) -> int:
        """Run the script with hot reloading."""
        if self.config.full_reload:
            return self._run_with_restart()
        if self.config.simple_mode:
            return self._run_simple_mode()
        return self._run_with_jurigged()

    def _run_with_jurigged(self) -> int:
        """Use jurigged for surgical code object patching (default)."""
        import jurigged

        self._running = True
        watch_paths = self._get_watch_paths()

        print(f"[superreload] Starting {self.config.script_path.name}")
        print(f"[superreload] Watching: {', '.join(str(p) for p in watch_paths)}")
        print("[superreload] Mode: jurigged (surgical patching)")
        print()

        # Configure jurigged to watch our paths
        for path in watch_paths:
            jurigged.watch(str(path))

        # Setup sys.path and argv
        script_dir = str(self.config.script_path.parent)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        original_argv = sys.argv.copy()
        sys.argv = [str(self.config.script_path)] + self.config.script_args

        try:
            main_globals: dict[str, Any] = {
                "__name__": "__main__",
                "__file__": str(self.config.script_path),
                "__builtins__": __builtins__,
            }

            with open(self.config.script_path) as f:
                source = f.read()
            code = compile(source, str(self.config.script_path), "exec")
            exec(code, main_globals)

            return 0
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 0
        except KeyboardInterrupt:
            print("\n[superreload] Interrupted")
            return 0
        except Exception as e:
            print(f"\n[superreload] Script error: {e}")
            traceback.print_exc()
            return 1
        finally:
            self._running = False
            sys.argv = original_argv

    def _run_simple_mode(self) -> int:
        """Simple mode: re-execute entire script on changes (reloading-style)."""
        self._running = True
        watch_paths = self._get_watch_paths()

        print(f"[superreload] Starting {self.config.script_path.name}")
        print(f"[superreload] Watching: {', '.join(str(p) for p in watch_paths)}")
        print("[superreload] Mode: simple (re-execute on change)")
        print()

        # Start watcher thread
        watcher_thread = threading.Thread(target=self._run_watcher_thread, daemon=True)
        watcher_thread.start()

        # Setup sys.path and argv
        script_dir = str(self.config.script_path.parent)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        original_argv = sys.argv.copy()
        sys.argv = [str(self.config.script_path)] + self.config.script_args

        try:
            while self._running:
                self._reload_event.clear()

                main_globals: dict[str, Any] = {
                    "__name__": "__main__",
                    "__file__": str(self.config.script_path),
                    "__builtins__": __builtins__,
                    "_superreload_check": self._check_reload,
                }

                try:
                    with open(self.config.script_path) as f:
                        source = f.read()
                    code = compile(source, str(self.config.script_path), "exec")
                    exec(code, main_globals)
                    # Script finished normally
                    break
                except _ReloadSignal:
                    print("[superreload] Reloading...")
                    continue
                except SyntaxError as e:
                    print(f"[superreload] Syntax error: {e}")
                    print("[superreload] Waiting for fix...")
                    self._reload_event.wait()
                    continue

            return 0
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 0
        except KeyboardInterrupt:
            print("\n[superreload] Interrupted")
            return 0
        except Exception as e:
            print(f"\n[superreload] Script error: {e}")
            traceback.print_exc()
            return 1
        finally:
            self._running = False
            sys.argv = original_argv

    def _run_with_restart(self) -> int:
        """Full reload mode: restart process on any change."""
        self._running = True
        watch_paths = self._get_watch_paths()

        print(f"[superreload] Starting {self.config.script_path.name}")
        print(f"[superreload] Watching: {', '.join(str(p) for p in watch_paths)}")
        print("[superreload] Mode: full restart")
        print()

        # Start watcher that triggers restart
        watcher_thread = threading.Thread(target=self._run_watcher_thread_restart, daemon=True)
        watcher_thread.start()

        # Setup and run
        script_dir = str(self.config.script_path.parent)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        original_argv = sys.argv.copy()
        sys.argv = [str(self.config.script_path)] + self.config.script_args

        try:
            main_globals: dict[str, Any] = {
                "__name__": "__main__",
                "__file__": str(self.config.script_path),
                "__builtins__": __builtins__,
            }

            with open(self.config.script_path) as f:
                source = f.read()
            code = compile(source, str(self.config.script_path), "exec")
            exec(code, main_globals)

            return 0
        except SystemExit as e:
            return e.code if isinstance(e.code, int) else 0
        except KeyboardInterrupt:
            print("\n[superreload] Interrupted")
            return 0
        except Exception as e:
            print(f"\n[superreload] Script error: {e}")
            traceback.print_exc()
            return 1
        finally:
            self._running = False
            sys.argv = original_argv

    def _check_reload(self) -> None:
        """Check if reload is pending and raise signal if so.

        Scripts can call this in their loops to enable hot reload:
            while True:
                _superreload_check()  # Check for file changes
                do_work()
        """
        if self._reload_event.is_set():
            raise _ReloadSignal()

    def _handle_changes(self, changes: list[FileChange]) -> None:
        if not changes:
            return

        py_changes = [c for c in changes if c.path.suffix == ".py"]
        if not py_changes:
            return

        changed_names = ", ".join(c.path.name for c in py_changes)
        print(f"\n[superreload] Changed: {changed_names}")
        self._reload_event.set()

    def _run_watcher_thread(self) -> None:
        import asyncio

        async def watch_loop() -> None:
            watch_paths = self._get_watch_paths()
            ignore_patterns = self._get_ignore_patterns()

            watcher_config = FileWatcherConfig(
                paths=watch_paths,
                patterns=["*.py"],
                ignore_patterns=ignore_patterns,
            )
            watcher = FileWatcher(watcher_config)

            try:
                async for changes in watcher.watch():
                    if not self._running:
                        break
                    self._handle_changes(changes)
            except Exception as e:
                print(f"[superreload] Watcher error: {e}")
            finally:
                watcher.stop()

        asyncio.run(watch_loop())

    def _run_watcher_thread_restart(self) -> None:
        """Watcher that triggers full process restart."""
        import asyncio

        async def watch_loop() -> None:
            watch_paths = self._get_watch_paths()
            ignore_patterns = self._get_ignore_patterns()

            watcher_config = FileWatcherConfig(
                paths=watch_paths,
                patterns=["*.py"],
                ignore_patterns=ignore_patterns,
            )
            watcher = FileWatcher(watcher_config)

            try:
                async for changes in watcher.watch():
                    if not self._running:
                        break
                    py_changes = [c for c in changes if c.path.suffix == ".py"]
                    if py_changes:
                        changed_names = ", ".join(c.path.name for c in py_changes)
                        print(f"\n[superreload] Changed: {changed_names}, restarting...")
                        os.execv(sys.executable, [sys.executable] + sys.argv)
            except Exception as e:
                print(f"[superreload] Watcher error: {e}")
            finally:
                watcher.stop()

        asyncio.run(watch_loop())

    def stop(self) -> None:
        self._running = False


class _ReloadSignal(Exception):
    """Internal signal to trigger reload in simple mode."""

    pass


# --- Reloading-style iterator wrapper (for explicit use in scripts) ---


def reloading(
    iterable: Any = None,
    *,
    forever: bool = False,
    every: int = 1,
) -> Iterator[Any]:
    """Wrap an iterator to enable hot reloading of the loop body.

    This is a reloading-style wrapper that re-parses and re-compiles
    the loop body when the source file changes.

    Usage:
        from superreload import reloading

        for i in reloading(range(100)):
            # This loop body reloads from source on each iteration
            process(i)

        for _ in reloading(forever=True):
            # Infinite loop with hot reload
            serve_request()

    Args:
        iterable: Any iterable to wrap
        forever: If True, loop forever (yields 0, 1, 2, ...)
        every: Check for reload every N iterations (default: 1)
    """
    import inspect

    # Get caller's frame info
    frame_info = inspect.stack()[1]
    caller_frame = frame_info.frame
    caller_globals = caller_frame.f_globals
    caller_locals = caller_frame.f_locals
    caller_filename = frame_info.filename
    caller_lineno = frame_info.lineno

    # Create iterator
    if forever:
        iter_seq: Iterator[Any] = _forever_iterator()
    elif iterable is not None:
        iter_seq = iter(iterable)
    else:
        raise ValueError("reloading() requires an iterable or forever=True")

    loop_id: str | None = None
    compiled_body: Any = None
    last_mtime: float = 0

    for i, value in enumerate(iter_seq):
        # Check for reload every Nth iteration
        if i % every == 0:
            try:
                current_mtime = os.path.getmtime(caller_filename)
                if current_mtime != last_mtime or compiled_body is None:
                    new_body, new_loop_id = _get_loop_code(caller_filename, caller_lineno, loop_id)
                    if new_body is not None:
                        compiled_body = new_body
                        loop_id = new_loop_id
                        last_mtime = current_mtime
                        if i > 0:
                            print(
                                f"[superreload] Reloaded loop at {caller_filename}:{caller_lineno}"
                            )
            except Exception as e:
                print(f"[superreload] Reload error: {e}")

        # Yield value, then execute compiled body in caller's namespace
        yield value

        if compiled_body is not None:
            try:
                exec(compiled_body, caller_globals, caller_locals)
            except Exception as e:
                print(f"[superreload] Execution error: {e}")
                traceback.print_exc()


def _forever_iterator() -> Iterator[int]:
    """Infinite iterator yielding 0, 1, 2, ..."""
    i = 0
    while True:
        yield i
        i += 1


def _get_loop_code(
    filename: str, lineno: int, loop_id: str | None
) -> tuple[Any | None, str | None]:
    """Parse file and extract the for-loop body at the given line."""
    try:
        with open(filename) as f:
            source = f.read()

        tree = ast.parse(source, filename)

        # Find the for loop with reloading() call near the given line
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.For)
                and hasattr(node, "lineno")
                and isinstance(node.iter, ast.Call)
            ):
                func = node.iter.func
                if (
                    isinstance(func, ast.Name)
                    and func.id == "reloading"
                    and abs(node.lineno - lineno) <= 2
                ):
                    # Extract body and compile
                    body_module = ast.Module(body=node.body, type_ignores=[])
                    ast.fix_missing_locations(body_module)
                    compiled = compile(body_module, filename, "exec")
                    new_loop_id = f"{filename}:{node.lineno}"
                    return compiled, new_loop_id

        return None, loop_id
    except SyntaxError as e:
        print(f"[superreload] Syntax error: {e}")
        return None, loop_id
    except Exception as e:
        print(f"[superreload] Parse error: {e}")
        return None, loop_id
