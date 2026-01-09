from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from watchfiles import Change

try:
    from watchfiles import Change, awatch

    HAS_WATCHFILES = True
except ImportError:
    HAS_WATCHFILES = False

    async def awatch(  # type: ignore[misc]
        *_args: Any, **_kwargs: Any
    ) -> AsyncIterator[set[tuple[Any, str]]]:
        raise ImportError("watchfiles is required for file watching")
        yield set()


@dataclass
class FileChange:
    path: Path
    change_type: str


@dataclass
class FileWatcherConfig:
    paths: list[Path] = field(default_factory=list)
    patterns: list[str] = field(default_factory=lambda: ["*.py"])
    ignore_patterns: list[str] = field(
        default_factory=lambda: [
            "__pycache__",
            "*.pyc",
            ".git",
            ".venv",
            "venv",
            "node_modules",
        ]
    )
    debounce_ms: int = 100


class FileWatcher:
    def __init__(self, config: FileWatcherConfig | None = None) -> None:
        self.config = config or FileWatcherConfig()
        self._running = False
        self._task: asyncio.Task[None] | None = None

    def _should_include(self, path: Path) -> bool:
        path_str = str(path)

        for ignore in self.config.ignore_patterns:
            if ignore.startswith("*"):
                if path_str.endswith(ignore[1:]):
                    return False
            elif ignore in path_str:
                return False

        if not self.config.patterns:
            return True

        for pattern in self.config.patterns:
            if pattern.startswith("*"):
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern in path_str:
                return True

        return False

    def _change_type_to_str(self, change: int) -> str:
        if not HAS_WATCHFILES:
            return "unknown"
        if change == Change.added:
            return "added"
        elif change == Change.modified:
            return "modified"
        elif change == Change.deleted:
            return "deleted"
        return "unknown"

    async def watch(
        self,
        callback: Callable[[list[FileChange]], None] | None = None,
    ) -> AsyncIterator[list[FileChange]]:
        if not HAS_WATCHFILES:
            raise ImportError("watchfiles is required. Install with: pip install superreload[dev]")

        if not self.config.paths:
            return

        watch_paths = [str(p) for p in self.config.paths if p.exists()]
        if not watch_paths:
            return

        self._running = True

        async for changes in awatch(
            *watch_paths,
            debounce=self.config.debounce_ms,
            step=50,
        ):
            if not self._running:
                break

            file_changes: list[FileChange] = []
            for change_type, path_str in changes:
                path = Path(path_str)
                if self._should_include(path):
                    file_changes.append(
                        FileChange(
                            path=path,
                            change_type=self._change_type_to_str(change_type),
                        )
                    )

            if file_changes:
                if callback:
                    callback(file_changes)
                yield file_changes

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()

    async def start(self, callback: Callable[[list[FileChange]], None]) -> None:
        async for _changes in self.watch(callback):
            pass
