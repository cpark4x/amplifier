"""Integration tests for project assistant workflow."""

import tempfile
from pathlib import Path

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from scenarios.project_assistant.state import Phase, ProjectState


@pytest.mark.asyncio
async def test_discovery_to_planning_transition():
    """Test transitioning from discovery to planning phase."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"

        # Create state in discovery
        state = ProjectState.create_new("Test Project", project_dir)
        assert state.current_phase == Phase.DISCOVERY

        # Simulate discovery completion
        state.discovery.questions_asked = [
            {"question": "What is your goal?", "answer": "Build an app"},
            {"question": "What is your timeline?", "answer": "6 months"},
        ]
        state.discovery.understanding_score = 0.9
        state.discovery.project_type = "software"
        state.discovery.synthesis = {
            "project_summary": "Build an app in 6 months",
            "goals": ["Create MVP", "Launch to users"],
        }
        state.discovery.completion_status = "completed"

        # Transition to planning
        state.current_phase = Phase.PLANNING
        state.save(project_dir)

        # Load and verify
        loaded_state = ProjectState.load(project_dir)
        assert loaded_state.current_phase == Phase.PLANNING
        assert loaded_state.discovery.understanding_score == 0.9
        assert loaded_state.discovery.synthesis["project_summary"] == "Build an app in 6 months"


@pytest.mark.asyncio
async def test_planning_to_execution_transition():
    """Test transitioning from planning to execution phase."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"

        # Create state and move to planning
        state = ProjectState.create_new("Test Project", project_dir)
        state.current_phase = Phase.PLANNING

        # Simulate planning completion
        state.planning.proposals = [
            {
                "title": "Proposal 1",
                "description": "Build with React",
                "steps": ["Setup", "Develop", "Test"],
            }
        ]
        state.planning.selected_approach = {
            "title": "Proposal 1",
            "description": "Build with React",
        }
        state.planning.completion_status = "completed"

        # Transition to execution
        state.current_phase = Phase.EXECUTION
        state.save(project_dir)

        # Load and verify
        loaded_state = ProjectState.load(project_dir)
        assert loaded_state.current_phase == Phase.EXECUTION
        assert len(loaded_state.planning.proposals) == 1
        assert loaded_state.planning.selected_approach["title"] == "Proposal 1"


@pytest.mark.asyncio
async def test_full_workflow_state_persistence():
    """Test state persistence across all phases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"

        # Phase 1: Discovery
        state = ProjectState.create_new("Full Test", project_dir)
        state.discovery.questions_asked = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]
        state.discovery.understanding_score = 0.85
        state.save(project_dir)

        # Phase 2: Planning
        state = ProjectState.load(project_dir)
        state.current_phase = Phase.PLANNING
        state.planning.proposals = [{"title": "Plan A"}]
        state.save(project_dir)

        # Phase 3: Execution
        state = ProjectState.load(project_dir)
        state.current_phase = Phase.EXECUTION

        from scenarios.project_assistant.state import ActionItem
        from datetime import datetime

        state.execution.action_items = [
            ActionItem(
                id="action-1",
                description="First action",
                status="completed",
                priority="high",
                created_at=datetime.now().isoformat(),
            )
        ]
        state.save(project_dir)

        # Final verification
        final_state = ProjectState.load(project_dir)
        assert final_state.current_phase == Phase.EXECUTION
        assert len(final_state.discovery.questions_asked) == 2
        assert len(final_state.planning.proposals) == 1
        assert len(final_state.execution.action_items) == 1
        assert final_state.execution.action_items[0].status == "completed"


@pytest.mark.asyncio
async def test_skip_tracking_prevents_repeated_questions():
    """Test that skipped questions are tracked to prevent repeats."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"

        state = ProjectState.create_new("Skip Test", project_dir)

        # User skips a question
        state.discovery.questions_asked.append({
            "question": "What is your budget?",
            "answer": "[skipped]"
        })
        state.save(project_dir)

        # Load state
        loaded_state = ProjectState.load(project_dir)

        # Verify skipped question is in history
        assert len(loaded_state.discovery.questions_asked) == 1
        assert loaded_state.discovery.questions_asked[0]["answer"] == "[skipped]"

        # AI should see this in context and not ask again
        questions_asked = [qa["question"] for qa in loaded_state.discovery.questions_asked]
        assert "What is your budget?" in questions_asked


@pytest.mark.asyncio
async def test_action_item_dependencies():
    """Test action items with dependencies."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"

        state = ProjectState.create_new("Dependency Test", project_dir)
        state.current_phase = Phase.EXECUTION

        from scenarios.project_assistant.state import ActionItem
        from datetime import datetime

        # Create dependent actions
        action1 = ActionItem(
            id="action-1",
            description="Setup environment",
            status="completed",
            created_at=datetime.now().isoformat(),
        )

        action2 = ActionItem(
            id="action-2",
            description="Install dependencies",
            status="in_progress",
            dependencies=["action-1"],
            created_at=datetime.now().isoformat(),
        )

        action3 = ActionItem(
            id="action-3",
            description="Run tests",
            status="pending",
            dependencies=["action-2"],
            created_at=datetime.now().isoformat(),
        )

        state.execution.action_items = [action1, action2, action3]
        state.save(project_dir)

        # Load and verify dependency chain
        loaded_state = ProjectState.load(project_dir)
        items = {item.id: item for item in loaded_state.execution.action_items}

        assert items["action-1"].status == "completed"
        assert items["action-2"].dependencies == ["action-1"]
        assert items["action-3"].dependencies == ["action-2"]

        # Verify only action-2 can proceed (action-1 is complete)
        # action-3 must wait for action-2
        assert items["action-2"].status == "in_progress"
        assert items["action-3"].status == "pending"
