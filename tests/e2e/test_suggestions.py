"""E2E tests for link suggestions section."""

EPISTEMOLOGY = "20260225100000"


class TestSuggestions:
    def test_suggestions_section_visible(self, page, suggestions_site):
        page.goto(f"{suggestions_site}/{EPISTEMOLOGY}/")
        section = page.locator(".suggested-links")
        assert section.count() >= 1

    def test_suggestion_has_link(self, page, suggestions_site):
        page.goto(f"{suggestions_site}/{EPISTEMOLOGY}/")
        links = page.locator(".suggested-links a")
        assert links.count() >= 1

    def test_suggestion_shows_reason(self, page, suggestions_site):
        page.goto(f"{suggestions_site}/{EPISTEMOLOGY}/")
        reasons = page.locator(".suggested-links .suggestion-reason")
        assert reasons.count() >= 1
        text = reasons.first.inner_text()
        assert "shared tag" in text

    def test_suggestions_absent_when_disabled(self, page, default_site):
        page.goto(f"{default_site}/{EPISTEMOLOGY}/")
        section = page.locator(".suggested-links")
        assert section.count() == 0

    def test_suggestions_json_exists(self, page, suggestions_site):
        response = page.goto(f"{suggestions_site}/suggestions.json")
        assert response.status == 200
