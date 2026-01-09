# SUPERRELOAD - Project Knowledge Base

**Generated:** 2026-01-09
**Commit:** d115638
**Branch:** main

## Overview

Hot reload for Django (Flask planned). Watches Python files, reloads modules in-place without server restart, auto-refreshes browser via WebSocket. CSS/JS hot reload without full page refresh.

## Structure

```
superreload/
├── src/superreload/
│   ├── core/           # Framework-agnostic reload engine
│   │   ├── reloader.py     # Module reload logic + dependency tracking
│   │   ├── watcher.py      # File system watching (watchfiles)
│   │   ├── websocket.py    # WebSocket server for browser
│   │   ├── framework.py    # Framework base class + registry
│   │   └── errors.py       # Error formatting with local vars
│   ├── frameworks/
│   │   └── django/         # Django adapter
│   │       ├── framework.py      # DjangoFramework (clears caches)
│   │       ├── middleware.py     # Injects JS client into HTML
│   │       ├── reload_server.py  # Orchestrates everything
│   │       └── management/commands/superreload.py
│   ├── browser/
│   │   └── client.js       # WebSocket client (22KB, embedded)
│   └── cli.py              # CLI entry point
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

## Tests

- Flat structure in `tests/`
- Only core tests exist (no Django integration tests yet)
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
- `browser/client.js` exists but middleware.py embeds its own copy as `SUPERRELOAD_JS`
- Docs use Docusaurus (Node.js), not Sphinx - separate build system
- RTD serves from `/en/latest/` - baseUrl is dynamic in docusaurus.config.ts
