---
sidebar_position: 3
---

# CSS Hot Reload

superreload can update CSS stylesheets without refreshing the entire page.

## How It Works

When a `.css` file changes:

1. The file watcher detects the change
2. A `css_reload` message is sent via WebSocket
3. The JavaScript client finds matching `<link>` elements
4. A new `<link>` element is created with a cache-busting query parameter
5. Once the new stylesheet loads, the old one is removed

This results in an instant visual update without losing page state.

## Requirements

Your CSS must be loaded via `<link>` elements:

```html
<link rel="stylesheet" href="{% static 'style.css' %}">
```

Inline styles in `<style>` tags are not hot-reloaded.

## File Matching

The client matches CSS files by filename. If you change `style.css`, it will reload any `<link>` element whose `href` contains `style.css`.

## Watched Directories

By default, these directories are watched for CSS changes:

- `<app>/static/` directories
- Any directory in `STATICFILES_DIRS`

These directories are **ignored**:

- `staticfiles/` (collected static output)
- `node_modules/`

## Debugging

Open browser DevTools console. When CSS reloads, you'll see:

```
[superreload] CSS reload: ['style.css']
```

And a green toast notification: "CSS Updated"

## Errors

If a CSS file fails to load (404, syntax error), the old stylesheet is kept and an error is logged to the console. This prevents your page from losing all styles due to a typo.
