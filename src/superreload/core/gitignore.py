from __future__ import annotations

import contextlib
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GitignoreParser:
    """Parse .gitignore files and match paths against patterns."""

    patterns: list[tuple[str, bool]] = field(default_factory=list)  # (pattern, is_negation)
    _regex_cache: dict[str, re.Pattern[str]] = field(default_factory=dict)

    def parse_file(self, gitignore_path: Path) -> None:
        """Parse a .gitignore file and add patterns."""
        if not gitignore_path.exists():
            return

        with open(gitignore_path) as f:
            for line in f:
                self._parse_line(line)

    def parse_string(self, content: str) -> None:
        """Parse gitignore content from a string."""
        for line in content.splitlines():
            self._parse_line(line)

    def _parse_line(self, line: str) -> None:
        """Parse a single line from a .gitignore file."""
        # Strip trailing whitespace (but not leading - it matters for some patterns)
        line = line.rstrip()

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            return

        # Handle negation patterns
        is_negation = False
        if line.startswith("!"):
            is_negation = True
            line = line[1:]

        # Handle escaped characters at the start
        if line.startswith("\\"):
            line = line[1:]

        # Normalize the pattern
        pattern = self._normalize_pattern(line)
        self.patterns.append((pattern, is_negation))

    def _normalize_pattern(self, pattern: str) -> str:
        pattern = pattern.rstrip("/")

        # Patterns without / can match anywhere in the tree - prefix with **/
        if "/" not in pattern:
            pattern = "**/" + pattern

        # Handle leading slash (anchored to root)
        if pattern.startswith("/"):
            pattern = pattern[1:]

        return pattern

    def _pattern_to_regex(self, pattern: str) -> re.Pattern[str]:
        """Convert a gitignore pattern to a regex."""
        if pattern in self._regex_cache:
            return self._regex_cache[pattern]

        # Escape special regex characters except * and ?
        regex = ""
        i = 0
        while i < len(pattern):
            c = pattern[i]
            if c == "*":
                if i + 1 < len(pattern) and pattern[i + 1] == "*":
                    # ** matches any path
                    if i + 2 < len(pattern) and pattern[i + 2] == "/":
                        regex += "(?:.*/)?"
                        i += 3
                        continue
                    else:
                        regex += ".*"
                        i += 2
                        continue
                else:
                    # * matches anything except /
                    regex += "[^/]*"
            elif c == "?":
                regex += "[^/]"
            elif c in ".^$+{}[]|()":
                regex += "\\" + c
            else:
                regex += c
            i += 1

        # Anchor the pattern
        regex = "^" + regex + "(?:/.*)?$"

        compiled = re.compile(regex)
        self._regex_cache[pattern] = compiled
        return compiled

    def is_ignored(self, path: Path | str, base_path: Path | None = None) -> bool:
        """Check if a path should be ignored based on the patterns."""
        if isinstance(path, str):
            path = Path(path)

        # Get relative path if base_path is provided
        if base_path:
            with contextlib.suppress(ValueError):
                path = path.relative_to(base_path)

        path_str = str(path).replace("\\", "/")  # Normalize to forward slashes

        ignored = False
        for pattern, is_negation in self.patterns:
            regex = self._pattern_to_regex(pattern)
            if regex.match(path_str):
                ignored = not is_negation

        return ignored

    def get_ignore_patterns(self) -> list[str]:
        """Get list of ignore patterns (non-negated) for use with file watcher."""
        return [pattern for pattern, is_negation in self.patterns if not is_negation]


def load_gitignore(directory: Path) -> GitignoreParser:
    """Load .gitignore from a directory and return a parser."""
    parser = GitignoreParser()
    gitignore_path = directory / ".gitignore"
    parser.parse_file(gitignore_path)
    return parser


def collect_gitignore_patterns(directories: list[Path]) -> list[str]:
    """Collect ignore patterns from .gitignore files in the given directories."""
    all_patterns: set[str] = set()

    for directory in directories:
        if directory.is_file():
            directory = directory.parent

        gitignore_path = directory / ".gitignore"
        if gitignore_path.exists():
            parser = GitignoreParser()
            parser.parse_file(gitignore_path)
            all_patterns.update(parser.get_ignore_patterns())

    return list(all_patterns)
