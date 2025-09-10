import pytest
from handoff import generate_handoff, format_for_new_task, emit_delegation_event


def test_generate_handoff_validates_against_schema():
    handoff = generate_handoff(
        mode="test",
        message="Test message",
        context="Test context",
        scope="Test scope",
        completion_signal="Test signal",
        parent_context="Test parent",
        dependencies=["test dep"],
        superseding_statement="Test superseding"
    )
    assert handoff["mode"] == "test"
    assert "superseding_statement" in handoff
    assert len(handoff["dependencies"]) == 1


def test_format_for_new_task_produces_valid_xml():
    handoff = {
        "mode": "test",
        "message": "Test message"
    }
    formatted = format_for_new_task(handoff)
    assert "<new_task>" in formatted
    assert "<mode>test</mode>" in formatted
    assert "<message>Test message</message>" in formatted
    assert "</new_task>" in formatted


def test_emit_delegation_event():
    handoff = {"mode": "code", "message": "Test"}
    event = emit_delegation_event(handoff)
    assert event["event"] == "handoff_delegated"
    assert event["actor"] == "orchestrator"
    assert event["target"] == "code"
    assert "details" in event