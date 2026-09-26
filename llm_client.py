"""
llm_client.py
--------------
Provider-agnostic LLM abstraction layer.

Keeping the LLM call behind an interface (LLMClient) means the rest of the
app (UI, prompt engine) never talks to a specific vendor SDK directly.
Swapping to a different provider, a local model, or a mock for testing only
requires writing a new class that implements `generate()`.
"""

from __future__ import annotations

import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from anthropic import Anthropic, APIConnectionError, APIStatusError, RateLimitError
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LLMResponse:
    """Normalized response object returned by any LLM client implementation."""
    text: str
    model: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None


class LLMClient(ABC):
    """Abstract base class every LLM provider client must implement."""

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Send a system+user prompt to the LLM and return a normalized response."""
        raise NotImplementedError


class AnthropicClient(LLMClient):
    """
    Concrete LLMClient implementation using the Anthropic Claude API.

    Handles:
        - Missing/invalid API key
        - Network failures
        - Rate limiting (with a single retry + backoff)
        - Generic API errors
    """

    def __init__(self, model: str = "claude-sonnet-4-5", api_key: Optional[str] = None):
        self.model = model
        resolved_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not resolved_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Set it in your .env file "
                "(see .env.example) or pass it explicitly to AnthropicClient()."
            )

        self._client = Anthropic(api_key=resolved_key)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        _retry_count: int = 0,
    ) -> LLMResponse:
        """
        Calls the Anthropic Messages API.

        Args:
            system_prompt: The system-level role/instruction prompt.
            user_prompt: The task-specific user prompt (already filled from a template).
            max_tokens: Max tokens to generate.
            temperature: Sampling temperature (0 = deterministic, 1 = creative).
            _retry_count: Internal counter used for rate-limit retry backoff.

        Returns:
            LLMResponse with either generated text or a populated error_message.
        """
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            text = "".join(
                block.text for block in response.content if block.type == "text"
            )

            return LLMResponse(
                text=text.strip(),
                model=self.model,
                input_tokens=getattr(response.usage, "input_tokens", None),
                output_tokens=getattr(response.usage, "output_tokens", None),
                success=True,
            )

        except RateLimitError:
            if _retry_count < 1:
                time.sleep(2)
                return self.generate(
                    system_prompt, user_prompt, max_tokens, temperature, _retry_count + 1
                )
            return LLMResponse(
                text="",
                model=self.model,
                success=False,
                error_message="Rate limit exceeded. Please wait a moment and try again.",
            )

        except APIConnectionError:
            return LLMResponse(
                text="",
                model=self.model,
                success=False,
                error_message="Could not connect to the API. Check your internet connection.",
            )

        except APIStatusError as e:
            return LLMResponse(
                text="",
                model=self.model,
                success=False,
                error_message=f"API returned an error (status {e.status_code}): {e.message}",
            )

        except Exception as e:  # noqa: BLE001 - last-resort guardrail for unexpected failures
            return LLMResponse(
                text="",
                model=self.model,
                success=False,
                error_message=f"Unexpected error: {str(e)}",
            )


def get_default_client() -> LLMClient:
    """Factory function so app.py doesn't need to know which provider is in use."""
    return AnthropicClient(model="claude-sonnet-4-5")
