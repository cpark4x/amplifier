"""State management for Project Assistant.

Handles persistence of project data across phases and sessions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
import json


class Phase(str, Enum):
    """Project phases."""

    DISCOVERY = "discovery"
    PLANNING = "planning"
    EXECUTION = "execution"
    COMPLETED = "completed"


@dataclass
class DiscoveryData:
    """Data collected during discovery phase."""

    questions_asked: list[dict[str, str]] = field(default_factory=list)
    answers: dict[str, Any] = field(default_factory=dict)
    understanding_score: float = 0.0
    project_type: str = ""
    synthesis: dict[str, Any] = field(default_factory=dict)  # Structured understanding from AI
    completion_status: str = "in_progress"


@dataclass
class PlanningData:
    """Data from planning phase."""

    research_notes: list[str] = field(default_factory=list)
    proposals: list[dict[str, Any]] = field(default_factory=list)
    selected_approach: dict[str, Any] = field(default_factory=dict)
    milestones: list[dict[str, Any]] = field(default_factory=list)
    completion_status: str = "in_progress"


@dataclass
class ActionItem:
    """A trackable action item."""

    id: str
    description: str
    status: str = "pending"  # pending, in_progress, completed, blocked
    priority: str = "medium"  # low, medium, high
    created_at: str = ""
    completed_at: str = ""
    notes: str = ""
    estimated_duration: str = ""  # e.g., "2 hours", "3 days"
    dependencies: list[str] = field(default_factory=list)  # IDs of actions this depends on
    tags: list[str] = field(default_factory=list)  # Categories/labels
    due_date: str = ""  # ISO format date


@dataclass
class CheckIn:
    """A progress check-in record."""

    timestamp: str
    progress_summary: str
    completed_actions: list[str]
    blockers: list[str]
    next_steps: list[str]
    morale_score: int = 5  # 1-10


@dataclass
class ExecutionData:
    """Data from execution phase."""

    action_items: list[ActionItem] = field(default_factory=list)
    check_ins: list[CheckIn] = field(default_factory=list)
    plan_adjustments: list[str] = field(default_factory=list)
    completion_status: str = "in_progress"


@dataclass
class ProjectState:
    """Complete project state."""

    project_name: str
    current_phase: Phase
    created_at: str
    updated_at: str
    discovery: DiscoveryData = field(default_factory=DiscoveryData)
    planning: PlanningData = field(default_factory=PlanningData)
    execution: ExecutionData = field(default_factory=ExecutionData)

    @classmethod
    def load(cls, project_dir: Path) -> "ProjectState":
        """Load project state from disk."""
        state_file = project_dir / "state.json"
        if not state_file.exists():
            raise FileNotFoundError(f"State file not found: {state_file}")

        with open(state_file) as f:
            data = json.load(f)

        # Reconstruct nested dataclasses
        discovery = DiscoveryData(**data.get("discovery", {}))
        planning = PlanningData(**data.get("planning", {}))

        # Reconstruct action items
        execution_data = data.get("execution", {})
        action_items = [
            ActionItem(**item) for item in execution_data.get("action_items", [])
        ]
        check_ins = [CheckIn(**ci) for ci in execution_data.get("check_ins", [])]
        execution = ExecutionData(
            action_items=action_items,
            check_ins=check_ins,
            plan_adjustments=execution_data.get("plan_adjustments", []),
            completion_status=execution_data.get("completion_status", "in_progress"),
        )

        return cls(
            project_name=data["project_name"],
            current_phase=Phase(data["current_phase"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            discovery=discovery,
            planning=planning,
            execution=execution,
        )

    def save(self, project_dir: Path) -> None:
        """Save project state to disk."""
        project_dir.mkdir(parents=True, exist_ok=True)
        state_file = project_dir / "state.json"

        self.updated_at = datetime.now().isoformat()

        # Convert to dict for JSON serialization
        data = {
            "project_name": self.project_name,
            "current_phase": self.current_phase.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "discovery": {
                "questions_asked": self.discovery.questions_asked,
                "answers": self.discovery.answers,
                "understanding_score": self.discovery.understanding_score,
                "project_type": self.discovery.project_type,
                "synthesis": self.discovery.synthesis,
                "completion_status": self.discovery.completion_status,
            },
            "planning": {
                "research_notes": self.planning.research_notes,
                "proposals": self.planning.proposals,
                "selected_approach": self.planning.selected_approach,
                "milestones": self.planning.milestones,
                "completion_status": self.planning.completion_status,
            },
            "execution": {
                "action_items": [
                    {
                        "id": item.id,
                        "description": item.description,
                        "status": item.status,
                        "priority": item.priority,
                        "created_at": item.created_at,
                        "completed_at": item.completed_at,
                        "notes": item.notes,
                        "estimated_duration": item.estimated_duration,
                        "dependencies": item.dependencies,
                        "tags": item.tags,
                        "due_date": item.due_date,
                    }
                    for item in self.execution.action_items
                ],
                "check_ins": [
                    {
                        "timestamp": ci.timestamp,
                        "progress_summary": ci.progress_summary,
                        "completed_actions": ci.completed_actions,
                        "blockers": ci.blockers,
                        "next_steps": ci.next_steps,
                        "morale_score": ci.morale_score,
                    }
                    for ci in self.execution.check_ins
                ],
                "plan_adjustments": self.execution.plan_adjustments,
                "completion_status": self.execution.completion_status,
            },
        }

        with open(state_file, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def create_new(cls, project_name: str, project_dir: Path) -> "ProjectState":
        """Create a new project state."""
        now = datetime.now().isoformat()
        state = cls(
            project_name=project_name,
            current_phase=Phase.DISCOVERY,
            created_at=now,
            updated_at=now,
        )
        state.save(project_dir)
        return state
