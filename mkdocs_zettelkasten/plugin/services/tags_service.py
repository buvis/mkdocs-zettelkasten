from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files

    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore

import logging
from pathlib import Path
from typing import Any

from mkdocs_zettelkasten.plugin.utils.jinja_utils import create_jinja_environment
from mkdocs_zettelkasten.plugin.utils.metadata_utils import extract_file_metadata

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class TagsService:
    """
    Handles tag extraction, template rendering, and tags file generation.
    """

    def __init__(self) -> None:
        self.tags_filename: Path = Path("tags.md")
        self.tags_folder: Path = Path(".build")
        self.tags_template: Path | None = None
        self.tags_key: str = "tags"
        self.role_key: str = "role"
        self.metadata: list[dict[str, Any]] = []
        self._docs_dir: str = ""
        self._site_dir: str = ""

    def configure(
        self,
        config: MkDocsConfig,
        tags_key: str = "tags",
        file_suffix: str = ".md",
        role_key: str = "role",
    ) -> None:
        """
        Configure paths and template from MkDocs config.
        """
        self.tags_key = tags_key
        self.role_key = role_key
        self.file_suffix = file_suffix
        self.tags_filename = Path(config.get("tags_filename", "tags.md"))
        self.tags_folder = Path(config.get("tags_folder", ".build"))

        logger.debug(
            "Configuring TagsService: tags_filename=%s, tags_folder=%s",
            self.tags_filename,
            self.tags_folder,
        )
        if not self.tags_folder.is_absolute():
            self.tags_folder = Path(config["docs_dir"]).parent / self.tags_folder
            logger.debug(
                "Resolved relative tags_folder to absolute path: %s", self.tags_folder
            )
        if config.get("tags_template"):
            self.tags_template = Path(config["tags_template"])
            logger.debug("Using custom tags_template: %s", self.tags_template)
        if not self.tags_folder.exists():
            self.tags_folder.mkdir(parents=True)
            logger.info("Created tags_folder: %s", self.tags_folder)

        self._docs_dir = config["docs_dir"]
        self._site_dir = config["site_dir"]

    def process_files(self, files: Files, store: ZettelStore | None = None) -> None:
        logger.info("Processing %d files for tag extraction.", len(files))
        self.process_metadata(files, store)
        self.generate_tags_file()
        self.add_tags_file_to_build(files)

    def process_metadata(self, files: Files, store: ZettelStore | None = None) -> None:
        """Extract metadata from Markdown files.

        Uses pre-parsed Zettel metadata when available (via store),
        falling back to extract_file_metadata for non-zettel files.
        """
        self.metadata.clear()
        for file in files:
            if not file.src_path.endswith(self.file_suffix):
                continue
            zettel = store.get_by_partial_path(file.src_path, self.file_suffix) if store else None
            if zettel:
                meta = dict(zettel.meta)
                meta["src_path"] = file.src_path
                self.metadata.append(meta)
            else:
                meta = extract_file_metadata(file.src_path, self._docs_dir)
                if meta:
                    meta["src_path"] = file.src_path
                    self.metadata.append(meta)

    def generate_tags_file(self) -> None:
        """
        Render and write the tags file.
        """
        tag_map = self._create_tag_map()
        rendered = self._render_tags_template(tag_map)
        self._write_tags_file(rendered)

    def add_tags_file_to_build(self, files: Files) -> None:
        """
        Add the generated tags file to the MkDocs build list.
        """
        # deferred: avoid import-time mkdocs coupling
        from mkdocs.structure.files import File

        new_file = File(
            path=str(self.tags_filename),
            src_dir=str(self.tags_folder),
            dest_dir=self._site_dir,
            use_directory_urls=False,
        )
        files.append(new_file)
        logger.info("List of pages per tag added as %s", new_file.src_path)

    def _create_tag_map(self) -> dict[str, list[dict[str, Any]]]:
        """
        Create a mapping of tags to metadata entries.
        """
        from collections import defaultdict

        tag_map = defaultdict(list)
        for meta in sorted(self.metadata, key=lambda x: x.get("year", 5000)):
            if tags := meta.get(self.tags_key):
                for tag in tags:
                    tag_map[tag].append(meta)

        logger.info("Found %d unique tags: %s", len(tag_map), ", ".join(tag_map))
        return dict(tag_map)

    def _render_tags_template(self, tag_map: dict[str, list[dict[str, Any]]]) -> str:
        """
        Render the tags page using a Jinja2 template.
        """
        env = create_jinja_environment(self.tags_template)
        template_name = self.tags_template.name if self.tags_template else "tags.md.j2"
        template = env.get_template(template_name)
        return template.render(
            tags=sorted(tag_map.items(), key=lambda t: t[0].lower()),
            role_key=self.role_key,
        )

    def _write_tags_file(self, content: str) -> None:
        """
        Write the rendered tags content to the output file.
        """
        output_path = self.tags_folder / self.tags_filename
        output_path.write_text(content, encoding="utf-8")
