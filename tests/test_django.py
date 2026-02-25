from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from superreload.core.framework import ReloadContext
from superreload.core.reloader import ReloadResult
from superreload.frameworks.django.framework import DjangoFramework
from superreload.frameworks.django.middleware import (
    SUPERRELOAD_JS,
    SuperReloadMiddleware,
    _get_superreload_config,
)


class TestDjangoFramework:
    def test_name(self) -> None:
        framework = DjangoFramework()
        assert framework.name == "django"

    def test_can_reload_normal_file(self) -> None:
        framework = DjangoFramework()
        ctx = ReloadContext(changed_files=[Path("/app/views.py")])
        assert framework.can_reload(ctx) is True

    def test_can_reload_blocks_migrations(self) -> None:
        framework = DjangoFramework()
        ctx = ReloadContext(changed_files=[Path("/app/migrations/0001_initial.py")])
        assert framework.can_reload(ctx) is False

    def test_can_reload_blocks_settings(self) -> None:
        framework = DjangoFramework()
        ctx = ReloadContext(changed_files=[Path("/app/settings.py")])
        assert framework.can_reload(ctx) is False

    def test_can_reload_blocks_settings_dir(self) -> None:
        framework = DjangoFramework()
        ctx = ReloadContext(changed_files=[Path("/app/settings/production.py")])
        assert framework.can_reload(ctx) is False

    def test_can_reload_allows_html(self) -> None:
        framework = DjangoFramework()
        ctx = ReloadContext(changed_files=[Path("/app/templates/base.html")])
        assert framework.can_reload(ctx) is True

    def test_get_watch_patterns(self) -> None:
        framework = DjangoFramework()
        patterns = framework.get_watch_patterns()
        assert "*.py" in patterns
        assert "*.html" in patterns
        assert "*.css" in patterns
        assert "*.js" in patterns

    def test_get_ignore_patterns(self) -> None:
        framework = DjangoFramework()
        patterns = framework.get_ignore_patterns()
        assert "*/migrations/*" in patterns
        assert "staticfiles" in patterns
        assert "__pycache__" in patterns

    def test_after_reload_clears_caches_on_success(self) -> None:
        framework = DjangoFramework()
        framework._clear_url_caches = MagicMock()  # type: ignore[method-assign]
        framework._clear_template_caches = MagicMock()  # type: ignore[method-assign]

        ctx = ReloadContext(changed_files=[])
        result = ReloadResult(success=True)
        framework.after_reload(ctx, result)

        framework._clear_url_caches.assert_called_once()
        framework._clear_template_caches.assert_called_once()

    def test_after_reload_skips_caches_on_failure(self) -> None:
        framework = DjangoFramework()
        framework._clear_url_caches = MagicMock()  # type: ignore[method-assign]
        framework._clear_template_caches = MagicMock()  # type: ignore[method-assign]

        ctx = ReloadContext(changed_files=[])
        result = ReloadResult(success=False)
        framework.after_reload(ctx, result)

        framework._clear_url_caches.assert_not_called()
        framework._clear_template_caches.assert_not_called()


