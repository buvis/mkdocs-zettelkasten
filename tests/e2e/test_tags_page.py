"""E2E tests for tags page rendering."""


def test_tags_page_loads(page, default_site):
    resp = page.goto(f"{default_site}/tags.html")
    assert resp.status == 200


def test_tags_page_has_heading(page, default_site):
    page.goto(f"{default_site}/tags.html")
    h1 = page.locator("h1#contents-grouped-by-tag")
    assert h1.is_visible()


def test_tags_page_lists_tags(page, default_site):
    page.goto(f"{default_site}/tags.html")
    tag_headings = page.locator("h2 span.tag")
    assert tag_headings.count() >= 3


def test_tags_have_anchors(page, default_site):
    page.goto(f"{default_site}/tags.html")
    # known tags from docs
    for tag_id in ["how-to", "mkdocs", "zettelkasten"]:
        assert page.locator(f"h2#{tag_id}").count() == 1


def test_tags_link_to_zettels(page, default_site):
    page.goto(f"{default_site}/tags.html")
    # each tag section should have at least one link to a zettel
    first_tag_section = page.locator("h2").first
    tag_id = first_tag_section.get_attribute("id")
    # links follow the h2 in a ul
    links = page.locator(f"h2#{tag_id} + ul a")
    assert links.count() >= 1


def test_tags_nav_button_links_to_tags_page(page, default_site):
    page.goto(default_site)
    tags_link = page.locator('a.nav-link[href*="tags"]')
    assert tags_link.count() >= 1
    tags_link.first.click()
    page.wait_for_url("**/tags.html")
