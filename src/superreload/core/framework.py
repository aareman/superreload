from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from superreload.core.reloader import ReloadResult


@dataclass
class ReloadContext:
    changed_files: list[Path]
    module_names: list[str] = field(default_factory=list)


class Framework(ABC):
    name: str = "base"

    @abstractmethod
    def setup(self) -> None:
        pass

    @abstractmethod
    def can_reload(self, ctx: ReloadContext) -> bool:
        pass

    @abstractmethod
    def before_reload(self, ctx: ReloadContext) -> None:
        pass

    @abstractmethod
    def after_reload(self, ctx: ReloadContext, result: ReloadResult) -> None:
        pass

    @abstractmethod
    def get_watch_paths(self) -> list[Path]:
        pass

    @abstractmethod
    def get_watch_patterns(self) -> list[str]:
        pass

    def get_ignore_patterns(self) -> list[str]:
        return [
            "__pycache__",
            "*.pyc",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            ".pytest_cache",
            "*.egg-info",
        ]


class FrameworkRegistry:
    _frameworks: dict[str, type[Framework]] = {}
    _instances: dict[str, Framework] = {}

    @classmethod
    def register(cls, name: str) -> Callable[[type[Framework]], type[Framework]]:
        def decorator(framework_cls: type[Framework]) -> type[Framework]:
            cls._frameworks[name] = framework_cls
            return framework_cls

        return decorator

    @classmethod
    def get(cls, name: str) -> Framework:
        if name not in cls._instances:
            if name not in cls._frameworks:
                available = ", ".join(cls._frameworks.keys()) or "none"
                raise ValueError(f"Unknown framework: {name}. Available: {available}")
            cls._instances[name] = cls._frameworks[name]()
        return cls._instances[name]

    @classmethod
    def available(cls) -> list[str]:
        return list(cls._frameworks.keys())

    @classmethod
    def detect(cls) -> Framework | None:
        for name, _framework_cls in cls._frameworks.items():
            try:
                instance = cls.get(name)
                if instance.get_watch_paths():
                    return instance
            except Exception:
                continue
        return None
