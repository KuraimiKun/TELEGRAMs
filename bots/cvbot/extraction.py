"""Bounded document extraction. Input bytes and OCR temporary files never reach durable storage."""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


class ExtractionError(ValueError):
    pass


@dataclass(slots=True)
class Extracted:
    text: str
    # Scanned pages are PNGs, consumed immediately by vision/OCR and then discarded.
    images: tuple[bytes, ...] = ()


def image_png(data: bytes) -> bytes:
    from PIL import Image, ImageOps

    try:
        with Image.open(io.BytesIO(data)) as opened:
            if opened.width * opened.height > 25_000_000:
                raise ExtractionError("image is too large")
            image = ImageOps.exif_transpose(opened).convert("RGB")
            image.thumbnail((1800, 1800))
            out = io.BytesIO()
            image.save(out, format="PNG")
            return out.getvalue()
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ExtractionError("invalid image") from exc


def extract(data: bytes, filename: str, *, max_pages: int = 12, max_chars: int = 40000) -> Extracted:
    """Extract readable text, returning scanned pages for the caller's AI/OCR path."""
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".pdf":
            import pymupdf as fitz

            with fitz.open(stream=data, filetype="pdf") as doc:
                if doc.needs_pass or not 0 < len(doc) <= max_pages:
                    raise ExtractionError("encrypted PDF or page limit exceeded")
                text_parts, images = [], []
                for page in doc:
                    page_text = page.get_text().strip()
                    text_parts.append(page_text)
                    if sum(len(p) for p in text_parts) > max_chars:
                        raise ExtractionError("text limit exceeded")
                    if len(page_text) < 30:
                        scale = min(2, 1600 / max(page.rect.width, page.rect.height))
                        images.append(page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).tobytes("png"))
                result = Extracted("\n\n".join(text_parts), tuple(images))
        elif suffix == ".docx":
            from docx import Document

            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if len(archive.infolist()) > 1000 or sum(i.file_size for i in archive.infolist()) > 50_000_000:
                    raise ExtractionError("expanded document is too large")
            docx = Document(io.BytesIO(data))
            paragraphs = [p.text for p in docx.paragraphs]
            paragraphs.extend(cell.text for table in docx.tables for row in table.rows for cell in row.cells)
            result = Extracted("\n".join(paragraphs).strip())
        elif suffix in {".jpg", ".jpeg", ".png", ".webp"}:
            result = Extracted("", (image_png(data),))
        elif suffix == ".txt":
            result = Extracted(data.decode("utf-8-sig").strip())
        else:
            raise ExtractionError("unsupported document")
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError("cannot read document") from exc
    if len(result.text) > max_chars:
        raise ExtractionError("text limit exceeded")
    if not result.text and not result.images:
        raise ExtractionError("empty document")
    return result


def tesseract_text(image: bytes) -> str:
    """Offline Arabic/English OCR fallback, with a deadline and automatic scratch cleanup."""
    binary = shutil.which("tesseract")
    if binary is None:
        raise ExtractionError("OCR is unavailable")
    with tempfile.TemporaryDirectory(prefix="cv-ocr-") as folder:
        path = Path(folder) / "page.png"
        path.write_bytes(image)
        try:
            result = subprocess.run(
                [binary, str(path), "stdout", "-l", "ara+eng", "--psm", "3"],
                capture_output=True, check=True, timeout=30,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            raise ExtractionError("OCR failed") from exc
        return result.stdout.decode("utf-8", errors="replace").strip()
