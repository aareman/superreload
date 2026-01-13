---
sidebar_position: 2
---

# Configuration

superreload is designed to work with zero configuration, but you can customize behavior if needed.

## Command Line Options

### Basic Usage

```bash
python manage.py superreload
```

### With Address

```bash
python manage.py superreload 0.0.0.0:8000
```

### All Options

| Option | Default | Description |
|--------|---------|-------------|
| `--ws-host HOST` | `localhost` | WebSocket host |
| `--ws-port PORT` | `9877` | WebSocket port |
| `--ws-path PATH` | `/superreload` | WebSocket URL path |
| `--force-polling` | disabled | Use polling for file watching (required for Docker) |
| `--poll-delay MS` | `300` | Polling interval in milliseconds |
| `--no-reload` | disabled | Disable hot reloading, run normal server |

### Examples

```bash
# Custom WebSocket port
python manage.py superreload --ws-port 9999

# Custom WebSocket host (for Docker)
python manage.py superreload --ws-host 0.0.0.0

# Custom WebSocket path (useful for reverse proxy)
python manage.py superreload --ws-path /my-custom-path

# Disable hot reloading
python manage.py superreload --no-reload

# All together
python manage.py superreload 0.0.0.0:8000 --ws-host 0.0.0.0 --ws-port 9999
```

## Django Settings

You can configure superreload in your `settings.py` file. These settings are optional and have sensible defaults.

### Available Settings

| Setting | Default | Type | Description |
|---------|---------|------|-------------|
| `SUPERRELOAD_WS_PORT` | `9877` | `int` | WebSocket server port for browser communication |
| `SUPERRELOAD_WS_HOST` | `"localhost"` | `str` | WebSocket host (use `"0.0.0.0"` for Docker) |
| `SUPERRELOAD_WS_PATH` | `"/superreload"` | `str` | WebSocket URL path |
| `SUPERRELOAD_WS_SECURE` | `False` | `bool` | Use secure WebSocket (`wss://`) instead of `ws://` |

### Example

```python
# settings.py

# WebSocket configuration (all optional)
SUPERRELOAD_WS_PORT = 9999          # Custom port
SUPERRELOAD_WS_HOST = "0.0.0.0"     # For Docker/external access
SUPERRELOAD_WS_PATH = "/ws/reload"  # Custom path (useful for reverse proxy)
SUPERRELOAD_WS_SECURE = True        # Use wss:// (for HTTPS sites)
```

### When to Use Settings vs Command Line

- **Settings**: Use when you want consistent configuration across your team or in Docker Compose
- **Command line**: Use for quick one-off overrides or local development

Command-line options take precedence over settings.py values.

### Docker Example

For Docker environments, you typically need to expose the WebSocket host:

```python
# settings.py
import os

if os.environ.get("DOCKER"):
    SUPERRELOAD_WS_HOST = "0.0.0.0"
```

## Manual Reload

Trigger a manual reload at any time:

| Method | Shortcut |
|--------|----------|
| Browser | `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac) |
| Console | `r` + `Enter` in terminal |

This is useful when you want to force a reload without making file changes.

## Watched Patterns

By default, superreload watches:

| Pattern | Action |
|---------|--------|
| `*.py` | Module reload + page refresh |
| `*.html` | Page refresh |
| `*.css` | CSS hot reload (no page refresh) |
| `*.js` | Page refresh |

## Ignored Patterns

These paths are ignored:

- `__pycache__/`
- `*.pyc`
- `.git/`
- `.venv/`, `venv/`
- `node_modules/`
- `*/migrations/*`
- `staticfiles/` (collected static output)
- `media/`
- `*.log`
- `*.sqlite3`

## Production

The middleware automatically detects `DEBUG = False` and disables itself. No configuration needed.
