from __future__ import annotations

import time
from io import StringIO
from unittest.mock import MagicMock, patch

from superreload.frameworks.django.management.commands.superreload import (
    _start_keyboard_listener,
)


class TestKeyboardListener:
    def test_keyboard_listener_skips_stdin_when_paused(self) -> None:
        """When reload_server.paused is True, stdin is NOT read."""
        reload_server = MagicMock()
        stdout = StringIO()

        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = True
        mock_stdin.fileno.return_value = 0  # stdin fd
        with (
            patch(
                "superreload.frameworks.django.management.commands.superreload.sys.stdin",
                mock_stdin,
            ),
            patch(
                "superreload.frameworks.django.management.commands.superreload.select.select",
                return_value=([], [], []),  # No stdin readable
            ),
        ):
            # paused returns True always — thread loops sleeping, never reads stdin
            type(reload_server).paused = property(lambda _self: True)

            _start_keyboard_listener(reload_server, stdout)

            # Give the daemon thread time to iterate
            time.sleep(1.0)

            # Verify readline was NOT called (skipped due to paused)
            mock_stdin.readline.assert_not_called()
            reload_server.trigger_reload.assert_not_called()

    def test_keyboard_listener_triggers_reload_when_not_paused(self) -> None:
        """When not paused and stdin provides 'r', trigger_reload IS called."""
        reload_server = MagicMock()
        stdout = StringIO()

        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = True
        mock_stdin.fileno.return_value = 0  # stdin fd
        # First readline returns 'r\n', second returns '' (EOF) to exit loop
        mock_stdin.readline.side_effect = ["r\n", ""]

        with (
            patch(
                "superreload.frameworks.django.management.commands.superreload.sys.stdin",
                mock_stdin,
            ),
            patch(
                "superreload.frameworks.django.management.commands.superreload.select.select",
                return_value=([mock_stdin], [], []),  # stdin always readable
            ),
        ):
            type(reload_server).paused = property(lambda _self: False)

            _start_keyboard_listener(reload_server, stdout)

            # Give the daemon thread time to process
            time.sleep(1.0)

            mock_stdin.readline.assert_called()
            reload_server.trigger_reload.assert_called()

    def test_keyboard_listener_exits_on_non_tty(self) -> None:
        """When isatty() returns False, listener returns early."""
        reload_server = MagicMock()
        stdout = StringIO()

        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = False

        with patch(
            "superreload.frameworks.django.management.commands.superreload.sys.stdin",
            mock_stdin,
        ):
            _start_keyboard_listener(reload_server, stdout)

            # Give the daemon thread time to start
            time.sleep(0.5)

            mock_stdin.isatty.assert_called()
            mock_stdin.readline.assert_not_called()
            reload_server.trigger_reload.assert_not_called()
