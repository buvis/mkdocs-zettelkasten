"""E2E tests for selenized theme support (testscript 065)."""


def _get_css_var(page, var):
    return page.evaluate(
        f"getComputedStyle(document.documentElement).getPropertyValue('{var}').trim()"
    )


def test_default_site_uses_solarized(page, default_site):
    page.goto(default_site)
    assert _get_css_var(page, "--bg-page") == "#f8f8f8"


def test_selenized_site_has_different_bg(page, selenized_site):
    page.goto(selenized_site)
    assert _get_css_var(page, "--bg-page") == "#fbf3db"


def test_selenized_css_files_loaded(page, selenized_site):
    page.goto(selenized_site)
    assert page.locator('link[href*="selenized-light"]').count() >= 1
    assert page.locator('link[href*="selenized-dark"]').count() >= 1


def test_selenized_dark_toggle(page, selenized_site):
    page.goto(selenized_site)
    page.click("#theme-toggle")
    assert _get_css_var(page, "--bg-page") == "#103c48"


def test_selenized_toggle_back_to_light(page, selenized_site):
    page.goto(selenized_site)
    page.click("#theme-toggle")
    page.click("#theme-toggle")
    assert _get_css_var(page, "--bg-page") == "#fbf3db"


def test_solarized_and_selenized_differ(page, default_site, selenized_site):
    page.goto(default_site)
    solarized_bg = _get_css_var(page, "--bg-page")
    page.goto(selenized_site)
    selenized_bg = _get_css_var(page, "--bg-page")
    assert solarized_bg != selenized_bg
