"""E2E tests for footer background styling (testscript 052)."""


def _get_computed(locator, prop):
    return locator.evaluate(f"el => getComputedStyle(el).{prop}")


def test_footer_bg_differs_from_body(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    refs_bg = _get_computed(page.locator(".file-references").first, "backgroundColor")
    body_bg = _get_computed(page.locator(".file-body").first, "backgroundColor")
    assert refs_bg != body_bg


def test_footer_has_border_top(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    style = _get_computed(page.locator(".file-references").first, "borderTopStyle")
    assert style == "solid"


def test_footer_italic_and_smaller(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    refs = page.locator(".file-references").first
    assert _get_computed(refs, "fontStyle") == "italic"
    refs_size = float(_get_computed(refs, "fontSize").replace("px", ""))
    body_size = float(
        _get_computed(page.locator(".file-body").first, "fontSize").replace("px", "")
    )
    assert refs_size < body_size


def test_footer_has_rounded_bottom_corners(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    refs = page.locator(".file-references").first
    bl = _get_computed(refs, "borderBottomLeftRadius")
    br = _get_computed(refs, "borderBottomRightRadius")
    assert bl != "0px"
    assert br != "0px"


def test_light_mode_accent_colors(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    bg_accent = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--bg-accent').trim()"
    )
    border_accent = page.evaluate(
        "getComputedStyle(document.documentElement).getPropertyValue('--border-accent').trim()"
    )
    assert bg_accent == "#eee8d5"
    assert border_accent == "#d4cbb3"


def test_dark_mode_footer_still_differs(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    page.click('[data-target="#mkdocs_settings_modal"]')
    page.wait_for_selector("#mkdocs_settings_modal.show", timeout=2000)
    page.click("#dark-mode-toggle")
    refs_bg = _get_computed(page.locator(".file-references").first, "backgroundColor")
    body_bg = _get_computed(page.locator(".file-body").first, "backgroundColor")
    assert refs_bg != body_bg
