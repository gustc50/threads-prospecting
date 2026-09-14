import os

import pytest

from threads_prospecting.client import ClaudeClient, MissingAPIKeyError


def test_missing_api_key_raises_clean_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(MissingAPIKeyError):
        ClaudeClient()


def test_client_constructs_when_api_key_is_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-key-not-real")

    client = ClaudeClient()

    assert client.model == os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
