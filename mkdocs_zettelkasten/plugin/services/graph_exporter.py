from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mkdocs_zettelkasten.plugin.entities.zettel import Zettel
    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


class GraphExporter:
    """Exports zettel graph data as a JSON-serializable dict."""

    def export(
        self,
        store: ZettelStore,
        tags_metadata: list[dict[str, Any]],
        backlinks: dict[str, list[Zettel]],
        file_suffix: str = ".md",
    ) -> dict:
        tags_by_path = {m["src_path"]: m.get("tags", []) for m in tags_metadata}
        id_set: set[str] = set()
        nodes = []

        for z in store.zettels:
            zid = str(z.id)
            id_set.add(zid)
            url = z.rel_path.removesuffix(file_suffix) + "/"
            tags = tags_by_path.get(z.rel_path, []) or []
            node: dict[str, Any] = {
                "id": zid,
                "title": z.title,
                "url": url,
                "tags": tags,
            }
            if z.note_type is not None:
                node["type"] = z.note_type
            if z.maturity is not None:
                node["maturity"] = z.maturity
            if z.role is not None:
                node["role"] = z.role
            nodes.append(node)

        edges = []
        seen_edges: set[tuple[str, str]] = set()

        # Build edges from precomputed backlinks (link_path -> source zettels)
        for link_path, source_zettels in backlinks.items():
            target = store.get_by_partial_path(link_path, file_suffix)
            if target is None:
                continue
            target_id = str(target.id)
            if target_id not in id_set:
                continue
            for source in source_zettels:
                source_id = str(source.id)
                if source_id not in id_set:
                    continue
                pair = (source_id, target_id)
                if pair not in seen_edges:
                    seen_edges.add(pair)
                    edges.append({"source": source_id, "target": target_id})

        return {"nodes": nodes, "edges": edges}
