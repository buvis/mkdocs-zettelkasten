from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files

    from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
    from mkdocs_zettelkasten.plugin.entities.zettel import Zettel
    from mkdocs_zettelkasten.plugin.services.link_resolver import LinkMap
    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


@dataclass
class PipelineContext:
    config: ZettelkastenConfig
    store: ZettelStore
    link_map: LinkMap
    invalid_files: list
    tags_metadata: list[dict[str, Any]]
    tags_folder: Path
    site_dir: str
    results: dict[str, Any] = field(default_factory=dict)

    @property
    def backlinks(self) -> dict[int, list[Zettel]]:
        return self.results.get("backlinks", {})

    @property
    def unlinked_mentions(self) -> dict[int, list[tuple[int, str]]]:
        return self.results.get("unlinked_mentions", {})

    @property
    def sequence_children(self) -> dict[int, list[int]]:
        return self.results.get("sequence_children", {})

    @property
    def suggestions(self) -> dict[int, list[dict]]:
        return self.results.get("suggestions", {})


def export_json(
    ctx: PipelineContext,
    filename: str,
    data: Any,
    files: Files,
    config: MkDocsConfig,
) -> None:
    """Write JSON data to tags_folder and add to MkDocs build."""
    from mkdocs.structure.files import File

    path = ctx.tags_folder / filename
    path.write_text(json.dumps(data), encoding="utf-8")
    files.append(
        File(
            path=filename,
            src_dir=str(ctx.tags_folder),
            dest_dir=config["site_dir"],
            use_directory_urls=False,
        )
    )
