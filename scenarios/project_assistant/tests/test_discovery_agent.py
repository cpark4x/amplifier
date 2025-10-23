"""Tests for discovery agent."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from scenarios.project_assistant.discovery.agent import DiscoveryAgent


@pytest.mark.asyncio
async def test_ask_first_question():
    """Test asking the first question."""
    agent = DiscoveryAgent()

    with patch("scenarios.project_assistant.discovery.agent.ClaudeSession") as mock_session:
        # Mock AI response
        mock_response = MagicMock()
        mock_response.content = '''{
            "question": "What is the main goal of your project?",
            "examples": ["renovate kitchen", "learn programming", "start a business"],
            "understanding_score": 0.1,
            "project_type": "unknown",
            "reasoning": "Starting with basics",
            "done": false
        }'''

        mock_session_instance = AsyncMock()
        mock_session_instance.query.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        result = await agent.ask_next_question([], "Test Project")

        assert result["question"] == "What is the main goal of your project?"
        assert "examples" in result
        assert len(result["examples"]) == 3
        assert result["understanding_score"] == 0.1
        assert result["done"] is False


@pytest.mark.asyncio
async def test_ask_followup_question():
    """Test asking a follow-up question with context."""
    agent = DiscoveryAgent()

    previous_qa = [
        {
            "question": "What is the main goal?",
            "answer": "Renovate my kitchen"
        }
    ]

    with patch("scenarios.project_assistant.discovery.agent.ClaudeSession") as mock_session:
        mock_response = MagicMock()
        mock_response.content = '''{
            "question": "What is your budget range?",
            "examples": ["under $5k", "$5k-$20k", "over $20k"],
            "understanding_score": 0.4,
            "project_type": "home_renovation",
            "reasoning": "Need to understand constraints",
            "done": false
        }'''

        mock_session_instance = AsyncMock()
        mock_session_instance.query.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        result = await agent.ask_next_question(previous_qa, "Kitchen Renovation")

        assert "budget" in result["question"].lower()
        assert result["understanding_score"] > 0.1
        assert result["project_type"] == "home_renovation"


@pytest.mark.asyncio
async def test_synthesize_understanding():
    """Test synthesizing Q&A into structured understanding."""
    agent = DiscoveryAgent()

    qa_pairs = [
        {"question": "What is your goal?", "answer": "Renovate kitchen"},
        {"question": "What is your budget?", "answer": "$10,000"},
        {"question": "What is your timeline?", "answer": "3 months"},
    ]

    with patch("scenarios.project_assistant.discovery.agent.ClaudeSession") as mock_session:
        mock_response = MagicMock()
        mock_response.content = '''{
            "project_summary": "Kitchen renovation with $10k budget in 3 months",
            "goals": ["Modernize kitchen", "Increase home value"],
            "motivation": "Improve cooking experience",
            "timeline": "3 months",
            "resources": ["$10,000 budget"],
            "constraints": ["Limited budget", "Time constraint"],
            "success_criteria": ["Functional kitchen", "Under budget"],
            "potential_obstacles": ["Contractor availability", "Supply chain"],
            "project_type": "home_renovation"
        }'''

        mock_session_instance = AsyncMock()
        mock_session_instance.query.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        result = await agent.synthesize_understanding(qa_pairs, "Kitchen Renovation")

        assert "project_summary" in result
        assert "goals" in result
        assert result["project_type"] == "home_renovation"
        assert len(result["goals"]) > 0


@pytest.mark.asyncio
async def test_ask_question_handles_malformed_json():
    """Test that agent handles malformed AI response gracefully."""
    agent = DiscoveryAgent()

    with patch("scenarios.project_assistant.discovery.agent.ClaudeSession") as mock_session:
        mock_response = MagicMock()
        mock_response.content = "This is not valid JSON"

        mock_session_instance = AsyncMock()
        mock_session_instance.query.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance

        result = await agent.ask_next_question([], "Test Project")

        # Should fallback to default
        assert result["question"] == "What is the main goal of your project?"
        assert result["understanding_score"] == 0.0
        assert result["done"] is False


def test_build_context_first_question():
    """Test building context for first question."""
    agent = DiscoveryAgent()
    context = agent._build_context([], "Test Project")

    assert "Test Project" in context
    assert "first question" in context


def test_build_context_with_history():
    """Test building context with Q&A history."""
    agent = DiscoveryAgent()

    qa_history = [
        {"question": "What is your goal?", "answer": "Build an app"},
        {"question": "What is your timeline?", "answer": "6 months"},
    ]

    context = agent._build_context(qa_history, "App Project")

    assert "App Project" in context
    assert "Build an app" in context
    assert "6 months" in context
    assert "Q1:" in context
    assert "A1:" in context
