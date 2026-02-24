"""E2E tests for note type and maturity badges in card header."""

# The zettel 20260224212155 has type: permanent, maturity: developing
ZETTEL_WITH_BADGES = "20260224212155"

# An existing zettel without type/maturity metadata
ZETTEL_WITHOUT_BADGES = "20211122194827"


def test_type_badge_visible(page, default_site):
    page.goto(f"{default_site}/features/{ZETTEL_WITH_BADGES}/")
    badge = page.locator(".zettel-type-badge")
    assert badge.count() == 1
    assert "permanent" in badge.inner_text()


def test_type_badge_has_icon(page, default_site):
    page.goto(f"{default_site}/features/{ZETTEL_WITH_BADGES}/")
    svg = page.locator(".zettel-type-badge svg")
    assert svg.count() == 1


def test_maturity_badge_visible(page, default_site):
    page.goto(f"{default_site}/features/{ZETTEL_WITH_BADGES}/")
    badge = page.locator(".zettel-maturity-badge")
    assert badge.count() == 1
    assert "developing" in badge.inner_text()


def test_maturity_badge_has_dot(page, default_site):
    page.goto(f"{default_site}/features/{ZETTEL_WITH_BADGES}/")
    dot = page.locator(".maturity-dot")
    assert dot.count() == 1


def test_no_badges_when_metadata_absent(page, default_site):
    page.goto(f"{default_site}/{ZETTEL_WITHOUT_BADGES}/")
    assert page.locator(".zettel-type-badge").count() == 0
    assert page.locator(".zettel-maturity-badge").count() == 0


def test_badges_row_not_rendered_when_absent(page, default_site):
    page.goto(f"{default_site}/{ZETTEL_WITHOUT_BADGES}/")
    assert page.locator(".zettel-badges").count() == 0
