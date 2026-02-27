"""E2E tests for outline page rendering."""


def test_outline_page_loads(page, default_site):
    response = page.goto(f"{default_site}/outline.html")
    assert response.status == 200


def test_moc_outline_visible(page, default_site):
    page.goto(f"{default_site}/outline.html")
    assert page.locator("text=Philosophy Overview").count() >= 1


def test_outline_entries_present(page, default_site):
    page.goto(f"{default_site}/outline.html")
    assert page.locator("text=Epistemology").count() >= 1
    assert page.locator("text=JTB Theory").count() >= 1


def test_gap_marker_present(page, default_site):
    page.goto(f"{default_site}/outline.html")
    assert page.locator("text=GAP").count() >= 1


def test_sequence_outline_visible(page, default_site):
    page.goto(f"{default_site}/outline.html")
    assert page.locator("text=Sequence: Epistemology").count() >= 1


def test_transclusion_hint_present(page, default_site):
    page.goto(f"{default_site}/outline.html")
    assert page.locator("text=Copy as transclusion").count() >= 1


def test_navbar_outline_icon(page, default_site):
    page.goto(f"{default_site}/outline.html")
    icon = page.locator(".fa-file-text-o")
    assert icon.count() >= 1
