"""Real middleware regression: rapid uploads are retained in Telegram send order."""

from bots.doctools.module import DocToolsBot
from core.runtime.dispatcher import build_dispatcher
from tests.bots.doctools.test_handlers import pdf_update
from tests.conftest import build_test_ctx, message_update


async def test_rapid_uploads_preserve_message_order(sm, redis, api, tmp_path):
    ctx = await build_test_ctx(DocToolsBot(), sm, redis, api, tmp_path)
    dp = build_dispatcher(ctx)
    first = pdf_update("first")
    second = pdf_update("second")
    second = second.model_copy(update={"message": second.message.model_copy(update={"message_id": 20})})
    # Deliberately handle the later message first, without disabling the production throttle.
    await dp.feed_update(ctx.bot, second)
    await dp.feed_update(ctx.bot, first)
    basket = await ctx.extras["doctools"].basket(42, 42)
    assert [asset.file_id for asset in basket.assets] == ["first", "second"]
    job = await ctx.extras["doctools"].submit(42, 42, "merge")
    assert [asset.message_id for asset in job.assets] == [10, 20]
    user = await ctx.users.get(42)
    assert not await redis.get(ctx.keys("throttle", "Message", user.id))


async def test_commands_and_assignment_text_keep_normal_throttling(sm, redis, api, tmp_path):
    ctx = await build_test_ctx(DocToolsBot(), sm, redis, api, tmp_path)
    dp = build_dispatcher(ctx)
    await dp.feed_update(ctx.bot, message_update("/help"))
    await dp.feed_update(ctx.bot, message_update("assignment text"))
    assert await ctx.extras["doctools"].basket(42, 42) is None
    assert api.calls("SendMessage")[-1].text == ctx.translator.get("en", "throttled")


async def test_commands_in_file_captions_are_not_exempt(sm, redis, api, tmp_path):
    ctx = await build_test_ctx(DocToolsBot(), sm, redis, api, tmp_path)
    dp = build_dispatcher(ctx)
    await dp.feed_update(ctx.bot, message_update("/help"))
    upload = pdf_update("file")
    upload = upload.model_copy(update={"message": upload.message.model_copy(update={"caption": "  /help"})})
    await dp.feed_update(ctx.bot, upload)
    assert len(api.calls("SendMessage")) == 2
    assert api.calls("SendMessage")[-1].text == ctx.translator.get("en", "throttled")
