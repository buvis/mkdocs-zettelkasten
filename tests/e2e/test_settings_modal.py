"""E2E tests for the settings modal."""


def _open_settings(page):
    page.click('[data-target="#mkdocs_settings_modal"]')
    page.wait_for_selector("#mkdocs_settings_modal.show", timeout=2000)


def test_settings_modal_opens(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    assert page.locator("#mkdocs_settings_modal").is_visible()


def test_settings_modal_has_scheme_grid(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    cards = page.locator(".scheme-card")
    assert cards.count() >= 25


def test_settings_modal_has_code_theme_picker(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    select = page.locator("#hljs-theme-select")
    assert select.is_visible()


def test_settings_modal_has_dark_toggle(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    toggle = page.locator("#dark-mode-toggle")
    assert toggle.is_visible()


def test_settings_modal_closes(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    page.click('#mkdocs_settings_modal .close')
    page.wait_for_timeout(500)
    assert not page.locator("#mkdocs_settings_modal").is_visible()
