"""E2E tests for MOC (Map of Content) card layout and navigation."""

MOC_ZETTEL = "20260225120000"
CHILD_ZETTEL = "20260224212155"  # linked from MOC
UNRELATED_ZETTEL = "20211122194827"  # not linked from any MOC


def test_moc_card_has_map_icon(page, default_site):
    page.goto(f"{default_site}/features/{MOC_ZETTEL}/")
    # MOC should have the map pin icon SVG (not the document icon)
    header = page.locator(".file-header")
    assert header.locator("svg").count() >= 1


def test_moc_card_shows_link_count(page, default_site):
    page.goto(f"{default_site}/features/{MOC_ZETTEL}/")
    count = page.locator(".moc-link-count")
    assert count.count() == 1
    assert "notes in this map" in count.inner_text()


def test_moc_card_hides_maturity_badge(page, default_site):
    page.goto(f"{default_site}/features/{MOC_ZETTEL}/")
    assert page.locator(".zettel-maturity-badge").count() == 0


def test_moc_card_shows_type_badge(page, default_site):
    page.goto(f"{default_site}/features/{MOC_ZETTEL}/")
    badge = page.locator(".zettel-type-badge")
    assert badge.count() == 1
    assert "permanent" in badge.inner_text()


def test_child_shows_part_of_breadcrumb(page, default_site):
    page.goto(f"{default_site}/features/{CHILD_ZETTEL}/")
    breadcrumb = page.locator(".moc-breadcrumb")
    assert breadcrumb.count() == 1
    assert "Part of" in breadcrumb.inner_text()
    assert "Zettelkasten features map" in breadcrumb.inner_text()


def test_unrelated_note_no_breadcrumb(page, default_site):
    page.goto(f"{default_site}/{UNRELATED_ZETTEL}/")
    assert page.locator(".moc-breadcrumb").count() == 0


def test_moc_link_count_not_shown_on_regular_note(page, default_site):
    page.goto(f"{default_site}/{UNRELATED_ZETTEL}/")
    assert page.locator(".moc-link-count").count() == 0


def test_tags_page_features_moc(page, default_site):
    page.goto(f"{default_site}/tags.html")
    page_text = page.locator("body").inner_text()
    assert "Entry points" in page_text
    assert "Zettelkasten features map" in page_text
