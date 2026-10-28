"""Environment of the Bot Factory: FACTORY_* variables (FACTORY_TOKEN, FACTORY_ADMIN_IDS…).

The encryption key of user bot tokens is platform-wide: FACTORY_SECRET_KEY.
"""

from __future__ import annotations

from core.config import BaseBotEnv


class FactoryEnv(BaseBotEnv):
    pass
