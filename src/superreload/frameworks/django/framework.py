from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from superreload.core.framework import Framework, FrameworkRegistry, ReloadContext

if TYPE_CHECKING:
    from superreload.core.reloader import ReloadResult


@FrameworkRegistry.register("django")
class DjangoFramework(Framework):
    name = "django"

    def __init__(self) -> None:
        self._settings_module: str | None = None
        self._base_dir: Path | None = None

    def setup(self) -> None:
        try:
            from django.conf import settings

            self._settings_module = settings.SETTINGS_MODULE
            self._base_dir = Path(settings.BASE_DIR) if hasattr(settings, "BASE_DIR") else None
        except Exception:
            pass

    def can_reload(self, ctx: ReloadContext) -> bool:
        for path in ctx.changed_files:
            if path.suffix == ".py":
                if "migrations" in path.parts:
                    return False
                if path.name == "settings.py" or "settings/" in str(path):
                    return False
        return True

    def before_reload(self, ctx: ReloadContext) -> None:  # noqa: ARG002
        try:
            from django.db import connection

            if connection.in_atomic_block:
                pass
        except Exception:
            pass

    def after_reload(self, ctx: ReloadContext, result: ReloadResult) -> None:  # noqa: ARG002
        if result.success:
            self._clear_url_caches()
            self._clear_template_caches()
            self._clear_app_registry_caches()

    def _clear_url_caches(self) -> None:
        try:
            from django.urls import clear_url_caches

            clear_url_caches()

            # Also reload the root URLconf to pick up new view references
            from importlib import reload

            from django.conf import settings

            root_urlconf = settings.ROOT_URLCONF
            if root_urlconf in sys.modules:
                reload(sys.modules[root_urlconf])
                clear_url_caches()
        except Exception:
            pass

    def _clear_template_caches(self) -> None:
        try:
            from django.template.loader import engines

            for engine in engines.all():
                if hasattr(engine, "engine") and hasattr(engine.engine, "template_loaders"):
                    for loader in engine.engine.template_loaders:
                        if hasattr(loader, "reset"):
                            loader.reset()
        except Exception:
            pass

    def _clear_app_registry_caches(self) -> None:
        try:
            from django.apps import apps

            apps.clear_cache()
        except Exception:
            pass

    def get_watch_paths(self) -> list[Path]:
        paths: list[Path] = []

        if self._base_dir and self._base_dir.exists():
            paths.append(self._base_dir)
            return paths

        try:
            from django.conf import settings

            if hasattr(settings, "BASE_DIR"):
                base = Path(settings.BASE_DIR)
                if base.exists():
                    paths.append(base)
                    return paths
        except Exception:
            pass

        cwd = Path.cwd()
        if (cwd / "manage.py").exists():
            paths.append(cwd)

        return paths

    def get_watch_patterns(self) -> list[str]:
        return ["*.py", "*.html", "*.css", "*.js"]

    def get_ignore_patterns(self) -> list[str]:
        return super().get_ignore_patterns() + [
            "*/migrations/*",
            "staticfiles",
            "media",
            ".devenv",
            "*.log",
            "*.sqlite3",
            "db.sqlite3",
        ]

    def get_reloadable_modules(self) -> list[str]:
        reloadable: list[str] = []
        try:
            from django.apps import apps

            for app_config in apps.get_app_configs():
                reloadable.append(app_config.name)
                if hasattr(app_config, "module") and app_config.module:
                    module_name = app_config.module.__name__
                    for name in list(sys.modules.keys()):
                        if name.startswith(module_name):
                            reloadable.append(name)
        except Exception:
            pass
        return list(set(reloadable))
