from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

import json
import logging
import os
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import colorlog
import tzlocal
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
from mkdocs_zettelkasten.plugin.services.graph_exporter import GraphExporter
from mkdocs_zettelkasten.plugin.services.outline_service import OutlineService
from mkdocs_zettelkasten.plugin.services.page_transformer import PageTransformer
from mkdocs_zettelkasten.plugin.services.preview_exporter import PreviewExporter
from mkdocs_zettelkasten.plugin.services.suggestion_service import SuggestionService
from mkdocs_zettelkasten.plugin.services.tags_service import TagsService
from mkdocs_zettelkasten.plugin.services.validation_service import ValidationService
from mkdocs_zettelkasten.plugin.services.workflow_service import WorkflowService
from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService


# reference: https://www.mkdocs.org/dev-guide/plugins
class ZettelkastenPlugin(BasePlugin):
    """
    MkDocs plugin entrypoint for Zettelkasten features.
    Orchestrates tag generation, zettel management, and page adaptation.
    """

    config_scheme = (
        (
            "log_level",
            config_options.Choice(
                choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
                default="INFO",
            ),
        ),
        (
            "log_format",
            config_options.Type(
                str,
                default="%(log_color)s%(levelname)-7s%(reset)s -  [%(green)s%(asctime)s.%(msecs)03d%(reset)s] <%(blue)s%(name)s%(reset)s>: %(message_log_color)s%(message)s%(reset)s",
            ),
        ),
        ("id_key", config_options.Type(str, default="id")),
        ("date_key", config_options.Type(str, default="date")),
        ("last_update_key", config_options.Type(str, default="last_update")),
        ("tags_key", config_options.Type(str, default="tags")),
        ("type_key", config_options.Type(str, default="type")),
        ("maturity_key", config_options.Type(str, default="maturity")),
        ("role_key", config_options.Type(str, default="role")),
        ("sequence_key", config_options.Type(str, default="sequence")),
        ("id_format", config_options.Type(str, default=r"^\d{14}$")),
        ("timezone", config_options.Type(str, default="")),
        ("validation_enabled", config_options.Type(bool, default=True)),
        ("editor_enabled", config_options.Type(bool, default=False)),
        ("editor_repo", config_options.Type(str, default="")),
        ("editor_branch", config_options.Type(str, default="master")),
        ("editor_docs_prefix", config_options.Type(str, default="docs")),
        ("date_format", config_options.Type(str, default="%Y-%m-%d")),
        ("icon_references", config_options.Type(str, default="fa fa-book")),
        ("icon_backlinks", config_options.Type(str, default="fa fa-link")),
        ("file_suffix", config_options.Type(str, default=".md")),
        ("graph_enabled", config_options.Type(bool, default=False)),
        ("preview_enabled", config_options.Type(bool, default=False)),
        ("suggestions_enabled", config_options.Type(bool, default=False)),
        ("workflow_enabled", config_options.Type(bool, default=False)),
        ("transclusion_strip_heading", config_options.Type(bool, default=True)),
        ("minify_js", config_options.Type(bool, default=True)),
    )

    def __init__(self) -> None:
        super().__init__()
        self.tags_service = TagsService()
        self.zettel_service = ZettelService()
        self.validation_service = ValidationService()
        self.graph_exporter = GraphExporter()
        self.outline_service = OutlineService()
        self.preview_exporter = PreviewExporter()
        self.suggestion_service = SuggestionService()
        self.workflow_service = WorkflowService()
        self.page_transformer = PageTransformer()
        self._is_serve = False
        self._initialize_logger()
        self.logger.debug("Initialized ZettelkastenPlugin with services and logger.")

    def on_startup(self, *, command: str, dirty: bool) -> None:  # noqa: ARG002
        self._is_serve = command == "serve"

    def on_config(self, config: MkDocsConfig) -> None:
        self.logger.setLevel(self.config["log_level"])
        if not any(
            isinstance(h, logging.StreamHandler)
            and not isinstance(h, logging.NullHandler)
            for h in self.logger.handlers
        ):
            self.logger.addHandler(self._create_logging_handler())
        tz = self._resolve_timezone()
        self.zk_config = ZettelkastenConfig(
            **{
                k: self.config[k]
                for k in ZettelkastenConfig.__dataclass_fields__
                if k != "timezone"
            },
            timezone=tz,
        )
        self.zettel_service.configure(self.zk_config)
        self.tags_service.configure(
            config,
            tags_key=self.zk_config.tags_key,
            file_suffix=self.zk_config.file_suffix,
            role_key=self.zk_config.role_key,
        )
        if self.zk_config.validation_enabled:
            self.validation_service.configure(self.zk_config.timezone, config)
        if self.config["editor_enabled"]:
            config["extra"]["editor_enabled"] = True
        if self.config["graph_enabled"]:
            config["extra"]["graph_enabled"] = True
        if self.config["preview_enabled"]:
            config["extra"]["preview_enabled"] = True
        if self.config["workflow_enabled"]:
            self.workflow_service.configure(
                self.zk_config.timezone,
                self.tags_service.tags_folder,
                config["site_dir"],
            )
            config["extra"]["workflow_enabled"] = True
        self.outline_service.configure(
            self.tags_service.tags_folder,
            config["site_dir"],
        )
        config["extra"]["transclusion_strip_heading"] = self.config[
            "transclusion_strip_heading"
        ]
        config["extra"]["plugin_version"] = version("mkdocs-zettelkasten")
        self.logger.info("Configured ZettelkastenPlugin with MkDocs config.")

    def _resolve_timezone(self) -> ZoneInfo:
        tz_name = (
            os.environ.get("ZETTELKASTEN_TZ")
            or self.config["timezone"]
            or tzlocal.get_localzone_name()
        )
        if not tz_name:
            self.logger.warning("Could not detect system timezone, falling back to UTC")
            return ZoneInfo("UTC")
        try:
            return ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, KeyError):
            self.logger.error("Invalid timezone '%s', falling back to UTC", tz_name)
            return ZoneInfo("UTC")

    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> None:
        self.zettel_service.process_files(files, config)
        self.tags_service.process_files(files, store=self.zettel_service.store)
        if self.config["graph_enabled"]:
            self._export_graph(files, config)
        if self.config["preview_enabled"]:
            self._export_previews(files, config)
        link_map = self.zettel_service.link_map
        if self.config["suggestions_enabled"]:
            if link_map is None:
                msg = "link_map not initialized; process_files must run first"
                raise RuntimeError(msg)
            self.zettel_service.suggestions = self.suggestion_service.compute(
                self.zettel_service.store,
                self.tags_service.metadata,
                link_map.resolved,
            )
            self._export_suggestions(files, config)
        outlines = self.outline_service.compute(
            self.zettel_service.store,
            self.zettel_service.sequence_children,
            file_suffix=self.config["file_suffix"],
        )
        if outlines["moc_outlines"] or outlines["sequence_outlines"]:
            self.outline_service.generate(outlines)
            self.outline_service.add_to_build(files)
            config["extra"]["outline_enabled"] = True
        if self.config["workflow_enabled"]:
            dashboard = self.workflow_service.compute(
                self.zettel_service.store,
                self.zettel_service.backlinks,
                self.zettel_service.unlinked_mentions,
            )
            self.workflow_service.generate(dashboard)
            self.workflow_service.add_to_build(files)
            config["extra"]["workflow_inbox_count"] = len(dashboard["inbox"])
        if self.config["validation_enabled"]:
            if link_map is None:
                msg = "link_map not initialized; process_files must run first"
                raise RuntimeError(msg)
            self.validation_service.validate(
                self.zettel_service,
                files,
                config,
                link_map.broken,
            )
            config["extra"]["validation_issues_count"] = (
                self.validation_service.total_actionable_issues()
            )
        self.logger.info("Processed %d files in on_files hook.", len(files))

    def _export_json(
        self, filename: str, data: Any, files: Files, config: MkDocsConfig
    ) -> None:
        # deferred: avoid import-time mkdocs coupling
        from mkdocs.structure.files import File

        path = self.tags_service.tags_folder / filename
        path.write_text(json.dumps(data), encoding="utf-8")
        files.append(
            File(
                path=filename,
                src_dir=str(self.tags_service.tags_folder),
                dest_dir=config["site_dir"],
                use_directory_urls=False,
            )
        )

    def _export_graph(self, files: Files, config: MkDocsConfig) -> None:
        graph_data = self.graph_exporter.export(
            self.zettel_service.store,
            self.tags_service.metadata,
            self.zettel_service.backlinks,
            file_suffix=self.config["file_suffix"],
        )
        self._export_json("graph.json", graph_data, files, config)

    def _export_previews(self, files: Files, config: MkDocsConfig) -> None:
        preview_data = self.preview_exporter.export(
            self.zettel_service.store,
            file_suffix=self.config["file_suffix"],
        )
        self._export_json("previews.json", preview_data, files, config)

    def _export_suggestions(self, files: Files, config: MkDocsConfig) -> None:
        sugg_data = {}
        store = self.zettel_service.store
        suffix = self.config["file_suffix"]
        for zid, suggs in self.zettel_service.suggestions.items():
            z = store.get_by_id(zid)
            if not z:
                continue
            entries = []
            for s in suggs:
                target = store.get_by_id(s["target_id"])
                if not target:
                    continue
                entries.append(
                    {
                        "target_id": str(s["target_id"]),
                        "target_title": target.title,
                        "target_url": target.rel_path.removesuffix(suffix) + "/",
                        "reason": s["reason"],
                        "confidence": s["confidence"],
                    }
                )
            if entries:
                sugg_data[str(zid)] = entries

        self._export_json("suggestions.json", sugg_data, files, config)

    def on_page_markdown(
        self,
        markdown: str,
        /,
        *,
        page: Page,
        config: MkDocsConfig,
        files: Files,
    ) -> str | None:
        self.logger.debug("Transforming markdown for page: %s.", page.url)
        transformed_markdown = self.page_transformer.transform(
            markdown,
            page,
            config,
            files,
            self.zettel_service,
        )
        if self.config["validation_enabled"]:
            page.meta["validation_issues"] = self.validation_service.get_issues(
                page.file.src_path
            )
        if self.config["editor_enabled"]:
            page.meta["editor"] = {
                "repo": self.config["editor_repo"],
                "branch": self.config["editor_branch"],
                "docs_prefix": self.config["editor_docs_prefix"],
            }
        page.meta["icons"] = {
            "references": self.config["icon_references"],
            "backlinks": self.config["icon_backlinks"],
        }
        self.logger.debug("Completed markdown transformation for page: %s.", page.url)

        return transformed_markdown

    def _initialize_logger(self) -> None:
        self.logger = logging.getLogger("mkdocs.plugins.zettelkasten")
        self.logger.propagate = False
        self.logger.addHandler(logging.NullHandler())

    def _create_logging_handler(self) -> logging.StreamHandler:
        handler = colorlog.StreamHandler()

        # Define color scheme for log levels (common practice)
        log_colors = {
            "DEBUG": "white",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        }

        # Create formatter with colors applied to specific parts
        formatter = colorlog.ColoredFormatter(
            fmt=self.config["log_format"],
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors=log_colors,
            secondary_log_colors={"message": log_colors},
            reset=True,
        )
        handler.setFormatter(formatter)

        return handler

    def on_post_build(self, *, config: MkDocsConfig) -> None:
        if self._is_serve or not self.config["minify_js"]:
            return
        import rjsmin

        js_dir = Path(config["site_dir"]) / "js"
        if not js_dir.is_dir():
            return
        for path in js_dir.iterdir():
            if path.suffix != ".js" or not path.is_file():
                continue
            source = path.read_text()
            minified = cast("str", rjsmin.jsmin(source))
            path.write_text(minified)
            self.logger.debug(
                "Minified %s (%d → %d bytes)", path.name, len(source), len(minified)
            )
