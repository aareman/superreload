---
sidebar_position: 1
slug: /
---

# Introduction

**superreload** is a hot reload tool for Django and Python web frameworks. It watches your files, reloads Python modules in-place without restarting the server, and refreshes your browser automatically.

## Why superreload?

Django's built-in `runserver --reload` restarts the entire server when you change a file. This means:

- Waiting for the server to restart
- Losing in-memory state
- Slow feedback loop

With superreload:

- Python modules reload instantly without server restart
- Browser refreshes automatically via WebSocket
- CSS updates without page refresh
- Errors show in a beautiful overlay with stack traces

## Features

- **Instant Python reload**: Modules reload without restarting the server
- **Browser auto-refresh**: WebSocket-based browser refresh on file changes
- **CSS hot reload**: Stylesheets update without page refresh
- **Error overlay**: Beautiful error display with stack traces and local variables
- **Django integration**: Deep integration with view, template, and URL cache clearing
- **Zero config**: Works out of the box with sensible defaults

## Quick Start

```bash
pip install superreload[django]
```

Add to your Django settings:

```python
INSTALLED_APPS = [
    # ...
    'superreload.frameworks.django',
]

MIDDLEWARE = [
    'superreload.frameworks.django.SuperReloadMiddleware',
    # ...
]
```

Run the development server:

```bash
python manage.py superreload
```

That's it! Edit any file and watch your browser update automatically.
