from conftest import ZETTEL_INSTALL
from playwright.sync_api import expect


def test_previews_json_exists(page, preview_site):
    resp = page.request.get(f"{preview_site}/previews.json")
    assert resp.ok
    data = resp.json()
    assert ZETTEL_INSTALL in data
    assert "title" in data[ZETTEL_INSTALL]
    assert "excerpt" in data[ZETTEL_INSTALL]


def test_hover_shows_popover(page, preview_site):
    page.goto(preview_site)
    link = page.locator(f"a[href*='{ZETTEL_INSTALL}']").first
    link.hover()
    popover = page.locator("#zettel-preview-popover")
    popover.wait_for(state="visible", timeout=5000)
    assert popover.is_visible()


def test_popover_contains_title(page, preview_site):
    page.goto(preview_site)
    link = page.locator(f"a[href*='{ZETTEL_INSTALL}']").first
    link.hover()
    popover = page.locator("#zettel-preview-popover")
    popover.wait_for(state="visible", timeout=5000)
    title = popover.locator(".preview-title")
    assert title.text_content() == "Install MkDocs Zettelkasten"


def test_popover_contains_excerpt(page, preview_site):
    page.goto(preview_site)
    link = page.locator(f"a[href*='{ZETTEL_INSTALL}']").first
    link.hover()
    popover = page.locator("#zettel-preview-popover")
    popover.wait_for(state="visible", timeout=5000)
    excerpt = popover.locator(".preview-excerpt")
    assert len(excerpt.text_content()) > 0


def test_popover_hides_on_mouseleave(page, preview_site):
    page.goto(preview_site)
    link = page.locator(f"a[href*='{ZETTEL_INSTALL}']").first
    link.hover()
    popover = page.locator("#zettel-preview-popover")
    popover.wait_for(state="visible", timeout=5000)
    # Move away from the link
    page.locator("h1").first.hover()
    expect(popover).to_have_css("opacity", "0")


def test_no_popover_on_external_link(page, preview_site):
    page.goto(preview_site)
    ext_link = page.locator("a[href*='wikipedia']").first
    ext_link.hover()
    popover = page.locator("#zettel-preview-popover")
    expect(popover).not_to_be_visible()


def test_no_popover_when_disabled(page, default_site):
    page.goto(default_site)
    popover = page.locator("#zettel-preview-popover")
    expect(popover).to_have_count(0)
