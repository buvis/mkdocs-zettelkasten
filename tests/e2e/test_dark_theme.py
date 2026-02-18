"""E2E tests for dark theme toggle (testscript 001)."""

import re


def test_toggle_button_exists(page, default_site):
    page.goto(default_site)
    toggle = page.locator("#theme-toggle")
    assert toggle.is_visible()
    assert page.locator("#theme-icon.fa.fa-moon-o").count() == 1


def test_toggle_to_dark_and_back(page, default_site):
    page.goto(default_site)
    page.click("#theme-toggle")
    assert page.locator("html").get_attribute("data-theme") == "dark"
    assert page.locator("#theme-icon.fa.fa-sun-o").count() == 1

    page.click("#theme-toggle")
    assert page.locator("html").get_attribute("data-theme") == "light"
    assert page.locator("#theme-icon.fa.fa-moon-o").count() == 1


def test_dark_theme_persists_on_reload(page, default_site):
    page.goto(default_site)
    page.click("#theme-toggle")
    assert page.locator("html").get_attribute("data-theme") == "dark"

    page.reload()
    assert page.locator("html").get_attribute("data-theme") == "dark"


def test_localstorage_stores_theme(page, default_site):
    page.goto(default_site)
    page.click("#theme-toggle")
    value = page.evaluate("localStorage.getItem('theme')")
    assert value == "dark"


def test_system_dark_preference_fallback(page, default_site):
    # must set emulate_media before navigation for the inline script to pick it up
    page.emulate_media(color_scheme="dark")
    page.goto(default_site)
    page.evaluate("localStorage.removeItem('theme')")
    page.reload()
    assert page.locator("html").get_attribute("data-theme") == "dark"


def test_code_highlight_differs_between_themes(page, default_site):
    page.goto(f"{default_site}/20211122195311/")
    light_bg = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--bg-codehilite').trim()"
    )
    page.click("#theme-toggle")
    dark_bg = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--bg-codehilite').trim()"
    )
    assert _normalize_color(light_bg) != _normalize_color(dark_bg)


def _normalize_color(color: str) -> str:
    """Normalize hex color to lowercase without spaces."""
    return re.sub(r"\s+", "", color).lower()
