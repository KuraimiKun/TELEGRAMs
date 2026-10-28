"""OpenAI alternative provider (Responses API)."""

from __future__ import annotations

import base64
from typing import Any

import openai

from core.ai.base import AIError, AIProvider, AIRequest, AIResult, parse_json


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str, fast_model: str, *, timeout: float = 120.0) -> None:
        self.client = openai.AsyncOpenAI(api_key=api_key, timeout=timeout, max_retries=2)
        self.model = model
        self.fast_model = fast_model

    @staticmethod
    def _content(req: AIRequest, text: str, role: str, last: bool) -> list[dict[str, Any]]:
        text_type = "output_text" if role == "assistant" else "input_text"
        parts: list[dict[str, Any]] = []
        if last:
            for i, a in enumerate(req.attachments):
                b64 = base64.standard_b64encode(a.data).decode()
                if a.kind == "image":
                    parts.append({"type": "input_image", "image_url": f"data:{a.media_type};base64,{b64}"})
                else:
                    parts.append(
                        {"type": "input_file", "filename": f"document{i}.pdf", "file_data": f"data:application/pdf;base64,{b64}"}
                    )
        parts.append({"type": text_type, "text": text})
        return parts

    async def complete(self, req: AIRequest) -> AIResult:
        model = self.fast_model if req.fast else self.model
        last_user = max((i for i, t in enumerate(req.turns) if t.role == "user"), default=-1)
        inputs = [
            {"role": t.role, "content": self._content(req, t.text, t.role, i == last_user)}
            for i, t in enumerate(req.turns)
        ]
        kwargs: dict[str, Any] = {
            "model": model,
            "instructions": req.system,
            "input": inputs,
            "max_output_tokens": req.max_tokens,
        }
        if req.schema is not None:
            kwargs["text"] = {"format": {"type": "json_schema", "name": "result", "schema": req.schema, "strict": True}}
        try:
            response = await self.client.responses.create(**kwargs)
        except openai.RateLimitError as e:
            raise AIError("rate limited by the AI provider") from e
        except openai.APIStatusError as e:
            raise AIError(f"AI provider error {e.status_code}") from e
        except openai.APIConnectionError as e:
            raise AIError("AI provider unreachable") from e

        text = response.output_text or ""
        usage = response.usage
        result = AIResult(
            text=text,
            model=response.model,
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
        )
        if req.schema is not None:
            result.data = parse_json(text)
        return result

    async def close(self) -> None:
        await self.client.close()
