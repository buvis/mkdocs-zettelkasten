import logging
from unittest.mock import MagicMock, patch

from mkdocs_zettelkasten.plugin.plugin import ZettelkastenPlugin


class TestZettelkastenPlugin:
    def _make_plugin(self) -> ZettelkastenPlugin:
        plugin = ZettelkastenPlugin()
        plugin.config = {
            "log_level": "WARNING",
            "log_format": "%(message)s",
            "id_key": "id",
            "date_key": "date",
            "last_update_key": "last_update",
            "tags_key": "tags",
            "id_format": r"^\d{14}$",
            "timezone": "",
            "validation_enabled": True,
            "editor_enabled": False,
            "editor_repo": "",
            "editor_branch": "main",
            "editor_docs_prefix": "docs",
            "date_format": "%Y-%m-%d",
            "icon_references": "fa fa-book",
            "icon_backlinks": "fa fa-link",
            "file_suffix": ".md",
            "graph_enabled": False,
            "preview_enabled": False,
            "transclusion_strip_heading": True,
        }
        return plugin

    def test_init_creates_services(self) -> None:
        plugin = ZettelkastenPlugin()
        assert plugin.tags_service is not None
        assert plugin.zettel_service is not None
        assert plugin.page_transformer is not None

    def test_init_creates_logger(self) -> None:
        plugin = ZettelkastenPlugin()
        assert plugin.logger is not None
        assert plugin.logger.name == "mkdocs.plugins.zettelkasten"

    def test_init_has_null_handler(self) -> None:
        plugin = ZettelkastenPlugin()
        has_null = any(
            isinstance(h, logging.NullHandler) for h in plugin.logger.handlers
        )
        assert has_null

    def test_on_config_sets_log_level(self) -> None:
        plugin = self._make_plugin()
        config = MagicMock()

        with patch.object(plugin.tags_service, "configure"):
            plugin.on_config(config)

        assert plugin.logger.level == logging.WARNING

    def test_on_config_passes_zettel_config(self) -> None:
        plugin = self._make_plugin()
        config = MagicMock()

        with (
            patch.object(plugin.zettel_service, "configure") as mock_cfg,
            patch.object(plugin.tags_service, "configure"),
        ):
            plugin.on_config(config)

        mock_cfg.assert_called_once()
        call_args = mock_cfg.call_args[0][0]
        assert call_args["id_key"] == "id"
        assert call_args["tags_key"] == "tags"
        assert call_args["date_format"] == "%Y-%m-%d"
        assert call_args["file_suffix"] == ".md"

    def test_on_config_passes_tags_key(self) -> None:
        plugin = self._make_plugin()
        config = MagicMock()

        with (
            patch.object(plugin.zettel_service, "configure"),
            patch.object(plugin.tags_service, "configure") as mock_tags,
        ):
            plugin.on_config(config)

        mock_tags.assert_called_once_with(config, tags_key="tags", file_suffix=".md")

    def test_on_files_delegates(self) -> None:
        plugin = self._make_plugin()
        files = MagicMock()
        files.__len__ = lambda self: 5
        config = MagicMock()

        with (
            patch.object(plugin.zettel_service, "process_files") as mock_zs,
            patch.object(plugin.tags_service, "process_files") as mock_ts,
            patch.object(plugin.validation_service, "validate"),
        ):
            plugin.on_files(files, config)

        mock_zs.assert_called_once_with(files, config)
        mock_ts.assert_called_once_with(files)

    def test_on_files_sets_validation_count(self) -> None:
        plugin = self._make_plugin()
        files = MagicMock()
        files.__len__ = lambda self: 5
        config = {"extra": {}}

        with (
            patch.object(plugin.zettel_service, "process_files"),
            patch.object(plugin.tags_service, "process_files"),
            patch.object(plugin.validation_service, "validate"),
            patch.object(plugin.validation_service, "total_issues", return_value=7),
        ):
            plugin.on_files(files, config)

        assert config["extra"]["validation_issues_count"] == 7

    def test_on_files_skips_validation_count_when_disabled(self) -> None:
        plugin = self._make_plugin()
        plugin.config["validation_enabled"] = False
        files = MagicMock()
        files.__len__ = lambda self: 5
        config = {"extra": {}}

        with (
            patch.object(plugin.zettel_service, "process_files"),
            patch.object(plugin.tags_service, "process_files"),
        ):
            plugin.on_files(files, config)

        assert "validation_issues_count" not in config["extra"]

    def test_on_page_markdown_returns_transformed(self) -> None:
        plugin = self._make_plugin()
        page = MagicMock()
        page.url = "/test/"
        config = MagicMock()
        files = MagicMock()

        with patch.object(
            plugin.page_transformer, "transform", return_value="transformed"
        ):
            result = plugin.on_page_markdown("original", page, config, files)

        assert result == "transformed"

    def test_on_page_markdown_sets_icons_meta(self) -> None:
        plugin = self._make_plugin()
        page = MagicMock()
        page.url = "/test/"
        page.meta = {}
        config = MagicMock()
        files = MagicMock()

        with patch.object(
            plugin.page_transformer, "transform", return_value="transformed"
        ):
            plugin.on_page_markdown("original", page, config, files)

        assert page.meta["icons"] == {
            "references": "fa fa-book",
            "backlinks": "fa fa-link",
        }

    def test_on_config_sets_graph_enabled_extra(self) -> None:
        plugin = self._make_plugin()
        plugin.config["graph_enabled"] = True
        config = MagicMock()
        config.__getitem__ = MagicMock(side_effect={"extra": {}}.get)
        extra = {}
        config.__getitem__ = lambda self_mock, key: extra if key == "extra" else MagicMock()

        with (
            patch.object(plugin.zettel_service, "configure"),
            patch.object(plugin.tags_service, "configure"),
        ):
            plugin.on_config(config)

        assert extra["graph_enabled"] is True

    def test_on_config_skips_graph_extra_when_disabled(self) -> None:
        plugin = self._make_plugin()
        extra = {}
        config = MagicMock()
        config.__getitem__ = lambda self_mock, key: extra if key == "extra" else MagicMock()

        with (
            patch.object(plugin.zettel_service, "configure"),
            patch.object(plugin.tags_service, "configure"),
        ):
            plugin.on_config(config)

        assert "graph_enabled" not in extra
