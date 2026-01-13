---
sidebar_position: 1
---

# Django

Complete guide for using superreload with Django.

## Installation

```bash
pip install superreload[django]
```

Or with uv:

```bash
uv add superreload[django]
```

## Setup

### 1. Add to INSTALLED_APPS

```python
# settings.py

INSTALLED_APPS = [
    # ...
    'superreload.frameworks.django',
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

The middleware should be placed early in the list so it can inject the JavaScript client into responses.

## Quick Start

Run the development server:

```bash
python manage.py superreload
```

Or with an address:

```bash
python manage.py superreload 0.0.0.0:8000
```

That's it! Edit any Python, HTML, CSS, or JS file and watch your browser update automatically.

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

### Files That Require Server Restart

Some files cannot be hot-reloaded and require a full server restart:

- `settings.py` or anything in `settings/`
- Migration files (`*/migrations/*`)

superreload will log a message when these files change.

## Production

The middleware automatically detects `DEBUG = False` and does nothing. You don't need to remove it from your middleware list for production.
