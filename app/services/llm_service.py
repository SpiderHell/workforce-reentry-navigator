"""Claude API wrapper with structured output and retry logic."""
import json
import re
from typing import Type, Optional, Any
from anthropic import AsyncAnthropic
from pydantic import BaseModel, ValidationError
from app.config import get_settings

settings = get_settings()


class LLMService:
    """Service for calling Claude with structured JSON output."""

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> BaseModel:
        """Generate structured output from Claude and validate against Pydantic model."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_text = response.content[0].text

        # Extract JSON from markdown code blocks or raw text
        json_str = self._extract_json(raw_text)

        try:
            data = json.loads(json_str)
            return response_model.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            # Retry once with explicit JSON instruction
            retry_prompt = f"""The previous response was not valid JSON. Please respond with ONLY valid JSON, no markdown, no explanations.

{user_prompt}

Previous (invalid) response: {raw_text}
"""
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.0,
                system=system_prompt,
                messages=[{"role": "user", "content": retry_prompt}],
            )
            raw_text = response.content[0].text
            json_str = self._extract_json(raw_text)
            data = json.loads(json_str)
            return response_model.model_validate(data)

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Generate free-form text from Claude."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    @staticmethod
    def _extract_json(text: str) -> str:
        """Extract JSON from text that may be wrapped in markdown or have extra content."""
        # Try code block first
        code_block = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if code_block:
            return code_block.group(1)

        # Try raw JSON object
        json_match = re.search(r"(\{.*\})", text, re.DOTALL)
        if json_match:
            return json_match.group(1)

        return text.strip()


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
