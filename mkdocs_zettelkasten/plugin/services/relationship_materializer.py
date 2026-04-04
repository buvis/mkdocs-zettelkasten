from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mkdocs_zettelkasten.plugin.utils.tree_utils import build_tree_node

if TYPE_CHECKING:
    from mkdocs_zettelkasten.plugin.entities.zettel import (
        LinkRef,
        SequenceRef,
        SequenceTreeNode,
        SuggestionRef,
        Zettel,
    )
    from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext
    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def _zettel_url(rel_path: str, file_suffix: str) -> str:
    return rel_path.removesuffix(file_suffix) + "/"


def _find_snippet(source: Zettel, target: Zettel, file_suffix: str) -> str | None:
    candidates = [
        str(target.id),
        target.rel_path,
        target.rel_path.removesuffix(file_suffix),
    ]
    for key in candidates:
        if snippet := source.link_snippets.get(key):
            return snippet
    return None


def materialize_backlinks(
    zettel: Zettel,
    backlinks: dict[int, list[Zettel]],
    file_suffix: str,
) -> None:
    source_zettels = backlinks.get(zettel.id, [])
    for source in source_zettels:
        snippet = _find_snippet(source, zettel, file_suffix)
        backlink: LinkRef = {
            "url": _zettel_url(source.rel_path, file_suffix),
            "title": source.title,
            "snippet": snippet,
        }
        zettel.backlinks.append(backlink)
        if source.is_moc:
            zettel.moc_parents.append(backlink)

    if zettel.backlinks:
        logger.debug(
            "Materialized %d backlinks for %s",
            len(zettel.backlinks),
            zettel.rel_path,
        )


def _find_sequence_root(
    zettel_id: int,
    store: ZettelStore,
) -> int:
    current = zettel_id
    visited: set[int] = set()
    while True:
        visited.add(current)
        z = store.get_by_id(current)
        if not z or z.sequence_parent_id is None or z.sequence_parent_id in visited:
            return current
        current = z.sequence_parent_id


def materialize_sequences(
    zettel: Zettel,
    sequence_children: dict[int, list[int]],
    store: ZettelStore,
    file_suffix: str,
) -> None:
    # Parent
    if zettel.sequence_parent_id is not None:
        parent = store.get_by_id(zettel.sequence_parent_id)
        if parent:
            zettel.sequence_parent = {
                "url": _zettel_url(parent.rel_path, file_suffix),
                "title": parent.title,
            }

    # Children
    for child_id in sequence_children.get(zettel.id, []):
        child = store.get_by_id(child_id)
        if child:
            zettel.sequence_children.append(
                {
                    "url": _zettel_url(child.rel_path, file_suffix),
                    "title": child.title,
                }
            )

    # Breadcrumb (walk ancestors root-ward, then reverse)
    breadcrumb: list[SequenceRef] = []
    current_id = zettel.sequence_parent_id
    visited: set[int] = set()
    while current_id is not None and current_id not in visited:
        visited.add(current_id)
        ancestor = store.get_by_id(current_id)
        if not ancestor:
            break
        breadcrumb.append(
            {
                "url": _zettel_url(ancestor.rel_path, file_suffix),
                "title": ancestor.title,
            }
        )
        current_id = ancestor.sequence_parent_id
    breadcrumb.reverse()
    zettel.sequence_breadcrumb = breadcrumb

    # Build full tree if zettel is in any sequence
    if zettel.sequence_parent_id is not None or zettel.id in sequence_children:
        root_id = _find_sequence_root(zettel.id, store)
        _cur = zettel.id
        _sfx = file_suffix

        def _make_tree_node(z: Zettel, ch: list[SequenceTreeNode]) -> SequenceTreeNode:
            return {
                "url": _zettel_url(z.rel_path, _sfx),
                "title": z.title,
                "current": z.id == _cur,
                "children": ch,
            }

        tree_node = build_tree_node(
            root_id,
            sequence_children,
            store.get_by_id,
            _make_tree_node,
            visited=set(),
        )
        zettel.sequence_tree = [tree_node] if tree_node else []

    logger.debug(
        "Sequence for %s: parent=%s, children=%d, depth=%d",
        zettel.rel_path,
        zettel.sequence_parent_id,
        len(zettel.sequence_children),
        len(zettel.sequence_breadcrumb),
    )


def materialize_unlinked_mentions(
    zettel: Zettel,
    unlinked_mentions: dict[int, list[tuple[int, str]]],
    store: ZettelStore,
    file_suffix: str,
) -> None:
    for src_id, snippet in unlinked_mentions.get(zettel.id, []):
        source = store.get_by_id(src_id)
        if not source:
            continue
        zettel.unlinked_mentions.append(
            {
                "url": _zettel_url(source.rel_path, file_suffix),
                "title": source.title,
                "snippet": snippet,
            }
        )

    if zettel.unlinked_mentions:
        logger.debug(
            "Materialized %d unlinked mentions for %s",
            len(zettel.unlinked_mentions),
            zettel.rel_path,
        )


def materialize_suggestions(
    zettel: Zettel,
    suggestions: dict[int, list[dict]],
    store: ZettelStore,
    file_suffix: str,
) -> None:
    for sugg in suggestions.get(zettel.id, []):
        target = store.get_by_id(sugg["target_id"])
        if not target:
            continue
        entry: SuggestionRef = {
            "url": _zettel_url(target.rel_path, file_suffix),
            "title": target.title,
            "reason": sugg["reason"],
            "confidence": f"{int(sugg['confidence'] * 100)}%",
        }
        zettel.suggested_links.append(entry)

    if zettel.suggested_links:
        logger.debug(
            "Materialized %d suggestions for %s",
            len(zettel.suggested_links),
            zettel.rel_path,
        )


class RelationshipMaterializer:
    @staticmethod
    def materialize_all(ctx: PipelineContext) -> None:
        store = ctx.store
        file_suffix = ctx.config.file_suffix
        for zettel in store.zettels:
            materialize_backlinks(zettel, ctx.backlinks, file_suffix)
            materialize_sequences(zettel, ctx.sequence_children, store, file_suffix)
            materialize_unlinked_mentions(
                zettel, ctx.unlinked_mentions, store, file_suffix
            )
            materialize_suggestions(zettel, ctx.suggestions, store, file_suffix)
        logger.info("Materialized relationships for %d zettels", len(store.zettels))
