from __future__ import annotations

import linecache
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ErrorFrame:
    filename: str
    lineno: int
    name: str
    line: str
    locals: dict[str, str] | None = None


@dataclass
class ReloadError:
    type: str
    message: str
    module: str | None
    frames: list[ErrorFrame]
    source_context: list[tuple[int, str]] | None = None
    error_line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "message": self.message,
            "module": self.module,
            "frames": [
                {
                    "filename": f.filename,
                    "lineno": f.lineno,
                    "name": f.name,
                    "line": f.line,
                    "locals": f.locals,
                }
                for f in self.frames
            ],
            "sourceContext": (
                [{"lineno": ln, "code": code} for ln, code in self.source_context]
                if self.source_context
                else None
            ),
            "errorLine": self.error_line,
        }


def _get_line(filename: str, lineno: int) -> str:
    """Get a single line from a file."""
    try:
        return linecache.getline(filename, lineno).strip()
    except Exception:
        return ""


def _extract_locals(local_vars: dict[str, Any], max_len: int = 100) -> dict[str, str]:
    """Extract local variables, converting to safe string representations."""
    result: dict[str, str] = {}

    skip_names = {"self", "cls"}

    for name, value in local_vars.items():
        if name.startswith("_") or name in skip_names:
            continue

        try:
            repr_value = repr(value)
            if len(repr_value) > max_len:
                repr_value = repr_value[:max_len] + "..."
            result[name] = repr_value
        except Exception:
            result[name] = "<error getting repr>"

    return result


def format_exception(exc: Exception, module_name: str | None = None) -> ReloadError:
    """Format an exception with full traceback and local variables."""
    frames: list[ErrorFrame] = []
    error_line: int | None = None
    error_file: str | None = None

    tb = exc.__traceback__
    while tb is not None:
        frame = tb.tb_frame
        lineno = tb.tb_lineno

        frame_locals = _extract_locals(frame.f_locals)

        frames.append(
            ErrorFrame(
                filename=frame.f_code.co_filename,
                lineno=lineno,
                name=frame.f_code.co_name,
                line=_get_line(frame.f_code.co_filename, lineno),
                locals=frame_locals if frame_locals else None,
            )
        )
        error_line = lineno
        error_file = frame.f_code.co_filename
        tb = tb.tb_next

    source_context: list[tuple[int, str]] | None = None
    if error_file and error_line:
        source_context = get_source_context(error_file, error_line)

    return ReloadError(
        type=type(exc).__name__,
        message=str(exc),
        module=module_name,
        frames=frames,
        source_context=source_context,
        error_line=error_line,
    )


def get_source_context(
    filename: str, lineno: int, context_lines: int = 5
) -> list[tuple[int, str]] | None:
    """Get surrounding source code lines for context."""
    try:
        path = Path(filename)
        if not path.exists():
            return None

        lines = path.read_text().splitlines()
        start = max(0, lineno - context_lines - 1)
        end = min(len(lines), lineno + context_lines)

        return [(i + 1, lines[i]) for i in range(start, end)]
    except Exception:
        return None
