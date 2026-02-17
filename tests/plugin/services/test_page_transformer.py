from unittest.mock import MagicMock, patch

from mkdocs_zettelkasten.plugin.services.page_transformer import PageTransformer


class TestPageTransformer:
    def test_transform_calls_all_adapters(self) -> None:
        transformer = PageTransformer()

        page = MagicMock()
        page.file.src_path = "test.md"
        page.meta = {"is_zettel": False}
        config = MagicMock()
        files = MagicMock()
        zettel_service = MagicMock()
        zettel_service.add_zettel_to_page.return_value = page
        zettel_service.get_zettels.return_value = []

        with (
            patch(
                "mkdocs_zettelkasten.plugin.services.page_transformer.adapt_page_title",
                return_value="md1",
            ) as mock_title,
            patch(
                "mkdocs_zettelkasten.plugin.services.page_transformer.adapt_page_links_to_zettels",
                return_value="md2",
            ) as mock_links,
            patch(
                "mkdocs_zettelkasten.plugin.services.page_transformer.get_page_ref",
                return_value=("md3", None),
            ) as mock_ref,
            patch(
                "mkdocs_zettelkasten.plugin.services.page_transformer.get_prev_next_page",
                return_value=(None, None),
            ) as mock_nav,
            patch(
                "mkdocs_zettelkasten.plugin.services.page_transformer.adapt_backlinks_to_page",
            ) as mock_backlinks,
        ):
            result = transformer.transform("original", page, config, files, zettel_service)

        assert result == "md3"
        mock_title.assert_called_once()
        mock_links.assert_called_once()
        mock_ref.assert_called_once()
        mock_nav.assert_called_once()
        mock_backlinks.assert_called_once()
