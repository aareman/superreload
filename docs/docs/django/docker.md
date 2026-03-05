---
sidebar_position: 5
---

# Docker

Running superreload in Docker requires special configuration because Docker bind mounts don't propagate filesystem events (inotify) from the host to the container.

## Required Flags

```bash
python manage.py superreload 0.0.0.0:8000 --ws-host 0.0.0.0 --force-polling
```

| Flag                | Why It's Needed                                                                                      |
| ------------------- | ---------------------------------------------------------------------------------------------------- |
| `0.0.0.0:8000`      | Binds Django server to all interfaces                                                                |
| `--ws-host 0.0.0.0` | Binds WebSocket server to all interfaces so the browser can connect through Docker's port forwarding |
| `--force-polling`   | Uses polling instead of inotify, which doesn't work with Docker bind mounts                          |

## Docker Compose Example

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
      - "9877:9877" # WebSocket port
    volumes:
      - .:/app
    command: python manage.py superreload 0.0.0.0:8000 --ws-host 0.0.0.0 --force-polling
```

## Makefile Example

```makefile
web:
    python manage.py superreload 0.0.0.0:8000 --ws-host 0.0.0.0 --force-polling
```

## Why Polling is Required

Docker bind mounts use a different mechanism than native filesystem access. When you edit a file on your host machine:

1. The host's filesystem updates the file
2. Docker's bind mount makes the new content visible inside the container
3. But **inotify events are NOT forwarded** to the container

Without `--force-polling`, superreload uses inotify (via the `watchfiles` library) which never sees the file changes. With polling enabled, superreload actively checks file modification times every 300ms (configurable via `--poll-delay`).

## Performance Considerations

Polling uses slightly more CPU than inotify. For large projects, you may want to increase the poll delay:

```bash
python manage.py superreload --force-polling --poll-delay 500
```

Lower values = faster detection but more CPU usage. The default of 300ms is a good balance.

## Reverse Proxy in Docker

If you're running Django behind a reverse proxy (nginx, etc.) in Docker, see the [Reverse Proxy Configuration](configuration.md#reverse-proxy-configuration) section for additional setup steps. You'll typically need to:

1. Configure the proxy to forward WebSocket connections
2. Use `--ws-frontend-host` to set the browser's WebSocket host (omitting the port)
3. Use `SUPERRELOAD_WS_SECURE = True` if the proxy terminates HTTPS
