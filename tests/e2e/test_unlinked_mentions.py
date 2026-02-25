"""E2E tests for unlinked mentions section."""

# This zettel should receive an unlinked mention from the fixture
COLOR_SCHEMES = "20260224141223"


def test_unlinked_mentions_section_visible(page, default_site):
    page.goto(f"{default_site}/{COLOR_SCHEMES}/")
    section = page.locator(".unlinked-mentions")
    assert section.count() >= 1


def test_unlinked_mention_has_source_link(page, default_site):
    page.goto(f"{default_site}/{COLOR_SCHEMES}/")
    mentions = page.locator(".unlinked-mentions a")
    texts = [mentions.nth(i).inner_text() for i in range(mentions.count())]
    assert any("Unlinked mention fixture" in t for t in texts)


def test_unlinked_mention_has_snippet(page, default_site):
    page.goto(f"{default_site}/{COLOR_SCHEMES}/")
    snippet = page.locator(".unlinked-mentions .backlink-snippet")
    assert snippet.count() >= 1


def test_unlinked_mention_snippet_has_highlight(page, default_site):
    page.goto(f"{default_site}/{COLOR_SCHEMES}/")
    mark = page.locator(".unlinked-mentions .backlink-snippet mark")
    assert mark.count() >= 1
