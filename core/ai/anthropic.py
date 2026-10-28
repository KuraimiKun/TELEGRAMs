"""Claude via the official Anthropic SDK (default provider)."""

from __future__ import annotations

import base64
from typing import Any

import anthropic

from core.ai.base import AIError, AIProvider, AIRequest, AIResult, parse_json

# Models that accept the server-side refusal fallback (routes a declined request to another model).
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}


class AnthropicProvider(AIProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str, fast_model: str, *, timeout: float = 120.0) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=api_key, timeout=timeout, max_retries=2)
        self.model = model
        self.fast_model = fast_model

    @staticmethod
    def _content(req: AIRequest, text: str, last: bool) -> list[dict[str, Any]] | str:
        if not (last and req.attachments):
            return text
        blocks: list[dict[str, Any]] = []
        for a in req.attachments:
            data = base64.standard_b64encode(a.data).decode()
            block_type = "document" if a.kind == "pdf" else "image"
            blocks.append({"type": block_type, "source": {"type": "base64", "media_type": a.media_type, "data": data}})
        blocks.append({"type": "text", "text": text})
        return blocks

    async def complete(self, req: AIRequest) -> AIResult:
        model = self.fast_model if req.fast else self.model
        last_user = max((i for i, t in enumerate(req.turns) if t.role == "user"), default=-1)
        messages = [
            {"role": t.role, "content": self._content(req, t.text, i == last_user)} for i, t in enumerate(req.turns)
        ]
        output_config: dict[str, Any] = {"effort": "low" if req.fast else "medium"}
        if req.schema is not None:
            output_config["format"] = {"type": "json_schema", "schema": req.schema}
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": req.max_tokens,
            "system": req.system,
            "messages": messages,
            "output_config": output_config,
        }
        try:
            if model in _FALLBACK_MODELS:
                response = await self.client.beta.messages.create(
                    betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs
                )
            else:
                response = await self.client.messages.create(**kwargs)
        except anthropic.RateLimitError as e:
            raise AIError("rate limited by the AI provider") from e
        except anthropic.APIStatusError as e:
            raise AIError(f"AI provider error {e.status_code}") from e
        except anthropic.APIConnectionError as e:
            raise AIError("AI provider unreachable") from e

        if response.stop_reason == "refusal":
            raise AIError("the model declined this request")
        text = "".join(b.text for b in response.content if b.type == "text")
        result = AIResult(
            text=text,
            model=response.model,
            input_tokens=response.usage.input_tokens or 0,
            output_tokens=response.usage.output_tokens or 0,
        )
        if req.schema is not None:
            result.data = parse_json(text)
        return result

    async def close(self) -> None:
        await self.client.close()
