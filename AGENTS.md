# SUPERRELOAD - Project Knowledge Base

**Generated:** 2026-01-13
**Commit:** 3f167ed
**Branch:** main

## Overview

Hot reload for Django (Flask planned). Watches Python files, reloads modules in-place without server restart, auto-refreshes browser via WebSocket. CSS/JS hot reload without full page refresh. Manual reload via keyboard shortcuts (Ctrl+Shift+R in browser, 'r' + Enter in console).

**CLI Mode**: Run any Python script with hot reloading via `superreload run script.py`. Supports `--watch`, `--gitignore`, `--full-reload` flags.

## Structure

```
superreload/
├── src/superreload/
│   ├── core/           # Framework-agnostic reload engine
│   │   ├── reloader.py     # Module reload logic + dependency tracking
│   │   ├── watcher.py      # File system watching (watchfiles)
│   │   ├── websocket.py    # WebSocket server for browser
│   │   ├── framework.py    # Framework base class + registry
│   │   ├── errors.py       # Error formatting with local vars
│   │   ├── gitignore.py    # Parse .gitignore files for filtering
│   │   └── script_runner.py # Run scripts with hot reload/restart
│   ├── frameworks/
│   │   └── django/         # Django adapter
│   │       ├── framework.py      # DjangoFramework (clears caches)
│   │       ├── middleware.py     # Injects JS client into HTML
│   │       ├── reload_server.py  # Orchestrates everything
│   │       └── management/commands/superreload.py
│   ├── browser/
│   │   └── client.js       # WebSocket client (22KB, embedded)
│   └── cli.py              # CLI entry point ('run' command)
├── tests/                  # Flat, core-focused only
└── docs/                   # Docusaurus (separate Node.js build)
```

## Where to Look

| Task | Location | Notes |
|------|----------|-------|
| Add framework support | `src/superreload/frameworks/{name}/` | Implement `Framework` interface, register via decorator |
| Modify reload behavior | `core/reloader.py` | `reload_module()`, `_compute_reload_order()` |
| Change file watching | `core/watcher.py` | Uses `watchfiles` library |
| Fix browser refresh | `core/websocket.py` + `browser/client.js` | Keep both in sync |
| CSS/JS hot reload | `frameworks/django/middleware.py` | `SUPERRELOAD_JS` constant |
| Error overlay | `core/errors.py` | `format_exception()` extracts locals |
| Django caches | `frameworks/django/framework.py` | URL + template cache clearing |
| CLI script running | `cli.py` + `core/script_runner.py` | `superreload run script.py`, uses jurigged by default |
| Script reload modes | `core/script_runner.py` | 3 modes: jurigged (surgical), simple (re-execute), full-reload (restart) |
| Gitignore parsing | `core/gitignore.py` | `GitignoreParser`, `collect_gitignore_patterns()` |
| Hot reload engine | jurigged (dependency) | Surgical code patching via `__code__` replacement |

## Commands

```bash
# Dev
uv sync --dev
uv run pytest -v
uv run ruff check src tests
uv run mypy src

# With Nix/devenv
test      # pytest
lint      # ruff check
fmt       # ruff format
typecheck # mypy

# Docs (separate build)
cd docs && npm ci && npm run build
```

## Conventions

- **Line length**: 100 chars (not 88)
- **Mypy**: Strict mode enabled
- **Imports**: `from __future__ import annotations` in all files
- **Type ignores**: Only for conditional imports (websockets/watchfiles fallbacks)
- **No setup.py**: pyproject.toml + hatchling only
- **Package manager**: uv (not pip/poetry)

## Commit Practices

**Conventional Commits required.** Format: `type: description`

| Type | Use For |
|------|---------|
| `feat` | New features |
| `fix` | Bug fixes |
| `docs` | Documentation only |
| `refactor` | Code changes that don't fix bugs or add features |
| `test` | Adding/updating tests |
| `ci` | CI/CD changes |
| `chore` | Maintenance (deps, configs) |

**Rules:**
- Commit each logical change separately (not batched)
- Commit immediately when a change is complete and working
- Keep commits atomic - one concern per commit
- Run tests before committing: `uv run pytest`
- Pre-commit hooks auto-run ruff check + format
- Docs MUST be updated as well

**Examples:**
```
feat: add Flask framework support
fix: CSS hot reload closure bug
docs: update installation instructions
refactor: extract WebSocket handler into separate class
test: add integration tests for Django middleware
ci: add Python 3.13 to test matrix
```

## Anti-Patterns

| Don't | Why |
|-------|-----|
| Reload migrations | Blocked in `DjangoFramework.can_reload()` |
| Reload settings.py | Blocked - causes Django to break |
| Suppress type errors | No `as any`, `@ts-ignore` |
| Edit `browser/client.js` without updating middleware | `SUPERRELOAD_JS` in middleware.py is the source of truth |
| Rapid file saves | Cooldown system blocks reloads within 1s of previous reload |

## Architecture Flow

```
Browser <--WebSocket:9877--> WebSocketServer
                                  ↑
                            DjangoReloadServer
                                  ↑
FileWatcher (watchfiles) ──→ detects changes
                                  ↓
                    ┌─────────────┴──────────────┐
                    ▼                            ▼
              .py files                    .css/.js files
                    ↓                            ↓
           Reloader.reload_module()    notify_css_reload()
                    ↓                  notify_js_reload()
           On error → format_exception()
                    ↓
           WebSocket sends error JSON
                    ↓
           Browser shows error overlay
```

## Adding a New Framework

1. Create `src/superreload/frameworks/{name}/`
2. Implement `Framework` subclass:
   ```python
   @FrameworkRegistry.register("flask")
   class FlaskFramework(Framework):
       name = "flask"
       def setup(self) -> None: ...
       def can_reload(self, ctx: ReloadContext) -> bool: ...
       def before_reload(self, ctx: ReloadContext) -> None: ...
       def after_reload(self, ctx: ReloadContext, result: ReloadResult) -> None: ...
       def get_watch_paths(self) -> list[Path]: ...
       def get_watch_patterns(self) -> list[str]: ...
   ```
3. Add entry point in pyproject.toml:
   ```toml
   [project.entry-points."superreload.frameworks"]
   flask = "superreload.frameworks.flask:FlaskFramework"
   ```
4. Create middleware for JS injection

**Framework lifecycle hooks (7 phases):**
1. `setup()` → Initialize framework state
2. `can_reload()` → Veto reload (block migrations, settings.py)
3. `before_reload()` → Pre-reload preparation
4. `after_reload()` → Cache clearing (URLs, templates, app registry)
5. `get_watch_paths()` → Directories to monitor
6. `get_watch_patterns()` → File patterns (`*.py`, `*.html`, etc.)
7. `get_ignore_patterns()` → Files to skip

## Tests

- Flat structure in `tests/`
- Core tests + Django integration tests in `tests/test_django.py`
- `pytest-asyncio` with `asyncio_mode = "auto"`
- Run: `uv run pytest -v`

## CI

Three parallel jobs:
1. **lint**: ruff check + format
2. **test**: Python 3.9-3.13 matrix
3. **typecheck**: mypy strict

All must pass. Pre-commit hooks run ruff on commit.

## Gotchas

- Directory named `reloadium`, package named `superreload` (rebrand in progress)
- `browser/client.js` (622 lines) exists but is NOT used at runtime; `SUPERRELOAD_JS` in middleware.py is the source of truth
- Docs use Docusaurus (Node.js), not Sphinx - separate build system
- RTD serves from `/en/latest/` - baseUrl is dynamic in docusaurus.config.ts
