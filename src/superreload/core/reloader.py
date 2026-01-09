from __future__ import annotations

import contextlib
import os
import sys
from dataclasses import dataclass, field
from importlib import import_module, invalidate_caches, reload
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from superreload.core.framework import Framework


@dataclass
class ReloadResult:
    success: bool
    reloaded_modules: list[str] = field(default_factory=list)
    failed_modules: list[str] = field(default_factory=list)
    errors: list[Exception] = field(default_factory=list)


class Reloader:
    def __init__(
        self,
        framework: Framework | None = None,
        on_reload: Callable[[ReloadResult], None] | None = None,
    ) -> None:
        self.framework = framework
        self.on_reload = on_reload
        self._module_mtimes: dict[str, float] = {}
        self._watched_modules: set[str] = set()

    def path_to_module_name(self, path: Path) -> str | None:
        path = path.resolve()
        for sys_path in sys.path:
            try:
                rel_path = path.relative_to(sys_path)
                parts = rel_path.with_suffix("").parts
                if parts[-1] == "__init__":
                    parts = parts[:-1]
                if parts:
                    return ".".join(parts)
            except ValueError:
                continue
        return None

    def get_module(self, name: str) -> ModuleType | None:
        return sys.modules.get(name)

    def get_dependent_modules(self, module_name: str) -> list[str]:
        dependents: list[str] = []
        target_module = self.get_module(module_name)
        if not target_module:
            return dependents

        for name, module in list(sys.modules.items()):
            if module is None or name == module_name:
                continue
            if not hasattr(module, "__file__") or module.__file__ is None:
                continue

            try:
                module_dict = vars(module)
                for attr_value in module_dict.values():
                    if isinstance(attr_value, ModuleType) and attr_value is target_module:
                        dependents.append(name)
                        break
                    if hasattr(attr_value, "__module__") and attr_value.__module__ == module_name:
                        dependents.append(name)
                        break
            except Exception:
                continue

        return dependents

    def reload_module(self, module_name: str) -> tuple[bool, Exception | None]:
        module = self.get_module(module_name)
        if module is None:
            try:
                import_module(module_name)
                return True, None
            except Exception as e:
                return False, e

        try:
            self._clear_bytecode_cache(module)
            self._ensure_mtime_changed(module)
            invalidate_caches()
            reload(module)
            return True, None
        except Exception as e:
            return False, e

    def _clear_bytecode_cache(self, module: ModuleType) -> None:
        cached = getattr(module, "__cached__", None)
        if cached and os.path.exists(cached):
            with contextlib.suppress(OSError):
                os.remove(cached)

    def _ensure_mtime_changed(self, module: ModuleType) -> None:
        source_file = getattr(module, "__file__", None)
        if not source_file or not os.path.exists(source_file):
            return

        try:
            import time

            current_mtime = os.path.getmtime(source_file)
            now = time.time()

            if (now - current_mtime) < 1.0:
                new_mtime = int(current_mtime) + 1
                os.utime(source_file, (new_mtime, new_mtime))
        except OSError:
            pass

    def reload_modules(self, module_names: list[str]) -> ReloadResult:
        result = ReloadResult(success=True)

        reload_order = self._compute_reload_order(module_names)

        for module_name in reload_order:
            success, error = self.reload_module(module_name)
            if success:
                result.reloaded_modules.append(module_name)
            else:
                result.failed_modules.append(module_name)
                if error:
                    result.errors.append(error)
                result.success = False

        if self.on_reload:
            self.on_reload(result)

        return result

    def _compute_reload_order(self, module_names: list[str]) -> list[str]:
        all_modules: set[str] = set(module_names)

        for name in module_names:
            dependents = self.get_dependent_modules(name)
            all_modules.update(dependents)

        ordered: list[str] = []
        visited: set[str] = set()

        def visit(name: str) -> None:
            if name in visited:
                return
            visited.add(name)
            for dep in self.get_dependent_modules(name):
                if dep in all_modules:
                    visit(dep)
            ordered.append(name)

        for name in all_modules:
            visit(name)

        return ordered

    async def reload_from_paths(self, paths: list[Path]) -> ReloadResult:
        module_names: list[str] = []
        for path in paths:
            if path.suffix == ".py":
                module_name = self.path_to_module_name(path)
                if module_name and module_name in sys.modules:
                    module_names.append(module_name)

        if not module_names:
            return ReloadResult(success=True)

        return self.reload_modules(module_names)
