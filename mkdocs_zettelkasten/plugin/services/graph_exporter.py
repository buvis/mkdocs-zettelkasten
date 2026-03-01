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
        nodes, id_set = self._build_nodes(store, tags_by_path, file_suffix)

        seen_edges: set[tuple[str, str]] = set()
        edges = self._build_backlink_edges(
            store, backlinks, id_set, seen_edges, file_suffix
        )
        edges += self._build_sequence_edges(store, id_set, seen_edges)

        degree: dict[str, int] = {}
        for edge in edges:
            degree[edge["source"]] = degree.get(edge["source"], 0) + 1
            degree[edge["target"]] = degree.get(edge["target"], 0) + 1
        for node in nodes:
            node["degree"] = degree.get(node["id"], 0)

        return {"nodes": nodes, "edges": edges}

    @staticmethod
    def _build_nodes(
        store: ZettelStore,
        tags_by_path: dict[str, list[str]],
        file_suffix: str,
    ) -> tuple[list[dict[str, Any]], set[str]]:
        id_set: set[str] = set()
        nodes = []
        for z in store.zettels:
            zid = str(z.id)
            id_set.add(zid)
            node: dict[str, Any] = {
                "id": zid,
                "title": z.title,
                "url": z.rel_path.removesuffix(file_suffix) + "/",
                "tags": tags_by_path.get(z.rel_path, []) or [],
            }
            if z.note_type is not None:
                node["type"] = z.note_type
            if z.maturity is not None:
                node["maturity"] = z.maturity
            if z.role is not None:
                node["role"] = z.role
            nodes.append(node)
        return nodes, id_set

    @staticmethod
    def _build_backlink_edges(
        store: ZettelStore,
        backlinks: dict[str, list[Zettel]],
        id_set: set[str],
        seen: set[tuple[str, str]],
        file_suffix: str,
    ) -> list[dict[str, str]]:
        edges = []
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
                if pair not in seen:
                    seen.add(pair)
                    edges.append({"source": source_id, "target": target_id})
        return edges

    @staticmethod
    def _build_sequence_edges(
        store: ZettelStore,
        id_set: set[str],
        seen: set[tuple[str, str]],
    ) -> list[dict[str, str]]:
        edges = []
        for z in store.zettels:
            if z.sequence_parent_id is None:
                continue
            child_id = str(z.id)
            parent_id = str(z.sequence_parent_id)
            if parent_id not in id_set or child_id not in id_set:
                continue
            pair = (child_id, parent_id)
            if pair not in seen:
                seen.add(pair)
                edges.append(
                    {"source": child_id, "target": parent_id, "type": "sequence"}
                )
        return edges
