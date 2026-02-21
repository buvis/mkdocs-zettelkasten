"""E2E tests for responsive layout at mobile viewport."""

MOBILE_WIDTH = 375
MOBILE_HEIGHT = 667


def test_navbar_collapses_on_mobile(page, default_site):
    page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
    page.goto(default_site)
    # hamburger button visible
    assert page.locator("button.navbar-toggler").is_visible()
    # nav items hidden
    assert not page.locator("#navbar-collapse").is_visible()


def test_hamburger_opens_nav(page, default_site):
    page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
    page.goto(default_site)
    page.click("button.navbar-toggler")
    page.locator("#navbar-collapse").wait_for(state="visible")
    assert page.locator("#navbar-collapse").is_visible()


def test_content_readable_on_mobile(page, default_site):
    page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
    page.goto(f"{default_site}/20211122194827/")
    body = page.locator(".file-body")
    assert body.is_visible()
    # content should not overflow horizontally
    overflow = page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    assert overflow is False


def test_zettel_card_fits_mobile(page, default_site):
    page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
    page.goto(f"{default_site}/20211122194827/")
    zettel = page.locator(".zettel")
    box = zettel.bounding_box()
    assert box["width"] <= MOBILE_WIDTH


def test_nav_items_accessible_on_mobile(page, default_site):
    page.set_viewport_size({"width": MOBILE_WIDTH, "height": MOBILE_HEIGHT})
    page.goto(f"{default_site}/20211122195311/")
    page.click("button.navbar-toggler")
    page.locator("#navbar-collapse").wait_for(state="visible")
    # settings button should be accessible in expanded nav
    assert page.locator('[data-target="#mkdocs_settings_modal"]').is_visible()