class TestSuperReloadMiddleware:
    def test_injects_script_into_html(self) -> None:
        get_response = MagicMock()
        response = MagicMock()
        response.get.return_value = "text/html; charset=utf-8"
        response.content = b"<html><body></body></html>"
        response.__contains__ = lambda _, key: key == "Content-Type"
        response.__getitem__ = lambda _, key: "text/html" if key == "Content-Type" else None
        get_response.return_value = response

        request = MagicMock()
        request.headers = {}

        middleware = SuperReloadMiddleware(get_response)
        result = middleware(request)

        assert b"superreload" in result.content
        assert b"WebSocket" in result.content

    def test_skips_non_html_response(self) -> None:
        get_response = MagicMock()
        response = MagicMock()
        response.get.return_value = "application/json"
        response.content = b'{"key": "value"}'
        get_response.return_value = response

        request = MagicMock()
        request.headers = {}

        middleware = SuperReloadMiddleware(get_response)
        result = middleware(request)

        assert result.content == b'{"key": "value"}'

    def test_skips_ajax_requests(self) -> None:
        get_response = MagicMock()
        response = MagicMock()
        response.get.return_value = "text/html"
        response.content = b"<html><body></body></html>"
        get_response.return_value = response

        request = MagicMock()
        request.headers = {"X-Requested-With": "XMLHttpRequest"}

        middleware = SuperReloadMiddleware(get_response)
        result = middleware(request)

        assert b"superreload" not in result.content

    def test_js_contains_websocket_connection(self) -> None:
        assert "WebSocket" in SUPERRELOAD_JS
        assert "__SUPERRELOAD_PORT__" in SUPERRELOAD_JS
        assert "__SUPERRELOAD_PATH__" in SUPERRELOAD_JS

    def test_js_contains_error_overlay(self) -> None:
        assert "superreload-overlay" in SUPERRELOAD_JS
        assert "createOverlay" in SUPERRELOAD_JS

    def test_js_contains_css_hot_reload(self) -> None:
        assert "reloadCSS" in SUPERRELOAD_JS
        assert "css_reload" in SUPERRELOAD_JS

    def test_js_contains_keyboard_shortcuts(self) -> None:
        assert "Escape" in SUPERRELOAD_JS
        assert "force_reload" in SUPERRELOAD_JS

    def test_get_superreload_config_proxied_omits_port(self) -> None:
        class MockSettings:
            SUPERRELOAD_PROXIED = True

        with patch("django.conf.settings", MockSettings()):
            port, path, host, secure = _get_superreload_config()

        assert port is None

    def test_get_superreload_config_not_proxied_uses_ws_port(self) -> None:
        class MockSettings:
            SUPERRELOAD_WS_PORT = 9999

        with patch("django.conf.settings", MockSettings()):
            port, path, host, secure = _get_superreload_config()

        assert port == 9999

    def test_get_superreload_config_defaults(self) -> None:
        class MockSettings:
            pass

        with patch("django.conf.settings", MockSettings()):
            port, path, host, secure = _get_superreload_config()

        assert port == 9877
        assert path == "/superreload"
        assert host == "localhost"
        assert secure is False


class TestDjangoReloadServer:
    @pytest.mark.asyncio
    async def test_trigger_reload(self) -> None:
        with (
            patch(
                "superreload.frameworks.django.reload_server.DjangoFramework"
            ) as mock_framework_cls,
            patch("superreload.frameworks.django.reload_server.FileWatcher"),
            patch("superreload.frameworks.django.reload_server.WebSocketServer") as mock_ws_cls,
        ):
            mock_framework = MagicMock()
            mock_framework.get_watch_paths.return_value = [Path("/app")]
            mock_framework.get_watch_patterns.return_value = ["*.py"]
            mock_framework.get_ignore_patterns.return_value = []
            mock_framework_cls.return_value = mock_framework

            mock_ws = MagicMock()
            mock_ws.notify_reload = AsyncMock()
            mock_ws_cls.return_value = mock_ws

            from superreload.frameworks.django.reload_server import DjangoReloadServer

            server = DjangoReloadServer()
            assert server.websocket is mock_ws

    @pytest.mark.asyncio
    async def test_file_change_handling(self) -> None:
        with (
            patch(
                "superreload.frameworks.django.reload_server.DjangoFramework"
            ) as mock_framework_cls,
            patch("superreload.frameworks.django.reload_server.FileWatcher"),
            patch("superreload.frameworks.django.reload_server.WebSocketServer") as mock_ws_cls,
            patch("superreload.frameworks.django.reload_server.Reloader") as mock_reloader_cls,
        ):
            mock_framework = MagicMock()
            mock_framework.get_watch_paths.return_value = [Path("/app")]
            mock_framework.get_watch_patterns.return_value = ["*.py"]
            mock_framework.get_ignore_patterns.return_value = []
            mock_framework.can_reload.return_value = True
            mock_framework_cls.return_value = mock_framework

            mock_ws = MagicMock()
            mock_ws.notify_reload = AsyncMock()
            mock_ws.notify_css_reload = AsyncMock()
            mock_ws_cls.return_value = mock_ws

            mock_reloader = MagicMock()
            mock_reloader.reload_from_paths = AsyncMock(
                return_value=ReloadResult(success=True, reloaded_modules=["app.views"])
            )
            mock_reloader_cls.return_value = mock_reloader

            from superreload.core.watcher import FileChange
            from superreload.frameworks.django.reload_server import DjangoReloadServer

            server = DjangoReloadServer()

            changes = [FileChange(path=Path("/app/views.py"), change_type="modified")]
            await server._handle_file_changes(changes)

            mock_reloader.reload_from_paths.assert_called_once()
            mock_ws.notify_reload.assert_called_once()


