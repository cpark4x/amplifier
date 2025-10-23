"""Tests for state management."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

from scenarios.project_assistant.state import (
    ActionItem,
    CheckIn,
    DiscoveryData,
    ExecutionData,
    Phase,
    PlanningData,
    ProjectState,
)


def test_project_state_create():
    """Test creating a new project state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"
        state = ProjectState.create_new("Test Project", project_dir)

        assert state.project_name == "Test Project"
        assert state.current_phase == Phase.DISCOVERY
        assert (project_dir / "state.json").exists()


def test_project_state_save_load():
    """Test saving and loading project state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"

        # Create and save
        state = ProjectState.create_new("Test Project", project_dir)
        state.discovery.questions_asked.append({
            "question": "What is your goal?",
            "answer": "Complete the project"
        })
        state.discovery.understanding_score = 0.5
        state.save(project_dir)

        # Load and verify
        loaded_state = ProjectState.load(project_dir)
        assert loaded_state.project_name == "Test Project"
        assert loaded_state.discovery.understanding_score == 0.5
        assert len(loaded_state.discovery.questions_asked) == 1


def test_action_item_creation():
    """Test creating action items."""
    item = ActionItem(
        id="test-1",
        description="Complete task",
        priority="high",
        created_at=datetime.now().isoformat(),
        estimated_duration="2 hours",
        dependencies=["test-0"],
        tags=["urgent"],
    )

    assert item.id == "test-1"
    assert item.status == "pending"
    assert item.priority == "high"
    assert item.estimated_duration == "2 hours"
    assert item.dependencies == ["test-0"]
    assert item.tags == ["urgent"]


def test_check_in_creation():
    """Test creating check-in records."""
    check_in = CheckIn(
        timestamp=datetime.now().isoformat(),
        progress_summary="Good progress",
        completed_actions=["action-1"],
        blockers=[],
        next_steps=["action-2"],
        morale_score=8,
    )

    assert check_in.progress_summary == "Good progress"
    assert check_in.morale_score == 8
    assert len(check_in.completed_actions) == 1


def test_phase_transitions():
    """Test phase transitions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"
        state = ProjectState.create_new("Test Project", project_dir)

        # Start in discovery
        assert state.current_phase == Phase.DISCOVERY

        # Move to planning
        state.current_phase = Phase.PLANNING
        state.save(project_dir)

        # Load and verify
        loaded_state = ProjectState.load(project_dir)
        assert loaded_state.current_phase == Phase.PLANNING

        # Move to execution
        loaded_state.current_phase = Phase.EXECUTION
        loaded_state.save(project_dir)

        # Final load and verify
        final_state = ProjectState.load(project_dir)
        assert final_state.current_phase == Phase.EXECUTION
