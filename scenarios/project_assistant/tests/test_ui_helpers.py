"""Tests for UI helper utilities."""

from scenarios.project_assistant.ui_helpers import (
    format_action_status,
    format_command_help,
    format_priority,
    progress_bar,
    show_progress_summary,
    suggest_command,
)


def test_progress_bar_empty():
    """Test progress bar with no progress."""
    result = progress_bar(0, 10, width=10)
    assert "0%" in result
    assert "░" in result
    assert "█" not in result


def test_progress_bar_partial():
    """Test progress bar with partial progress."""
    result = progress_bar(5, 10, width=10)
    assert "50%" in result
    assert "█" in result
    assert "░" in result


def test_progress_bar_complete():
    """Test progress bar with full progress."""
    result = progress_bar(10, 10, width=10)
    assert "100%" in result
    assert "█" in result
    assert "░" not in result


def test_progress_bar_zero_total():
    """Test progress bar handles zero total."""
    result = progress_bar(0, 0, width=10)
    assert "0%" in result
    # When total is 0, it shows spaces not the filled/empty symbols
    assert "[" in result and "]" in result


def test_format_priority():
    """Test priority formatting with colors."""
    assert "🔴" in format_priority("high")
    assert "🟡" in format_priority("medium")
    assert "🔵" in format_priority("low")
    assert format_priority("unknown") == "unknown"  # Returns as-is


def test_format_action_status():
    """Test action status formatting."""
    symbol, display = format_action_status("pending")
    assert symbol == "○"
    assert display == "Pending"

    symbol, display = format_action_status("in_progress")
    assert symbol == "◐"
    assert display == "In Progress"

    symbol, display = format_action_status("completed")
    assert symbol == "●"
    assert display == "Completed"

    symbol, display = format_action_status("blocked")
    assert symbol == "✗"
    assert display == "Blocked"


def test_show_progress_summary():
    """Test progress summary formatting."""
    result = show_progress_summary(5, 2, 3, 1)
    assert "5/11" in result or "5 / 11" in result  # Completed out of total
    assert "●" in result  # Completed symbol
    assert "◐" in result  # In progress symbol
    assert "○" in result  # Pending symbol
    assert "✗" in result  # Blocked symbol


def test_format_command_help():
    """Test command help formatting."""
    help_text = format_command_help()
    assert "status" in help_text
    assert "checkin" in help_text
    assert "complete" in help_text
    assert "help" in help_text


def test_suggest_command_prefix_match():
    """Test command suggestion with prefix match."""
    assert suggest_command("sta") == "status"
    assert suggest_command("che") == "checkin"
    assert suggest_command("com") == "complete"


def test_suggest_command_typo():
    """Test command suggestion with common typo."""
    assert suggest_command("chckin") == "checkin"
    assert suggest_command("chekin") == "checkin"
    assert suggest_command("stat") == "status"  # Prefix match


def test_suggest_command_no_match():
    """Test command suggestion with no match."""
    assert suggest_command("xyz") is None
    assert suggest_command("invalidcmd") is None
