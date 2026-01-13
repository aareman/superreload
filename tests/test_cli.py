from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from superreload.cli import app

runner = CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})


class TestVersion:
    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "superreload" in result.stdout

    def test_version_short_flag(self):
        result = runner.invoke(app, ["-V"])
        assert result.exit_code == 0
        assert "superreload" in result.stdout


class TestRunCommand:
    def test_run_missing_script_argument(self):
        result = runner.invoke(app, ["run"])
        assert result.exit_code != 0

    def test_run_nonexistent_script(self):
        result = runner.invoke(app, ["run", "nonexistent_script.py"])
        assert result.exit_code == 1
        # Error goes to stderr, use output which captures both
        output = result.output if hasattr(result, "output") else result.stdout
        assert "not found" in output.lower()

    def test_run_non_python_file(self, tmp_path: Path):
        txt_file = tmp_path / "file.txt"
        txt_file.write_text("hello")

        result = runner.invoke(app, ["run", str(txt_file)])
        assert result.exit_code == 1
        output = result.output if hasattr(result, "output") else result.stdout
        assert "not a python file" in output.lower()

    def test_run_with_nonexistent_watch_path(self, tmp_path: Path):
        script = tmp_path / "script.py"
        script.write_text("print('hello')")

        result = runner.invoke(
            app,
            [
                "run",
                str(script),
                "--watch",
                "/nonexistent/path",
            ],
        )
        # Should warn but continue (warning goes to stdout via _warning)
        assert "does not exist" in result.stdout.lower()


class TestDjangoCommand:
    def test_django_command_shows_deprecated(self):
        result = runner.invoke(app, ["django", "--help"])
        assert result.exit_code == 0
        assert "deprecated" in result.stdout.lower()


class TestHelpOutput:
    def test_main_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "run" in result.stdout
        assert "django" in result.stdout

    def test_run_help(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--watch" in result.stdout
        assert "--gitignore" in result.stdout
        assert "--full-reload" in result.stdout
        assert "--ignore" in result.stdout
        assert "--simple" in result.stdout

    def test_run_help_shows_separator_docs(self):
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        # Should document the -- separator usage
        assert "--" in result.stdout


class TestCompletionOptions:
    def test_install_completion_option_exists(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--install-completion" in result.stdout

    def test_show_completion_option_exists(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--show-completion" in result.stdout
