"""Full CLI/webhook/worker flow with a mock HTTP Bot API and real disposable services.

Run with TEST_DATABASE_URL (a local Postgres role allowed to CREATE DATABASE) and TEST_REDIS_URL
(an empty disposable Redis database). No .env file or external AI credentials are used by the child.
The harness creates/drops its own PostgreSQL database and refuses a nonempty Redis database.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import itertools
import json
import os
import signal
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import fitz
import pytest
from aiohttp import ClientSession, web
from aiohttp.test_utils import TestServer
from redis.asyncio import from_url
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

ROOT = Path(__file__).resolve().parents[2]
SLUG_IDS = {"anonymous": 710001, "groupguard": 710002, "factory": 710003, "cvbot": 710004, "doctools": 710005}
CHILD_ID = 710010
FACTORY_KEY = "isolated-e2e-factory-key"
TOKENS = {slug: f"{bot_id}:" + "A" * 35 for slug, bot_id in SLUG_IDS.items()}
CHILD_TOKEN = f"{CHILD_ID}:" + "B" * 35
pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL") or not os.environ.get("TEST_REDIS_URL"),
    reason="TEST_DATABASE_URL and TEST_REDIS_URL required for isolated runtime tests",
)


def user(uid: int, *, bot: bool = False) -> dict[str, Any]:
    return {"id": uid, "is_bot": bot, "first_name": f"User{uid}", "username": f"user_{uid}", "language_code": "en"}


class MockBotAPI:
    """HTTP and multipart coverage, including downloaded fixtures and generated output bytes."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.files: dict[str, bytes] = {}
        self.uploads: list[dict[str, Any]] = []
        self.ids = itertools.count(100)

    async def handle(self, request: web.Request) -> web.Response:
        bot_id = int(request.match_info["token"].split(":", 1)[0])
        method = request.match_info["method"]
        fields: dict[str, Any] = {}
        if request.content_type.startswith("multipart/"):
            reader = await request.multipart()
            while part := await reader.next():
                if part.filename:
                    self.uploads.append({"bot_id": bot_id, "method": method, "name": part.filename,
                                         "data": bytes(await part.read())})
                    fields[part.name] = part.filename
                else:
                    fields[part.name] = await part.text()
        else:
            fields = dict(await request.post())
        for key in ("reply_markup", "permissions"):
            if isinstance(fields.get(key), str):
                fields[key] = json.loads(fields[key])
        record = {"bot_id": bot_id, "method": method, **fields}
        self.calls.append(record)
        if method == "getMe":
            result: Any = {**user(bot_id, bot=True), "username": f"e2e_{bot_id}_bot"}
        elif method == "getFile":
            fid = str(fields["file_id"])
            result = {"file_id": fid, "file_unique_id": fid, "file_path": fid, "file_size": len(self.files[fid])}
        elif method == "copyMessage":
            result = {"message_id": next(self.ids)}
        elif method == "getChatMember":
            uid = int(fields["user_id"])
            if uid in (bot_id, 1):
                result = {"status": "administrator", "user": user(uid, bot=uid == bot_id),
                          "can_be_edited": True, "is_anonymous": False, "can_manage_chat": True,
                          "can_delete_messages": True, "can_manage_video_chats": True,
                          "can_restrict_members": True, "can_promote_members": True,
                          "can_change_info": True, "can_invite_users": True,
                          "can_post_stories": True, "can_edit_stories": True, "can_delete_stories": True,
                          "can_send_welcome_messages": True, "can_pin_messages": True, "can_manage_topics": True}
            else:
                result = {"status": "member", "user": user(uid)}
        elif method == "getChat":
            result = {"id": int(fields["chat_id"]), "type": "supergroup", "title": "Study group",
                      "accent_color_id": 0, "max_reaction_count": 1, "permissions": {"can_send_messages": True},
                      "accepted_gift_types": {"unlimited_gifts": False, "limited_gifts": False,
                                              "unique_gifts": False, "premium_subscription": False,
                                              "gifts_from_channels": False}}
        elif method == "getChatAdministrators":
            result = [{"status": "creator", "user": user(1), "is_anonymous": False}]
        elif method == "getChatMemberCount":
            result = 12
        elif method == "getUpdates":
            result = []
        elif method.startswith("send") or method == "editMessageText":
            chat_id = int(fields.get("chat_id", 1))
            result = {"message_id": next(self.ids), "date": int(time.time()), "from": user(bot_id, bot=True),
                      "chat": {"id": chat_id, "type": "supergroup" if chat_id < 0 else "private"}}
            if fields.get("text"):
                result["text"] = fields["text"]
            if fields.get("caption"):
                result["caption"] = fields["caption"]
            if fields.get("reply_markup"):
                result["reply_markup"] = fields["reply_markup"]
            record["result_message_id"] = result["message_id"]
        else:
            result = True
        return web.json_response({"ok": True, "result": result})

    async def download(self, request: web.Request) -> web.Response:
        return web.Response(body=self.files[request.match_info["file_id"]], content_type="application/pdf")

    def matching(self, bot_id: int, method: str, chat_id: int | None = None) -> list[dict[str, Any]]:
        return [c for c in self.calls if c["bot_id"] == bot_id and c["method"] == method
                and (chat_id is None or str(c.get("chat_id")) == str(chat_id))]


