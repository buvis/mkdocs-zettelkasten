import pytest
from playwright.sync_api import Page

TRANSCLUSION_PAGE = "20260223131905"
TARGET_ID = "20260223124437"


class TestTransclusion:
    @pytest.mark.parametrize(
        ("index", "check"),
        [
            (0, "introduction section"),
            (1, "introduction section"),
        ],
        ids=["full-embed", "section-embed"],
    )
    def test_embed_renders_expected_content(
        self, page: Page, default_site: str, index: int, check: str
    ) -> None:
        page.goto(f"{default_site}/{TRANSCLUSION_PAGE}/")
        embed = page.locator(".zettel-embed").nth(index)
        assert embed.is_visible()
        assert check in embed.inner_text().lower()

    def test_section_embed_excludes_other_sections(
        self, page: Page, default_site: str
    ) -> None:
        page.goto(f"{default_site}/{TRANSCLUSION_PAGE}/")
        content = (
            page.locator(".zettel-embed")
            .nth(1)
            .locator(".zettel-embed-content")
            .inner_text()
        )
        assert "details" not in content.lower()

    def test_full_embed_has_header_link(self, page: Page, default_site: str) -> None:
        page.goto(f"{default_site}/{TRANSCLUSION_PAGE}/")
        header_link = page.locator(".zettel-embed-header a").first
        assert header_link.is_visible()
        assert "Embed Target Note" in header_link.inner_text()
        assert TARGET_ID in header_link.get_attribute("href")

    def test_alias_shows_custom_title(self, page: Page, default_site: str) -> None:
        page.goto(f"{default_site}/{TRANSCLUSION_PAGE}/")
        header = page.locator(".zettel-embed").nth(2).locator(".zettel-embed-header a")
        assert "Custom Title" in header.inner_text()

    def test_unresolved_embed_shows_warning(
        self, page: Page, default_site: str
    ) -> None:
        page.goto(f"{default_site}/{TRANSCLUSION_PAGE}/")
        warning = page.locator(".admonition.warning")
        assert warning.count() > 0
        assert "nonexistent99" in warning.first.inner_text()

    def test_embed_has_styled_container(self, page: Page, default_site: str) -> None:
        page.goto(f"{default_site}/{TRANSCLUSION_PAGE}/")
        embed = page.locator(".zettel-embed").first
        assert embed.is_visible()
        content = embed.locator(".zettel-embed-content")
        assert content.is_visible()
