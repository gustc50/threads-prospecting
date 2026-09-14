"""Thin wrapper around the Claude API used to run the prompt templates."""

import os
from typing import Protocol

DEFAULT_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")
DEFAULT_MAX_TOKENS = 300


class LLMClient(Protocol):
    """Minimal interface required from an LLM client (real or fake, e.g. in tests)."""

    def complete(self, system_prompt: str, user_message: str) -> str: ...


class ClaudeClient:
    """Calls the Claude API via the official Anthropic SDK."""

    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = DEFAULT_MAX_TOKENS):
        import anthropic

        self._client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens

    def complete(self, system_prompt: str, user_message: str) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
