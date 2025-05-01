from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

import logging

import colorlog
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

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
    )

    def __init__(self) -> None:
        super().__init__()
        self.tags_service = TagsService()
        self.zettel_service = ZettelService()
        self.page_transformer = PageTransformer()
        self._initialize_logger()
        self.logger.debug("Initialized ZettelkastenPlugin with services and logger.")

    def on_config(self, config: MkDocsConfig) -> None:
        self.logger.setLevel(self.config["log_level"])
        self.logger.addHandler(self._create_logging_handler())
        self.tags_service.configure(config)
        self.logger.info("Configured ZettelkastenPlugin with MkDocs config.")

    def on_files(self, files: Files, config: MkDocsConfig) -> None:
        _ = config
        self.zettel_service.process_files(files, config)
        self.tags_service.process_files(files)
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
