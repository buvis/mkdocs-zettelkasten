"""E2E tests for validation badges and page (testscript 061)."""

from playwright.sync_api import expect


def test_validation_badge_visible_on_zettel(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    badge = page.locator(".validation-badge")
    assert badge.count() >= 1
    assert badge.first.locator("i.fa.fa-exclamation-triangle").count() == 1


def test_validation_page_exists(page, default_site):
    resp = page.goto(f"{default_site}/validation.html")
    assert resp.status == 200
    content = page.locator("body").inner_text()
    assert len(content) > 0


def test_validation_page_has_issues(page, default_site):
    page.goto(f"{default_site}/validation.html")
    body = page.locator(".file-body")
    expect(body).not_to_be_empty()


def test_validation_navbar_icon_visible(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    icon = page.locator(".navbar .fa-exclamation-triangle")
    assert icon.count() == 1
    link = icon.locator("..")
    assert "validation.html" in link.get_attribute("href")


def test_validation_navbar_icon_shows_count(page, default_site):
    page.goto(f"{default_site}/20211122194827/")
    badge = page.locator(".navbar .badge-warning")
    assert badge.count() == 1
    count = int(badge.inner_text())
    assert count > 0


def test_validation_navbar_icon_hidden_when_zero_issues(page, clean_validation_site):
    page.goto(f"{clean_validation_site}/20990101000001/")
    assert page.locator(".navbar .fa-exclamation-triangle").count() == 0


def test_validation_navbar_icon_hidden_when_disabled(page, no_validation_site):
    page.goto(f"{no_validation_site}/20211122194827/")
    assert page.locator(".navbar .fa-exclamation-triangle").count() == 0


def test_no_validation_badge_when_disabled(page, no_validation_site):
    page.goto(f"{no_validation_site}/20211122194827/")
    assert page.locator(".validation-badge").count() == 0


def test_validation_report_links_navigate_to_zettel(page, default_site):
    page.goto(f"{default_site}/validation.html")
    links = page.locator(".file-body li a")
    assert links.count() > 0
    href = links.first.get_attribute("href")
    resp = page.goto(href)
    assert resp.status == 200


def test_no_validation_page_when_disabled(page, no_validation_site):
    resp = page.goto(f"{no_validation_site}/validation.html")
    assert resp.status == 404
