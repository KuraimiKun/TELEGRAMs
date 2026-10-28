"""Small Group Guard actor and outcome values; no persistent schema."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Right = Literal["change_info", "delete_messages", "restrict_members", "pin_messages", "invite_users",
                "promote_members", "manage_topics", "creator", "post_messages"]
ActorKind = Literal["human", "anonymous_group", "channel", "bot", "unknown", "internal"]


@dataclass(frozen=True, slots=True)
class Actor:
    bot_id: int
    source_chat_id: int
    kind: ActorKind
    human_id: int | None = None
    sender_chat_id: int | None = None
    message_id: int | None = None
    thread_id: int | None = None
    bot_sender_id: int | None = None


@dataclass(frozen=True, slots=True)
class StepResult:
    operation: str
    status: Literal["applied", "acknowledged", "failed", "skipped"]
    error_code: str | None = None
    retry_after: int | None = None

    @property
    def completed(self) -> bool:
        return self.status in {"applied", "acknowledged"}

    def __bool__(self) -> bool:
        raise TypeError("Inspect StepResult.completed/status explicitly")


@dataclass(frozen=True, slots=True)
class ActionResult:
    status: Literal["applied", "partial", "failed", "noop"]
    steps: tuple[StepResult, ...]
    primary_completed: bool
    requested_message_ids: tuple[int, ...] = ()
    acknowledged_message_ids: tuple[int, ...] = ()
    confirmed_deleted_count: int | None = None
    until_date: int | None = None

    def __bool__(self) -> bool:
        raise TypeError("Inspect ActionResult.primary_completed/status explicitly")

    def with_steps(self, *steps: StepResult) -> ActionResult:
        all_steps = (*self.steps, *steps)
        failed = any(s.status == "failed" for s in all_steps)
        applied = any(s.completed for s in all_steps)
        status: Literal["applied", "partial", "failed", "noop"] = (
            "partial" if failed and applied else "failed" if failed else self.status
        )
        return ActionResult(status, all_steps, self.primary_completed, self.requested_message_ids,
                            self.acknowledged_message_ids, self.confirmed_deleted_count, self.until_date)


def result_of(*steps: StepResult, primary_count: int | None = None) -> ActionResult:
    primary = steps[:primary_count] if primary_count is not None else steps
    completed = bool(primary) and all(s.completed for s in primary)
    failed = any(s.status == "failed" for s in steps)
    applied = any(s.completed for s in steps)
    status: Literal["applied", "partial", "failed", "noop"] = (
        "partial" if failed and applied else "failed" if failed else "applied" if applied else "noop"
    )
    return ActionResult(status, tuple(steps), completed)
