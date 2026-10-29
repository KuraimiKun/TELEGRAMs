"""Pure wall-clock recurrence and weekly-calendar calculations with explicit DST behavior."""

from __future__ import annotations

import math
from datetime import UTC, datetime, time, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bots.channelmanager.content import ContentError


def local_instant(point: datetime, timezone: str, dst: str = "skip") -> datetime | None:
    zone = ZoneInfo(timezone)
    candidates = {p.astimezone(UTC) for fold in (0, 1)
        if (p := point.replace(tzinfo=zone, fold=fold)).astimezone(UTC).astimezone(zone).replace(tzinfo=None) == point}
    if not candidates or (len(candidates) > 1 and dst == "skip"):
        return None
    return max(candidates) if dst == "later" else min(candidates)


class Rule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    timezone: str = "UTC"
    anchor: datetime
    every_minutes: int = Field(default=1440, ge=1, le=525600)
    weekdays: list[int] = Field(default_factory=lambda: list(range(7)), min_length=1, max_length=7)
    monthdays: list[int] = Field(default_factory=list, max_length=31)
    window_start: time | None = None
    window_end: time | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    dst: Literal["skip", "earlier", "later"] = "skip"

    @model_validator(mode="after")
    def validate_rule(self):
        try:
            ZoneInfo(self.timezone)
        except (KeyError, ValueError) as exc:
            raise ContentError("time") from exc
        if any(p is not None and p.tzinfo is None for p in (self.anchor, self.start_at, self.end_at)):
            raise ContentError("time")
        if self.end_at and self.start_at and self.end_at <= self.start_at:
            raise ContentError("time")
        if any(d not in range(7) for d in self.weekdays) or any(d not in range(1, 32) for d in self.monthdays):
            raise ContentError("time")
        if (self.window_start is None) != (self.window_end is None):
            raise ContentError("time")
        if any(t and (t.tzinfo or t.second or t.microsecond) for t in (self.window_start, self.window_end)):
            raise ContentError("time")
        if self.anchor.second or self.anchor.microsecond:
            raise ContentError("time")
        return self

    def next(self, after: datetime, count: int = 5, *, inclusive: bool = False) -> list[datetime]:
        if after.tzinfo is None or not 1 <= count <= 100:
            raise ContentError("time")
        zone = ZoneInfo(self.timezone)
        anchor = self.anchor.astimezone(zone).replace(tzinfo=None)
        lower = max(after, self.start_at) if self.start_at else after
        # Revisit local candidates around backward timezone transitions, then compare UTC.
        local_lower = lower.astimezone(zone).replace(tzinfo=None) - timedelta(days=2)
        step = timedelta(minutes=self.every_minutes)
        k = max(0, math.floor((local_lower - anchor) / step))
        horizon = lower.astimezone(zone).replace(tzinfo=None) + timedelta(days=366 * 5)
        result: list[datetime] = []
        for _ in range(50000):
            point = anchor + k * step
            if point > horizon:
                break
            if point.weekday() not in self.weekdays or (self.monthdays and point.day not in self.monthdays):
                tomorrow = datetime.combine(point.date() + timedelta(days=1), time())
                k = max(k + 1, math.ceil((tomorrow - anchor) / step))
                continue
            start, end = self.window_start, self.window_end
            clock = point.time()
            if start is not None and end is not None and start != end:
                inside = start <= clock < end if start < end else clock >= start or clock < end
                if not inside:
                    boundary = datetime.combine(point.date(), start)
                    if boundary <= point:
                        boundary += timedelta(days=1)
                    k = max(k + 1, math.ceil((boundary - anchor) / step))
                    continue
            instant = local_instant(point, self.timezone, self.dst)
            k += 1
            if instant is None or instant < after or (instant == after and not inclusive):
                continue
            if self.start_at and instant < self.start_at:
                continue
            if self.end_at and instant >= self.end_at:
                break
            result.append(instant)
            if len(result) == count:
                break
        return sorted(set(result))


class WeeklySlot(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weekday: int = Field(ge=0, le=6)
    at: time

    @model_validator(mode="after")
    def valid_time(self):
        if self.at.tzinfo or self.at.second or self.at.microsecond:
            raise ContentError("time")
        return self


def calendar_times(slots: list[dict], timezone: str, start: datetime, count: int,
                   occupied: set[datetime] | None = None) -> list[datetime]:
    if start.tzinfo is None or not 1 <= count <= 100:
        raise ContentError("time")
    try:
        zone = ZoneInfo(timezone)
    except (KeyError, ValueError) as exc:
        raise ContentError("time") from exc
    parsed = [WeeklySlot.model_validate(slot) for slot in slots]
    if not 1 <= len(parsed) <= 100 or len({(s.weekday, s.at) for s in parsed}) != len(parsed):
        raise ContentError("time")
    date = start.astimezone(zone).date()
    candidates = []
    for day in range(366 * 3):
        current = date + timedelta(days=day)
        for slot in parsed:
            if slot.weekday == current.weekday():
                instant = local_instant(datetime.combine(current, slot.at), timezone)
                if instant and instant >= start and instant not in (occupied or set()):
                    candidates.append(instant)
        if len(candidates) >= count:
            return sorted(candidates)[:count]
    raise ContentError("time")
