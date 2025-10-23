#!/usr/bin/env python3
"""
Project Assistant - AI-powered project completion coach

Helps users complete personal projects through:
1. Discovery: Adaptive questioning to understand goals
2. Planning: Research and proposal generation
3. Execution: Action tracking and progress monitoring

Contract:
  Inputs: Project name, optional state directory
  Outputs: Completed project with full documentation
  Failures: Invalid state, API errors

Philosophy:
  - Ruthless simplicity: Three clear phases
  - User-centered: Adapts to their needs and pace
  - Progress-focused: Always moving forward
  - Supportive: Encouraging and realistic
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from amplifier.utils.logger import get_logger

from .discovery.agent import DiscoveryAgent
from .execution.agent import ExecutionAgent
from .planning.agent import PlanningAgent
from .state import CheckIn, Phase, ProjectState
from .onboarding import (
    mark_welcome_shown,
    should_show_welcome,
    show_discovery_intro,
    show_phase_transition,
    show_welcome,
)
from .progress_indicator import ProgressSpinner, show_progress_message
from .ui_helpers import (
    format_action_status,
    format_command_help,
    format_priority,
    progress_bar,
    show_progress_summary,
    suggest_command,
)
from .validation import ValidationError, validate_action_id, validate_project_name

logger = get_logger(__name__)


class ProjectAssistant:
    """Main orchestrator for project assistant."""

    def __init__(self, project_name: str, data_dir: Path):
        """Initialize project assistant."""
        self.project_name = project_name
        self.data_dir = data_dir
        self.project_dir = data_dir / project_name.replace(" ", "_")
        self.state: Optional[ProjectState] = None

        # Initialize agents
        self.discovery_agent = DiscoveryAgent()
        self.planning_agent = PlanningAgent()
        self.execution_agent = ExecutionAgent()

    def load_or_create_state(self) -> None:
        """Load existing state or create new project."""
        try:
            self.state = ProjectState.load(self.project_dir)
            logger.info(
                f"Loaded existing project: {self.project_name} (Phase: {self.state.current_phase.value})"
            )
        except FileNotFoundError:
            logger.info(f"Creating new project: {self.project_name}")
            self.state = ProjectState.create_new(self.project_name, self.project_dir)

    async def run_discovery_phase(self) -> None:
        """Run the discovery phase - ask questions until we understand the project."""
        show_discovery_intro(self.project_name)

        estimated_total_questions = 7  # Rough estimate

        while True:
            # Show progress
            num_asked = len(self.state.discovery.questions_asked)
            understanding_pct = self.state.discovery.understanding_score

            if num_asked > 0:
                progress = progress_bar(
                    int(understanding_pct * 10), 10, width=10
                )
                logger.info(
                    f"\n━━━ Question {num_asked + 1} of ~{estimated_total_questions} | Understanding: {understanding_pct:.0%} {progress}"
                )

            # Generate next question with spinner
            async with ProgressSpinner("Generating next question", estimated_seconds=10):
                result = await self.discovery_agent.ask_next_question(
                    self.state.discovery.questions_asked, self.project_name
                )

            self.state.discovery.understanding_score = result.get(
                "understanding_score", 0.0
            )
            self.state.discovery.project_type = result.get("project_type", "unknown")

            # Check if we're done
            if result.get("done", False):
                show_progress_message(
                    f"Discovery complete! Understanding score: {self.state.discovery.understanding_score:.0%}",
                    "✅"
                )
                break

            # Ask the question
            question = result["question"]
            logger.info(f"\nQ: {question}")

            # Show examples if provided
            if result.get("examples"):
                logger.info(f"   💡 e.g., {', '.join(result['examples'])}")

            logger.info("   (Type 'skip' to skip | 'back' to go back | 'quit' to save and exit)\n")

            answer = input("Your answer: ").strip()

            # Handle special commands
            if answer.lower() == 'quit':
                logger.info("\n💾 Saving progress...")
                self.state.save(self.project_dir)
                logger.info("✓ Progress saved. Resume anytime!")
                sys.exit(0)

            elif answer.lower() == 'skip':
                logger.info("⏭️  Skipping this question...")
                # Record the skip so AI knows not to ask again
                qa_pair = {"question": question, "answer": "[skipped]"}
                self.state.discovery.questions_asked.append(qa_pair)
                self.state.save(self.project_dir)
                continue

            elif answer.lower() == 'back':
                if len(self.state.discovery.questions_asked) > 0:
                    removed = self.state.discovery.questions_asked.pop()
                    logger.info(f"⏪ Going back. Previous question was: {removed['question']}")
                    self.state.save(self.project_dir)
                else:
                    logger.info("⚠️  No previous questions to go back to.")
                continue

            elif answer.lower() == 'enough':
                if self.state.discovery.understanding_score >= 0.6:
                    logger.info(
                        f"\n✓ Ending discovery early. Understanding: {self.state.discovery.understanding_score:.0%}"
                    )
                    break
                else:
                    logger.info(
                        f"⚠️  Need at least 60% understanding to end early (currently {self.state.discovery.understanding_score:.0%})"
                    )
                continue

            elif not answer:
                logger.info("⚠️  Please provide an answer, or type 'skip' to skip this question.")
                continue

            # Store Q&A
            qa_pair = {"question": question, "answer": answer}
            self.state.discovery.questions_asked.append(qa_pair)
            self.state.discovery.answers[f"q{len(self.state.discovery.questions_asked)}"] = answer

            # Save progress
            self.state.save(self.project_dir)

        # Synthesize understanding with spinner
        async with ProgressSpinner("Synthesizing your answers into a comprehensive understanding", estimated_seconds=20):
            understanding = await self.discovery_agent.synthesize_understanding(
                self.state.discovery.questions_asked, self.project_name
            )

        # Store structured synthesis in state
        self.state.discovery.synthesis = understanding

        # Save understanding document
        understanding_file = self.project_dir / "discovery_notes.md"
        understanding_md = self._format_understanding(understanding)
        understanding_file.write_text(understanding_md)

        show_progress_message(f"Understanding document saved to: {understanding_file.name}")

        # Update state
        self.state.discovery.completion_status = "completed"
        self.state.current_phase = Phase.PLANNING
        self.state.save(self.project_dir)

        # Show transition
        show_phase_transition("discovery", "planning")

    def _show_proposal_preview(self, proposal_md: str, proposal_file: Path) -> None:
        """Show proposal preview inline."""
        lines = proposal_md.split('\n')
        preview_lines = lines[:25]  # First 25 lines

        logger.info("\n" + "━" * 60)
        logger.info("📋 PROPOSAL PREVIEW")
        logger.info("━" * 60)
        for line in preview_lines:
            logger.info(line)

        if len(lines) > 25:
            logger.info(f"\n... ({len(lines) - 25} more lines)")

        logger.info("━" * 60)
        logger.info(f"Full proposal saved to: {proposal_file.name}\n")

    async def run_planning_phase(self) -> None:
        """Run the planning phase - research and create proposals."""
        logger.info("\n=== PLANNING PHASE ===")
        logger.info("Creating a detailed project proposal...\n")

        # Load structured understanding from state
        if not self.state.discovery.synthesis:
            logger.error("Discovery not completed. Run discovery phase first.")
            return

        # Use structured synthesis for better planning
        understanding = self.state.discovery.synthesis

        # Conduct research with spinner
        async with ProgressSpinner("Researching best practices and approaches", estimated_seconds=30):
            research_notes = await self.planning_agent.conduct_research(understanding)
        self.state.planning.research_notes = research_notes

        show_progress_message(f"Completed research ({len(research_notes)} insights)")

        # Generate proposal with spinner
        async with ProgressSpinner("Generating detailed project proposal", estimated_seconds=45):
            proposal = await self.planning_agent.generate_proposal(
                understanding, research_notes
            )
        self.state.planning.proposals.append(proposal)

        # Save proposal
        proposal_file = self.project_dir / "proposal.md"
        proposal_md = self._format_proposal(proposal)
        proposal_file.write_text(proposal_md)

        # Show inline preview
        self._show_proposal_preview(proposal_md, proposal_file)

        # Get feedback
        logger.info("Options:")
        logger.info("  'read' - Show full proposal")
        logger.info("  'approve' - Accept and proceed")
        logger.info("  'feedback <your thoughts>' - Request changes")
        logger.info("  'quit' - Save and exit\n")

        while True:
            choice = input("Your choice: ").strip()
            if not choice:
                continue

            if choice.lower() == "quit":
                logger.info("\n💾 Saving progress...")
                self.state.save(self.project_dir)
                logger.info("✓ Progress saved. Resume anytime!")
                sys.exit(0)

            elif choice.lower() == "read":
                logger.info("\n" + proposal_md)
                continue

            elif choice.lower() == "approve":
                logger.info("\n✅ Proposal approved!")
                self.state.planning.selected_approach = proposal
                break

            elif choice.lower().startswith("feedback"):
                feedback = choice[8:].strip()  # Remove "feedback" prefix
                if not feedback:
                    logger.info("⚠️  Please provide your feedback after 'feedback'")
                    logger.info("   Example: feedback I need a shorter timeline")
                    continue

                # Refine proposal with spinner
                async with ProgressSpinner("Refining proposal based on your feedback", estimated_seconds=30):
                    proposal = await self.planning_agent.refine_proposal(proposal, feedback)
                self.state.planning.proposals.append(proposal)

                # Save and show updated proposal
                proposal_md = self._format_proposal(proposal)
                proposal_file.write_text(proposal_md)
                self._show_proposal_preview(proposal_md, proposal_file)

                logger.info("Review the changes. Type 'approve' when ready, or provide more feedback.\n")

            else:
                logger.info("⚠️  Please type 'read', 'approve', 'feedback <text>', or 'quit'")

        # Update state
        self.state.planning.completion_status = "completed"
        self.state.current_phase = Phase.EXECUTION
        self.state.save(self.project_dir)

    async def run_execution_phase(self) -> None:
        """Run the execution phase - track actions and monitor progress."""
        logger.info("\n=== EXECUTION PHASE ===")
        logger.info("Let's get started on your project!\n")

        # Generate initial action items if needed
        if not self.state.execution.action_items:
            logger.info("Generating initial action items...")
            action_items = await self.execution_agent.generate_action_items(
                self.state.planning.selected_approach
            )
            self.state.execution.action_items = action_items
            self.state.save(self.project_dir)

            # Show action items
            logger.info("\n✓ Here are your initial action items:\n")
            for item in action_items:
                logger.info(f"  [{item.priority.upper()}] {item.description}")

        # Main execution loop
        logger.info("\n--- Execution Menu ---")
        logger.info("Commands:")
        logger.info("  checkin - Get progress update and encouragement")
        logger.info("  complete <id> - Mark action as completed")
        logger.info("  block <id> <reason> - Mark action as blocked")
        logger.info("  adjust - Request plan adjustment")
        logger.info("  status - View all actions")
        logger.info("  done - Mark project as completed")
        logger.info("  exit - Save and exit\n")

        while True:
            try:
                cmd = input(f"[{self.project_name}] > ").strip().lower()

                if not cmd:
                    continue

                if cmd == "exit":
                    self.state.save(self.project_dir)
                    logger.info("Progress saved. See you next time!")
                    break

                elif cmd == "status":
                    self._show_status()

                elif cmd == "checkin":
                    await self._do_checkin()

                elif cmd == "help":
                    logger.info(format_command_help())

                elif cmd.startswith("complete "):
                    parts = cmd.split(" ", 1)
                    if len(parts) < 2:
                        logger.info("Usage: complete <action-id>")
                        continue
                    action_id = parts[1]
                    self._complete_action(action_id)

                elif cmd.startswith("start "):
                    parts = cmd.split(" ", 1)
                    if len(parts) < 2:
                        logger.info("Usage: start <action-id>")
                        continue
                    action_id = parts[1]
                    self._start_action(action_id)

                elif cmd.startswith("block "):
                    parts = cmd.split(" ", 2)
                    if len(parts) < 3:
                        logger.info("Usage: block <action-id> <reason>")
                        continue
                    action_id, reason = parts[1], parts[2]
                    self._block_action(action_id, reason)

                elif cmd == "adjust":
                    await self._adjust_plan()

                elif cmd == "done":
                    self.state.current_phase = Phase.COMPLETED
                    self.state.save(self.project_dir)
                    logger.info("\n🎉 Congratulations on completing your project! 🎉")
                    break

                else:
                    # Try to suggest similar command
                    suggestion = suggest_command(cmd)
                    if suggestion:
                        logger.info(f"Unknown command: '{cmd}'. Did you mean '{suggestion}'?")
                    else:
                        logger.info(f"Unknown command: '{cmd}'. Type 'help' for available commands.")

            except KeyboardInterrupt:
                logger.info("\nInterrupted. Type 'exit' to save and quit.")
            except ValidationError as e:
                logger.error(f"Validation error: {e}")
            except Exception as e:
                logger.error(f"Error executing command: {e}")
                logger.info("Please try again or type 'exit' to quit.")

    def _show_status(self) -> None:
        """Show current action items status with progress bar."""
        # Count statuses
        completed = len([i for i in self.state.execution.action_items if i.status == "completed"])
        in_progress = len([i for i in self.state.execution.action_items if i.status == "in_progress"])
        pending = len([i for i in self.state.execution.action_items if i.status == "pending"])
        blocked = len([i for i in self.state.execution.action_items if i.status == "blocked"])

        # Show progress summary
        logger.info(show_progress_summary(completed, in_progress, pending, blocked))

        # Show individual items
        logger.info("--- Action Items ---")
        for item in self.state.execution.action_items:
            symbol, _ = format_action_status(item.status)
            priority_display = format_priority(item.priority)

            logger.info(f"{symbol} [{item.id}] {item.description} | {priority_display}")

            if item.estimated_duration:
                logger.info(f"   ⏱ Estimated: {item.estimated_duration}")
            if item.due_date:
                logger.info(f"   📅 Due: {item.due_date}")
            if item.dependencies:
                logger.info(f"   🔗 Depends on: {', '.join(item.dependencies)}")
            if item.notes:
                logger.info(f"   📝 Notes: {item.notes}")
            if item.tags:
                logger.info(f"   🏷 Tags: {', '.join(item.tags)}")

        logger.info("")

    def _complete_action(self, action_id: str) -> None:
        """Mark an action as completed."""
        try:
            valid_ids = [item.id for item in self.state.execution.action_items]
            validate_action_id(action_id, valid_ids)

            for item in self.state.execution.action_items:
                if item.id == action_id:
                    item.status = "completed"
                    item.completed_at = datetime.now().isoformat()
                    self.state.save(self.project_dir)
                    logger.info(f"✅ Marked '{item.description}' as completed!")
                    return
        except ValidationError as e:
            logger.error(str(e))

    def _start_action(self, action_id: str) -> None:
        """Mark an action as in-progress."""
        try:
            valid_ids = [item.id for item in self.state.execution.action_items]
            validate_action_id(action_id, valid_ids)

            for item in self.state.execution.action_items:
                if item.id == action_id:
                    item.status = "in_progress"
                    self.state.save(self.project_dir)
                    logger.info(f"▶️ Started working on '{item.description}'")
                    return
        except ValidationError as e:
            logger.error(str(e))

    def _block_action(self, action_id: str, reason: str) -> None:
        """Mark an action as blocked."""
        for item in self.state.execution.action_items:
            if item.id == action_id:
                item.status = "blocked"
                item.notes = reason
                self.state.save(self.project_dir)
                logger.info(f"Marked {action_id} as blocked: {reason}")
                return
        logger.info(f"Action {action_id} not found")

    async def _do_checkin(self) -> None:
        """Conduct a progress check-in."""
        logger.info("\nConducting progress check-in...")
        result = await self.execution_agent.conduct_check_in(
            self.state.execution.action_items, self.state.execution.check_ins
        )

        # Create check-in record
        completed_ids = [
            item.id
            for item in self.state.execution.action_items
            if item.status == "completed"
        ]
        blocked_items = [
            item.description
            for item in self.state.execution.action_items
            if item.status == "blocked"
        ]

        check_in = CheckIn(
            timestamp=datetime.now().isoformat(),
            progress_summary=result["progress_summary"],
            completed_actions=completed_ids,
            blockers=blocked_items,
            next_steps=result["suggested_next_steps"],
            morale_score=result.get("recommended_morale_score", 5),
        )
        self.state.execution.check_ins.append(check_in)
        self.state.save(self.project_dir)

        # Display check-in
        logger.info(f"\n{result['progress_summary']}\n")
        if result["completed_highlights"]:
            logger.info("✓ Great work on:")
            for highlight in result["completed_highlights"]:
                logger.info(f"  - {highlight}")
        if result["blockers_identified"]:
            logger.info("\n⚠ Blockers to address:")
            for blocker in result["blockers_identified"]:
                logger.info(f"  - {blocker}")
        if result["suggested_next_steps"]:
            logger.info("\n→ Suggested next steps:")
            for step in result["suggested_next_steps"]:
                logger.info(f"  - {step}")
        logger.info(f"\n{result['encouragement']}\n")

    async def _adjust_plan(self) -> None:
        """Request plan adjustments."""
        logger.info("\nWhat changes would you like to make to the plan?")
        user_input = input("Your feedback: ").strip()
        if not user_input:
            return

        logger.info("\nAnalyzing and suggesting adjustments...")
        result = await self.execution_agent.suggest_plan_adjustment(
            self.state.planning.selected_approach,
            self.state.execution.action_items,
            self.state.execution.check_ins,
            user_input,
        )

        if not result["adjustment_needed"]:
            logger.info(f"\n{result['reasoning']}")
            return

        logger.info(f"\n{result['reasoning']}\n")
        logger.info("Suggested changes:")
        for change in result["suggested_changes"]:
            logger.info(f"\n  {change['area'].upper()}:")
            logger.info(f"    Current: {change['current']}")
            logger.info(f"    Proposed: {change['proposed']}")
            logger.info(f"    Why: {change['rationale']}")

        approve = input("\nApprove these changes? (yes/no): ").strip().lower()
        if approve == "yes":
            adjustment_note = f"{datetime.now().isoformat()}: {result['reasoning']}"
            self.state.execution.plan_adjustments.append(adjustment_note)
            self.state.save(self.project_dir)
            logger.info("✓ Plan adjusted!")

    def _format_understanding(self, understanding: dict) -> str:
        """Format understanding document as markdown."""
        md = f"""# Project Understanding: {self.project_name}

