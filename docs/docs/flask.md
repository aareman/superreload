---
sidebar_position: 4
---

# Flask

:::info Coming Soon
Flask support is coming in a future release.
:::

## Planned Features

- Flask integration with automatic browser refresh
- Jinja2 template hot reload
- CSS/JS hot reload
- Error overlay with Flask-specific context

## Current Status

The core reloading infrastructure is framework-agnostic. Flask support requires implementing:

- `FlaskFramework` adapter
- Flask-specific middleware for JavaScript injection
- Flask CLI integration

## Contributing

Want to help implement Flask support? See the [Contributing Guide](https://github.com/superreload/superreload/blob/main/CONTRIBUTING.md).
