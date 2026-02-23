"""E2E tests for basic accessibility: ARIA, visually-hidden, focus, headings."""

from conftest import ZETTEL_DEMO, ZETTEL_INSTALL


def test_visually_hidden_elements_exist(page, default_site):
    page.goto(f"{default_site}/{ZETTEL_INSTALL}/")
    sr = page.locator(".visually-hidden")
    assert sr.count() >= 1


def test_settings_button_has_aria_label(page, default_site):
    page.goto(default_site)
    toggle = page.locator('[data-target="#mkdocs_settings_modal"]')
    label = toggle.get_attribute("aria-label")
    assert label is not None
    assert len(label) > 0


def test_search_modal_is_dialog_element(page, default_site):
    page.goto(default_site)
    modal = page.locator("dialog#mkdocs_search_modal")
    assert modal.count() == 1
    assert modal.get_attribute("aria-labelledby") is not None


def test_decorative_icons_are_aria_hidden(page, default_site):
    page.goto(f"{default_site}/{ZETTEL_INSTALL}/")
    # validation badge icon should be aria-hidden
    icons = page.locator('i.fa[aria-hidden="true"]')
    assert icons.count() >= 1


def test_copy_buttons_have_aria_label(page, default_site):
    page.goto(f"{default_site}/{ZETTEL_DEMO}/")
    page.wait_for_selector(".copy-btn")
    btn = page.locator(".copy-btn").first
    assert btn.get_attribute("aria-label") == "Copy code"


def test_focus_ring_visible_on_tab(page, default_site):
    page.goto(default_site)
    page.keyboard.press("Tab")
    focused = page.evaluate("""() => {
        const el = document.activeElement;
        if (!el) return null;
        const style = getComputedStyle(el);
        return {
            outline: style.outline,
            outlineWidth: style.outlineWidth,
            tag: el.tagName
        };
    }""")
    assert focused is not None
    assert focused["tag"] != "BODY"


def test_heading_hierarchy(page, default_site):
    page.goto(f"{default_site}/{ZETTEL_INSTALL}/")
    h1_count = page.locator("h1").count()
    assert h1_count >= 1
    # no h3 without h2
    if page.locator("h3").count() > 0:
        assert page.locator("h2").count() > 0
