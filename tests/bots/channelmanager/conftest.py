from datetime import UTC, datetime

import pytest
from aiogram.types import Chat, ChatMemberAdministrator, ChatMemberMember, ChatMemberUpdated, Update, User

from core.runtime.dispatcher import build_dispatcher
from core.sdk.registry import discover
from tests.conftest import BOT_ID, build_test_ctx

CHANNEL_ID = -1001234567890
OPERATOR = 42


async def insert_legacy(connection, model, **values):
    """Seed an earlier revision using only columns present there, including its Python defaults."""
    from sqlalchemy import MetaData, Table
    def insert(sync):
        table = Table(model.__tablename__, MetaData(), autoload_with=sync, resolve_fks=False)
        defaults = {column.name: column.default.arg(None) if column.default.is_callable else column.default.arg
            for column in model.__table__.columns if column.name in table.c and column.default is not None}
        sync.execute(table.insert().values(**(defaults | values)))
    await connection.run_sync(insert)


def admin_member(user_id=BOT_ID, *, post=True):
    return ChatMemberAdministrator(user=User(id=user_id, is_bot=user_id == BOT_ID, first_name="Admin"),
        can_be_edited=False, is_anonymous=False, can_manage_chat=True, can_delete_messages=True,
        can_manage_video_chats=False, can_restrict_members=True, can_promote_members=False,
        can_change_info=True, can_invite_users=True, can_post_stories=False, can_edit_stories=False,
        can_delete_stories=False, can_send_welcome_messages=False, can_post_messages=post, can_edit_messages=True)


def membership_update(update_id=50, *, member=None, date=None):
    event = ChatMemberUpdated(chat=Chat(id=CHANNEL_ID, type="channel", title="Test <channel>"),
        from_user=User(id=OPERATOR, is_bot=False, first_name="Owner"), date=date or datetime.now(UTC),
        old_chat_member=admin_member(), new_chat_member=member or admin_member())
    return Update(update_id=update_id, my_chat_member=event)


@pytest.fixture
async def chm(sm, redis, api, tmp_path):
    ctx = await build_test_ctx(discover(["channelmanager"])[0], sm, redis, api, tmp_path)
    api.responses["GetChat"] = Chat(id=CHANNEL_ID, type="channel", title="Test <channel>")
    api.responses["GetChatMember"] = lambda method: admin_member(method.user_id) if method.user_id in {BOT_ID, OPERATOR} else (
        ChatMemberMember(user=User(id=method.user_id, is_bot=False, first_name="Outsider")))
    return ctx


@pytest.fixture
def dp(chm):
    return build_dispatcher(chm)
