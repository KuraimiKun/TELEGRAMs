"""Two clean, paginated CV templates; all AI content is escaped before entering HTML."""

from __future__ import annotations

import html

from bots.cvbot.schemas import ImprovedCV

TEMPLATES = {
    "classic": "h1 { color: #172554; } h2 { border-bottom: 1px solid #94a3b8; color: #172554; }",
    "modern": "h1 { color: #0f766e; } h2 { background-color: #ecfdf5; color: #115e59; padding: 5px; }",
}


def render_pdf(cv: ImprovedCV, template: str = "classic") -> bytes:
    import pymupdf as fitz

    if template not in TEMPLATES:
        raise ValueError("unknown CV template")
    e = html.escape
    sections = "".join(
        f"<h2>{e(s.title)}</h2>" + "".join(f"<p class='bullet'>• {e(b)}</p>" for b in s.bullets)
        for s in cv.sections
    )
    # MuPDF Story supports Unicode shaping and font fallback for Arabic as well as Latin content.
    direction = ' dir="rtl"' if any("\u0600" <= char <= "\u06ff" for char in cv.summary) else ""
    markup = (
        f"<html><body{direction}><h1>{e(cv.name)}</h1><p class='headline'>{e(cv.headline)}</p>"
        f"<p class='contact'>{e(cv.contact)}</p><p>{e(cv.summary)}</p>{sections}</body></html>"
    )
    css = (
        "body {font-family: sans-serif; font-size: 10.5pt; color: #1e293b; line-height: 1.45;}"
        "h1 {font-size: 26pt; margin-bottom: 4pt;} h2 {font-size: 13pt; margin-top: 14pt;}"
        ".bullet {margin-top: 0pt; margin-bottom: 5pt;} .headline {font-size: 13pt;} .contact {font-size: 9pt; color: #475569;}"
        + TEMPLATES[template]
    )
    story = fitz.Story(html=markup, user_css=css)

    def rectangle(number, filled):
        if number > 30:
            raise ValueError("generated CV exceeds page cap")
        return fitz.Rect(0, 0, 595, 842), fitz.Rect(44, 40, 551, 802), None

    with story.write_with_links(rectangle) as document:
        return document.tobytes(garbage=4, deflate=True)
