"""E2E tests for backlink context snippets."""

# Child zettel linked from MOC — should have backlink with snippet
CHILD_ZETTEL = "20260224212155"
MOC_ZETTEL = "20260225120000"


def test_backlink_snippet_visible(page, default_site):
    page.goto(f"{default_site}/features/{CHILD_ZETTEL}/")
    snippet = page.locator(".backlink-snippet")
    assert snippet.count() >= 1


def test_backlink_snippet_contains_context(page, default_site):
    page.goto(f"{default_site}/features/{CHILD_ZETTEL}/")
    snippet = page.locator(".backlink-snippet")
    assert "type and maturity metadata support" in snippet.first.inner_text()


def test_backlink_snippet_has_highlight(page, default_site):
    page.goto(f"{default_site}/features/{CHILD_ZETTEL}/")
    mark = page.locator(".backlink-snippet mark")
    assert mark.count() >= 1


def test_backlink_highlight_contains_link_text(page, default_site):
    page.goto(f"{default_site}/features/{CHILD_ZETTEL}/")
    mark = page.locator(".backlink-snippet mark")
    assert "Note types and maturity badges" in mark.first.inner_text()
