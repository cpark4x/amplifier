"""Validation utilities for project assistant."""

from pathlib import Path
from typing import Any


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_project_name(name: str) -> str:
    """Validate and sanitize project name.

    Args:
        name: Raw project name from user

    Returns:
        Sanitized project name

    Raises:
        ValidationError: If name is invalid
    """
    if not name or not name.strip():
        raise ValidationError("Project name cannot be empty")

    name = name.strip()

    if len(name) > 100:
        raise ValidationError("Project name must be 100 characters or less")

    # Check for invalid filesystem characters
    invalid_chars = set('<>:"/\\|?*')
    if any(c in invalid_chars for c in name):
        raise ValidationError(f"Project name contains invalid characters: {invalid_chars}")

    return name


def validate_action_id(action_id: str, valid_ids: list[str]) -> str:
    """Validate action ID exists.

    Args:
        action_id: ID to validate
        valid_ids: List of valid IDs

    Returns:
        Valid action ID

    Raises:
        ValidationError: If ID doesn't exist
    """
    if not action_id:
        raise ValidationError("Action ID cannot be empty")

    if action_id not in valid_ids:
        raise ValidationError(
            f"Action '{action_id}' not found. Valid IDs: {', '.join(valid_ids[:5])}"
            + ("..." if len(valid_ids) > 5 else "")
        )

    return action_id


def validate_phase_transition(current: str, next_phase: str) -> None:
    """Validate phase transition is valid.

    Args:
        current: Current phase
        next_phase: Target phase

    Raises:
        ValidationError: If transition is invalid
    """
    valid_transitions = {
        "discovery": ["planning"],
        "planning": ["execution"],
        "execution": ["completed"],
        "completed": []  # No transitions from completed
    }

    if next_phase not in valid_transitions.get(current, []):
        raise ValidationError(
            f"Cannot transition from {current} to {next_phase}. "
            f"Valid next phases: {valid_transitions.get(current, [])}"
        )


def validate_understanding_synthesis(synthesis: dict[str, Any]) -> None:
    """Validate understanding synthesis has required fields.

    Args:
        synthesis: Synthesis dictionary from AI

    Raises:
        ValidationError: If required fields missing
    """
    required_fields = ["project_summary", "goals"]
    missing = [f for f in required_fields if not synthesis.get(f)]

    if missing:
        raise ValidationError(
            f"Understanding synthesis missing required fields: {', '.join(missing)}"
        )


def sanitize_user_input(user_input: str, max_length: int = 10000) -> str:
    """Sanitize user input.

    Args:
        user_input: Raw user input
        max_length: Maximum allowed length

    Returns:
        Sanitized input

    Raises:
        ValidationError: If input is too long
    """
    if len(user_input) > max_length:
        raise ValidationError(
            f"Input too long ({len(user_input)} chars). Maximum: {max_length}"
        )

    return user_input.strip()
