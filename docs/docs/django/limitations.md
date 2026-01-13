---
sidebar_position: 6
---

# Limitations

Some Django components cannot be hot-reloaded and require a full server restart.

## Components That Require Restart

| Component | Reason |
|-----------|--------|
| `settings.py` | Global configuration, database connections, INSTALLED_APPS |
| `migrations/` | Database schema changes require `migrate` command |
| Middleware classes | Built once at server startup |
| Admin ModelAdmin | Registry not designed for runtime updates |
| `apps.py` AppConfig | `ready()` method only runs once |
| Signal handlers (without dispatch_uid) | May register duplicate handlers |

## Signal Handler Best Practice

To prevent duplicate signal handlers after hot reload, always use `dispatch_uid`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=MyModel, dispatch_uid='myapp.my_handler')
def my_handler(sender, **kwargs):
    pass
```

## Patterns That Don't Reload Well

- Module-level code that runs on import
- Singleton patterns
- Cached imports in other modules

For these cases, you may need a full server restart.

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
