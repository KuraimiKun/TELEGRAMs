"""Redis key namespacing so bots sharing one Redis never collide."""

from __future__ import annotations


class KeySpace:
    """Builds bot-scoped Redis keys.

    >>> ks = KeySpace("socialdownload")
    >>> ks("q", "high")
    'socialdownload:q:high'
    """

    __slots__ = ("prefix", "slug")

    def __init__(self, slug: str) -> None:
        self.slug = slug
        self.prefix = f"{slug}:"

    def __call__(self, *parts: object) -> str:
        return self.prefix + ":".join(str(p) for p in parts)

    def __repr__(self) -> str:
        return f"KeySpace({self.slug!r})"


# Keys shared by the whole platform (not owned by any bot).
PLATFORM = KeySpace("platform")
