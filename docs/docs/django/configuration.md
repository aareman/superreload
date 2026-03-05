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

| Option                           | Default          | Description                                                   |
| -------------------------------- | ---------------- | ------------------------------------------------------------- |
| `--ws-host HOST[:PORT]`          | `localhost:9877` | WebSocket server bind address                                 |
| `--ws-frontend-host HOST[:PORT]` | same as ws-host  | WebSocket address for browser connections (for reverse proxy) |
| `--ws-path PATH`                 | `/superreload`   | WebSocket URL path                                            |
| `--force-polling`                | disabled         | Use polling for file watching (required for Docker)           |
| `--poll-delay MS`                | `300`            | Polling interval in milliseconds                              |
| `--no-reload`                    | disabled         | Disable hot reloading, run normal server                      |

### Examples

```bash
# Custom WebSocket port
python manage.py superreload --ws-host localhost:9999

# Custom WebSocket host (for Docker)
python manage.py superreload --ws-host 0.0.0.0

# Custom WebSocket path (useful for reverse proxy)
python manage.py superreload --ws-path /my-custom-path

# Behind a reverse proxy (browser connects to example.com, no port)
python manage.py superreload 0.0.0.0:8000 --ws-host 0.0.0.0 --ws-frontend-host example.com

# Disable hot reloading
python manage.py superreload --no-reload
```

## Django Settings

You can configure superreload in your `settings.py` file. These settings are optional and have sensible defaults.

### Available Settings

| Setting                 | Default          | Type   | Description                                        |
| ----------------------- | ---------------- | ------ | -------------------------------------------------- |
| `SUPERRELOAD_WS_PATH`   | `"/superreload"` | `str`  | WebSocket URL path                                 |
| `SUPERRELOAD_WS_SECURE` | `False`          | `bool` | Use secure WebSocket (`wss://`) instead of `ws://` |

### Example

```python
# settings.py

# WebSocket configuration (all optional)
SUPERRELOAD_WS_PATH = "/ws/reload"  # Custom path (useful for reverse proxy)
SUPERRELOAD_WS_SECURE = True        # Use wss:// (for HTTPS sites)
```

## Manual Reload

Trigger a manual reload at any time:

| Method  | Shortcut                                 |
| ------- | ---------------------------------------- |
| Browser | `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac) |
| Console | `r` + `Enter` in terminal                |

This is useful when you want to force a reload without making file changes.

## Watched Patterns

By default, superreload watches:

| Pattern  | Action                           |
| -------- | -------------------------------- |
| `*.py`   | Module reload + page refresh     |
| `*.html` | Page refresh                     |
| `*.css`  | CSS hot reload (no page refresh) |
| `*.js`   | Page refresh                     |

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

## Reverse Proxy Configuration

When running behind a reverse proxy (like nginx-proxy), the browser connects to the WebSocket on a different host/port than the server listens on. Use `--ws-frontend-host` to tell the browser where to connect:

- `--ws-host` controls what the WebSocket server binds to (e.g., `0.0.0.0:9877`)
- `--ws-frontend-host` controls what the browser connects to (e.g., `example.com`)

When `--ws-frontend-host` is provided without a port, the port is omitted from the browser's WebSocket URL (since the proxy handles routing). If a port is included (e.g., `example.com:8443`), it is used in the browser URL.

### Docker Compose with nginx-proxy

```yaml
services:
  nginx-proxy:
    image: nginxproxy/nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro

  django:
    build: .
    environment:
      VIRTUAL_HOST: example.com
      VIRTUAL_PORT: 8000
    expose:
      - "8000"
      - "9877"
    volumes:
      - .:/app
    command: >
      python manage.py superreload 0.0.0.0:8000
      --ws-host 0.0.0.0
      --ws-frontend-host example.com
      --force-polling
```

```python
# Django settings.py
SUPERRELOAD_WS_SECURE = True
```

## Production

The middleware automatically detects `DEBUG = False` and disables itself. No configuration needed.