## Summary
{understanding.get('project_summary', '')}

## Goals
"""
        for goal in understanding.get("goals", []):
            md += f"- {goal}\n"

        md += f"""
## Motivation
{understanding.get('motivation', '')}

## Timeline
{understanding.get('timeline', '')}

## Available Resources
"""
        for resource in understanding.get("resources", []):
            md += f"- {resource}\n"

        md += "\n## Constraints\n"
        for constraint in understanding.get("constraints", []):
            md += f"- {constraint}\n"

        md += "\n## Success Criteria\n"
        for criterion in understanding.get("success_criteria", []):
            md += f"- {criterion}\n"

        md += "\n## Potential Obstacles\n"
        for obstacle in understanding.get("potential_obstacles", []):
            md += f"- {obstacle}\n"

        return md

    def _format_proposal(self, proposal: dict) -> str:
        """Format proposal as markdown."""
        md = f"""# Project Proposal: {self.project_name}

## Recommended Approach
**Description:** {proposal.get('recommended_approach', {}).get('description', '')}

**Rationale:** {proposal.get('recommended_approach', {}).get('rationale', '')}

**Estimated Duration:** {proposal.get('recommended_approach', {}).get('estimated_duration', '')}

**Difficulty:** {proposal.get('recommended_approach', {}).get('difficulty_level', '')}

