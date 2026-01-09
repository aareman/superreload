# 🔥 superreload

**True hot reload for Django and Python web frameworks — no server restart needed.**

superreload watches your Python files and automatically reloads modules when they change, then refreshes your browser via WebSocket. This dramatically speeds up the development feedback loop.

## Features

- **Instant reload**: Python modules reload without restarting the server
- **Browser auto-refresh**: WebSocket-based browser refresh on file changes
- **Django-first**: Deep Django integration with view, template, and URL cache clearing
- **Extensible**: Framework-agnostic core with pluggable framework adapters
- **Zero config**: Works out of the box with sensible defaults

## Installation

```bash
pip install superreload

# With Django support
pip install superreload[django]
```

## Quick Start (Django)

### Option 1: Middleware (Recommended)

Add to your `settings.py`:

```python
MIDDLEWARE = [
    'superreload.frameworks.django.SuperReloadMiddleware',
    # ... other middleware
]
```

Then run with the management command:

```bash
python manage.py superreload
```

### Option 2: Manual Setup

```python
from superreload.frameworks.django import DjangoReloadServer

server = DjangoReloadServer()
server.start(background=True)
```

## How It Works

1. **File Watcher**: Monitors your project for `.py`, `.html`, `.css`, `.js` changes
2. **Module Reloader**: Intelligently reloads changed Python modules and their dependents
3. **WebSocket Server**: Notifies connected browsers to refresh
4. **Middleware**: Injects a tiny JavaScript client into HTML responses

## Configuration

### WebSocket Port

Default port is `9877`. Change it via:

```bash
python manage.py superreload --superreload-port 9999
```

### Disable for Production

The middleware automatically detects `DEBUG = False` and disables itself.

## Supported Frameworks

- ✅ **Django** (4.2+)
- 🔜 **Flask** (coming soon)
- 🔜 **FastAPI** (coming soon)

## Development

This project uses [devenv](https://devenv.sh) for reproducible development environments.

```bash
# Enter development shell
devenv shell

# Run tests
pytest

# Lint and format
ruff check src tests
ruff format src tests
```

## Architecture

```
superreload/
├── core/
│   ├── framework.py    # Base framework abstraction
│   ├── reloader.py     # Python module reloading
│   ├── watcher.py      # File system watching
│   └── websocket.py    # WebSocket server
└── frameworks/
    └── django/
        ├── framework.py      # Django-specific reload logic
        ├── middleware.py     # Auto-inject JS client
        └── reload_server.py  # Orchestrates everything
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! Please read the contributing guidelines first.

---

**superreload** — Stop waiting for restarts. Start shipping faster. 🚀
