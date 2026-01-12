---
sidebar_position: 7
---

# Configuration

superreload is designed to work with zero configuration, but you can customize behavior if needed.

## Command Line Options

### WebSocket Host

Default: `localhost`

```bash
python manage.py superreload --ws-host 0.0.0.0
```

### WebSocket Port

Default: `9877`

```bash
python manage.py superreload --ws-port 9999
```

### WebSocket Path

Default: `/superreload`

Useful for Docker or reverse proxy setups where you need to route WebSocket traffic to a specific path:

```bash
python manage.py superreload --ws-path /my-custom-path
```

### Disable Hot Reload

Run the server without superreload:

```bash
python manage.py superreload --no-reload
```

## Manual Reload

Trigger a manual reload at any time:

| Method | Shortcut |
|--------|----------|
| Browser | `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac) |
| Console | `r` + `Enter` in terminal |

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

## Environment Variables

Currently, superreload does not use environment variables. All configuration is via command line arguments.

## Future Configuration

Planned for future releases:

- `superreload.toml` configuration file
- Per-project watch patterns
- Custom ignore patterns
