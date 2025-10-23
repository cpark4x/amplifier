"""Planning phase agent - conducts research and generates proposals."""

import asyncio
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class PlanningAgent:
    """Researches and creates detailed project proposals."""

    def __init__(self):
        """Initialize planning agent."""
        pass

    async def conduct_research(self, understanding: dict[str, Any]) -> list[str]:
        """Conduct research relevant to the project type."""
        system_prompt = """You are a research assistant who gathers relevant information for project planning.

Given project details, identify 3-5 key research areas and provide actionable insights for each.

Return as JSON:
{
  "research_notes": [
    "Research finding 1 with actionable insights",
    "Research finding 2 with actionable insights",
    ...
  ]
}"""

        context = f"""Project Summary: {understanding.get('project_summary', '')}
Project Type: {understanding.get('project_type', '')}
Goals: {', '.join(understanding.get('goals', []))}
Constraints: {', '.join(understanding.get('constraints', []))}
Timeline: {understanding.get('timeline', '')}

Based on this project, what research insights would be most valuable for planning?
Focus on: best practices, common pitfalls, recommended approaches, resource requirements, typical timelines."""

        options = SessionOptions(
            system_prompt=system_prompt,
            retry_attempts=2,
            timeout=90,
        )

        async with ClaudeSession(options) as session:
            response = await session.query(context)
            result = parse_llm_json(
                response.content,
                default={"research_notes": ["General research on project type"]},
            )

        return result.get("research_notes", [])

    async def generate_proposal(
        self,
        understanding: dict[str, Any],
        research_notes: list[str],
    ) -> dict[str, Any]:
        """Generate a detailed project proposal with options."""
        system_prompt = """You are a project planning expert who creates detailed, actionable proposals.

Create a comprehensive proposal that includes:
- Recommended approach with rationale
- Alternative approaches with tradeoffs
- Detailed milestones with timelines
- Resource requirements
- Risk mitigation strategies

Return as JSON:
{
  "recommended_approach": {
    "description": "Detailed description of the recommended approach",
    "rationale": "Why this approach is best for this project",
    "estimated_duration": "How long it will take",
    "difficulty_level": "Easy/Medium/Hard"
  },
  "alternative_approaches": [
    {
      "name": "Alternative approach name",
      "description": "What makes this different",
      "tradeoffs": "Pros and cons compared to recommended"
    }
  ],
  "milestones": [
    {
      "name": "Milestone 1",
      "description": "What needs to be accomplished",
      "estimated_duration": "Time estimate",
      "dependencies": ["What needs to be done first"],
      "success_criteria": ["How to know it's complete"]
    }
  ],
  "resources_needed": [
    {
      "type": "Resource category",
      "items": ["Specific resource 1", "Specific resource 2"],
      "estimated_cost": "Cost if applicable"
    }
  ],
  "risks_and_mitigations": [
    {
      "risk": "Potential problem",
      "likelihood": "High/Medium/Low",
      "impact": "High/Medium/Low",
      "mitigation": "How to prevent or handle it"
    }
  ]
}"""

        context = f"""Project Understanding:
{understanding}

Research Insights:
{chr(10).join(f'- {note}' for note in research_notes)}

Based on this understanding and research, create a comprehensive project proposal."""

        options = SessionOptions(
            system_prompt=system_prompt,
            retry_attempts=2,
            timeout=120,
        )

        async with ClaudeSession(options) as session:
            response = await session.query(context)
            result = parse_llm_json(
                response.content,
                default={
                    "recommended_approach": {
                        "description": "Proceed step by step",
                        "rationale": "Systematic approach",
                        "estimated_duration": "Unknown",
                        "difficulty_level": "Medium",
                    },
                    "alternative_approaches": [],
                    "milestones": [],
                    "resources_needed": [],
                    "risks_and_mitigations": [],
                },
            )

        return result

    async def refine_proposal(
        self,
        current_proposal: dict[str, Any],
        user_feedback: str,
    ) -> dict[str, Any]:
        """Refine the proposal based on user feedback."""
        system_prompt = """You are a project planner refining a proposal based on user feedback.

Update the proposal to address the user's concerns and preferences while maintaining comprehensiveness.

Return the updated proposal in the same JSON format as before."""

        context = f"""Current Proposal:
{current_proposal}

User Feedback:
{user_feedback}

Please update the proposal to address this feedback."""

        options = SessionOptions(
            system_prompt=system_prompt,
            retry_attempts=2,
            timeout=90,
        )

        async with ClaudeSession(options) as session:
            response = await session.query(context)
            result = parse_llm_json(response.content, default=current_proposal)

        return result
