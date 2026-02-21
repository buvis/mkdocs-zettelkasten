"""E2E tests for code block copy button (testscript 032)."""

TARGET = "/20211122195311/"
# pymdownx.superfences produces .highlight, codehilite produces .codehilite
CODE_BLOCK = ".highlight"


def _goto_and_wait(page, url):
    """Navigate and wait for JS to inject copy buttons."""
    page.goto(url)
    page.wait_for_selector(f"{CODE_BLOCK} .copy-btn")


def test_copy_button_exists_on_code_blocks(page, default_site):
    _goto_and_wait(page, f"{default_site}{TARGET}")
    blocks = page.locator(CODE_BLOCK)
    assert blocks.count() > 0
    for i in range(blocks.count()):
        assert blocks.nth(i).locator(".copy-btn").count() == 1


def test_copy_button_hidden_by_default(page, default_site):
    _goto_and_wait(page, f"{default_site}{TARGET}")
    btn = page.locator(f"{CODE_BLOCK} .copy-btn").first
    opacity = btn.evaluate("el => getComputedStyle(el).opacity")
    assert float(opacity) == 0


def test_copy_button_visible_on_hover(page, default_site):
    _goto_and_wait(page, f"{default_site}{TARGET}")
    block = page.locator(CODE_BLOCK).first
    block.hover()
    # wait for 0.2s CSS opacity transition to finish
    page.wait_for_timeout(300)
    opacity = block.locator(".copy-btn").evaluate("el => getComputedStyle(el).opacity")
    assert float(opacity) == 1


def test_copy_button_fades_on_mouse_leave(page, default_site):
    _goto_and_wait(page, f"{default_site}{TARGET}")
    block = page.locator(CODE_BLOCK).first
    block.hover()
    block.locator(".copy-btn").wait_for(state="visible")

    page.locator("body").hover(position={"x": 0, "y": 0})
    page.wait_for_timeout(500)
    opacity = block.locator(".copy-btn").evaluate("el => getComputedStyle(el).opacity")
    assert float(opacity) == 0


def test_copy_button_shows_checkmark_on_click(page, default_site):
    _goto_and_wait(page, f"{default_site}{TARGET}")
    block = page.locator(CODE_BLOCK).first
    block.hover()
    btn = block.locator(".copy-btn")
    btn.wait_for(state="visible")
    btn.click()
    assert btn.inner_text() == "\u2713"


def test_copy_button_works_in_dark_mode(page, default_site):
    _goto_and_wait(page, f"{default_site}{TARGET}")
    page.click('[data-target="#mkdocs_settings_modal"]')
    page.wait_for_selector("#mkdocs_settings_modal.show", timeout=2000)
    page.click("#dark-mode-toggle")
    page.click('#mkdocs_settings_modal .close')
    page.wait_for_timeout(500)
    block = page.locator(CODE_BLOCK).first
    block.hover()
    page.wait_for_timeout(300)
    opacity = block.locator(".copy-btn").evaluate("el => getComputedStyle(el).opacity")
    assert float(opacity) == 1
