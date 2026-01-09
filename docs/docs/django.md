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
| `--superreload-port PORT` | WebSocket port (default: 9877) |
| `--no-superreload` | Disable hot reloading, run normal server |

### Examples

```bash
# Custom WebSocket port
python manage.py superreload --superreload-port 9999

# Disable hot reloading
python manage.py superreload --no-superreload

# All together
python manage.py superreload 0.0.0.0:8000 --superreload-port 9999
```

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
