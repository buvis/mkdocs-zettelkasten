from playwright.sync_api import Page


class TestTransclusion:
    def test_full_embed_renders_content(self, page: Page, default_site: str) -> None:
        page.goto(f"{default_site}/20990201000002/")
        embed = page.locator(".zettel-embed").first
        assert embed.is_visible()
        assert "introduction section" in embed.inner_text().lower()

    def test_full_embed_has_header_link(self, page: Page, default_site: str) -> None:
        page.goto(f"{default_site}/20990201000002/")
        header_link = page.locator(".zettel-embed-header a").first
        assert header_link.is_visible()
        assert "Embed Target Note" in header_link.inner_text()
        assert "20990201000001" in header_link.get_attribute("href")

    def test_section_embed_only_shows_section(
        self, page: Page, default_site: str
    ) -> None:
        page.goto(f"{default_site}/20990201000002/")
        embeds = page.locator(".zettel-embed")
        # Second embed is the section embed
        section_embed = embeds.nth(1)
        content = section_embed.locator(".zettel-embed-content").inner_text()
        assert "introduction section" in content.lower()
        assert "details" not in content.lower()

    def test_alias_shows_custom_title(self, page: Page, default_site: str) -> None:
        page.goto(f"{default_site}/20990201000002/")
        embeds = page.locator(".zettel-embed")
        # Third embed has alias
        alias_embed = embeds.nth(2)
        header = alias_embed.locator(".zettel-embed-header a")
        assert "Custom Title" in header.inner_text()

    def test_unresolved_embed_shows_warning(
        self, page: Page, default_site: str
    ) -> None:
        page.goto(f"{default_site}/20990201000002/")
        warning = page.locator(".admonition.warning")
        assert warning.count() > 0
        assert "nonexistent99" in warning.first.inner_text()

    def test_embed_has_styled_container(self, page: Page, default_site: str) -> None:
        page.goto(f"{default_site}/20990201000002/")
        embed = page.locator(".zettel-embed").first
        assert embed.is_visible()
        content = embed.locator(".zettel-embed-content")
        assert content.is_visible()
