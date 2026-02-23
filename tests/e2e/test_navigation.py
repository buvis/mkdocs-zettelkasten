"""E2E tests for navigation: prev/next links, search modal, keyboard shortcuts."""

from conftest import ZETTEL_DEMO, ZETTEL_INSTALL, ZETTEL_PUBLISH

# 20211122195311 (Run a demo) has both prev and next links
TARGET = f"/{ZETTEL_DEMO}/"


def test_prev_link_exists_and_navigates(page, default_site):
    page.goto(f"{default_site}{TARGET}")
    prev_link = page.locator('a[rel="prev"]')
    assert prev_link.count() == 1
    href = prev_link.get_attribute("href")
    assert href is not None
    assert ZETTEL_INSTALL in href
    prev_link.click()
    page.wait_for_url(f"**/{ZETTEL_INSTALL}/**")


def test_next_link_exists_and_navigates(page, default_site):
    page.goto(f"{default_site}{TARGET}")
    next_link = page.locator('a[rel="next"]')
    assert next_link.count() == 1
    href = next_link.get_attribute("href")
    assert href is not None
    assert ZETTEL_PUBLISH in href
    next_link.click()
    page.wait_for_url(f"**/{ZETTEL_PUBLISH}/**")


def test_search_modal_opens_on_click(page, default_site):
    page.goto(f"{default_site}{TARGET}")
    page.click('a[data-target="#mkdocs_search_modal"]')
    modal = page.locator("#mkdocs_search_modal")
    modal.wait_for(state="visible")
    assert page.locator("#mkdocs-search-query").is_visible()


def test_search_modal_opens_with_s_key(page, default_site):
    page.goto(f"{default_site}{TARGET}")
    page.keyboard.press("s")
    modal = page.locator("#mkdocs_search_modal")
    modal.wait_for(state="visible")
    assert page.locator("#mkdocs-search-query").is_visible()


def test_keyboard_shortcut_n_navigates_next(page, default_site):
    page.goto(f"{default_site}{TARGET}")
    page.keyboard.press("n")
    page.wait_for_url(f"**/{ZETTEL_PUBLISH}/**")


def test_keyboard_shortcut_p_navigates_prev(page, default_site):
    page.goto(f"{default_site}{TARGET}")
    page.keyboard.press("p")
    page.wait_for_url(f"**/{ZETTEL_INSTALL}/**")
