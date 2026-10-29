"""Container progress probe, independent of tokens, configuration loading and process heartbeat."""

import sys
import time
from pathlib import Path

PROGRESS_FILE = Path("/tmp/channelmanager-worker-progress")
MAX_AGE = 90


def pulse(path: Path = PROGRESS_FILE):
    path.write_text(str(time.time()), encoding="utf-8")


def healthy(path: Path = PROGRESS_FILE, *, now=None, max_age=MAX_AGE):
    try:
        age = (time.time() if now is None else now) - float(path.read_text(encoding="utf-8"))
        return 0 <= age < max_age
    except (OSError, ValueError):
        return False


if __name__ == "__main__":
    sys.exit(0 if healthy() else 1)
