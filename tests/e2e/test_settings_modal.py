"""E2E tests for the settings modal."""

from playwright.sync_api import expect


def _open_settings(page):
    page.click('[data-target="#mkdocs_settings_modal"]')
    page.wait_for_selector("#mkdocs_settings_modal[open]", timeout=2000)


def test_settings_modal_opens(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    assert page.locator("#mkdocs_settings_modal").is_visible()


def test_settings_modal_has_scheme_grid(page, default_site):
    expected = len(page.request.get(f"{default_site}/css/schemes/registry.json").json())
    page.goto(default_site)
    _open_settings(page)
    cards = page.locator("#scheme-grid .scheme-card")
    assert cards.count() == expected


def test_settings_modal_has_code_theme_picker(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    grid = page.locator("#code-theme-grid")
    assert grid.is_visible()
    cards = grid.locator(".scheme-card")
    assert cards.count() > 0


def test_settings_modal_has_dark_toggle(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    toggle = page.locator("#dark-mode-toggle")
    assert toggle.is_visible()


def test_settings_modal_closes(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    page.click("#mkdocs_settings_modal .modal-close")
    expect(page.locator("#mkdocs_settings_modal")).not_to_be_visible()