class TestWebSocketForceReload:
    @pytest.mark.asyncio
    async def test_force_reload_message_handling(self) -> None:
        from superreload.core.websocket import WebSocketMessage

        msg = WebSocketMessage.from_json('{"type": "force_reload"}')
        assert msg.type == "force_reload"

    def test_websocket_message_parsing(self) -> None:
        from superreload.core.websocket import WebSocketMessage

        msg = WebSocketMessage(type="reload", data={"files": ["app.py"]})
        json_str = msg.to_json()
        parsed = WebSocketMessage.from_json(json_str)

        assert parsed.type == "reload"
        assert parsed.data["files"] == ["app.py"]


class TestDjangoReloadServerVerbosity:
    def test_default_verbosity(self) -> None:
        with (
            patch(
                "superreload.frameworks.django.reload_server.DjangoFramework"
            ) as mock_framework_cls,
            patch("superreload.frameworks.django.reload_server.FileWatcher"),
            patch("superreload.frameworks.django.reload_server.WebSocketServer"),
        ):
            mock_framework = MagicMock()
            mock_framework.get_watch_paths.return_value = [Path("/app")]
            mock_framework.get_watch_patterns.return_value = ["*.py"]
            mock_framework.get_ignore_patterns.return_value = []
            mock_framework_cls.return_value = mock_framework

            from superreload.frameworks.django.reload_server import DjangoReloadServer

            server = DjangoReloadServer()
            assert server.verbosity == 1

    def test_custom_verbosity(self) -> None:
        with (
            patch(
                "superreload.frameworks.django.reload_server.DjangoFramework"
            ) as mock_framework_cls,
            patch("superreload.frameworks.django.reload_server.FileWatcher"),
            patch("superreload.frameworks.django.reload_server.WebSocketServer"),
        ):
            mock_framework = MagicMock()
            mock_framework.get_watch_paths.return_value = [Path("/app")]
            mock_framework.get_watch_patterns.return_value = ["*.py"]
            mock_framework.get_ignore_patterns.return_value = []
            mock_framework_cls.return_value = mock_framework

            from superreload.frameworks.django.reload_server import DjangoReloadServer

            server = DjangoReloadServer(verbosity=3)
            assert server.verbosity == 3


class TestSuperReloadCommandArguments:
    def test_command_has_debug_argument(self) -> None:
        from superreload.frameworks.django.management.commands.superreload import Command

        command = Command()
        parser = MagicMock()
        parser.add_argument = MagicMock()

        command.add_arguments(parser)

        call_args_list = [call[0] for call in parser.add_argument.call_args_list]
        debug_calls = [args for args in call_args_list if "--debug" in args]
        assert len(debug_calls) == 1

    def test_verbosity_constants_defined(self) -> None:
        from superreload.frameworks.django.management.commands.superreload import (
            DJANGO_VERBOSITY_DEBUG,
            DJANGO_VERBOSITY_MINIMAL,
            DJANGO_VERBOSITY_NORMAL,
            DJANGO_VERBOSITY_VERBOSE,
        )

        assert DJANGO_VERBOSITY_MINIMAL == 0
        assert DJANGO_VERBOSITY_NORMAL == 1
        assert DJANGO_VERBOSITY_VERBOSE == 2
        assert DJANGO_VERBOSITY_DEBUG == 3
