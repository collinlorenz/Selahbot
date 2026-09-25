"""Small shared wrapper so seo/ and outreach/ don't duplicate Anthropic client setup."""

import json
import os

import anthropic


def call_fable_json(system: str, user: str, max_tokens: int = 4000) -> dict | list:
    """Calls Fable with a system+user prompt and parses the reply as JSON.

    Both modules' prompts instruct the model to return ONLY JSON, so this
    strips markdown code fences defensively and raises a clear error with
    the raw text if parsing still fails (rather than crashing on a stray
    KeyError three functions later).
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.environ.get("CLAUDE_MODEL", "claude-fable-5-1")

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Fable returned non-JSON output, inspect manually:\n{text}") from e