## Alternative Approaches
"""
        for alt in proposal.get("alternative_approaches", []):
            md += f"\n### {alt.get('name', 'Alternative')}\n"
            md += f"{alt.get('description', '')}\n\n"
            md += f"**Tradeoffs:** {alt.get('tradeoffs', '')}\n"

        md += "\n## Milestones\n"
        for milestone in proposal.get("milestones", []):
            md += f"\n### {milestone.get('name', '')}\n"
            md += f"{milestone.get('description', '')}\n\n"
            md += f"**Duration:** {milestone.get('estimated_duration', '')}\n\n"
            if milestone.get("dependencies"):
                md += "**Dependencies:**\n"
                for dep in milestone["dependencies"]:
                    md += f"- {dep}\n"

        return md

    async def run(self) -> None:
        """Run the project assistant."""
        # Show welcome for first-time users
        if should_show_welcome(self.data_dir):
            if not show_welcome():
                return  # User declined
            mark_welcome_shown(self.data_dir)

        self.load_or_create_state()

        # Run appropriate phase
        if self.state.current_phase == Phase.DISCOVERY:
            await self.run_discovery_phase()

        if self.state.current_phase == Phase.PLANNING:
            await self.run_planning_phase()

        if self.state.current_phase == Phase.EXECUTION:
            await self.run_execution_phase()

        if self.state.current_phase == Phase.COMPLETED:
            logger.info(f"\n✓ Project '{self.project_name}' is completed!")
            logger.info(f"All files saved in: {self.project_dir}")


@click.command()
@click.option(
    "--project",
    "-p",
    required=True,
    help="Project name",
)
@click.option(
    "--data-dir",
    "-d",
    type=click.Path(path_type=Path),
    default=Path(".data/project_assistant"),
    help="Data directory for project state",
)
def main(project: str, data_dir: Path) -> None:
    """Project Assistant - Complete your projects with AI coaching."""
    assistant = ProjectAssistant(project, data_dir)
    try:
        asyncio.run(assistant.run())
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted. Progress saved.")
        assistant.state.save(assistant.project_dir)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