async def wait_until(predicate, timeout: float = 20) -> Any:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        await asyncio.sleep(0.05)
    raise AssertionError("runtime did not produce the expected result before the deadline")


def port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def pdf(label: str) -> bytes:
    with fitz.open() as doc:
        doc.new_page().insert_text((72, 72), label)
        return doc.tobytes()


@pytest.fixture
async def disposable_services():
    base_url = make_url(os.environ["TEST_DATABASE_URL"])
    if base_url.get_backend_name() != "postgresql":
        pytest.fail("runtime verification requires PostgreSQL, not an in-memory database")
    db_name = "e2e_" + uuid.uuid4().hex
    admin = create_async_engine(base_url, isolation_level="AUTOCOMMIT")
    redis = from_url(os.environ["TEST_REDIS_URL"])
    redis_version = (await redis.info("server"))["redis_version"]
    if int(redis_version.split(".")[0]) < 7:
        await redis.aclose()
        await admin.dispose()
        pytest.fail(f"runtime verification requires Redis 7+, found {redis_version}")
    if await redis.dbsize():
        await redis.aclose()
        await admin.dispose()
        pytest.fail("TEST_REDIS_URL must point at an empty disposable Redis database")
    async with admin.connect() as conn:
        await conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    isolated_url = base_url.set(database=db_name).render_as_string(hide_password=False)
    try:
        yield isolated_url, redis
    finally:
        # The selected database was verified empty, and belongs only to this opt-in harness.
        keys = [key async for key in redis.scan_iter()]
        if keys:
            await redis.delete(*keys)
        await redis.aclose()
        async with admin.connect() as conn:
            await conn.execute(text(f'DROP DATABASE "{db_name}" WITH (FORCE)'))
        await admin.dispose()


