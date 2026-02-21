"""E2E tests for color scheme gallery page."""


def test_gallery_page_loads(page, default_site):
    page.goto(f"{default_site}/color-schemes.html")
    assert page.locator("h1").text_content() == "Color Schemes"


def test_gallery_has_all_schemes(page, default_site):
    page.goto(f"{default_site}/color-schemes.html")
    page.wait_for_selector(".gallery-card", timeout=3000)
    cards = page.locator(".gallery-card")
    assert cards.count() >= 25


def test_gallery_has_category_headings(page, default_site):
    page.goto(f"{default_site}/color-schemes.html")
    page.wait_for_selector("#gallery-grid h2", timeout=3000)
    headings = page.locator("#gallery-grid h2")
    assert headings.count() >= 4
