"""Source adapter and chunking tests."""

from __future__ import annotations

from studium.sources.adapters import detect_kind, extract_units
from studium.sources.chunking import chunk_units
from studium.sources.models import ExtractedUnit, SourceKind


def test_kind_detection() -> None:
    assert detect_kind("notes.md", "text/markdown") == SourceKind.MARKDOWN
    assert detect_kind("paper.pdf", None) == SourceKind.PDF
    assert detect_kind("page.html", "text/html") == SourceKind.HTML
    assert detect_kind("talk.vtt", None) == SourceKind.TRANSCRIPT
    assert detect_kind("plain.txt", "text/plain") == SourceKind.TEXT


def test_markdown_and_html_extraction_preserve_sections() -> None:
    markdown, _metadata = extract_units(
        b"# Title\n\n## Momentum\n\nVelocity accumulates updates.\n",
        filename="notes.md",
        kind=SourceKind.MARKDOWN,
    )
    assert any(unit.section == "Momentum" for unit in markdown)
    html, _html_metadata = extract_units(
        b"<html><body><h2>Learning Rate</h2><p>Step size controls stability.</p></body></html>",
        filename="page.html",
        kind=SourceKind.HTML,
    )
    assert html
    assert "Step size" in html[0].text


def test_chunking_keeps_page_and_offsets() -> None:
    units = [
        ExtractedUnit(text="Alpha. " + ("Word " * 80), page=1, section="Intro"),
        ExtractedUnit(text="Beta concludes the argument.", page=2, section="Close"),
    ]
    chunks = chunk_units("source_test", units, target_chars=80, overlap_chars=20)
    assert chunks
    assert chunks[0].page == 1
    assert chunks[0].section == "Intro"
    assert chunks[0].char_start is not None
    assert chunks[-1].page == 2
    assert chunks[-1].id.startswith("source_test:chunk:")
