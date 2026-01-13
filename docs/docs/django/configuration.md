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
