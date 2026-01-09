---
sidebar_position: 8
---

# Architecture

An overview of superreload's internal architecture.

## Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  JavaScript Client (injected by middleware)          │    │
│  │  - WebSocket connection                              │    │
│  │  - CSS hot swap                                      │    │
│  │  - Error overlay                                     │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket (port 9877)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    WebSocketServer                          │
│  - Manages client connections                               │
│  - Broadcasts reload/error messages                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   DjangoReloadServer                        │
│  - Orchestrates file watching and reloading                 │
│  - Determines file type and appropriate action              │
│  - Handles cooldown to prevent duplicate reloads            │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   FileWatcher   │  │    Reloader     │  │ DjangoFramework │
│                 │  │                 │  │                 │
│ - watchfiles    │  │ - importlib     │  │ - URL cache     │
│ - debouncing    │  │ - reload()      │  │ - Template cache│
│ - filtering     │  │ - error capture │  │ - App discovery │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Core Modules

### `superreload.core.watcher`

File system watching using the `watchfiles` library (Rust-based, fast).

- `FileWatcher`: Async generator that yields file changes
- `FileWatcherConfig`: Configuration for paths, patterns, ignores
- `FileChange`: Dataclass representing a single file change

### `superreload.core.reloader`

Python module reloading.

- `Reloader`: Coordinates module reloading
- `ReloadResult`: Result of a reload attempt (success/failure, errors)
- Uses `importlib.reload()` under the hood

### `superreload.core.websocket`

WebSocket server for browser communication.

- `WebSocketServer`: Async WebSocket server using `websockets`
- `WebSocketMessage`: Message format for client communication
- Supports multiple concurrent browser connections

### `superreload.core.errors`

Error formatting for the overlay.

- `format_exception()`: Extracts error details including local variables
- `get_source_context()`: Gets source code around error line
- `ReloadError`: Dataclass with all error information

### `superreload.core.framework`

Framework abstraction layer.

- `Framework`: Base class for framework adapters
- `FrameworkRegistry`: Registry for discovering/loading frameworks
- `ReloadContext`: Context passed to framework hooks

## Django Integration

### `superreload.frameworks.django.framework`

Django-specific framework adapter.

- Clears URL resolvers after reload
- Clears template caches
- Identifies non-reloadable files (migrations, settings)
- Discovers Django app paths to watch

### `superreload.frameworks.django.middleware`

WSGI middleware that injects the JavaScript client.

- Only active when `DEBUG = True`
- Injects script before `</body>`
- Handles error responses too (for recovery)

### `superreload.frameworks.django.reload_server`

Orchestrates everything for Django.

- Creates FileWatcher, Reloader, WebSocketServer
- Routes file changes to appropriate handlers
- Manages reload cooldown

## Message Types

WebSocket messages between server and browser:

| Type | Direction | Description |
|------|-----------|-------------|
| `connected` | Server → Browser | Connection acknowledged |
| `reload` | Server → Browser | Trigger page refresh |
| `css_reload` | Server → Browser | Hot swap CSS files |
| `js_reload` | Server → Browser | Reload JavaScript (full refresh) |
| `error` | Server → Browser | Show error overlay |

## Data Flow

1. User saves a file
2. `watchfiles` detects the change
3. `FileWatcher` yields the change after debouncing
4. `DjangoReloadServer._handle_file_changes()` processes it:
   - Python: Reload module via `Reloader`, notify browser
   - CSS: Send `css_reload` message
   - JS/HTML: Send `reload` message
5. Browser receives message and acts accordingly
