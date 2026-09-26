"""
utils.py
---------
Helper functions: input validation, guardrails, and output export utilities.
Keeping these separate from app.py keeps the UI layer thin and testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Guardrails
MAX_INPUT_CHARS = 8000                # Prevents runaway token usage / cost on huge pastes
MIN_INPUT_CHARS_FOR_TEXT_TASKS = 20   # Summarize/Rewrite need substantive input
MAX_TOPIC_CHARS = 500                 # Generate: topic/brief should be a short prompt, not an essay


@dataclass
class ValidationResult:
    is_valid: bool
    error_message: Optional[str] = None


def validate_generate_input(topic: str) -> ValidationResult:
    """Validate input for the 'Generate' task."""
    topic = topic.strip() if topic else ""

    if not topic:
        return ValidationResult(False, "Please enter a topic or brief to generate content about.")

    if len(topic) > MAX_TOPIC_CHARS:
        return ValidationResult(
            False,
            f"Topic/brief is too long ({len(topic)} chars). "
            f"Please keep it under {MAX_TOPIC_CHARS} characters — "
            "this should be a brief, not the full content.",
        )

    return ValidationResult(True)


def validate_text_input(text: str, task_name: str = "This task") -> ValidationResult:
    """Validate input for tasks that operate on a block of source text (Summarize/Rewrite)."""
    text = text.strip() if text else ""

    if not text:
        return ValidationResult(False, f"Please paste some text for {task_name.lower()} to work on.")

    if len(text) < MIN_INPUT_CHARS_FOR_TEXT_TASKS:
        return ValidationResult(
            False,
            f"Input text is too short ({len(text)} chars). "
            f"Please provide at least {MIN_INPUT_CHARS_FOR_TEXT_TASKS} characters "
            "of meaningful text.",
        )

    if len(text) > MAX_INPUT_CHARS:
        return ValidationResult(
            False,
            f"Input text is too long ({len(text)} chars). "
            f"Please keep it under {MAX_INPUT_CHARS} characters.",
        )

    return ValidationResult(True)


def estimate_max_output_tokens(length_choice: str) -> int:
    """Map a UI length choice to a reasonable max_tokens budget for the API call."""
    mapping = {"Short": 400, "Medium": 700, "Long": 1200}
    return mapping.get(length_choice, 700)


def prepare_download_bytes(text: str) -> bytes:
    """Convert output text into UTF-8 bytes for Streamlit's download_button."""
    return text.encode("utf-8")


def build_filename(task: str, extension: str = "txt") -> str:
    """Generate a simple, readable filename for exported output."""
    safe_task = task.lower().replace(" ", "_")
    return f"content_{safe_task}_output.{extension}"
