---
sidebar_position: 6
---

# Error Overlay

When a Python reload error occurs, superreload displays a detailed error overlay in the browser.

## Features

The error overlay shows:

- **Error type**: The exception class (e.g., `SyntaxError`, `ImportError`)
- **Error message**: The exception message
- **Module name**: Which module failed to reload
- **Stack trace**: Full traceback with file locations
- **Local variables**: Variables in scope at each frame
- **Source code**: Code context around the error line

## Example

When you introduce an error like:

```python
# views.py
def my_view(request):
    x = 1
    y = 0
    result = x / y  # ZeroDivisionError
    return HttpResponse(result)
```

The overlay will show:

- Error type: `ZeroDivisionError`
- Message: `division by zero`
- Stack trace pointing to the exact line
- Local variables: `x = 1`, `y = 0`, `request = <WSGIRequest ...>`

## Dismissing the Overlay

- Press `ESC`
- Click the X button

## Auto-Recovery

When you fix the error and save:

1. superreload attempts to reload the module again
2. If successful, the overlay is dismissed automatically
3. The page refreshes with the fixed code

## Styling

The overlay uses a dark theme optimized for readability:

- Red accent for error indicators
- Purple for variable names
- Green for variable values
- Blue for function names
- Monospace font for code

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `ESC` | Dismiss overlay |
