"""Environment for the document worker (DOCTOOLS_*)."""

from pydantic import Field

from core.config import BaseBotEnv


class DocToolsEnv(BaseBotEnv):
    worker_concurrency: int = Field(default=2, ge=1, le=16)
    job_timeout_seconds: int = Field(default=300, ge=30, le=1800)
    ocr_timeout_seconds: int = Field(default=45, ge=5, le=180)
    tesseract_command: str = "tesseract"
