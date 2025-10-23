"""Progress indicators for better UX during AI operations."""

import asyncio
import sys
from typing import Callable, TypeVar, Any

T = TypeVar('T')


class ProgressSpinner:
    """Animated spinner for long-running operations."""

    def __init__(self, message: str, estimated_seconds: int = 0):
        """Initialize spinner.

        Args:
            message: Message to display
            estimated_seconds: Estimated duration (0 = unknown)
        """
        self.message = message
        self.estimated_seconds = estimated_seconds
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.idx = 0
        self.running = False
        self.task = None

    async def _spin(self):
        """Run the spinner animation."""
        while self.running:
            spinner = self.spinner_chars[self.idx % len(self.spinner_chars)]

            if self.estimated_seconds > 0:
                time_msg = f" (~{self.estimated_seconds} seconds)"
            else:
                time_msg = ""

            sys.stdout.write(f'\r{spinner} {self.message}{time_msg}')
            sys.stdout.flush()

            await asyncio.sleep(0.1)
            self.idx += 1

    async def __aenter__(self):
        """Start the spinner."""
        self.running = True
        self.task = asyncio.create_task(self._spin())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Stop the spinner."""
        self.running = False
        if self.task:
            await self.task
        # Clear the line
        sys.stdout.write('\r' + ' ' * (len(self.message) + 50) + '\r')
        sys.stdout.flush()


async def with_progress(
    coroutine: Callable[..., Any],
    message: str,
    estimated_seconds: int = 0,
    *args,
    **kwargs
) -> Any:
    """Execute async function with progress spinner.

    Args:
        coroutine: Async function to execute
        message: Progress message to show
        estimated_seconds: Estimated duration
        *args: Arguments for coroutine
        **kwargs: Keyword arguments for coroutine

    Returns:
        Result from coroutine

    Example:
        result = await with_progress(
            agent.ask_question,
            "Generating next question",
            estimated_seconds=15,
            context="previous answers"
        )
    """
    async with ProgressSpinner(message, estimated_seconds):
        result = await coroutine(*args, **kwargs)

    return result


def show_progress_message(message: str, symbol: str = "✓"):
    """Show a completed progress message.

    Args:
        message: Message to display
        symbol: Symbol to show (✓, ✗, ⚠, etc.)
    """
    print(f"{symbol} {message}")
