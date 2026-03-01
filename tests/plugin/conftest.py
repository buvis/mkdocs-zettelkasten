from __future__ import annotations

from pathlib import Path, PurePosixPath
from unittest.mock import MagicMock


def _make_zettel_mock(
    zettel_id: int,
    *,
    title: str = "Untitled",
    rel_path: str = "note.md",
    path: Path | PurePosixPath | None = None,
    note_type: str | None = None,
    maturity: str | None = None,
    links: list[str] | None = None,
    role: str | None = None,
    body: str = "",
    sequence_parent_id: int | None = None,
    source: str | None = None,
    backlinks: list[dict[str, str]] | None = None,
    moc_parents: list[dict[str, str]] | None = None,
    link_snippets: dict[str, str] | None = None,
    unlinked_mentions: list[dict[str, str]] | None = None,
    suggested_links: list[dict[str, str]] | None = None,
    sequence_parent: dict[str, str] | None = None,
    sequence_children: list[dict[str, str]] | None = None,
    sequence_breadcrumb: list[dict[str, str]] | None = None,
    sequence_tree: list[dict] | None = None,
    last_update_date: str = "",
) -> MagicMock:
    """Build a MagicMock zettel with all standard attributes.

    Plain function (not a fixture) — importable from conftest by any test module
    under tests/plugin/.
    """
    z = MagicMock()
    z.id = zettel_id
    z.title = title
    z.rel_path = rel_path
    z.path = path if path is not None else PurePosixPath(rel_path)
    z.note_type = note_type
    z.maturity = maturity
    z.links = links if links is not None else []
    z.role = role
    z.is_moc = role in ("moc", "index", "hub", "structure") if role else False
    z.body = body
    z.sequence_parent_id = sequence_parent_id
    z.source = source
    z.backlinks = backlinks if backlinks is not None else []
    z.moc_parents = moc_parents if moc_parents is not None else []
    z.link_snippets = link_snippets if link_snippets is not None else {}
    z.unlinked_mentions = unlinked_mentions if unlinked_mentions is not None else []
    z.suggested_links = suggested_links if suggested_links is not None else []
    z.sequence_parent = sequence_parent
    z.sequence_children = sequence_children if sequence_children is not None else []
    z.sequence_breadcrumb = (
        sequence_breadcrumb if sequence_breadcrumb is not None else []
    )
    z.sequence_tree = sequence_tree if sequence_tree is not None else []
    z.last_update_date = last_update_date

    z.__hash__ = lambda _self: hash(zettel_id)
    z.__eq__ = lambda _self, other: getattr(other, "id", None) == zettel_id
    return z
