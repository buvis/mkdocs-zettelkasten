"""E2E tests for color scheme switching."""


def _get_css_var(page, var):
    return page.evaluate(
        f"getComputedStyle(document.documentElement).getPropertyValue('{var}').trim()"
    )


def _wait_for_scheme_css(page, expected_bg):
    """Wait for the scheme stylesheet to load and CSS variables to update."""
    page.wait_for_function(
        f"getComputedStyle(document.documentElement)"
        f".getPropertyValue('--bg-page').trim() === '{expected_bg}'"
    )


def _open_settings(page):
    page.click('[data-target="#mkdocs_settings_modal"]')
    page.wait_for_selector("#mkdocs_settings_modal[open]", timeout=2000)


def test_default_site_uses_solarized(page, default_site):
    page.goto(default_site)
    assert page.locator("html").get_attribute("data-color-scheme") == "solarized"


def test_default_site_loads_solarized_colors(page, default_site):
    page.goto(default_site)
    assert _get_css_var(page, "--bg-page") == "#f8f8f8"


def test_switch_to_selenized_via_modal(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    page.click('.scheme-card[data-scheme-id="selenized"]')
    _wait_for_scheme_css(page, "#fbf3db")
    assert _get_css_var(page, "--bg-page") == "#fbf3db"


def test_scheme_persists_on_reload(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    page.click('.scheme-card[data-scheme-id="selenized"]')
    _wait_for_scheme_css(page, "#fbf3db")
    page.reload()
    assert page.locator("html").get_attribute("data-color-scheme") == "selenized"
    assert _get_css_var(page, "--bg-page") == "#fbf3db"


def test_scheme_stored_in_localstorage(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    page.click('.scheme-card[data-scheme-id="selenized"]')
    value = page.evaluate("localStorage.getItem('color-scheme')")
    assert value == "selenized"
