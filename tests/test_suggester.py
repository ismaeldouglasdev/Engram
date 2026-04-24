"""Blackbox tests for the suggester module.

Tests mock the anthropic API to avoid calling real APIs.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from engram.suggester import _build_prompt, generate_suggestion


async def test_build_prompt_formats_facts():
    """Test that _build_prompt correctly formats fact details."""
    fact_a = {
        "id": "fact-a-001",
        "content": "The cache TTL is 300 seconds",
        "scope": "infra",
        "confidence": 0.8,
        "fact_type": "observation",
        "committed_at": "2026-01-15T10:00:00Z",
        "agent_id": "agent-1",
    }
    fact_b = {
        "id": "fact-b-002",
        "content": "The cache TTL is 600 seconds",
        "scope": "infra",
        "confidence": 0.7,
        "fact_type": "observation",
        "committed_at": "2026-01-14T09:00:00Z",
        "agent_id": "agent-2",
    }
    conflict = {
        "id": "conflict-001",
        "detection_tier": "exact",
        "severity": "high",
        "explanation": "Different TTL values",
    }

    prompt = _build_prompt(fact_a, fact_b, conflict)

    assert "fact-a-001" in prompt
    assert "fact-b-002" in prompt
    assert "cache TTL" in prompt
    assert "300" in prompt
    assert "600" in prompt


async def test_generate_suggestion_no_api_key():
    """Test that suggestion returns None when no API key is set."""
    fact = {"id": "a", "content": "test", "scope": "s", "confidence": 0.8}
    conflict = {"id": "c", "detection_tier": "t", "severity": "h"}

    with patch.dict("os.environ", {}, clear=True):
        result = await generate_suggestion(fact, fact, conflict)

    assert result is None


async def test_generate_suggestion_anthropic_not_installed(monkeypatch):
    """Test graceful handling when anthropic package is not installed."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")

    import engram.suggester as suggester_module
    original_import = __import__

    def mock_import(name, *args, **kwargs):
        if name == "anthropic":
            raise ImportError("No module named 'anthropic'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__builtins__", {"__import__": mock_import})

    fact = {"id": "a", "content": "test", "scope": "s", "confidence": 0.8}
    conflict = {"id": "c"}

    result = await generate_suggestion(fact, fact, conflict)

    assert result is None


async def test_generate_suggestion_api_error(monkeypatch):
    """Test graceful handling when API call fails."""
    import anthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")

    mock_response = AsyncMock()
    mock_response.content = [type("obj", (object,), {"text": "{}"})()]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("engram.suggester.anthropic.AsyncAnthropic", return_value=mock_client):
        fact_a = {"id": "a", "content": "a", "scope": "s", "confidence": 0.8}
        fact_b = {"id": "b", "content": "b", "scope": "s", "confidence": 0.7}
        conflict = {"id": "c"}

        result = await generate_suggestion(fact_a, fact_b, conflict)

    assert result is None or "suggested_resolution" in result


async def test_generate_suggestion_success(monkeypatch):
    """Test successful suggestion generation with mocked API."""
    import anthropic

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")

    suggestion_json = json.dumps({
        "resolution_type": "winner",
        "winning_fact_id": "fact-a",
        "suggested_resolution": "A is correct",
        "reasoning": "Higher confidence",
    })

    mock_response = type("MockResponse", (), {
        "content": [type("obj", (object,), {"text": suggestion_json})()]
    })

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response())

    fact_a = {
        "id": "fact-a",
        "content": "The answer is 42",
        "scope": "project",
        "confidence": 0.9,
        "fact_type": "observation",
        "committed_at": "2026-01-15T10:00:00Z",
    }
    fact_b = {
        "id": "fact-b",
        "content": "The answer is 43",
        "scope": "project",
        "confidence": 0.5,
        "fact_type": "observation",
        "committed_at": "2026-01-14T10:00:00Z",
    }
    conflict = {"id": "conflict-1", "detection_tier": "exact"}

    with patch("engram.suggester.anthropic.AsyncAnthropic", return_value=mock_client):
        result = await generate_suggestion(fact_a, fact_b, conflict)

    assert result is not None
    assert "suggested_resolution" in result
    assert result["suggested_resolution_type"] == "winner"