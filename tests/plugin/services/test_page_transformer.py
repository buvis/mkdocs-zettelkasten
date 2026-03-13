import logging
from unittest.mock import MagicMock, patch

import pytest

from mkdocs_zettelkasten.plugin.services.page_transformer import PageTransformer

MODULE = "mkdocs_zettelkasten.plugin.services.page_transformer"


def _make_transform_fixtures():
    transformer = PageTransformer()
    page = MagicMock()
    page.file.src_path = "test.md"
    page.meta = {"is_zettel": False}
    config = MagicMock()
    config.__getitem__ = lambda self, key: {"site_url": "https://example.com/"}.get(
        key, MagicMock()
    )
    config.get = lambda key, default=None: {"extra": {}}.get(key, default)
    files = MagicMock()
    zettel_service = MagicMock()
    zettel_service.add_zettel_to_page.return_value = page
    zettel_service.get_zettels.return_value = []
    zettel_service.file_suffix = ".md"
    features = []
    ctx = MagicMock()
    return transformer, page, config, files, zettel_service, features, ctx


class TestPageTransformer:
    def test_transform_calls_core_adapters(self) -> None:
        transformer, page, config, files, svc, features, ctx = (
            _make_transform_fixtures()
        )

        with (
            patch(f"{MODULE}.adapt_page_title", return_value="md1") as mock_title,
            patch(
                f"{MODULE}.adapt_transclusion", return_value="md1t"
            ) as mock_transclusion,
            patch(
                f"{MODULE}.adapt_page_links_to_zettels", return_value="md2"
            ) as mock_links,
            patch(f"{MODULE}.get_page_ref", return_value=("md3", None)) as mock_ref,
            patch(
                f"{MODULE}.get_prev_next_page", return_value=(None, None)
            ) as mock_nav,
        ):
            result = transformer.transform(
                "original", page, config, files, svc, features, ctx
            )

        assert result == "md3"
        mock_title.assert_called_once()
        mock_transclusion.assert_called_once()
        mock_links.assert_called_once()
        mock_ref.assert_called_once()
        mock_nav.assert_called_once()

    def test_transform_calls_feature_adapt_page(self) -> None:
        transformer, page, config, files, svc, _, ctx = _make_transform_fixtures()
        feature1 = MagicMock()
        feature1.name = "feat1"
        feature2 = MagicMock()
        feature2.name = "feat2"
        features = [feature1, feature2]

        with (
            patch(f"{MODULE}.adapt_page_title", return_value="md1"),
            patch(f"{MODULE}.adapt_transclusion", return_value="md1t"),
            patch(f"{MODULE}.adapt_page_links_to_zettels", return_value="md2"),
            patch(f"{MODULE}.get_page_ref", return_value=("md3", None)),
            patch(f"{MODULE}.get_prev_next_page", return_value=(None, None)),
        ):
            transformer.transform("original", page, config, files, svc, features, ctx)

        feature1.adapt_page.assert_called_once_with(page, ctx)
        feature2.adapt_page.assert_called_once_with(page, ctx)

    def test_transform_chains_adapters_in_order(self) -> None:
        """Each adapter receives the output of the previous one."""
        transformer, page, config, files, svc, features, ctx = (
            _make_transform_fixtures()
        )

        with (
            patch(f"{MODULE}.adapt_page_title", return_value="after_title") as m_title,
            patch(
                f"{MODULE}.adapt_transclusion", return_value="after_transclusion"
            ) as m_trans,
            patch(
                f"{MODULE}.adapt_page_links_to_zettels", return_value="after_links"
            ) as m_links,
            patch(f"{MODULE}.get_page_ref", return_value=("after_ref", None)) as m_ref,
            patch(f"{MODULE}.get_prev_next_page", return_value=(None, None)),
        ):
            result = transformer.transform(
                "original", page, config, files, svc, features, ctx
            )

        # title gets the raw markdown
        assert m_title.call_args[0][0] == "original"
        # transclusion gets title output
        assert m_trans.call_args[0][0] == "after_title"
        # links gets transclusion output
        assert m_links.call_args[0][0] == "after_transclusion"
        # ref gets links output
        assert m_ref.call_args[0][0] == "after_links"
        # final result is ref output
        assert result == "after_ref"

    def test_exception_logs_adapter_name(self, caplog) -> None:
        transformer, page, config, files, svc, features, ctx = (
            _make_transform_fixtures()
        )

        with (
            patch(f"{MODULE}.adapt_page_title", return_value="md1"),
            patch(f"{MODULE}.adapt_transclusion", side_effect=ValueError("boom")),
            caplog.at_level(logging.ERROR),
            pytest.raises(ValueError, match="boom"),
        ):
            transformer.transform("original", page, config, files, svc, features, ctx)

        assert "adapt_transclusion" in caplog.text
        assert "test.md" in caplog.text

    def test_feature_exception_logs_feature_name(self, caplog) -> None:
        transformer, page, config, files, svc, _, ctx = _make_transform_fixtures()
        feature = MagicMock()
        feature.name = "my_feature"
        feature.adapt_page.side_effect = RuntimeError("feature boom")

        with (
            patch(f"{MODULE}.adapt_page_title", return_value="md1"),
            patch(f"{MODULE}.adapt_transclusion", return_value="md1t"),
            patch(f"{MODULE}.adapt_page_links_to_zettels", return_value="md2"),
            patch(f"{MODULE}.get_page_ref", return_value=("md3", None)),
            patch(f"{MODULE}.get_prev_next_page", return_value=(None, None)),
            caplog.at_level(logging.ERROR),
            pytest.raises(RuntimeError, match="feature boom"),
        ):
            transformer.transform(
                "original", page, config, files, svc, [feature], ctx
            )

        assert "my_feature" in caplog.text
