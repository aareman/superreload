---
sidebar_position: 3
---

# Django

Detailed guide for using superreload with Django.

## Installation

```bash
pip install superreload[django]
```

## Configuration

### settings.py

```python
INSTALLED_APPS = [
    # ...
    'superreload.frameworks.django',
]

MIDDLEWARE = [
    'superreload.frameworks.django.SuperReloadMiddleware',
    # ... other middleware
]
```

The middleware should be placed early in the list so it can inject the JavaScript client into responses.

## Management Command

### Basic Usage

```bash
python manage.py superreload
```

### With Address

```bash
python manage.py superreload 0.0.0.0:8000
```

### Options

| Option | Description |
|--------|-------------|
| `--ws-host HOST` | WebSocket host (default: localhost) |
| `--ws-port PORT` | WebSocket port (default: 9877) |
| `--ws-path PATH` | WebSocket URL path (default: /superreload) |
| `--force-polling` | Use polling for file watching (required for Docker) |
| `--poll-delay MS` | Polling interval in milliseconds (default: 300) |
| `--no-reload` | Disable hot reloading, run normal server |

### Examples

```bash
# Custom WebSocket port
python manage.py superreload --ws-port 9999

# Custom WebSocket host
python manage.py superreload --ws-host 0.0.0.0

# Disable hot reloading
python manage.py superreload --no-reload

# Custom WebSocket path (useful for Docker/reverse proxy)
python manage.py superreload --ws-path /my-custom-path

# All together
python manage.py superreload 0.0.0.0:8000 --ws-host 0.0.0.0 --ws-port 9999 --ws-path /superreload
```

## Manual Reload

You can trigger a manual reload at any time:

- **Browser**: Press `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
- **Console**: Press `r` + `Enter` in the terminal running superreload

This is useful when you want to force a reload without making file changes.

## How It Works

1. The management command starts the Django development server with `--noreload` (disabling Django's built-in reloader)
2. superreload's file watcher monitors your project
3. When a file changes:
   - Python files: Module is reloaded in-place, URL caches cleared, browser refreshed
   - CSS files: Stylesheet is hot-swapped without page refresh
   - Other files: Browser is refreshed
4. The middleware injects a small JavaScript client that connects via WebSocket

## What Gets Reloaded

### Python Files

When a `.py` file changes:

1. The module is reloaded using `importlib.reload()`
2. Django's URL caches are cleared
3. Template caches are cleared
4. The browser is refreshed

### Files That Trigger Server Restart

Some files cannot be hot-reloaded and require a full server restart:

- `settings.py` or anything in `settings/`
- Migration files (`*/migrations/*`)

superreload will log a message when these files change.

## Production

The middleware automatically detects `DEBUG = False` and does nothing. You don't need to remove it from your middleware list for production.

## Troubleshooting

### Browser not refreshing

1. Check browser console for `[superreload] Connected`
2. Ensure WebSocket port (9877) is not blocked
3. Verify middleware is in `MIDDLEWARE` list

### Module not reloading

Some patterns don't reload well:

- Module-level code that runs on import
- Singleton patterns
- Cached imports in other modules

For these cases, you may need a full server restart.

### CSS not updating

Ensure your CSS files are in a directory being watched. By default, `staticfiles/` (the collected static output) is ignored, but `static/` directories within apps are watched.

## Docker

Running superreload in Docker requires special configuration because Docker bind mounts don't propagate filesystem events (inotify) from the host to the container.

### Required Flags

```bash
python manage.py superreload 0.0.0.0:8000 --ws-host 0.0.0.0 --force-polling
```

| Flag | Why It's Needed |
|------|-----------------|
| `--ws-host 0.0.0.0` | Binds WebSocket server to all interfaces so the browser can connect through Docker's port forwarding |
| `--force-polling` | Uses polling instead of inotify, which doesn't work with Docker bind mounts |

### Docker Compose Example

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
      - "9877:9877"  # WebSocket port
    volumes:
      - .:/app
    command: python manage.py superreload 0.0.0.0:8000 --ws-host 0.0.0.0 --force-polling
```

### Makefile Example

```makefile
web:
    python manage.py superreload 0.0.0.0:8000 --ws-host 0.0.0.0 --force-polling
```

### Why Polling is Required

Docker bind mounts use a different mechanism than native filesystem access. When you edit a file on your host machine:

1. The host's filesystem updates the file
2. Docker's bind mount makes the new content visible inside the container
3. But **inotify events are NOT forwarded** to the container

Without `--force-polling`, superreload uses inotify (via the `watchfiles` library) which never sees the file changes. With polling enabled, superreload actively checks file modification times every 300ms (configurable via `--poll-delay`).

### Performance Considerations

Polling uses slightly more CPU than inotify. For large projects, you may want to increase the poll delay:

```bash
python manage.py superreload --force-polling --poll-delay 500
```

## Limitations

Some Django components cannot be hot-reloaded and require a full server restart:

| Component | Reason |
|-----------|--------|
| `settings.py` | Global configuration, database connections, INSTALLED_APPS |
| `migrations/` | Database schema changes require `migrate` command |
| Middleware classes | Built once at server startup |
| Admin ModelAdmin | Registry not designed for runtime updates |
| `apps.py` AppConfig | `ready()` method only runs once |
| Signal handlers (without dispatch_uid) | May register duplicate handlers |

### Signal Handler Best Practice

To prevent duplicate signal handlers after hot reload, always use `dispatch_uid`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=MyModel, dispatch_uid='myapp.my_handler')
def my_handler(sender, **kwargs):
    pass
```
