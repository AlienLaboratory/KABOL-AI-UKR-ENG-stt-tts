"""Tests for action registry."""

import pytest
from kabolai.actions.registry import ActionRegistry, registry
from kabolai.actions.base import ActionResult


class TestActionRegistry:
    def test_register_decorator(self):
        @registry.register(
            name="test_action",
            category="test",
            description_en="Test action",
            description_uk="Тестова дія",
        )
        def test_action():
            return ActionResult(success=True, message="test")

        meta = registry.get("test_action")
        assert meta is not None
        assert meta.name == "test_action"
        assert meta.category == "test"

    def test_register_with_aliases(self):
        @registry.register(
            name="my_action",
            category="test",
            description_en="My action",
            description_uk="Моя дія",
            aliases=["alias1", "alias2"],
        )
        def my_action():
            return ActionResult(success=True, message="ok")

        assert registry.get("my_action") is not None
        assert registry.get("alias1") is not None
        assert registry.get("alias1").name == "my_action"

    def test_execute_action(self):
        @registry.register(
            name="exec_test",
            category="test",
            description_en="Exec test",
            description_uk="Тест",
            parameters=[{"name": "x", "type": "int", "required": True}],
        )
        def exec_test(x: int):
            return ActionResult(success=True, message=f"got {x}")

        result = registry.execute("exec_test", {"x": 42})
        assert result.success is True
        assert "42" in result.message

    def test_execute_unknown_action(self):
        result = registry.execute("nonexistent_action_xyz", {})
        assert result.success is False

    def test_list_actions(self):
        actions = registry.list_actions()
        assert isinstance(actions, list)

    def test_get_schema_for_llm(self):
        # Import real actions to populate registry
        import kabolai.actions.apps  # noqa
        import kabolai.actions.system  # noqa

        schema = registry.get_schema_for_llm("en")
        assert "open_app" in schema
        assert "get_time" in schema

    def test_get_schema_ukrainian(self):
        import kabolai.actions.apps  # noqa
        import kabolai.actions.system  # noqa

        schema = registry.get_schema_for_llm("uk")
        assert "open_app" in schema
        # Ukrainian description should be present
        assert "Відкрити" in schema
