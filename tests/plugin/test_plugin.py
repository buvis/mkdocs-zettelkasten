import logging
import os
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from mkdocs_zettelkasten.plugin.plugin import ZettelkastenPlugin
from mkdocs_zettelkasten.plugin.services.link_resolver import LinkMap

_EMPTY_LINK_MAP = LinkMap(resolved={}, broken=[])


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
            "type_key": "type",
            "maturity_key": "maturity",
            "role_key": "role",
            "sequence_key": "sequence",
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
            "suggestions_enabled": False,
            "workflow_enabled": False,
            "transclusion_strip_heading": True,
            "minify_js": True,
        }
        return plugin

    def test_init_creates_services(self) -> None:
        plugin = ZettelkastenPlugin()
        assert plugin.tags_service is not None
        assert plugin.zettel_service is not None
        assert plugin.page_transformer is not None
        assert len(plugin._features) == 9

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

        with (
            patch.object(plugin.tags_service, "configure"),
        ):
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
        assert call_args.id_key == "id"
        assert call_args.tags_key == "tags"
        assert call_args.type_key == "type"
        assert call_args.maturity_key == "maturity"
        assert call_args.date_format == "%Y-%m-%d"
        assert call_args.file_suffix == ".md"

    def test_on_config_passes_tags_key(self) -> None:
        plugin = self._make_plugin()
        config = MagicMock()

        with (
            patch.object(plugin.zettel_service, "configure"),
            patch.object(plugin.tags_service, "configure") as mock_tags,
        ):
            plugin.on_config(config)

        mock_tags.assert_called_once_with(
            config, tags_key="tags", file_suffix=".md", role_key="role"
        )

    def test_on_files_delegates(self) -> None:
        plugin = self._make_plugin()
        plugin.zk_config = MagicMock()
        plugin._active_features = []
        plugin.zettel_service.link_map = _EMPTY_LINK_MAP
        files = MagicMock()
        files.__len__ = lambda self: 5
        config = {"extra": {}, "site_dir": "/tmp"}

        with (
            patch.object(plugin.zettel_service, "process_files") as mock_zs,
            patch.object(plugin.tags_service, "process_files") as mock_ts,
        ):
            plugin.on_files(files, config=config)

        mock_zs.assert_called_once_with(files, config)
        mock_ts.assert_called_once_with(files, store=plugin.zettel_service.store)

    def test_on_files_sets_validation_count(self) -> None:
        plugin = self._make_plugin()
        plugin.zk_config = MagicMock()
        plugin.zettel_service.link_map = _EMPTY_LINK_MAP
        files = MagicMock()
        files.__len__ = lambda self: 5
        config = {"extra": {}, "site_dir": "/tmp"}

        # Create a mock validation feature that sets the count
        mock_feature = MagicMock()
        mock_feature.name = "validation"

        def _set_count(_ctx, _f, c):
            c["extra"]["validation_issues_count"] = 7

        mock_feature.export.side_effect = _set_count
        plugin._active_features = [mock_feature]

        with (
            patch.object(plugin.zettel_service, "process_files"),
            patch.object(plugin.tags_service, "process_files"),
        ):
            plugin.on_files(files, config=config)

        assert config["extra"]["validation_issues_count"] == 7

    def test_on_files_skips_validation_count_when_disabled(self) -> None:
        plugin = self._make_plugin()
        plugin.config["validation_enabled"] = False
        plugin.zk_config = MagicMock()
        plugin._active_features = []
        plugin.zettel_service.link_map = _EMPTY_LINK_MAP
        files = MagicMock()
        files.__len__ = lambda self: 5
        config = {"extra": {}, "site_dir": "/tmp"}

        with (
            patch.object(plugin.zettel_service, "process_files"),
            patch.object(plugin.tags_service, "process_files"),
        ):
            plugin.on_files(files, config=config)

        assert "validation_issues_count" not in config["extra"]

    def test_on_page_markdown_returns_transformed(self) -> None:
        plugin = self._make_plugin()
        plugin._ctx = MagicMock()
        plugin._active_features = []
        page = MagicMock()
        page.url = "/test/"
        config = MagicMock()
        files = MagicMock()

        with patch.object(
            plugin.page_transformer, "transform", return_value="transformed"
        ):
            result = plugin.on_page_markdown(
                "original", page=page, config=config, files=files
            )

        assert result == "transformed"

    def test_on_page_markdown_sets_icons_meta(self) -> None:
        plugin = self._make_plugin()
        plugin._ctx = MagicMock()
        plugin._active_features = []
        page = MagicMock()
        page.url = "/test/"
        page.meta = {}
        config = MagicMock()
        files = MagicMock()

        with patch.object(
            plugin.page_transformer, "transform", return_value="transformed"
        ):
            plugin.on_page_markdown("original", page=page, config=config, files=files)

        assert page.meta["icons"] == {
            "references": "fa fa-book",
            "backlinks": "fa fa-link",
        }

    def test_on_config_sets_graph_enabled_extra(self) -> None:
        plugin = self._make_plugin()
        plugin.config["graph_enabled"] = True
        config = MagicMock()
        extra = {}
        config.__getitem__ = lambda self_mock, key: (
            extra if key == "extra" else MagicMock()
        )

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
        config.__getitem__ = lambda self_mock, key: (
            extra if key == "extra" else MagicMock()
        )

        with (
            patch.object(plugin.zettel_service, "configure"),
            patch.object(plugin.tags_service, "configure"),
        ):
            plugin.on_config(config)

        assert "graph_enabled" not in extra

    def test_resolve_timezone_from_env(self) -> None:
        plugin = self._make_plugin()
        with patch.dict(os.environ, {"ZETTELKASTEN_TZ": "US/Eastern"}):
            tz = plugin._resolve_timezone()
        assert tz == ZoneInfo("US/Eastern")

    def test_resolve_timezone_from_config(self) -> None:
        plugin = self._make_plugin()
        plugin.config["timezone"] = "Europe/Berlin"
        with patch.dict(os.environ, {}, clear=True):
            tz = plugin._resolve_timezone()
        assert tz == ZoneInfo("Europe/Berlin")

    def test_resolve_timezone_invalid_falls_back_to_utc(self) -> None:
        plugin = self._make_plugin()
        plugin.config["timezone"] = "Invalid/Zone"
        with patch.dict(os.environ, {}, clear=True):
            tz = plugin._resolve_timezone()
        assert tz == ZoneInfo("UTC")

    def test_on_files_exports_graph_json(self, tmp_path) -> None:
        plugin = self._make_plugin()
        plugin.config["graph_enabled"] = True
        plugin.zk_config = MagicMock()
        plugin.zettel_service.link_map = _EMPTY_LINK_MAP
        files = MagicMock()
        files.__len__ = lambda self: 1
        config = {"extra": {}, "site_dir": str(tmp_path / "site")}

        # Create a mock graph feature that writes graph.json
        mock_feature = MagicMock()
        mock_feature.name = "graph"

        def _export_graph(ctx, _f, _c):
            import json

            path = ctx.tags_folder / "graph.json"
            path.write_text(json.dumps({}))

        mock_feature.export.side_effect = _export_graph
        plugin._active_features = [mock_feature]

        with (
            patch.object(plugin.zettel_service, "process_files"),
            patch.object(plugin.tags_service, "process_files"),
            patch.object(plugin.tags_service, "tags_folder", tmp_path),
        ):
            plugin.on_files(files, config=config)

        assert (tmp_path / "graph.json").exists()

    def test_on_files_exports_previews_json(self, tmp_path) -> None:
        plugin = self._make_plugin()
        plugin.config["preview_enabled"] = True
        plugin.zk_config = MagicMock()
        plugin.zettel_service.link_map = _EMPTY_LINK_MAP
        files = MagicMock()
        files.__len__ = lambda self: 1
        config = {"extra": {}, "site_dir": str(tmp_path / "site")}

        mock_feature = MagicMock()
        mock_feature.name = "preview"

        def _export_preview(ctx, _f, _c):
            import json

            path = ctx.tags_folder / "previews.json"
            path.write_text(json.dumps({}))

        mock_feature.export.side_effect = _export_preview
        plugin._active_features = [mock_feature]

        with (
            patch.object(plugin.zettel_service, "process_files"),
            patch.object(plugin.tags_service, "process_files"),
            patch.object(plugin.tags_service, "tags_folder", tmp_path),
        ):
            plugin.on_files(files, config=config)

        assert (tmp_path / "previews.json").exists()

    def test_on_page_markdown_sets_validation_issues(self) -> None:
        plugin = self._make_plugin()
        plugin._ctx = MagicMock()

        # Create a mock validation feature that sets issues on adapt_page
        issues = [{"msg": "test issue"}]
        mock_feature = MagicMock()
        mock_feature.name = "validation"
        mock_feature.adapt_page.side_effect = lambda page, ctx: page.meta.update(
            {"validation_issues": issues}
        )
        plugin._active_features = [mock_feature]

        page = MagicMock()
        page.url = "/test/"
        page.meta = {}
        config = MagicMock()
        files = MagicMock()

        # Mock transform to call features like the real implementation does
        def _mock_transform(_md, pg, _cfg, _f, _svc, features, ctx):
            for feat in features:
                feat.adapt_page(pg, ctx)
            return "md"

        with patch.object(
            plugin.page_transformer, "transform", side_effect=_mock_transform
        ):
            plugin.on_page_markdown("original", page=page, config=config, files=files)

        assert page.meta["validation_issues"] == issues

    def test_on_page_markdown_sets_editor_meta(self) -> None:
        plugin = self._make_plugin()
        plugin.config["editor_enabled"] = True
        plugin.config["editor_repo"] = "https://github.com/test/repo"
        plugin._ctx = MagicMock()
        plugin._active_features = []
        page = MagicMock()
        page.url = "/test/"
        page.meta = {}
        config = MagicMock()
        files = MagicMock()

        with patch.object(plugin.page_transformer, "transform", return_value="md"):
            plugin.on_page_markdown("original", page=page, config=config, files=files)

        assert page.meta["editor"]["repo"] == "https://github.com/test/repo"
        assert page.meta["editor"]["branch"] == "main"

    def test_config_scheme_has_sequence_key(self) -> None:
        keys = [name for name, _ in ZettelkastenPlugin.config_scheme]
        assert "sequence_key" in keys

    def test_on_startup_sets_serve_flag(self) -> None:
        plugin = self._make_plugin()
        plugin.on_startup(command="serve", dirty=False)
        assert plugin._is_serve is True

    def test_on_startup_clears_serve_flag_for_build(self) -> None:
        plugin = self._make_plugin()
        plugin._is_serve = True
        plugin.on_startup(command="build", dirty=False)
        assert plugin._is_serve is False

    def test_on_post_build_minifies_js(self, tmp_path) -> None:
        plugin = self._make_plugin()
        js_dir = tmp_path / "js"
        js_dir.mkdir()
        (js_dir / "app.js").write_text("var x  =  1 ;  /* comment */")
        config = {"site_dir": str(tmp_path)}
        plugin.on_post_build(config=config)
        result = (js_dir / "app.js").read_text()
        assert "/* comment */" not in result
        assert len(result) < len("var x  =  1 ;  /* comment */")

    def test_on_post_build_skips_during_serve(self, tmp_path) -> None:
        plugin = self._make_plugin()
        plugin._is_serve = True
        js_dir = tmp_path / "js"
        js_dir.mkdir()
        original = "var x  =  1 ;  /* comment */"
        (js_dir / "app.js").write_text(original)
        config = {"site_dir": str(tmp_path)}
        plugin.on_post_build(config=config)
        assert (js_dir / "app.js").read_text() == original

    def test_on_post_build_skips_when_disabled(self, tmp_path) -> None:
        plugin = self._make_plugin()
        plugin.config["minify_js"] = False
        js_dir = tmp_path / "js"
        js_dir.mkdir()
        original = "var x  =  1 ;  /* comment */"
        (js_dir / "app.js").write_text(original)
        config = {"site_dir": str(tmp_path)}
        plugin.on_post_build(config=config)
        assert (js_dir / "app.js").read_text() == original

    def test_on_config_sets_both_graph_and_workflow_extra(self) -> None:
        plugin = self._make_plugin()
        plugin.config["graph_enabled"] = True
        plugin.config["workflow_enabled"] = True
        extra = {}
        config = MagicMock()
        config.__getitem__ = lambda self_mock, key: (
            extra if key == "extra" else MagicMock()
        )

        with (
            patch.object(plugin.zettel_service, "configure"),
            patch.object(plugin.tags_service, "configure"),
        ):
            plugin.on_config(config)

        assert extra["graph_enabled"] is True
        assert extra["workflow_enabled"] is True

    def test_on_config_propagates_custom_file_suffix(self) -> None:
        plugin = self._make_plugin()
        plugin.config["file_suffix"] = ".txt"
        config = MagicMock()

        with (
            patch.object(plugin.zettel_service, "configure") as mock_zcfg,
            patch.object(plugin.tags_service, "configure") as mock_tcfg,
        ):
            plugin.on_config(config)

        assert mock_zcfg.call_args[0][0].file_suffix == ".txt"
        mock_tcfg.assert_called_once_with(
            config, tags_key="tags", file_suffix=".txt", role_key="role"
        )

    def test_on_post_build_skips_vendor_subdir(self, tmp_path) -> None:
        plugin = self._make_plugin()
        js_dir = tmp_path / "js"
        vendor_dir = js_dir / "vendor"
        vendor_dir.mkdir(parents=True)
        original = "var x  =  1 ;  /* comment */"
        (vendor_dir / "lib.js").write_text(original)
        config = {"site_dir": str(tmp_path)}
        plugin.on_post_build(config=config)
        assert (vendor_dir / "lib.js").read_text() == original

    def test_on_files_runs_feature_compute_and_export(self) -> None:
        plugin = self._make_plugin()
        plugin.zk_config = MagicMock()
        plugin.zettel_service.link_map = _EMPTY_LINK_MAP
        files = MagicMock()
        files.__len__ = lambda self: 1
        config = {"extra": {}, "site_dir": "/tmp"}

        mock_feature = MagicMock()
        mock_feature.name = "test"
        mock_feature.compute.return_value = {"data": 1}
        plugin._active_features = [mock_feature]

        with (
            patch.object(plugin.zettel_service, "process_files"),
            patch.object(plugin.tags_service, "process_files"),
        ):
            plugin.on_files(files, config=config)

        mock_feature.compute.assert_called_once()
        mock_feature.export.assert_called_once()
