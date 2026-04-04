"""Tests for RelationshipMaterializer and its materialize_* functions."""

from __future__ import annotations

from pathlib import Path

from mkdocs_zettelkasten.plugin.entities.zettel import (
    Zettel,
    ZettelMeta,
)
from mkdocs_zettelkasten.plugin.services.relationship_materializer import (
    materialize_backlinks,
    materialize_sequences,
    materialize_suggestions,
    materialize_unlinked_mentions,
)
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


def _make_zettel(
    zettel_id: int,
    title: str = "",
    role: str | None = None,
    seq_parent: int | None = None,
    links: list[str] | None = None,
    link_snippets: dict[str, str] | None = None,
) -> Zettel:
    meta = ZettelMeta(
        id=zettel_id,
        title=title or f"Note {zettel_id}",
        path=Path(f"/tmp/{zettel_id}.md"),
        rel_path=f"{zettel_id}.md",
        body="",
        last_update_date="2024-01-01",
        meta={"id": zettel_id},
        links=links or [],
        link_snippets=link_snippets or {},
        role=role,
        sequence_parent_id=seq_parent,
    )
    return Zettel.from_parts(meta)


class TestMaterializeBacklinks:
    def test_no_backlinks(self) -> None:
        target = _make_zettel(1)
        materialize_backlinks(target, {}, ".md")
        assert target.backlinks == []

    def test_single_backlink(self) -> None:
        source = _make_zettel(2, title="Source")
        target = _make_zettel(1, title="Target")
        backlinks = {1: [source]}
        materialize_backlinks(target, backlinks, ".md")
        assert len(target.backlinks) == 1
        assert target.backlinks[0]["url"] == "2/"
        assert target.backlinks[0]["title"] == "Source"

    def test_moc_parent_populated(self) -> None:
        moc = _make_zettel(2, title="MOC", role="moc")
        target = _make_zettel(1)
        backlinks = {1: [moc]}
        materialize_backlinks(target, backlinks, ".md")
        assert len(target.backlinks) == 1
        assert len(target.moc_parents) == 1
        assert target.moc_parents[0]["title"] == "MOC"

    def test_non_moc_no_moc_parent(self) -> None:
        source = _make_zettel(2, role=None)
        target = _make_zettel(1)
        materialize_backlinks(target, {1: [source]}, ".md")
        assert len(target.moc_parents) == 0

    def test_snippet_from_link_snippets(self) -> None:
        source = _make_zettel(
            2,
            link_snippets={"1": "see <mark>1</mark>"},
        )
        target = _make_zettel(1)
        materialize_backlinks(target, {1: [source]}, ".md")
        assert target.backlinks[0]["snippet"] == "see <mark>1</mark>"


class TestMaterializeSequences:
    def test_no_sequence(self) -> None:
        zettel = _make_zettel(1)
        store = ZettelStore([zettel])
        materialize_sequences(zettel, {}, store, ".md")
        assert zettel.sequence_parent is None
        assert zettel.sequence_children == []

    def test_parent_resolved(self) -> None:
        parent = _make_zettel(1, title="Parent")
        child = _make_zettel(2, seq_parent=1)
        store = ZettelStore([parent, child])
        materialize_sequences(child, {}, store, ".md")
        assert child.sequence_parent is not None
        assert child.sequence_parent["title"] == "Parent"
        assert child.sequence_parent["url"] == "1/"

    def test_children_resolved(self) -> None:
        parent = _make_zettel(1)
        child = _make_zettel(2, seq_parent=1)
        store = ZettelStore([parent, child])
        seq_children = {1: [2]}
        materialize_sequences(parent, seq_children, store, ".md")
        assert len(parent.sequence_children) == 1
        assert parent.sequence_children[0]["title"] == "Note 2"

    def test_breadcrumb_built(self) -> None:
        root = _make_zettel(1, title="Root")
        mid = _make_zettel(2, title="Mid", seq_parent=1)
        leaf = _make_zettel(3, title="Leaf", seq_parent=2)
        store = ZettelStore([root, mid, leaf])
        seq_children = {1: [2], 2: [3]}
        materialize_sequences(leaf, seq_children, store, ".md")
        assert len(leaf.sequence_breadcrumb) == 2
        assert leaf.sequence_breadcrumb[0]["title"] == "Root"
        assert leaf.sequence_breadcrumb[1]["title"] == "Mid"

    def test_tree_built(self) -> None:
        root = _make_zettel(1, title="Root")
        child = _make_zettel(2, title="Child", seq_parent=1)
        store = ZettelStore([root, child])
        seq_children = {1: [2]}
        materialize_sequences(child, seq_children, store, ".md")
        assert len(child.sequence_tree) == 1
        tree_root = child.sequence_tree[0]
        assert tree_root["title"] == "Root"
        assert len(tree_root["children"]) == 1
        assert tree_root["children"][0]["current"] is True


class TestMaterializeUnlinkedMentions:
    def test_no_mentions(self) -> None:
        zettel = _make_zettel(1)
        store = ZettelStore([zettel])
        materialize_unlinked_mentions(zettel, {}, store, ".md")
        assert zettel.unlinked_mentions == []

    def test_single_mention(self) -> None:
        source = _make_zettel(2, title="Mentioner")
        target = _make_zettel(1)
        store = ZettelStore([source, target])
        mentions = {1: [(2, "snippet text")]}
        materialize_unlinked_mentions(target, mentions, store, ".md")
        assert len(target.unlinked_mentions) == 1
        assert target.unlinked_mentions[0]["url"] == "2/"
        assert target.unlinked_mentions[0]["title"] == "Mentioner"
        assert target.unlinked_mentions[0]["snippet"] == "snippet text"


class TestMaterializeSuggestions:
    def test_no_suggestions(self) -> None:
        zettel = _make_zettel(1)
        store = ZettelStore([zettel])
        materialize_suggestions(zettel, {}, store, ".md")
        assert zettel.suggested_links == []

    def test_single_suggestion(self) -> None:
        source = _make_zettel(1)
        target = _make_zettel(2, title="Suggested")
        store = ZettelStore([source, target])
        suggestions = {
            1: [{"target_id": 2, "reason": "similar topic", "confidence": 0.85}]
        }
        materialize_suggestions(source, suggestions, store, ".md")
        assert len(source.suggested_links) == 1
        assert source.suggested_links[0]["url"] == "2/"
        assert source.suggested_links[0]["title"] == "Suggested"
        assert source.suggested_links[0]["reason"] == "similar topic"
        assert source.suggested_links[0]["confidence"] == "85%"

    def test_missing_target_skipped(self) -> None:
        source = _make_zettel(1)
        store = ZettelStore([source])
        suggestions = {1: [{"target_id": 999, "reason": "r", "confidence": 0.5}]}
        materialize_suggestions(source, suggestions, store, ".md")
        assert source.suggested_links == []
