def test_previews_json_exists(page, preview_site):
    resp = page.request.get(f"{preview_site}/previews.json")
    assert resp.ok
    data = resp.json()
    assert "20211122194827" in data
    assert "title" in data["20211122194827"]
    assert "excerpt" in data["20211122194827"]


def test_hover_shows_popover(page, preview_site):
    page.goto(preview_site)
    link = page.locator("a[href*='20211122194827']").first
    link.hover()
    popover = page.locator("#zettel-preview-popover")
    popover.wait_for(state="visible", timeout=5000)
    assert popover.is_visible()


def test_popover_contains_title(page, preview_site):
    page.goto(preview_site)
    link = page.locator("a[href*='20211122194827']").first
    link.hover()
    popover = page.locator("#zettel-preview-popover")
    popover.wait_for(state="visible", timeout=5000)
    title = popover.locator(".preview-title")
    assert title.text_content() == "Install MkDocs Zettelkasten"


def test_popover_contains_excerpt(page, preview_site):
    page.goto(preview_site)
    link = page.locator("a[href*='20211122194827']").first
    link.hover()
    popover = page.locator("#zettel-preview-popover")
    popover.wait_for(state="visible", timeout=5000)
    excerpt = popover.locator(".preview-excerpt")
    assert len(excerpt.text_content()) > 0


def test_popover_hides_on_mouseleave(page, preview_site):
    page.goto(preview_site)
    link = page.locator("a[href*='20211122194827']").first
    link.hover()
    popover = page.locator("#zettel-preview-popover")
    popover.wait_for(state="visible", timeout=5000)
    # Move away from the link
    page.locator("h1").first.hover()
    page.wait_for_timeout(500)
    assert popover.evaluate("el => getComputedStyle(el).opacity") == "0"


def test_no_popover_on_external_link(page, preview_site):
    page.goto(preview_site)
    ext_link = page.locator("a[href*='wikipedia']").first
    ext_link.hover()
    page.wait_for_timeout(500)
    popover = page.locator("#zettel-preview-popover")
    assert popover.count() == 0 or popover.evaluate(
        "el => getComputedStyle(el).display"
    ) == "none"


def test_no_popover_when_disabled(page, default_site):
    page.goto(default_site)
    page.wait_for_timeout(500)
    popover = page.locator("#zettel-preview-popover")
    assert popover.count() == 0
