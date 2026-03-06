from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mkdocs_zettelkasten.plugin.utils.tree_utils import build_tree_node

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def adapt_sequence_to_page(
    page: Page,
    sequence_children: dict[int, list[int]],
    zettel_lookup: Callable[[int], Zettel | None],
    file_suffix: str = ".md",
) -> None:
    """Populate sequence parent, children, breadcrumb, and tree on the page's zettel."""
    if not page.meta.get("is_zettel"):
        return

    zettel = page.meta.get("zettel")
    if not zettel:
        return

    # Parent
    if zettel.sequence_parent_id is not None:
        parent = zettel_lookup(zettel.sequence_parent_id)
        if parent:
            zettel.sequence_parent = {
                "url": parent.rel_path.removesuffix(file_suffix) + "/",
                "title": parent.title,
            }

    # Children
    for child_id in sequence_children.get(zettel.id, []):
        child = zettel_lookup(child_id)
        if child:
            zettel.sequence_children.append(
                {
                    "url": child.rel_path.removesuffix(file_suffix) + "/",
                    "title": child.title,
                }
            )

    # Breadcrumb (walk ancestors root-ward, then reverse)
    breadcrumb = []
    current_id = zettel.sequence_parent_id
    visited: set[int] = set()
    while current_id is not None and current_id not in visited:
        visited.add(current_id)
        ancestor = zettel_lookup(current_id)
        if not ancestor:
            break
        breadcrumb.append(
            {
                "url": ancestor.rel_path.removesuffix(file_suffix) + "/",
                "title": ancestor.title,
            }
        )
        current_id = ancestor.sequence_parent_id
    breadcrumb.reverse()
    zettel.sequence_breadcrumb = breadcrumb

    # Build full tree if zettel is in any sequence
    if zettel.sequence_parent_id is not None or zettel.id in sequence_children:
        root_id = _find_sequence_root(zettel.id, zettel_lookup)
        _cur = zettel.id
        _sfx = file_suffix
        tree_node = build_tree_node(
            root_id,
            sequence_children,
            zettel_lookup,
            lambda z, ch: {
                "url": z.rel_path.removesuffix(_sfx) + "/",
                "title": z.title,
                "current": z.id == _cur,
                "children": ch,
            },
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


def _find_sequence_root(
    zettel_id: int,
    zettel_lookup: Callable[[int], Zettel | None],
) -> int:
    """Walk up the sequence tree to find the root."""
    current = zettel_id
    visited: set[int] = set()
    while True:
        visited.add(current)
        z = zettel_lookup(current)
        if not z or z.sequence_parent_id is None or z.sequence_parent_id in visited:
            return current
        current = z.sequence_parent_id
