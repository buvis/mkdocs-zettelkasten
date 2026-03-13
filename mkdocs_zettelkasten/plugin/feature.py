from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
    from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext


@runtime_checkable
class Feature(Protocol):
    name: str
    depends_on: tuple[str, ...]

    def is_enabled(self, config: ZettelkastenConfig) -> bool: ...
    def compute(self, ctx: PipelineContext) -> Any: ...
    def export(self, ctx: PipelineContext, files: Files, config: MkDocsConfig) -> None: ...
    def adapt_page(self, page: Page, ctx: PipelineContext) -> None: ...


def resolve_features(
    features: list[Feature], config: ZettelkastenConfig
) -> list[Feature]:
    """Filter to enabled features and topological sort by depends_on (DFS)."""
    enabled = [f for f in features if f.is_enabled(config)]
    by_name = {f.name: f for f in enabled}
    visited: set[str] = set()
    in_stack: set[str] = set()
    order: list[Feature] = []

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in in_stack:
            msg = f"Circular feature dependency: {name}"
            raise ValueError(msg)
        in_stack.add(name)
        f = by_name.get(name)
        if f is not None:
            for dep in f.depends_on:
                visit(dep)
            order.append(f)
        visited.add(name)
        in_stack.discard(name)

    for f in enabled:
        visit(f.name)

    return order
