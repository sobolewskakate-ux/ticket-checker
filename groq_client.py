"""Thin wrapper around the Groq API call used for scoring."""

from __future__ import annotations

import os

from groq import Groq

DEFAULT_MODEL = "openai/gpt-oss-120b"


class ScoringServiceError(Exception):
    """Raised when the Groq API call fails or cannot be made."""


def get_completion(prompt: str) -> str:
    """Call the Groq API with `prompt`, requesting a JSON response, return raw text."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ScoringServiceError(
            "GROQ_API_KEY environment variable is not set. "
            "Set it before running the app (see .env.example)."
        )

    model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        raise ScoringServiceError(f"Groq API request failed: {exc}") from exc

    try:
        return completion.choices[0].message.content
    except (IndexError, AttributeError) as exc:
        raise ScoringServiceError("Groq API returned an unexpected response shape") from exc
