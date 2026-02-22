"""E2E tests for reference/backlink icons (testscript 051)."""


def test_references_section_has_book_icon(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    refs = page.locator(".file-references")
    assert refs.count() > 0
    assert refs.locator("i.fa.fa-book").count() >= 1


def test_visually_hidden_text_exists(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    sr = page.locator(".file-references .visually-hidden")
    assert sr.count() >= 1
    assert "References" in sr.first.inner_text()


def test_icons_visible_in_light_mode(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    icon = page.locator(".file-references i.fa.fa-book").first
    assert icon.is_visible()


def test_icons_visible_in_dark_mode(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    page.click('[data-target="#mkdocs_settings_modal"]')
    page.wait_for_selector("#mkdocs_settings_modal[open]", timeout=2000)
    page.click("#dark-mode-toggle")
    icon = page.locator(".file-references i.fa.fa-book").first
    assert icon.is_visible()
