from __future__ import annotations

from pathlib import Path

from superreload.core.gitignore import GitignoreParser, collect_gitignore_patterns, load_gitignore


class TestGitignoreParser:
    def test_parse_simple_pattern(self) -> None:
        parser = GitignoreParser()
        parser.parse_string("*.pyc")

        assert len(parser.patterns) == 1
        assert parser.patterns[0][0] == "**/*.pyc"
        assert parser.patterns[0][1] is False

    def test_parse_directory_pattern(self) -> None:
        parser = GitignoreParser()
        parser.parse_string("__pycache__/")

        assert len(parser.patterns) == 1
        assert parser.patterns[0][0] == "**/__pycache__"

    def test_parse_negation_pattern(self) -> None:
        parser = GitignoreParser()
        parser.parse_string("*.log\n!important.log")

        assert len(parser.patterns) == 2
        assert parser.patterns[0][1] is False
        assert parser.patterns[1][1] is True

    def test_parse_comment_and_empty_lines(self) -> None:
        parser = GitignoreParser()
        parser.parse_string("# This is a comment\n\n*.pyc")

        assert len(parser.patterns) == 1

    def test_parse_anchored_pattern(self) -> None:
        parser = GitignoreParser()
        parser.parse_string("/build")

        assert len(parser.patterns) == 1
        assert parser.patterns[0][0] == "build"

    def test_is_ignored_simple(self) -> None:
        parser = GitignoreParser()
        parser.parse_string("*.pyc\n__pycache__/")

        assert parser.is_ignored("foo.pyc") is True
        assert parser.is_ignored("dir/bar.pyc") is True
        assert parser.is_ignored("foo.py") is False
        assert parser.is_ignored("__pycache__/foo.pyc") is True

    def test_is_ignored_negation(self) -> None:
        parser = GitignoreParser()
        parser.parse_string("*.log\n!important.log")

        assert parser.is_ignored("debug.log") is True
        assert parser.is_ignored("important.log") is False

    def test_is_ignored_with_base_path(self) -> None:
        parser = GitignoreParser()
        parser.parse_string("*.pyc")

        base = Path("/home/user/project")
        full_path = Path("/home/user/project/src/foo.pyc")

        assert parser.is_ignored(full_path, base_path=base) is True

    def test_get_ignore_patterns(self) -> None:
        parser = GitignoreParser()
        parser.parse_string("*.pyc\n!important.pyc\n__pycache__/")

        patterns = parser.get_ignore_patterns()
        assert len(patterns) == 2
        assert "**/*.pyc" in patterns
        assert "**/__pycache__" in patterns


class TestLoadGitignore:
    def test_load_gitignore_file(self, tmp_path: Path) -> None:
        gitignore_file = tmp_path / ".gitignore"
        gitignore_file.write_text("*.pyc\n__pycache__/\n.venv/")

        parser = load_gitignore(tmp_path)

        assert len(parser.patterns) == 3
        assert parser.is_ignored("foo.pyc") is True
        assert parser.is_ignored(".venv/lib/python") is True

    def test_load_gitignore_missing_file(self, tmp_path: Path) -> None:
        parser = load_gitignore(tmp_path)
        assert len(parser.patterns) == 0


class TestCollectGitignorePatterns:
    def test_collect_from_single_directory(self, tmp_path: Path) -> None:
        gitignore_file = tmp_path / ".gitignore"
        gitignore_file.write_text("*.pyc\n__pycache__/")

        patterns = collect_gitignore_patterns([tmp_path])

        assert len(patterns) == 2

    def test_collect_from_multiple_directories(self, tmp_path: Path) -> None:
        dir1 = tmp_path / "project1"
        dir1.mkdir()
        (dir1 / ".gitignore").write_text("*.pyc")

        dir2 = tmp_path / "project2"
        dir2.mkdir()
        (dir2 / ".gitignore").write_text("*.log")

        patterns = collect_gitignore_patterns([dir1, dir2])

        assert len(patterns) == 2
        assert "**/*.pyc" in patterns
        assert "**/*.log" in patterns

    def test_collect_deduplicates_patterns(self, tmp_path: Path) -> None:
        dir1 = tmp_path / "project1"
        dir1.mkdir()
        (dir1 / ".gitignore").write_text("*.pyc")

        dir2 = tmp_path / "project2"
        dir2.mkdir()
        (dir2 / ".gitignore").write_text("*.pyc")

        patterns = collect_gitignore_patterns([dir1, dir2])

        assert len(patterns) == 1

    def test_collect_handles_file_path(self, tmp_path: Path) -> None:
        (tmp_path / ".gitignore").write_text("*.pyc")
        script_file = tmp_path / "script.py"
        script_file.write_text("print('hello')")

        patterns = collect_gitignore_patterns([script_file])

        assert len(patterns) == 1
        assert "**/*.pyc" in patterns
