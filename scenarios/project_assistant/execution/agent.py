"""Execution phase agent - tracks actions and monitors progress."""

import asyncio
from datetime import datetime
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.utils.logger import get_logger

from ..state import ActionItem, CheckIn

logger = get_logger(__name__)


class ExecutionAgent:
    """Manages action items and progress tracking."""

    def __init__(self):
        """Initialize execution agent."""
        pass

    async def generate_action_items(
        self, proposal: dict[str, Any]
    ) -> list[ActionItem]:
        """Generate concrete action items from the proposal."""
        system_prompt = """You are a project manager breaking down a proposal into actionable tasks.

Create specific, concrete action items that can be tracked and completed.
Each action should be:
- Specific and measurable
- Achievable in a reasonable timeframe
- Properly prioritized

Return as JSON:
{
  "action_items": [
    {
      "description": "Specific action to take",
      "priority": "high|medium|low",
      "estimated_duration": "How long it will take"
    }
  ]
}"""

        context = f"""Project Proposal:
{proposal}

Generate 5-10 initial action items to get this project started.
Focus on immediate next steps based on the first milestone."""

        options = SessionOptions(
            system_prompt=system_prompt,
            retry_attempts=2,
            timeout=60,
        )

        async with ClaudeSession(options) as session:
            response = await session.query(context)
            result = parse_llm_json(
                response.content, default={"action_items": []}
            )

        # Convert to ActionItem objects
        action_items = []
        now = datetime.now().isoformat()
        for i, item_data in enumerate(result.get("action_items", []), 1):
            action_items.append(
                ActionItem(
                    id=f"action-{i}",
                    description=item_data.get("description", ""),
                    priority=item_data.get("priority", "medium"),
                    created_at=now,
                )
            )

        return action_items

    async def conduct_check_in(
        self,
        action_items: list[ActionItem],
        previous_check_ins: list[CheckIn],
    ) -> dict[str, Any]:
        """Conduct a progress check-in."""
        system_prompt = """You are a supportive project coach checking in on progress.

Review the current state of action items and provide:
- Progress summary
- Celebration of completed items
- Help with blockers
- Suggested next steps
- Encouragement

Return as JSON:
{
  "progress_summary": "Overall progress assessment",
  "completed_highlights": ["Notable completion 1"],
  "blockers_identified": ["Blocker 1 if any"],
  "suggested_next_steps": ["Next step 1", "Next step 2"],
  "encouragement": "Motivational message",
  "recommended_morale_score": 7
}"""

        # Build current state
        total = len(action_items)
        completed = len([a for a in action_items if a.status == "completed"])
        in_progress = len([a for a in action_items if a.status == "in_progress"])
        blocked = len([a for a in action_items if a.status == "blocked"])

        context = f"""Progress Overview:
Total actions: {total}
Completed: {completed}
In progress: {in_progress}
Blocked: {blocked}
Pending: {total - completed - in_progress - blocked}

Action Items Status:
"""
        for item in action_items:
            context += f"\n[{item.status.upper()}] {item.description}"
            if item.notes:
                context += f"\n  Notes: {item.notes}"

        if previous_check_ins:
            context += "\n\nLast Check-in:\n"
            last = previous_check_ins[-1]
            context += f"Date: {last.timestamp}\n"
            context += f"Summary: {last.progress_summary}\n"

        context += "\n\nProvide an encouraging check-in assessment with actionable next steps."

        options = SessionOptions(
            system_prompt=system_prompt,
            retry_attempts=2,
            timeout=60,
        )

        async with ClaudeSession(options) as session:
            response = await session.query(context)
            result = parse_llm_json(
                response.content,
                default={
                    "progress_summary": "Making progress",
                    "completed_highlights": [],
                    "blockers_identified": [],
                    "suggested_next_steps": [],
                    "encouragement": "Keep going!",
                    "recommended_morale_score": 5,
                },
            )

        return result

    async def suggest_plan_adjustment(
        self,
        original_proposal: dict[str, Any],
        action_items: list[ActionItem],
        check_ins: list[CheckIn],
        user_input: str,
    ) -> dict[str, Any]:
        """Suggest adjustments to the plan based on progress and feedback."""
        system_prompt = """You are a project advisor helping adapt a plan based on real-world progress.

Analyze the situation and suggest specific adjustments to:
- Timeline
- Approach
- Resources
- Milestones

Be realistic and supportive. Sometimes plans need to change.

Return as JSON:
{
  "adjustment_needed": true,
  "reasoning": "Why this adjustment makes sense",
  "suggested_changes": [
    {
      "area": "timeline|approach|resources|milestones",
      "current": "What it is now",
      "proposed": "What it should be",
      "rationale": "Why this change"
    }
  ],
  "updated_next_steps": ["Revised action 1", "Revised action 2"]
}"""

        # Build context
        completed_count = len([a for a in action_items if a.status == "completed"])
        blocked_count = len([a for a in action_items if a.status == "blocked"])

        context = f"""Original Proposal:
{original_proposal}

Current Progress:
- Total actions: {len(action_items)}
- Completed: {completed_count}
- Blocked: {blocked_count}

Recent Check-ins:
"""
        for ci in check_ins[-3:]:  # Last 3 check-ins
            context += f"\n{ci.timestamp}: {ci.progress_summary}"
            if ci.blockers:
                context += f"\n  Blockers: {', '.join(ci.blockers)}"

        context += f"\n\nUser Input:\n{user_input}"
        context += "\n\nShould we adjust the plan? If so, what specific changes do you recommend?"

        options = SessionOptions(
            system_prompt=system_prompt,
            retry_attempts=2,
            timeout=90,
        )

        async with ClaudeSession(options) as session:
            response = await session.query(context)
            result = parse_llm_json(
                response.content,
                default={
                    "adjustment_needed": False,
                    "reasoning": "Current plan still viable",
                    "suggested_changes": [],
                    "updated_next_steps": [],
                },
            )

        return result
