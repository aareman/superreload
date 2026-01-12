# 🔥 superreload

**True hot reload for Django and Python web frameworks — no server restart needed.**

superreload watches your Python files and automatically reloads modules when they change, then refreshes your browser via WebSocket. This dramatically speeds up the development feedback loop.

## Features

- **Instant reload**: Python modules reload without restarting the server
- **Browser auto-refresh**: WebSocket-based browser refresh on file changes
- **CSS hot reload**: Stylesheets update without page refresh
- **Error overlay**: Beautiful error display with stack traces and local variables
- **Keyboard shortcuts**: Manual reload via Ctrl+Shift+R (browser) or 'r' + Enter (console)
- **Django-first**: Deep Django integration with view, template, and URL cache clearing
- **Extensible**: Framework-agnostic core with pluggable framework adapters
- **Zero config**: Works out of the box with sensible defaults

## Installation

```bash
pip install superreload[django]
```

Or with uv:

```bash
uv add superreload[django]
```

## Quick Start (Django)

### 1. Add to INSTALLED_APPS

```python
# settings.py

INSTALLED_APPS = [
    # ...
    'superreload.frameworks.django',
    # ...
]
```

### 2. Add the Middleware

```python
# settings.py

MIDDLEWARE = [
    'superreload.frameworks.django.SuperReloadMiddleware',
    # ... other middleware
]
```

### 3. Run the Development Server

```bash
python manage.py superreload
```

Or with an address:

```bash
python manage.py superreload 0.0.0.0:8000
```

That's it! Edit any Python, HTML, CSS, or JS file and watch your browser update automatically.

## How It Works

1. **File Watcher**: Monitors your project for `.py`, `.html`, `.css`, `.js` changes
2. **Module Reloader**: Intelligently reloads changed Python modules and their dependents
3. **WebSocket Server**: Notifies connected browsers to refresh
4. **Middleware**: Injects a tiny JavaScript client into HTML responses
5. **CSS Hot Reload**: Swaps stylesheets without full page refresh
6. **Error Overlay**: Shows reload errors with full stack traces in the browser

## Configuration

### WebSocket Port

Default port is `9877`. Change it via:

```bash
python manage.py superreload --ws-port 9999
```

### WebSocket Host

Default host is `localhost`. Change it via:

```bash
python manage.py superreload --ws-host 0.0.0.0
```

### WebSocket Path

Default path is `/superreload`. Useful for Docker/reverse proxy setups:

```bash
python manage.py superreload --ws-path /my-custom-path
```

### Disable superreload

Run without hot reloading:

```bash
python manage.py superreload --no-reload
```

### Manual Reload

Trigger a manual reload at any time:

- **Browser**: Press `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
- **Console**: Press `r` + `Enter` in the terminal running superreload

### Production

The middleware only activates when `DEBUG = True`. In production, it does nothing.

## Supported Frameworks

- ✅ **Django** (4.2+)
- 🔜 **Flask** (coming soon)
- 🔜 **FastAPI** (coming soon)

## Requirements

- Python 3.9+
- Django 4.2+ (for Django integration)

## Development

```bash
# Clone the repo
git clone https://github.com/superreload/superreload.git
cd superreload

# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Lint
uv run ruff check src tests

# Type check
uv run mypy src
```

## Architecture

```
superreload/
├── core/
│   ├── errors.py       # Error formatting with local variables
│   ├── framework.py    # Base framework abstraction
│   ├── reloader.py     # Python module reloading
│   ├── watcher.py      # File system watching
│   └── websocket.py    # WebSocket server
└── frameworks/
    └── django/
        ├── framework.py      # Django-specific reload logic
        ├── middleware.py     # Auto-inject JS client + error overlay
        └── reload_server.py  # Orchestrates everything
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
