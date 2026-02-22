"""E2E tests for dark theme toggle via settings modal."""



def _open_settings(page):
    page.click('[data-target="#mkdocs_settings_modal"]')
    page.wait_for_selector("#mkdocs_settings_modal[open]", timeout=2000)


def test_settings_button_exists(page, default_site):
    page.goto(default_site)
    toggle = page.locator('[data-target="#mkdocs_settings_modal"]')
    assert toggle.is_visible()


def test_toggle_to_dark_and_back(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    page.click("#dark-mode-toggle")
    assert page.locator("html").get_attribute("data-theme") == "dark"

    page.click("#dark-mode-toggle")
    assert page.locator("html").get_attribute("data-theme") == "light"


def test_dark_theme_persists_on_reload(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    page.click("#dark-mode-toggle")
    assert page.locator("html").get_attribute("data-theme") == "dark"

    page.reload()
    assert page.locator("html").get_attribute("data-theme") == "dark"


def test_localstorage_stores_theme(page, default_site):
    page.goto(default_site)
    _open_settings(page)
    page.click("#dark-mode-toggle")
    value = page.evaluate("localStorage.getItem('theme')")
    assert value == "dark"


def test_system_dark_preference_fallback(page, default_site):
    page.emulate_media(color_scheme="dark")
    page.goto(default_site)
    page.evaluate("localStorage.removeItem('theme')")
    page.reload()
    assert page.locator("html").get_attribute("data-theme") == "dark"
