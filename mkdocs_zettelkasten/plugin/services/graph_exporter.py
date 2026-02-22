from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore

from mkdocs_zettelkasten.plugin.services.backlink_processor import BacklinkProcessor


class GraphExporter:
    """Exports zettel graph data as a JSON-serializable dict."""

    def export(
        self,
        store: ZettelStore,
        tags_metadata: list[dict[str, Any]],
        file_suffix: str = ".md",
    ) -> dict:
        tags_by_path = {m["src_path"]: m.get("tags", []) for m in tags_metadata}
        nodes = []
        id_set = set()

        for z in store.zettels:
            zid = str(z.id)
            id_set.add(zid)
            url = z.rel_path.removesuffix(file_suffix) + "/"
            tags = tags_by_path.get(z.rel_path, []) or []
            nodes.append({"id": zid, "title": z.title, "url": url, "tags": tags})

        edges = []
        seen_edges: set[tuple[str, str]] = set()

        for z in store.zettels:
            source_id = str(z.id)
            for link in BacklinkProcessor.normalize_links(z.links, file_suffix):
                target = store.get_by_partial_path(link, file_suffix)
                if target is None:
                    continue
                target_id = str(target.id)
                pair = (source_id, target_id)
                if pair not in seen_edges:
                    seen_edges.add(pair)
                    edges.append({"source": source_id, "target": target_id})

        return {"nodes": nodes, "edges": edges}
