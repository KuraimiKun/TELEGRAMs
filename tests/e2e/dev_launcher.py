"""Test-only CLI launcher: fake AI, real runtime and explicit Windows shutdown support."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
import threading


def main() -> None:
    # Import before the CLI imports the registry so every process gets the scripted AI client.
    import core.sdk.registry as registry
    from tests.fake_ai import fake_ai

    analysis = {
        "score": 82,
        "subscores": {"ats": 80, "impact": 85, "clarity": 82, "formatting": 81},
        "strengths": ["Clear skills and experience"],
        "issues": [{"issue": "Generic achievement", "fix": "Add a measured outcome"}],
        "rewritten_bullets": [{"original": "Built a service", "improved": "Built a service; [add measured impact]"}],
        "missing_sections": ["Education"],
        "suggested_roles": ["Software engineer"],
        "language": "en",
    }
    registry.build_ai = lambda _platform, redis: fake_ai(redis, analysis)[0]

    if os.name == "nt":
        import core.runtime.app as app

        def install_windows_signals(stop: asyncio.Event) -> None:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGBREAK):
                signal.signal(sig, lambda *_: loop.call_soon_threadsafe(stop.set))

            # Windows subprocesses do not always share a console, so CTRL_BREAK is unavailable.
            # Ask the child to raise SIGTERM on its main thread, exercising the same drain handler.
            def read_shutdown() -> None:
                for line in sys.stdin:
                    if line.strip() == "SIGTERM":
                        loop.call_soon_threadsafe(signal.raise_signal, signal.SIGTERM)
                        return

            threading.Thread(target=read_shutdown, daemon=True).start()

        app.install_signal_handlers = install_windows_signals

    from core.__main__ import main as core_main

    core_main()


if __name__ == "__main__":
    main()
