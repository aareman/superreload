from __future__ import annotations

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

from superreload.core.reloader import Reloader, ReloadResult


class TestReloadResult:
    def test_default_success(self) -> None:
        result = ReloadResult(success=True)
        assert result.success is True
        assert result.reloaded_modules == []
        assert result.failed_modules == []
        assert result.errors == []

    def test_with_modules(self) -> None:
        result = ReloadResult(
            success=True,
            reloaded_modules=["myapp.views", "myapp.models"],
        )
        assert len(result.reloaded_modules) == 2


class TestReloader:
    def test_path_to_module_name(self, tmp_path: Path) -> None:
        reloader = Reloader()

        test_file = tmp_path / "mymodule.py"
        test_file.write_text("x = 1")

        original_path = sys.path.copy()
        sys.path.insert(0, str(tmp_path))
        try:
            result = reloader.path_to_module_name(test_file)
            assert result == "mymodule"
        finally:
            sys.path = original_path

    def test_path_to_module_name_package(self, tmp_path: Path) -> None:
        reloader = Reloader()

        pkg_dir = tmp_path / "mypkg"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("")
        (pkg_dir / "views.py").write_text("def index(): pass")

        original_path = sys.path.copy()
        sys.path.insert(0, str(tmp_path))
        try:
            result = reloader.path_to_module_name(pkg_dir / "views.py")
            assert result == "mypkg.views"
        finally:
            sys.path = original_path

    def test_get_module_existing(self) -> None:
        reloader = Reloader()
        result = reloader.get_module("sys")
        assert result is sys

    def test_get_module_nonexistent(self) -> None:
        reloader = Reloader()
        result = reloader.get_module("nonexistent_module_12345")
        assert result is None

    def test_reload_callback(self) -> None:
        callback = MagicMock()
        reloader = Reloader(on_reload=callback)

        result = reloader.reload_modules([])
        assert result.success is True
        callback.assert_called_once()


class TestReloaderIntegration:
    def test_reload_simple_module(self, tmp_path: Path) -> None:
        reloader = Reloader()

        test_file = tmp_path / "test_reload_module.py"
        test_file.write_text("VALUE = 1")

        original_path = sys.path.copy()
        sys.path.insert(0, str(tmp_path))
        try:
            import test_reload_module

            assert test_reload_module.VALUE == 1

            test_file.write_text("VALUE = 2")

            result = reloader.reload_modules(["test_reload_module"])
            assert result.success is True
            assert "test_reload_module" in result.reloaded_modules

            assert test_reload_module.VALUE == 2
        finally:
            sys.path = original_path
            if "test_reload_module" in sys.modules:
                del sys.modules["test_reload_module"]


class TestReloaderLogging:
    def test_path_to_module_name_logs_resolution(self, tmp_path: Path, caplog: object) -> None:
        reloader = Reloader()

        test_file = tmp_path / "logged_module.py"
        test_file.write_text("x = 1")

        original_path = sys.path.copy()
        sys.path.insert(0, str(tmp_path))
        try:
            with caplog.at_level(logging.DEBUG, logger="superreload.core.reloader"):  # type: ignore[union-attr]
                result = reloader.path_to_module_name(test_file)
                assert result == "logged_module"
                assert "Resolved" in caplog.text  # type: ignore[union-attr]
                assert "logged_module" in caplog.text  # type: ignore[union-attr]
        finally:
            sys.path = original_path

    def test_reload_module_logs_activity(self, tmp_path: Path, caplog: object) -> None:
        reloader = Reloader()

        test_file = tmp_path / "test_log_reload.py"
        test_file.write_text("VALUE = 1")

        original_path = sys.path.copy()
        sys.path.insert(0, str(tmp_path))
        try:
            with caplog.at_level(logging.DEBUG, logger="superreload.core.reloader"):  # type: ignore[union-attr]
                reloader.reload_modules(["test_log_reload"])
                assert "Reloading module" in caplog.text  # type: ignore[union-attr]
                assert "test_log_reload" in caplog.text  # type: ignore[union-attr]
        finally:
            sys.path = original_path
            if "test_log_reload" in sys.modules:
                del sys.modules["test_log_reload"]

    def test_compute_reload_order_logs_dependents(self, caplog: object) -> None:
        reloader = Reloader()

        with caplog.at_level(logging.DEBUG, logger="superreload.core.reloader"):  # type: ignore[union-attr]
            reloader._compute_reload_order(["sys"])
            assert "Reload order" in caplog.text  # type: ignore[union-attr]
