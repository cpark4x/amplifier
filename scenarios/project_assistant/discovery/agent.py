"""Discovery phase agent - asks adaptive questions to deeply understand the project."""

import asyncio
from pathlib import Path
from typing import Any

from amplifier.ccsdk_toolkit import ClaudeSession, SessionOptions
from amplifier.ccsdk_toolkit.defensive import parse_llm_json
from amplifier.utils.logger import get_logger

logger = get_logger(__name__)


class DiscoveryAgent:
    """Asks adaptive questions to deeply understand project goals."""

    def __init__(self):
        """Initialize discovery agent."""
        self.system_prompt = """You are a project discovery expert who helps people clarify their project goals through thoughtful questioning.

Your role is to:
1. Ask ONE question at a time that helps understand the project better
2. Build on previous answers to ask increasingly specific follow-up questions
3. Assess how well you understand the project (0.0 to 1.0 understanding score)
4. Continue until you have a comprehensive understanding (score >= 0.85)

Key areas to explore:
- Project goals and desired outcomes
- Motivation (why this project matters)
- Timeline and constraints
- Available resources
- Success criteria
- Potential obstacles
- Past attempts or related experience

CRITICAL RULES:
1. NEVER ask the same question twice - review previous Q&A carefully
2. If a question was skipped (answer: "[skipped]"), ask a DIFFERENT question about a different topic
3. Build on information already provided - don't ask for info you already have
4. Your understanding_score should INCREASE as you get more answers, NEVER reset to 0
5. Be efficient - aim for 5-7 questions total, not 10+

CRITICAL: Provide helpful examples WITHOUT being leading
- Give 2-3 diverse examples to inspire thinking
- Examples should cover different possibilities
- Frame as "e.g." or "for instance" - not as recommendations
- Make it easy for users to answer without feeling overwhelmed

Good question format:
"What's your timeline for this project?
   e.g., '2 weeks', 'by end of year', 'flexible/no rush'"

Bad question format:
"What's your timeline?" (too open-ended, anxiety-inducing)

Adapt your questions based on:
- Project type (e.g., renovation vs personal development vs creative project)
- Answers already given
- Gaps in understanding

Return your response as JSON:
{
  "question": "The next question to ask with helpful examples",
  "examples": ["example 1", "example 2", "example 3"],
  "understanding_score": 0.75,
  "project_type": "kitchen_renovation",
  "reasoning": "Why you're asking this question",
  "done": false
}

Set "done": true when understanding_score >= 0.85"""

    async def ask_next_question(
        self, previous_qa: list[dict[str, str]], project_name: str
    ) -> dict[str, Any]:
        """Generate the next question based on previous Q&A."""
        context = self._build_context(previous_qa, project_name)

        options = SessionOptions(
            system_prompt=self.system_prompt,
            retry_attempts=2,
            timeout=60,
        )

        async with ClaudeSession(options) as session:
            response = await session.query(context)
            result = parse_llm_json(
                response.content,
                default={
                    "question": "What is the main goal of your project?",
                    "understanding_score": 0.0,
                    "project_type": "unknown",
                    "reasoning": "Starting with basics",
                    "done": False,
                },
            )

        return result

    def _build_context(self, previous_qa: list[dict[str, str]], project_name: str) -> str:
        """Build context string from previous Q&A."""
        if not previous_qa:
            return f'Project name: "{project_name}"\n\nThis is the first question. Start by understanding what the project is about.'

        context = f'Project name: "{project_name}"\n\nPrevious questions and answers:\n\n'
        for i, qa in enumerate(previous_qa, 1):
            context += f"Q{i}: {qa['question']}\n"
            context += f"A{i}: {qa['answer']}\n\n"

        context += "Based on these answers, what's the next most important question to ask?"
        return context

    async def synthesize_understanding(
        self, qa_pairs: list[dict[str, str]], project_name: str
    ) -> dict[str, Any]:
        """Synthesize all Q&A into a comprehensive understanding document."""
        system_prompt = """You are a project analyst who synthesizes discovery information into clear documentation.

Given a series of questions and answers about a project, create a comprehensive understanding document.

Return as JSON:
{
  "project_summary": "Clear 2-3 sentence summary of the project",
  "goals": ["Primary goal", "Secondary goal"],
  "motivation": "Why this project matters to the person",
  "timeline": "When they want to complete it",
  "resources": ["Available resource 1", "Available resource 2"],
  "constraints": ["Constraint 1", "Constraint 2"],
  "success_criteria": ["How they'll know it's successful"],
  "potential_obstacles": ["Obstacle 1", "Obstacle 2"],
  "project_type": "category of project"
}"""

        context = f'Project: "{project_name}"\n\nDiscovery Q&A:\n\n'
        for i, qa in enumerate(qa_pairs, 1):
            context += f"Q{i}: {qa['question']}\n"
            context += f"A{i}: {qa['answer']}\n\n"

        context += "Please synthesize this into a comprehensive understanding document."

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
                    "project_summary": "Project understanding synthesis",
                    "goals": [],
                    "motivation": "",
                    "timeline": "",
                    "resources": [],
                    "constraints": [],
                    "success_criteria": [],
                    "potential_obstacles": [],
                    "project_type": "unknown",
                },
            )

        return result
