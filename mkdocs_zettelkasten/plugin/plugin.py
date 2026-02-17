from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

import logging
import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import colorlog
import tzlocal
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

from mkdocs_zettelkasten.plugin.services.page_transformer import PageTransformer
from mkdocs_zettelkasten.plugin.services.tags_service import TagsService
from mkdocs_zettelkasten.plugin.services.validation_service import ValidationService
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
        ("id_format", config_options.Type(str, default=r"^\d{14}$")),
        ("timezone", config_options.Type(str, default="")),
        ("validation_enabled", config_options.Type(bool, default=True)),
        ("editor_enabled", config_options.Type(bool, default=False)),
        ("editor_repo", config_options.Type(str, default="")),
        ("editor_branch", config_options.Type(str, default="main")),
        ("editor_docs_prefix", config_options.Type(str, default="docs")),
        ("date_format", config_options.Type(str, default="%Y-%m-%d")),
        ("icon_references", config_options.Type(str, default="fa fa-book")),
        ("icon_backlinks", config_options.Type(str, default="fa fa-link")),
        ("file_suffix", config_options.Type(str, default=".md")),
    )

    def __init__(self) -> None:
        super().__init__()
        self.tags_service = TagsService()
        self.zettel_service = ZettelService()
        self.validation_service = ValidationService()
        self.page_transformer = PageTransformer()
        self._initialize_logger()
        self.logger.debug("Initialized ZettelkastenPlugin with services and logger.")

    def on_config(self, config: MkDocsConfig) -> None:
        self.logger.setLevel(self.config["log_level"])
        self.logger.addHandler(self._create_logging_handler())
        tz = self._resolve_timezone()
        zettel_config = {
            "id_key": self.config["id_key"],
            "date_key": self.config["date_key"],
            "last_update_key": self.config["last_update_key"],
            "tags_key": self.config["tags_key"],
            "id_format": self.config["id_format"],
            "timezone": tz,
            "date_format": self.config["date_format"],
            "file_suffix": self.config["file_suffix"],
        }
        self.zettel_service.configure(zettel_config)
        self.tags_service.configure(
            config,
            tags_key=self.config["tags_key"],
            file_suffix=self.config["file_suffix"],
        )
        if self.config["validation_enabled"]:
            self.validation_service.configure(
                config, file_suffix=self.config["file_suffix"]
            )
        if self.config["editor_enabled"]:
            config["extra"]["editor_enabled"] = True
        self.logger.info("Configured ZettelkastenPlugin with MkDocs config.")

    def _resolve_timezone(self) -> ZoneInfo:
        tz_name = (
            os.environ.get("ZETTELKASTEN_TZ")
            or self.config["timezone"]
            or tzlocal.get_localzone_name()
        )
        try:
            return ZoneInfo(tz_name)
        except (ZoneInfoNotFoundError, KeyError):
            self.logger.error("Invalid timezone '%s', falling back to UTC", tz_name)
            return ZoneInfo("UTC")

    def on_files(self, files: Files, config: MkDocsConfig) -> None:
        self.zettel_service.process_files(files, config)
        self.tags_service.process_files(files)
        if self.config["validation_enabled"]:
            self.validation_service.validate(self.zettel_service, files, config)
        self.logger.info("Processed %d files in on_files hook.", len(files))

    def on_page_markdown(
        self,
        markdown: str,
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
