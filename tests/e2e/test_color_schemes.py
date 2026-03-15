"""E2E tests for color scheme gallery page."""


def test_gallery_page_loads(page, default_site):
    page.goto(f"{default_site}/color-schemes.html")
    assert page.locator("h1").text_content() == "Color Schemes"


def test_gallery_has_all_schemes(page, default_site):
    expected = len(page.request.get(f"{default_site}/css/schemes/registry.json").json())
    page.goto(f"{default_site}/color-schemes.html")
    page.wait_for_selector(".gallery-card", timeout=3000)
    cards = page.locator(".gallery-card")
    assert cards.count() == expected


def test_gallery_has_category_headings(page, default_site):
    page.goto(f"{default_site}/color-schemes.html")
    page.wait_for_selector("#gallery-grid h2", timeout=3000)
    headings = page.locator("#gallery-grid h2")
    assert headings.count() >= 4


def test_gallery_marks_current_scheme(page, default_site):
    page.goto(f"{default_site}/color-schemes.html")
    current = page.locator(".gallery-card--active .gallery-current")
    current.wait_for(state="visible", timeout=3000)
    assert current.inner_text() == "Current"
