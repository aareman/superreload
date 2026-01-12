from __future__ import annotations

import contextlib
import logging
import sys
from dataclasses import dataclass, field
from importlib import import_module, invalidate_caches, reload
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from superreload.core.framework import Framework

logger = logging.getLogger(__name__)


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
                    module_name = ".".join(parts)
                    logger.debug(f"Resolved {path} -> {module_name}")
                    return module_name
            except ValueError:
                continue
        logger.debug(f"Could not resolve module name for {path}")
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
            # Skip __main__ - it can't be reloaded safely
            if name == "__main__":
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
            logger.debug(f"Module {module_name} not loaded, importing fresh")
            try:
                import_module(module_name)
                return True, None
            except Exception as e:
                logger.debug(f"Import failed for {module_name}: {e}")
                return False, e

        try:
            logger.debug(f"Reloading module {module_name}")
            invalidate_caches()
            self._clear_bytecode_cache(module)
            self._clear_loader_cache(module)
            invalidate_caches()
            reload(module)
            logger.debug(f"Successfully reloaded {module_name}")
            return True, None
        except Exception as e:
            logger.debug(f"Reload failed for {module_name}: {e}")
            return False, e

    def _clear_loader_cache(self, module: ModuleType) -> None:
        spec = getattr(module, "__spec__", None)
        if spec and hasattr(spec, "loader") and spec.loader:
            loader = spec.loader
            if hasattr(loader, "path"):
                path = loader.path
                if hasattr(loader, "_cache") and isinstance(loader._cache, dict):
                    loader._cache.pop(path, None)

    def _clear_bytecode_cache(self, module: ModuleType) -> None:
        source_file = getattr(module, "__file__", None)
        if not source_file:
            return

        source_path = Path(source_file)
        pycache_dir = source_path.parent / "__pycache__"

        if pycache_dir.exists():
            module_stem = source_path.stem
            for pyc_file in pycache_dir.glob(f"{module_stem}.*.pyc"):
                with contextlib.suppress(OSError):
                    pyc_file.unlink()

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
        changed_set = set(module_names)
        dependents: set[str] = set()

        for name in module_names:
            deps = self.get_dependent_modules(name)
            for dep in deps:
                if dep not in changed_set:
                    dependents.add(dep)
            if deps:
                logger.debug(f"Found dependents of {name}: {deps}")

        reload_order = list(module_names) + list(dependents)
        logger.debug(f"Reload order: {reload_order}")
        return reload_order

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
