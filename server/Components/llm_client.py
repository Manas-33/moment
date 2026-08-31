"""Shared Anthropic Claude client used by chat-style components.

All chat/text generation calls in the project go through `claude_chat` so the
model id and credential handling live in one place.
"""

import os
from anthropic import Anthropic

CLAUDE_MODEL = "claude-sonnet-4-6"


def get_anthropic_client() -> Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. Set it in the server .env file."
        )
    return Anthropic(api_key=api_key)


def claude_chat(
    system: str,
    user: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    """Run a single-turn chat against Claude and return the text content."""
    client = get_anthropic_client()
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text
