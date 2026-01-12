from __future__ import annotations

from pathlib import Path

from superreload.core.script_runner import ScriptRunner, ScriptRunnerConfig


class TestScriptRunnerConfig:
    def test_default_config(self) -> None:
        config = ScriptRunnerConfig(script_path=Path("script.py"))

        assert config.script_path == Path("script.py")
        assert config.script_args == []
        assert config.watch_paths == []
        assert config.use_gitignore is False
        assert config.full_reload is False
        assert config.ignore_patterns == []
        assert config.simple_mode is False

    def test_config_with_options(self) -> None:
        config = ScriptRunnerConfig(
            script_path=Path("script.py"),
            script_args=["--port", "8080"],
            watch_paths=[Path("src"), Path("lib")],
            use_gitignore=True,
            full_reload=True,
            ignore_patterns=["*.tmp"],
        )

        assert config.script_args == ["--port", "8080"]
        assert len(config.watch_paths) == 2
        assert config.use_gitignore is True
        assert config.full_reload is True

    def test_config_simple_mode(self) -> None:
        config = ScriptRunnerConfig(
            script_path=Path("script.py"),
            simple_mode=True,
        )

        assert config.simple_mode is True


class TestScriptRunner:
    def test_get_watch_paths_includes_script_parent(self, tmp_path: Path) -> None:
        script = tmp_path / "script.py"
        script.write_text("print('hello')")

        config = ScriptRunnerConfig(script_path=script)
        runner = ScriptRunner(config)

        watch_paths = runner._get_watch_paths()

        assert tmp_path.resolve() in watch_paths

    def test_get_watch_paths_includes_additional_paths(self, tmp_path: Path) -> None:
        script = tmp_path / "script.py"
        script.write_text("print('hello')")

        src_dir = tmp_path / "src"
        src_dir.mkdir()

        config = ScriptRunnerConfig(
            script_path=script,
            watch_paths=[src_dir],
        )
        runner = ScriptRunner(config)

        watch_paths = runner._get_watch_paths()

        assert src_dir.resolve() in watch_paths

    def test_get_ignore_patterns_basic(self, tmp_path: Path) -> None:
        script = tmp_path / "script.py"
        script.write_text("print('hello')")

        config = ScriptRunnerConfig(
            script_path=script,
            ignore_patterns=["*.tmp", "*.log"],
        )
        runner = ScriptRunner(config)

        patterns = runner._get_ignore_patterns()

        assert "*.tmp" in patterns
        assert "*.log" in patterns

    def test_get_ignore_patterns_with_gitignore(self, tmp_path: Path) -> None:
        script = tmp_path / "script.py"
        script.write_text("print('hello')")

        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/")

        config = ScriptRunnerConfig(
            script_path=script,
            use_gitignore=True,
        )
        runner = ScriptRunner(config)

        patterns = runner._get_ignore_patterns()

        assert "**/*.pyc" in patterns
        assert "**/__pycache__" in patterns

    def test_is_main_script(self, tmp_path: Path) -> None:
        script = tmp_path / "main.py"
        script.write_text("print('hello')")

        other = tmp_path / "other.py"
        other.write_text("x = 1")

        config = ScriptRunnerConfig(script_path=script)
        runner = ScriptRunner(config)

        assert runner._is_main_script(script) is True
        assert runner._is_main_script(other) is False

    def test_is_main_script_resolves_paths(self, tmp_path: Path) -> None:
        script = tmp_path / "main.py"
        script.write_text("print('hello')")

        config = ScriptRunnerConfig(script_path=script)
        runner = ScriptRunner(config)

        relative_path = tmp_path / "." / "main.py"
        assert runner._is_main_script(relative_path) is True
