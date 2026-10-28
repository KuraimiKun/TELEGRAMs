"""Recorded bibliographic metadata, source validation and inline citation rendering."""

import json
from datetime import UTC, datetime

import pytest

from bots.doctools.citations import (
    CitationError,
    CitationService,
    check_url,
    classify,
    crossref_reference,
    format_citations,
    openlibrary_reference,
    page_reference,
)

CROSSREF = {
    "message": {
        "DOI": "10.1038/nphys1170", "type": "journal-article",
        "title": ["The rise of quantum technology"], "container-title": ["Nature Physics"],
        "author": [{"given": "Jeremy", "family": "O'Brien"}, {"given": "Akira", "family": "Furusawa"}],
        "published-print": {"date-parts": [[2009, 10]]}, "volume": "5", "issue": "10", "page": "686-689",
        "publisher": "Springer Nature",
    },
}


def test_recorded_crossref_formats_four_styles():
    ref = crossref_reference(CROSSREF)
    result = format_citations(ref)
    assert set(result) == {"APA", "MLA", "Harvard", "Chicago"}
    assert "O'Brien, J. &amp; Furusawa, A." in result["APA"]
    assert "(2009)" in result["APA"]
    assert "<i>Nature Physics, 5</i>(10), 686–689" in result["APA"]
    assert "vol. 5, no. 10, 2009, pp. 686–689" in result["MLA"]
    assert "https://doi.org/10.1038/nphys1170" in result["Chicago"]


def test_isbn_book_and_page_metadata_missing_date_and_escaping():
    book = openlibrary_reference({"ISBN:9780140328721": {"title": "Matilda", "authors": [{"name": "Roald Dahl"}],
                                  "publish_date": "1988", "publishers": [{"name": "Puffin"}]}}, "9780140328721")
    assert format_citations(book)["APA"] == "Dahl, R. (1988). <i>Matilda</i>. Puffin."
    page = page_reference(b'<title>Example &amp; study</title><meta name="author" content="Jane Smith">', "https://example.org/study")
    styles = format_citations(page, accessed=datetime(2026, 10, 9, tzinfo=UTC))
    assert "(n.d.)" in styles["APA"]
    assert "Example &amp; study" in styles["APA"]
    assert "09 October 2026" in styles["Harvard"]


@pytest.mark.parametrize("value", ["10.1038/nphys1170", "doi:10.1038/nphys1170", "https://doi.org/10.1038/nphys1170"])
def test_doi_normalization(value):
    assert classify(value) == ("doi", "10.1038/nphys1170")


def test_isbn_checksums():
    assert classify("ISBN: 978-0-14-032872-1") == ("isbn", "9780140328721")
    assert classify("0-8044-2957-X") == ("isbn", "080442957X")
    with pytest.raises(CitationError):
        classify("9780140328722")


@pytest.mark.parametrize("url", ["file:///a", "http://127.0.0.1/a", "http://[::1]", "https://localhost",
                                "http://169.254.169.254/latest", "http://10.0.0.5", "http://example.org:6379/",
                                "https://user:pass@example.org", "http://[::ffff:127.0.0.1]/"])
def test_public_url_guard(url):
    with pytest.raises(CitationError):
        check_url(url)


async def test_lookup_uses_recorded_response_and_cache(ctx):
    calls = []

    async def fetch(url):
        calls.append(url)
        return json.dumps(CROSSREF).encode()

    svc = CitationService(ctx, fetch=fetch)
    first = await svc.lookup("10.1038/nphys1170")
    second = await svc.lookup("https://doi.org/10.1038/nphys1170")
    assert first == second
    assert calls == ["https://api.crossref.org/works/10.1038%2Fnphys1170"]
