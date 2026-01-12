---
sidebar_position: 2
---

# Getting Started

## Requirements

- Python 3.9+
- Django 4.2+ (for Django integration)

## Installation

Install with pip:

```bash
pip install superreload[django]
```

Or with uv:

```bash
uv add superreload[django]
```

Or with poetry:

```bash
poetry add superreload[django]
```

## Django Setup

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

Add the middleware at the top of your middleware list:

```python
# settings.py

MIDDLEWARE = [
    'superreload.frameworks.django.SuperReloadMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # ... other middleware
]
```

### 3. Run the Development Server

Instead of `runserver`, use:

```bash
python manage.py superreload
```

With a specific address:

```bash
python manage.py superreload 0.0.0.0:8000
```

## What Gets Watched

By default, superreload watches for changes to:

- `.py` - Python files (triggers module reload + page refresh)
- `.html` - Templates (triggers page refresh)
- `.css` - Stylesheets (hot reload without page refresh)
- `.js` - JavaScript (triggers page refresh)

## Verify It's Working

1. Open your Django app in the browser
2. Open browser DevTools console
3. You should see: `[superreload] Connected`
4. Edit a Python file and save
5. The browser should refresh automatically

## Manual Reload

You can also trigger a manual reload at any time:

- **Browser**: Press `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
- **Console**: Press `r` + `Enter` in the terminal running superreload

## Next Steps

- [Django Configuration](/docs/django) - Detailed Django setup
- [CSS Hot Reload](/docs/css-hot-reload) - How CSS hot reload works
- [Error Overlay](/docs/error-overlay) - Understanding the error overlay
