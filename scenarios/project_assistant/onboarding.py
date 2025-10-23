"""Onboarding experience for first-time users."""

from pathlib import Path


def should_show_welcome(data_dir: Path) -> bool:
    """Check if this is the first time running the tool.

    Args:
        data_dir: Data directory

    Returns:
        True if welcome should be shown
    """
    welcome_file = data_dir / ".welcome_shown"
    return not welcome_file.exists()


def mark_welcome_shown(data_dir: Path) -> None:
    """Mark that welcome has been shown.

    Args:
        data_dir: Data directory
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    welcome_file = data_dir / ".welcome_shown"
    welcome_file.touch()


def show_welcome() -> bool:
    """Show welcome message and get user confirmation.

    Returns:
        True if user wants to continue, False otherwise
    """
    welcome_text = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🎯 Welcome to Project Assistant!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

I'm your AI project coach. I'll help you complete any
personal project through a structured 3-phase approach:

  1️⃣  DISCOVERY (5-10 minutes)
      I'll ask questions to deeply understand your project
      → Your goals, timeline, resources, constraints

  2️⃣  PLANNING (10-15 minutes)
      I'll research best practices and create a detailed plan
      → Multiple approaches, milestones, risk mitigation

  3️⃣  EXECUTION (ongoing)
      I'll track your progress and keep you motivated
      → Action items, check-ins, plan adjustments

💡 Tips:
   • Be specific in your answers - more detail = better plan
   • You can pause anytime and resume later
   • Type 'help' anytime to see available commands

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    print(welcome_text)

    while True:
        response = input("Ready to start? [y/n]: ").strip().lower()
        if response in ['y', 'yes']:
            print("\nGreat! Let's begin! 🚀\n")
            return True
        elif response in ['n', 'no']:
            print("\nNo problem! Run this command again when you're ready.")
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")


def show_phase_transition(from_phase: str, to_phase: str) -> None:
    """Show transition message between phases.

    Args:
        from_phase: Phase we're leaving
        to_phase: Phase we're entering
    """
    transitions = {
        ("discovery", "planning"): """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ✅ Discovery Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Great! I now understand your project. Next, I'll:
  • Research best practices for your project type
  • Generate a detailed proposal with options
  • Present it for your review and feedback

This will take about 10-15 minutes.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
        ("planning", "execution"): """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ✅ Planning Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Excellent! Your plan is approved. Now let's execute!

I'll help you:
  • Track concrete action items
  • Monitor your progress
  • Provide regular check-ins
  • Adapt the plan as needed

Let's make this happen! 💪
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""",
    }

    message = transitions.get((from_phase, to_phase), "")
    if message:
        print(message)


def show_discovery_intro(project_name: str) -> None:
    """Show introduction to discovery phase.

    Args:
        project_name: Name of the project
    """
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Phase 1: Discovery - "{project_name}"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Let's understand your project through conversation.
I'll ask questions until I have a clear picture of:
  • What you want to accomplish
  • Why it matters to you
  • What resources and constraints you have
  • How success looks

💡 During questions, you can:
   • Type your answer normally
   • Type 'skip' to skip a question
   • Type 'back' to revise previous answer
   • Type 'quit' to save and exit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
