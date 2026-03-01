from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from mkdocs_zettelkasten.plugin.utils.jinja_utils import create_jinja_environment

if TYPE_CHECKING:
    from pathlib import Path

    from mkdocs.structure.files import Files

    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)

PREVIEW_LENGTH = 120


class OutlineService:
    """Computes outline data from MOCs and Folgezettel sequences."""

    def __init__(self) -> None:
        self.output_folder: Path | None = None
        self._site_dir: str | None = None

    def compute(
        self,
        store: ZettelStore,
        sequence_children: dict[int, list[int]],
        file_suffix: str = ".md",
    ) -> dict[str, Any]:
        return {
            "moc_outlines": self._moc_outlines(store, file_suffix),
            "sequence_outlines": self._sequence_outlines(store, sequence_children),
        }

    def configure(self, output_folder: Path, site_dir: str) -> None:
        self.output_folder = output_folder
        self._site_dir = site_dir

    def generate(self, outlines: dict[str, Any]) -> None:
        if self.output_folder is None:
            msg = "configure() must be called before generate()"
            raise RuntimeError(msg)
        env = create_jinja_environment(None)
        template = env.get_template("outline.md.j2")
        content = template.render(**outlines)
        output_path = self.output_folder / "outline.md"
        output_path.write_text(content, encoding="utf-8")
        logger.info("Generated outline page.")

    def add_to_build(self, files: Files) -> None:
        if self.output_folder is None or self._site_dir is None:
            msg = "configure() must be called before add_to_build()"
            raise RuntimeError(msg)
        from mkdocs.structure.files import File

        new_file = File(
            path="outline.md",
            src_dir=str(self.output_folder),
            dest_dir=self._site_dir,
            use_directory_urls=False,
        )
        files.append(new_file)

    def _moc_outlines(self, store, file_suffix):
        outlines = []
        for z in store.zettels:
            if not z.is_moc:
                continue
            entries = self._resolve_moc_entries(z, store, file_suffix)
            if not entries:
                continue
            self._mark_gaps(entries)
            transclusion = "\n".join(f"![[{e['id']}|{e['title']}]]" for e in entries)
            outlines.append(
                {
                    "id": z.id,
                    "title": z.title,
                    "rel_path": z.rel_path,
                    "entries": entries,
                    "transclusion_text": transclusion,
                }
            )
        return outlines

    def _resolve_moc_entries(self, moc, store, file_suffix):
        entries = []
        for link_url in moc.links:
            target = store.get_by_partial_path(link_url, file_suffix)
            if not target or target.id == moc.id:
                continue
            entries.append(
                {
                    "id": target.id,
                    "title": target.title,
                    "rel_path": target.rel_path,
                    "note_type": target.note_type,
                    "maturity": target.maturity,
                    "preview": self._preview(target.body),
                    "gap_before": False,
                    "_linked_ids": self._linked_ids(target, store, file_suffix),
                }
            )
        return entries

    def _mark_gaps(self, entries):
        for i in range(1, len(entries)):
            prev = entries[i - 1]
            curr = entries[i]
            has_link = (
                curr["id"] in prev["_linked_ids"] or prev["id"] in curr["_linked_ids"]
            )
            curr["gap_before"] = not has_link
        for e in entries:
            del e["_linked_ids"]

    def _linked_ids(self, zettel, store, file_suffix):
        ids = set()
        for link_url in zettel.links:
            target = store.get_by_partial_path(link_url, file_suffix)
            if target:
                ids.add(target.id)
        return ids

    def _preview(self, body):
        text = body.strip()
        if text.startswith("#"):
            newline = text.find("\n")
            if newline != -1:
                text = text[newline:].strip()
            else:
                return ""
        if len(text) <= PREVIEW_LENGTH:
            return text
        return text[:PREVIEW_LENGTH].rsplit(" ", 1)[0] + "..."

    def _sequence_outlines(self, store, sequence_children):
        roots = []
        for parent_id in sequence_children:
            parent = store.get_by_id(parent_id)
            if parent and parent.sequence_parent_id is None:
                roots.append(parent)
        roots.sort(key=lambda z: z.title)
        outlines = []
        for z in roots:
            node = self._build_tree_node(z, store, sequence_children)
            node["flat_entries"] = self._flatten_tree(node)
            outlines.append(node)
        return outlines

    def _build_tree_node(self, zettel, store, sequence_children):
        children = []
        for child_id in sequence_children.get(zettel.id, []):
            child = store.get_by_id(child_id)
            if child:
                children.append(self._build_tree_node(child, store, sequence_children))
        return {
            "id": zettel.id,
            "title": zettel.title,
            "rel_path": zettel.rel_path,
            "children": children,
        }

    def _flatten_tree(self, node, depth=0):
        items = [
            {"title": node["title"], "rel_path": node["rel_path"], "indent": depth}
        ]
        for child in node["children"]:
            items.extend(self._flatten_tree(child, depth + 1))
        return items
