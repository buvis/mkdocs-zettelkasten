"""E2E tests for error paths and graceful degradation."""

from conftest import ZETTEL_PUBLISH


def test_broken_link_shows_validation_warning(page, default_site):
    """Zettel with broken internal links shows validation badge."""
    page.goto(f"{default_site}/{ZETTEL_PUBLISH}/")
    badge = page.locator(".validation-badge")
    assert badge.count() >= 1


def test_tags_page_renders_without_errors(page, default_site):
    """Non-zettel page (tags) renders successfully."""
    resp = page.goto(f"{default_site}/tags.html")
    assert resp.status == 200
    assert page.locator("h1").count() >= 1


def test_index_page_renders_without_errors(page, default_site):
    """Non-zettel page (index) renders successfully."""
    resp = page.goto(f"{default_site}/")
    assert resp.status == 200
    assert page.locator("body").inner_text() != ""


def test_graph_page_absent_when_disabled(page, default_site):
    """Graph page returns 404 when graph_enabled=false."""
    resp = page.goto(f"{default_site}/graph.html")
    assert resp.status == 404


def test_preview_popover_absent_when_disabled(page, default_site):
    """No preview popover element when preview_enabled=false."""
    page.goto(default_site)
    assert page.locator("#zettel-preview-popover").count() == 0
