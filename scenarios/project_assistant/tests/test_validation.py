"""Tests for validation module."""

import pytest

from scenarios.project_assistant.validation import (
    ValidationError,
    sanitize_user_input,
    validate_action_id,
    validate_phase_transition,
    validate_project_name,
    validate_understanding_synthesis,
)


def test_validate_project_name_valid():
    """Test valid project names."""
    assert validate_project_name("My Project") == "My Project"
    assert validate_project_name("  Whitespace  ") == "Whitespace"
    assert validate_project_name("a" * 100) == "a" * 100


def test_validate_project_name_empty():
    """Test empty project name raises error."""
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_project_name("")

    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_project_name("   ")


def test_validate_project_name_too_long():
    """Test project name length validation."""
    with pytest.raises(ValidationError, match="100 characters or less"):
        validate_project_name("a" * 101)


def test_validate_project_name_invalid_chars():
    """Test project name with invalid filesystem characters."""
    with pytest.raises(ValidationError, match="invalid characters"):
        validate_project_name("My Project<>")

    with pytest.raises(ValidationError, match="invalid characters"):
        validate_project_name("Project/Name")


def test_validate_action_id_valid():
    """Test valid action ID."""
    valid_ids = ["action-1", "action-2", "action-3"]
    assert validate_action_id("action-1", valid_ids) == "action-1"
    assert validate_action_id("action-3", valid_ids) == "action-3"


def test_validate_action_id_invalid():
    """Test invalid action ID."""
    valid_ids = ["action-1", "action-2"]

    with pytest.raises(ValidationError, match="not found"):
        validate_action_id("action-99", valid_ids)

    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_action_id("", valid_ids)


def test_validate_phase_transition_valid():
    """Test valid phase transitions."""
    # Should not raise errors
    validate_phase_transition("discovery", "planning")
    validate_phase_transition("planning", "execution")
    validate_phase_transition("execution", "completed")


def test_validate_phase_transition_invalid():
    """Test invalid phase transitions."""
    with pytest.raises(ValidationError, match="Cannot transition"):
        validate_phase_transition("discovery", "execution")  # Skip planning

    with pytest.raises(ValidationError, match="Cannot transition"):
        validate_phase_transition("completed", "planning")  # Go backwards

    with pytest.raises(ValidationError, match="Cannot transition"):
        validate_phase_transition("completed", "completed")  # No transitions from completed


def test_validate_understanding_synthesis_valid():
    """Test valid synthesis."""
    synthesis = {
        "project_summary": "Test summary",
        "goals": ["Goal 1", "Goal 2"],
        "motivation": "Because reasons",
    }
    # Should not raise error
    validate_understanding_synthesis(synthesis)


def test_validate_understanding_synthesis_missing_fields():
    """Test synthesis with missing required fields."""
    with pytest.raises(ValidationError, match="missing required fields"):
        validate_understanding_synthesis({"motivation": "test"})  # Missing summary and goals

    with pytest.raises(ValidationError, match="missing required fields"):
        validate_understanding_synthesis({"project_summary": "test"})  # Missing goals


def test_sanitize_user_input():
    """Test user input sanitization."""
    assert sanitize_user_input("  test input  ") == "test input"
    assert sanitize_user_input("normal input") == "normal input"


def test_sanitize_user_input_too_long():
    """Test input length validation."""
    with pytest.raises(ValidationError, match="too long"):
        sanitize_user_input("a" * 10001)
