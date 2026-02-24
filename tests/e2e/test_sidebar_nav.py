"""E2E tests for sidebar navigation."""


def _open_sidebar(page):
    page.click("#sidebar-toggle")
    page.wait_for_selector("#sidebar-nav.open", timeout=2000)


def test_sidebar_toggle_visible(page, default_site):
    """Toggle button exists and is visible on page load."""
    page.goto(default_site)
    toggle = page.locator("#sidebar-toggle")
    assert toggle.is_visible()


def test_sidebar_closed_by_default(page, default_site):
    """Sidebar does not have .open class on initial load."""
    page.goto(default_site)
    sidebar = page.locator("#sidebar-nav")
    assert sidebar.count() == 1
    assert "open" not in (sidebar.get_attribute("class") or "")


def test_sidebar_opens_on_toggle_click(page, default_site):
    """Clicking toggle opens sidebar."""
    page.goto(default_site)
    _open_sidebar(page)
    assert page.locator("#sidebar-nav.open").count() == 1


def test_sidebar_closes_on_backdrop_click(page, default_site):
    """Clicking backdrop closes sidebar."""
    page.goto(default_site)
    _open_sidebar(page)
    page.click("#sidebar-backdrop")
    page.wait_for_selector("#sidebar-nav:not(.open)", timeout=2000)
    assert "open" not in (page.locator("#sidebar-nav").get_attribute("class") or "")


def test_sidebar_closes_on_close_button(page, default_site):
    """Clicking X button closes sidebar."""
    page.goto(default_site)
    _open_sidebar(page)
    page.click(".sidebar-close")
    page.wait_for_selector("#sidebar-nav:not(.open)", timeout=2000)
    assert "open" not in (page.locator("#sidebar-nav").get_attribute("class") or "")


def test_sidebar_closes_on_leaf_click(page, default_site):
    """Clicking a leaf link closes sidebar."""
    page.goto(default_site)
    _open_sidebar(page)
    # Click first visible leaf link
    leaf = page.locator(".sidebar-link").first
    leaf.click()
    page.wait_for_selector("#sidebar-nav:not(.open)", timeout=2000)


def test_sidebar_closes_on_escape(page, default_site):
    """Pressing Escape closes sidebar."""
    page.goto(default_site)
    _open_sidebar(page)
    page.keyboard.press("Escape")
    page.wait_for_selector("#sidebar-nav:not(.open)", timeout=2000)


def test_sidebar_tree_section_expands(page, default_site):
    """Clicking a section toggle expands its subtree."""
    page.goto(default_site)
    _open_sidebar(page)
    # Find a collapsed section toggle (one without .open class)
    toggle = page.locator(".sidebar-section-toggle:not(.open)").first
    if toggle.count() > 0:
        toggle.click()
        assert "open" in (toggle.get_attribute("class") or "")
        subtree = toggle.locator("+ .sidebar-subtree")
        assert "expanded" in (subtree.get_attribute("class") or "")


def test_sidebar_active_section_preexpanded(page, default_site):
    """Active page's parent section is pre-expanded on load."""
    page.goto(default_site)
    _open_sidebar(page)
    # Active link should exist and its parent subtree should be expanded
    active_link = page.locator(".sidebar-link.active")
    if active_link.count() > 0:
        # The subtree containing the active link should have .expanded
        parent_subtree = active_link.locator("xpath=ancestor::ul[contains(@class, 'sidebar-subtree')]").first
        if parent_subtree.count() > 0:
            assert "expanded" in (parent_subtree.get_attribute("class") or "")


def test_topnav_mode_no_sidebar(page, topnav_site):
    """With nav_position: top, no sidebar elements exist."""
    page.goto(topnav_site)
    assert page.locator("#sidebar-toggle").count() == 0
    assert page.locator("#sidebar-nav").count() == 0
    # Old navbar nav should be present
    assert page.locator(".navbar-nav:not(.ml-auto)").count() == 1
