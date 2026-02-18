"""E2E tests for navigation: prev/next links, search modal, keyboard shortcuts."""

# 20211122195311 (Run a demo) has both prev and next links
TARGET = "/20211122195311/"


def test_prev_link_exists_and_navigates(page, default_site):
    page.goto(f"{default_site}{TARGET}")
    prev_link = page.locator('a[rel="prev"]')
    assert prev_link.count() == 1
    href = prev_link.get_attribute("href")
    assert href is not None
    assert "20211122194827" in href
    prev_link.click()
    page.wait_for_url("**/20211122194827/**")


def test_next_link_exists_and_navigates(page, default_site):
    page.goto(f"{default_site}{TARGET}")
    next_link = page.locator('a[rel="next"]')
    assert next_link.count() == 1
    href = next_link.get_attribute("href")
    assert href is not None
    assert "20211122195910" in href
    next_link.click()
    page.wait_for_url("**/20211122195910/**")


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
    page.wait_for_url("**/20211122195910/**")


def test_keyboard_shortcut_p_navigates_prev(page, default_site):
    page.goto(f"{default_site}{TARGET}")
    page.keyboard.press("p")
    page.wait_for_url("**/20211122194827/**")
