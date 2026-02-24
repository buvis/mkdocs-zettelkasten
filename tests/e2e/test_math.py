from playwright.sync_api import Page


def test_katex_css_loaded(page: Page, math_site: str) -> None:
    page.goto(f"{math_site}/20260223142755/")
    link = page.locator("link[href*='katex']")
    assert link.count() == 1


def test_katex_js_loaded(page: Page, math_site: str) -> None:
    page.goto(f"{math_site}/20260223142755/")
    script = page.locator("script[src*='katex']")
    assert script.count() == 1


def test_inline_math_rendered(page: Page, math_site: str) -> None:
    page.goto(f"{math_site}/20260223142755/")
    page.locator("span.arithmatex .katex").first.wait_for(
        state="attached", timeout=5000
    )
    inline = page.locator("span.arithmatex .katex")
    assert inline.count() > 0


def test_display_math_rendered(page: Page, math_site: str) -> None:
    page.goto(f"{math_site}/20260223142755/")
    page.locator("div.arithmatex .katex-display").first.wait_for(
        state="attached", timeout=5000
    )
    display = page.locator("div.arithmatex .katex-display")
    assert display.count() > 0


def test_katex_not_loaded_when_disabled(page: Page, default_site: str) -> None:
    page.goto(default_site)
    link = page.locator("link[href*='katex']")
    assert link.count() == 0
    script = page.locator("script[src*='katex']")
    assert script.count() == 0
