from __future__ import annotations

from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

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
from mkdocs_zettelkasten.plugin.feature import Feature, resolve_features
from mkdocs_zettelkasten.plugin.features.backlink_feature import BacklinkFeature
from mkdocs_zettelkasten.plugin.features.graph_feature import GraphFeature
from mkdocs_zettelkasten.plugin.features.outline_feature import OutlineFeature
from mkdocs_zettelkasten.plugin.features.preview_feature import PreviewFeature
from mkdocs_zettelkasten.plugin.features.sequence_feature import SequenceFeature
from mkdocs_zettelkasten.plugin.features.suggestion_feature import SuggestionFeature
from mkdocs_zettelkasten.plugin.features.unlinked_mention_feature import (
    UnlinkedMentionFeature,
)
from mkdocs_zettelkasten.plugin.features.validation_feature import ValidationFeature
from mkdocs_zettelkasten.plugin.features.workflow_feature import WorkflowFeature
from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext
from mkdocs_zettelkasten.plugin.services.page_transformer import PageTransformer
from mkdocs_zettelkasten.plugin.services.tags_service import TagsService
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
        self.page_transformer = PageTransformer()
        self._features: list[Feature] = [
            BacklinkFeature(),
            UnlinkedMentionFeature(),
            SequenceFeature(),
            SuggestionFeature(),
            GraphFeature(),
            PreviewFeature(),
            OutlineFeature(),
            WorkflowFeature(),
            ValidationFeature(),
        ]
        self._active_features: list[Feature] = []
        self._ctx: PipelineContext | None = None
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
        self._active_features = resolve_features(self._features, self.zk_config)
        for f in self._active_features:
            extra_key = getattr(f, "extra_key", None)
            if extra_key:
                config["extra"][extra_key] = True
        if self.config["editor_enabled"]:
            config["extra"]["editor_enabled"] = True
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
        link_map = self.zettel_service.link_map
        if link_map is None:
            msg = "link_map not initialized; process_files must run first"
            raise RuntimeError(msg)
        self._ctx = PipelineContext(
            config=self.zk_config,
            store=self.zettel_service.store,
            link_map=link_map,
            invalid_files=self.zettel_service.invalid_files,
            tags_metadata=self.tags_service.metadata,
            tags_folder=self.tags_service.tags_folder,
            site_dir=config["site_dir"],
        )
        for f in self._active_features:
            self._ctx.results[f.name] = f.compute(self._ctx)
            f.export(self._ctx, files, config)
        self.logger.info("Processed %d files in on_files hook.", len(files))

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
        if self._ctx is None:
            msg = "PipelineContext not initialized; on_files must run first"
            raise RuntimeError(msg)
        transformed_markdown = self.page_transformer.transform(
            markdown,
            page,
            config,
            files,
            self.zettel_service,
            self._active_features,
            self._ctx,
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
