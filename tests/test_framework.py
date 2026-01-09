from __future__ import annotations

import pytest

from superreload.core.framework import Framework, FrameworkRegistry, ReloadContext


class TestReloadContext:
    def test_reload_context(self) -> None:
        from pathlib import Path

        ctx = ReloadContext(changed_files=[Path("/app/views.py")])
        assert len(ctx.changed_files) == 1
        assert ctx.module_names == []

    def test_reload_context_with_modules(self) -> None:
        from pathlib import Path

        ctx = ReloadContext(
            changed_files=[Path("/app/views.py")],
            module_names=["myapp.views"],
        )
        assert ctx.module_names == ["myapp.views"]


class TestFrameworkRegistry:
    def test_register_and_get(self) -> None:
        @FrameworkRegistry.register("test_framework")
        class TestFramework(Framework):
            name = "test"

            def setup(self) -> None:
                pass

            def can_reload(self, ctx: ReloadContext) -> bool:  # noqa: ARG002
                return True

            def before_reload(self, ctx: ReloadContext) -> None:  # noqa: ARG002
                pass

            def after_reload(self, ctx: ReloadContext, result) -> None:  # type: ignore[no-untyped-def]  # noqa: ARG002
                pass

            def get_watch_paths(self) -> list:  # type: ignore[type-arg]
                return []

            def get_watch_patterns(self) -> list:  # type: ignore[type-arg]
                return ["*.py"]

        framework = FrameworkRegistry.get("test_framework")
        assert framework.name == "test"
        assert framework.can_reload(ReloadContext(changed_files=[])) is True

    def test_get_unknown_framework(self) -> None:
        with pytest.raises(ValueError, match="Unknown framework"):
            FrameworkRegistry.get("nonexistent_framework_xyz")

    def test_available(self) -> None:
        available = FrameworkRegistry.available()
        assert isinstance(available, list)
