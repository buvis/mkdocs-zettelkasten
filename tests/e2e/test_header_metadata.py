"""E2E tests for file header metadata layout."""

ZETTEL_WITH_RICH_METADATA = "20260224212155"
ZETTEL_WITH_SIMPLE_METADATA = "20211122194827"


def test_update_date_moves_into_secondary_metadata(page, default_site):
    page.goto(f"{default_site}/features/{ZETTEL_WITH_RICH_METADATA}/")
    date = page.locator(".file-header-secondary .file-header-date")
    assert date.count() == 1
    assert "Updated" in date.inner_text()


def test_regular_note_still_renders_secondary_metadata_for_date(page, default_site):
    page.goto(f"{default_site}/{ZETTEL_WITH_SIMPLE_METADATA}/")
    date = page.locator(".file-header-secondary .file-header-date")
    assert date.count() == 1
    assert "Updated" in date.inner_text()


def test_homepage_has_no_empty_file_header(page, default_site):
    page.goto(default_site)
    assert page.locator(".file-header").count() == 0