async def test_all_bots_through_dev_webhooks_and_worker(disposable_services, tmp_path):
    database_url, redis = disposable_services
    api = MockBotAPI()
    api.files = {"cv.pdf": pdf("Engineer: Python, SQL, Redis. Built a service and improved delivery."),
                 "one.pdf": pdf("First study page"), "two.pdf": pdf("Second study page")}
    app = web.Application()
    app.router.add_post("/bot{token}/{method}", api.handle)
    app.router.add_get("/file/bot{token}/{file_id}", api.download)
    gateway_port, metrics_port = port(), port()
    gateway = f"http://127.0.0.1:{gateway_port}"
    # Allowlist the child environment so workspace .env and real provider keys cannot leak into the run.
    env = {k: v for k, v in os.environ.items() if k.upper() in
           {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "USERPROFILE", "HOME"}}
    pythonpath = os.pathsep.join([str(ROOT), os.environ.get("PYTHONPATH", "")]).rstrip(os.pathsep)
    env.update(PYTHONPATH=pythonpath, DATABASE_URL=database_url, REDIS_URL=os.environ["TEST_REDIS_URL"],
               REDIS_CACHE_URL=os.environ["TEST_REDIS_URL"], ENABLED_BOTS=",".join(SLUG_IDS),
               FACTORY_SECRET_KEY=FACTORY_KEY, WEBHOOK_BASE_URL=gateway, WEB_HOST="127.0.0.1",
               WEB_PORT=str(gateway_port), METRICS_PORT=str(metrics_port), DATA_DIR=str(tmp_path / "data"),
               LOG_JSON="true", ENVIRONMENT="test", DEFAULT_LANG="en", SUPER_ADMIN_IDS="1",
               TELEGRAM_API_LOCAL_FILES="false", AI_PROVIDER="anthropic")
    for slug, token in TOKENS.items():
        env[f"{slug.upper()}_TOKEN"] = token
    process = None
    log_file = tmp_path / "dev.log"
    counter = itertools.count(1)
    async with TestServer(app) as server, ClientSession() as client:
        env["TELEGRAM_API_URL"] = str(server.make_url("/")).rstrip("/")
        migration = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "core", "migrate", env=env, cwd=tmp_path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        output, _ = await migration.communicate()
        assert migration.returncode == 0, output.decode(errors="replace")
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        with log_file.open("wb") as log:
            process = await asyncio.to_thread(
                subprocess.Popen, [sys.executable, "-m", "tests.e2e.dev_launcher", "dev"],
                env=env, cwd=tmp_path, stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT,
                creationflags=flags,
            )
            try:
                async def post(slug: str, payload: dict[str, Any], *, fast: bool = False) -> None:
                    if not fast:
                        await asyncio.sleep(1.05)  # Preserve real private-message throttle behavior.
                    payload["update_id"] = next(counter)
                    if slug == "child":
                        path = f"/webhook/c/{CHILD_ID}"
                        secret = hmac.new(FACTORY_KEY.encode(), f"webhook:{CHILD_ID}".encode(), hashlib.sha256).hexdigest()[:48]
                    else:
                        path = f"/webhook/{slug}"
                        secret = hashlib.sha256(TOKENS[slug].encode()).hexdigest()[:48]
                    async with client.post(gateway + path, json=payload,
                                           headers={"X-Telegram-Bot-Api-Secret-Token": secret}) as response:
                        assert response.status == 200, await response.text()

                def message(uid: int, content: str = "", **kwargs) -> dict[str, Any]:
                    chat_id = kwargs.pop("chat_id", uid)
                    msg = {"message_id": next(counter), "date": int(time.time()), "from": user(uid),
                           "chat": {"id": chat_id, "type": "supergroup" if chat_id < 0 else "private"}, **kwargs}
                    if content:
                        msg["text"] = content
                    return {"message": msg}

                def callback(uid: int, data: str, chat_id: int | None = None, *, message_id: int = 100, bot_id: int | None = None) -> dict[str, Any]:
                    chat_id = uid if chat_id is None else chat_id
                    return {"callback_query": {"id": str(next(counter)), "from": user(uid),
                            "chat_instance": "isolated", "data": data,
                            "message": {"message_id": message_id, "date": int(time.time()),
                                        **({"from": user(bot_id, bot=True)} if bot_id is not None else {}),
                                        "chat": {"id": chat_id, "type": "supergroup" if chat_id < 0 else "private"},
                                        "text": "menu"}}}

                deadline = time.monotonic() + 25
                while True:
                    assert process.poll() is None, log_file.read_text(errors="replace")
                    try:
                        async with client.get(gateway + "/health/ready") as response:
                            if response.status == 200:
                                assert (await response.json())["bots"] == len(SLUG_IDS)
                                break
                    except OSError:
                        pass
                    assert time.monotonic() < deadline, log_file.read_text(errors="replace")
                    await asyncio.sleep(0.1)

                # Group member restriction -> captcha solve -> unrestricted, then flood mute.
                group_id, member_id = -100710001, 66
                group_bot = SLUG_IDS["groupguard"]
                engine = create_async_engine(database_url)
                try:
                    async with engine.begin() as conn:
                        await conn.execute(text(
                            "INSERT INTO gg_chats (bot_id, chat_id, title, active, night, config, created_at, updated_at) "
                            "VALUES (:bot, :chat, 'Study group', true, false, "
                            "CAST(:config AS jsonb), now(), now())"
                        ), {"bot": group_bot, "chat": group_id,
                            "config": json.dumps({"cas": False, "captcha": "button", "flood_count": 3,
                                                  "flood_seconds": 8})})
                finally:
                    await engine.dispose()
                await post("groupguard", {"chat_member": {
                    "chat": {"id": group_id, "type": "supergroup", "title": "Study group"},
                    "from": user(1), "date": int(time.time()),
                    "old_chat_member": {"status": "left", "user": user(member_id)},
                    "new_chat_member": {"status": "member", "user": user(member_id)},
                }}, fast=True)
                await wait_until(lambda: api.matching(group_bot, "restrictChatMember", group_id))
                challenge = await wait_until(lambda: [c for c in api.matching(group_bot, "sendMessage", group_id)
                                                       if c.get("reply_markup")])
                answer = challenge[-1]["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
                await post("groupguard", callback(member_id, answer, group_id,
                    message_id=challenge[-1]["result_message_id"], bot_id=group_bot), fast=True)
                await wait_until(lambda: [c for c in api.matching(group_bot, "restrictChatMember", group_id)
                                         if c["permissions"].get("can_send_messages") is True])
                before = len(api.matching(group_bot, "restrictChatMember", group_id))
                for number in range(5):
                    await post("groupguard", message(member_id, f"Flood {number}", chat_id=group_id), fast=True)
                    await asyncio.sleep(0.05)
                await wait_until(lambda: len(api.matching(group_bot, "restrictChatMember", group_id)) > before)
                assert api.matching(group_bot, "restrictChatMember", group_id)[-1]["permissions"]["can_send_messages"] is False

                # Anonymous link -> visitor -> anonymous owner reply.
                anon = SLUG_IDS["anonymous"]
                await post("anonymous", message(11, "/start"))
                sent = await wait_until(lambda: api.matching(anon, "sendMessage", 11))
                import re

                code = re.search(r"start=([A-Za-z0-9_-]+)", sent[-1]["text"]).group(1)
                await post("anonymous", message(22, f"/start {code}"))
                await wait_until(lambda: api.matching(anon, "sendMessage", 22))
                await post("anonymous", message(22, "Anonymous hello"))
                delivery = await wait_until(lambda: [c for c in api.matching(anon, "sendMessage", 11)
                                                     if "Anonymous hello" in c.get("text", "")])
                assert "user_22" not in delivery[-1]["text"] and "<code>22</code>" not in delivery[-1]["text"]
                reply = delivery[-1]["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
                await post("anonymous", callback(11, reply))
                await wait_until(lambda: api.matching(anon, "answerCallbackQuery"))
                await post("anonymous", message(11, "Anonymous reply"))
                await wait_until(lambda: [c for c in api.matching(anon, "sendMessage", 22)
                                         if "Anonymous reply" in c.get("text", "")])

                # Factory creates a real child row, installs a webhook, then feedback replies route back.
                factory = SLUG_IDS["factory"]
                before = len(api.matching(factory, "sendMessage", 1))
                await post("factory", message(1, "/newbot"))
                await wait_until(lambda: len(api.matching(factory, "sendMessage", 1)) > before)
                await post("factory", callback(1, "fac:tpl:0:1:feedback"))
                await wait_until(lambda: api.matching(factory, "editMessageText", 1))
                await post("factory", message(1, CHILD_TOKEN))
                await wait_until(lambda: api.matching(CHILD_ID, "setWebhook"))
                await post("child", message(33, "Customer question"))
                feedback = await wait_until(lambda: [c for c in api.matching(CHILD_ID, "sendMessage", 1)
                                                     if "Customer question" in c.get("text", "")])
                reply_to = {"message_id": feedback[-1]["result_message_id"], "date": int(time.time()),
                            "from": user(CHILD_ID, bot=True), "chat": {"id": 1, "type": "private"},
                            "text": feedback[-1]["text"]}
                await post("child", message(1, "Owner answer", reply_to_message=reply_to))
                await wait_until(lambda: api.matching(CHILD_ID, "copyMessage", 33))

                # CV PDF travels through HTTP getFile/download, fake structured AI and PNG upload.
                def document(fid: str) -> dict[str, Any]:
                    return {"document": {"file_id": fid, "file_unique_id": fid, "file_name": fid,
                                         "mime_type": "application/pdf", "file_size": len(api.files[fid])}}

                await post("cvbot", message(44, **document("cv.pdf")))
                await wait_until(lambda: [c for c in api.matching(SLUG_IDS["cvbot"], "sendMessage", 44)
                                         if "82" in c.get("text", "")])
                await post("cvbot", message(44, "/share"))
                await wait_until(lambda: [u for u in api.uploads if u["bot_id"] == SLUG_IDS["cvbot"]
                                         and u["method"] == "sendPhoto"])

                # Two PDFs enter the basket and leave through the worker as one verified PDF.
                doctools = SLUG_IDS["doctools"]
                # Consecutive uploads exercise basket collection with production throttling enabled.
                await post("doctools", message(55, **document("one.pdf")), fast=True)
                await post("doctools", message(55, **document("two.pdf")), fast=True)
                menus = await wait_until(lambda: [c for c in api.matching(doctools, "sendMessage", 55)
                                                  if any(b.get("callback_data", "").startswith("dt:merge:")
                                                         for row in c.get("reply_markup", {}).get("inline_keyboard", [])
                                                         for b in row)])
                data = [b["callback_data"] for row in menus[-1]["reply_markup"]["inline_keyboard"]
                        for b in row if b.get("callback_data", "").startswith("dt:merge:")]
                assert data, "document basket must offer merging"
                await post("doctools", callback(55, data[0]))
                outputs = await wait_until(lambda: [u for u in api.uploads if u["bot_id"] == doctools
                                                    and u["method"] == "sendDocument"], timeout=30)
                with fitz.open(stream=outputs[-1]["data"], filetype="pdf") as merged:
                    assert len(merged) == 2
                    assert "First study page" in merged[0].get_text()
                    assert "Second study page" in merged[1].get_text()
            finally:
                if process.poll() is None:
                    if os.name == "nt":
                        process.stdin.write(b"SIGTERM\n")
                        process.stdin.flush()
                    else:
                        process.send_signal(signal.SIGTERM)
                    try:
                        await asyncio.to_thread(process.wait, timeout=35)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        await asyncio.to_thread(process.wait)
                        pytest.fail("dev runtime did not drain after shutdown signal")
                if process.stdin is not None:
                    process.stdin.close()
        logs = log_file.read_text(errors="replace")
        assert process.returncode == 0, logs
        assert "process_stopped" in logs, logs
        assert '"level": "error"' not in logs and "Traceback" not in logs, logs
        assert not await redis.keys("platform:hb:dev:*")
