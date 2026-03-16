from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

_N = TypeVar("_N")


def build_tree_node(
    zettel_id: int,
    sequence_children: dict[int, list[int]],
    lookup: Callable[[int], Any],
    node_factory: Callable[[Any, list[_N]], _N],
    visited: set[int] | None = None,
) -> _N | None:
    """Recursively build a tree node from sequence_children.

    Pass *visited* as a set to enable cycle prevention, or leave as None
    (outline behaviour) to skip the check.
    """
    if visited is not None:
        if zettel_id in visited:
            return None
        visited.add(zettel_id)
    z = lookup(zettel_id)
    if not z:
        return None
    children: list[_N] = []
    for child_id in sequence_children.get(zettel_id, []):
        child_node = build_tree_node(
            child_id,
            sequence_children,
            lookup,
            node_factory,
            visited,
        )
        if child_node:
            children.append(child_node)
    return node_factory(z, children)
