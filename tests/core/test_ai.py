import pytest

from core.ai import AIError, AIUnavailable, Attachment, Turn
from core.ai.anthropic import AnthropicProvider
from core.ai.base import parse_json
from core.ai.registry import build_provider
from core.config import PlatformConfig
from tests.fake_ai import fake_ai


def test_provider_selection():
    assert build_provider(PlatformConfig()) is None  # no key -> AI disabled
    p = build_provider(PlatformConfig(anthropic_api_key="sk-test"))
    assert isinstance(p, AnthropicProvider) and p.model == "claude-opus-5-5" and p.fast_model == "claude-haiku-5-5"
    assert build_provider(PlatformConfig(ai_provider="openai")) is None
    p2 = build_provider(PlatformConfig(ai_provider="openai", openai_api_key="sk-o", ai_model="m1"))
    assert p2 is not None and p2.name == "openai" and p2.model == "m1"
    with pytest.raises(ValueError):
        PlatformConfig(ai_provider="other")


async def test_ask_meters_tokens_and_enforces_budget(redis):
    ai, provider = fake_ai(redis, "hello", daily_token_budget=50)
    res = await ai.ask("hi", system="s", bot="cv", user_id=7)
    assert res.text == "hello" and res.tokens == 20
    assert await ai.tokens_today() == 20 and await ai.user_tokens_today("cv", 7) == 20
    await ai.ask([Turn("user", "a"), Turn("assistant", "b"), Turn("user", "c")], system="s", bot="cv")
    await ai.ask("again", system="s", bot="cv")  # 60 tokens used now: over budget afterwards
    with pytest.raises(AIUnavailable):
        await ai.ask("more", system="s", bot="cv")
    assert len(provider.requests) == 3
    assert [t.role for t in provider.requests[1].turns] == ["user", "assistant", "user"]


async def test_structured_and_errors(redis):
    ai, provider = fake_ai(redis, {"score": 80})
    res = await ai.ask("cv", system="s", bot="cv", schema={"type": "object"}, attachments=[Attachment.pdf(b"%PDF")])
    assert res.data == {"score": 80}
    assert provider.requests[0].attachments[0].kind == "pdf"

    provider.reply = RuntimeError("boom")  # unexpected provider exceptions surface as AIError
    with pytest.raises(AIError):
        await ai.ask("x", system="s", bot="cv")


def test_parse_json_tolerates_fences():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    with pytest.raises(AIError):
        parse_json("not json")


def test_anthropic_content_blocks():
    from core.ai.base import AIRequest

    req = AIRequest(system="s", turns=[Turn("user", "look")], attachments=(Attachment.image(b"img", "image/png"),))
    blocks = AnthropicProvider._content(req, "look", True)
    assert isinstance(blocks, list)
    assert blocks[0]["type"] == "image" and blocks[0]["source"]["media_type"] == "image/png"
    assert blocks[-1] == {"type": "text", "text": "look"}
    assert AnthropicProvider._content(req, "earlier", False) == "earlier"
