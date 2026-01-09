from __future__ import annotations

from pathlib import Path

from superreload.core.watcher import FileChange, FileWatcher, FileWatcherConfig


class TestFileWatcherConfig:
    def test_default_config(self) -> None:
        config = FileWatcherConfig()
        assert config.paths == []
        assert config.patterns == ["*.py"]
        assert "__pycache__" in config.ignore_patterns
        assert config.debounce_ms == 100

    def test_custom_config(self) -> None:
        config = FileWatcherConfig(
            paths=[Path("/tmp")],
            patterns=["*.py", "*.html"],
            debounce_ms=200,
        )
        assert len(config.paths) == 1
        assert "*.html" in config.patterns
        assert config.debounce_ms == 200


class TestFileChange:
    def test_file_change(self) -> None:
        change = FileChange(path=Path("/test/file.py"), change_type="modified")
        assert change.path == Path("/test/file.py")
        assert change.change_type == "modified"


class TestFileWatcher:
    def test_should_include_py_file(self) -> None:
        watcher = FileWatcher(FileWatcherConfig(patterns=["*.py"]))
        assert watcher._should_include(Path("/app/views.py")) is True

    def test_should_exclude_pycache(self) -> None:
        watcher = FileWatcher(FileWatcherConfig(patterns=["*.py"]))
        assert watcher._should_include(Path("/app/__pycache__/views.cpython-312.pyc")) is False

    def test_should_exclude_pyc(self) -> None:
        watcher = FileWatcher(FileWatcherConfig(patterns=["*.py"]))
        assert watcher._should_include(Path("/app/views.pyc")) is False

    def test_should_exclude_git(self) -> None:
        watcher = FileWatcher(FileWatcherConfig(patterns=["*.py"]))
        assert watcher._should_include(Path("/app/.git/config")) is False

    def test_should_exclude_venv(self) -> None:
        watcher = FileWatcher(FileWatcherConfig(patterns=["*.py"]))
        assert watcher._should_include(Path("/app/.venv/lib/site.py")) is False

    def test_should_include_html_when_configured(self) -> None:
        watcher = FileWatcher(FileWatcherConfig(patterns=["*.py", "*.html"]))
        assert watcher._should_include(Path("/app/templates/index.html")) is True

    def test_stop(self) -> None:
        watcher = FileWatcher()
        watcher.stop()
        assert watcher._running is False
