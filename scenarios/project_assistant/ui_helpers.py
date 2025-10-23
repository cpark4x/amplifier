"""UI helper functions for better user experience."""


def progress_bar(completed: int, total: int, width: int = 40) -> str:
    """Generate a text-based progress bar.

    Args:
        completed: Number of completed items
        total: Total number of items
        width: Width of the progress bar in characters

    Returns:
        Progress bar string
    """
    if total == 0:
        return f"[{' ' * width}] 0%"

    percentage = completed / total
    filled = int(width * percentage)
    bar = "█" * filled + "░" * (width - filled)

    return f"[{bar}] {percentage:.0%}"


def format_action_status(status: str) -> tuple[str, str]:
    """Get symbol and color for action status.

    Args:
        status: Action status string

    Returns:
        Tuple of (symbol, status_display)
    """
    status_map = {
        "pending": ("○", "Pending"),
        "in_progress": ("◐", "In Progress"),
        "completed": ("●", "Completed"),
        "blocked": ("✗", "Blocked"),
    }

    return status_map.get(status, ("?", "Unknown"))


def format_priority(priority: str) -> str:
    """Format priority with visual indicator.

    Args:
        priority: Priority string (low/medium/high)

    Returns:
        Formatted priority string
    """
    priority_map = {
        "low": "🔵 Low",
        "medium": "🟡 Medium",
        "high": "🔴 High",
    }

    return priority_map.get(priority, priority)


def show_progress_summary(completed: int, in_progress: int, pending: int, blocked: int) -> str:
    """Create a progress summary string.

    Args:
        completed: Number of completed actions
        in_progress: Number of in-progress actions
        pending: Number of pending actions
        blocked: Number of blocked actions

    Returns:
        Formatted summary string
    """
    total = completed + in_progress + pending + blocked
    bar = progress_bar(completed, total)

    lines = [
        "",
        f"Progress: {bar}  ({completed}/{total} complete)",
        f"● Completed: {completed}  ◐ In Progress: {in_progress}  ○ Pending: {pending}  ✗ Blocked: {blocked}",
        "",
    ]

    return "\n".join(lines)


def format_command_help() -> str:
    """Format command help message.

    Returns:
        Formatted help string
    """
    return """
Available Commands:
  status              - View all action items and their status
  checkin             - Get progress update and encouragement
  complete <id>       - Mark an action as completed
  block <id> <reason> - Mark an action as blocked
  start <id>          - Mark an action as in-progress
  adjust              - Request plan adjustments
  help                - Show this help message
  done                - Mark project as completed
  exit                - Save and exit (resume later)
""".strip()


def suggest_command(invalid_cmd: str) -> str | None:
    """Suggest correct command for misspelled input.

    Args:
        invalid_cmd: The invalid command entered

    Returns:
        Suggested command or None
    """
    commands = ["status", "checkin", "complete", "block", "start", "adjust", "help", "done", "exit"]

    # Simple fuzzy matching - check if any command starts with the input
    for cmd in commands:
        if cmd.startswith(invalid_cmd.lower()):
            return cmd

    # Check edit distance for common typos
    if invalid_cmd.lower() in ["chckin", "chekin", "checkn"]:
        return "checkin"
    elif invalid_cmd.lower() in ["stat", "stats"]:
        return "status"
    elif invalid_cmd.lower() in ["comp", "complet"]:
        return "complete"

    return None
