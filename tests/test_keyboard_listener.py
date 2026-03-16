from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock, patch

from superreload.frameworks.django.management.commands.superreload import (
    _start_keyboard_listener,
)


class TestKeyboardListener:
    def test_keyboard_listener_skips_stdin_when_debugger_active(self) -> None:
        """
        When sys.gettrace() returns non-None (debugger active),
        verify that stdin is NOT read and trigger_reload is NOT called.
        The thread should skip the select.select call entirely.
        """
        reload_server = MagicMock()
        stdout = StringIO()

        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = True

        # Patch at module level where the function uses them
        with (
            patch(
                "superreload.frameworks.django.management.commands.superreload.sys.gettrace"
            ) as mock_gettrace,
            patch(
                "superreload.frameworks.django.management.commands.superreload.select.select"
            ) as mock_select,
            patch(
                "superreload.frameworks.django.management.commands.superreload.sys.stdin",
                mock_stdin,
            ),
        ):
            # Return a debugger object on first call, then None to break loop
            mock_gettrace.side_effect = [MagicMock(), None]
            mock_select.return_value = ([], [], [])

            _start_keyboard_listener(reload_server, stdout)

            # Verify stdin.read was NOT called (skipped due to debugger)
            mock_stdin.read.assert_not_called()
            # Verify reload was NOT triggered
            reload_server.trigger_reload.assert_not_called()

    def test_keyboard_listener_triggers_reload_without_debugger(self) -> None:
        """
        When sys.gettrace() returns None (no debugger),
        and stdin provides 'r', verify that trigger_reload IS called.
        """
        reload_server = MagicMock()
        stdout = StringIO()

        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = True
        mock_stdin.read.return_value = "r"

        with (
            patch(
                "superreload.frameworks.django.management.commands.superreload.sys.gettrace"
            ) as mock_gettrace,
            patch(
                "superreload.frameworks.django.management.commands.superreload.select.select"
            ) as mock_select,
            patch(
                "superreload.frameworks.django.management.commands.superreload.sys.stdin",
                mock_stdin,
            ),
        ):
            # No debugger
            mock_gettrace.return_value = None
            # First call: stdin is readable, second call breaks loop
            mock_select.side_effect = [([mock_stdin], [], []), ([], [], [])]

            _start_keyboard_listener(reload_server, stdout)

            # Verify stdin.read was called
            mock_stdin.read.assert_called()
            # Verify reload was triggered
            reload_server.trigger_reload.assert_called()

    def test_keyboard_listener_exits_on_non_tty(self) -> None:
        """
        When isatty() returns False (not a TTY),
        verify that the listener returns early without attempting stdin reads.
        """
        reload_server = MagicMock()
        stdout = StringIO()

        mock_stdin = MagicMock()
        mock_stdin.isatty.return_value = False

        with patch(
            "superreload.frameworks.django.management.commands.superreload.sys.stdin",
            mock_stdin,
        ):
            _start_keyboard_listener(reload_server, stdout)

            # Verify isatty was called
            mock_stdin.isatty.assert_called()
            # Verify no stdin reads attempted
            mock_stdin.read.assert_not_called()
            # Verify no reload triggered
            reload_server.trigger_reload.assert_not_called()
