"""Tests for ZettelMeta, ZettelRelationships, and Zettel facade composition."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from mkdocs_zettelkasten.plugin.entities.zettel import (
    Zettel,
    ZettelMeta,
    ZettelRelationships,
)


@pytest.fixture
def sample_meta() -> ZettelMeta:
    return ZettelMeta(
        id=20240101120000,
        title="Test Note",
        path=Path("/tmp/test.md"),
        rel_path="test.md",
        body="Some body text",
        last_update_date="2024-01-01",
        meta={"id": 20240101120000, "title": "Test Note"},
        links=["other"],
        link_snippets={"other": "see <mark>other</mark>"},
        note_type="permanent",
        maturity="evergreen",
        role="moc",
    )


class TestZettelMeta:
    def test_fields_accessible(self, sample_meta: ZettelMeta) -> None:
        assert sample_meta.id == 20240101120000
        assert sample_meta.title == "Test Note"
        assert sample_meta.rel_path == "test.md"
        assert sample_meta.note_type == "permanent"
        assert sample_meta.maturity == "evergreen"

    def test_frozen_prevents_assignment(self, sample_meta: ZettelMeta) -> None:
        with pytest.raises(FrozenInstanceError):
            sample_meta.id = 99  # type: ignore[misc]

    def test_frozen_prevents_title_assignment(self, sample_meta: ZettelMeta) -> None:
        with pytest.raises(FrozenInstanceError):
            sample_meta.title = "Changed"  # type: ignore[misc]

    def test_is_moc_true(self, sample_meta: ZettelMeta) -> None:
        assert sample_meta.is_moc is True

    def test_is_moc_false(self) -> None:
        meta = ZettelMeta(
            id=1,
            title="t",
            path=Path("/tmp/t.md"),
            rel_path="t.md",
            body="",
            last_update_date="",
            meta={},
            links=[],
            link_snippets={},
            role=None,
        )
        assert meta.is_moc is False

    def test_optional_fields_default_none(self) -> None:
        meta = ZettelMeta(
            id=1,
            title="t",
            path=Path("/tmp/t.md"),
            rel_path="t.md",
            body="",
            last_update_date="",
            meta={},
            links=[],
            link_snippets={},
        )
        assert meta.note_type is None
        assert meta.maturity is None
        assert meta.source is None
        assert meta.role is None
        assert meta.sequence_parent_id is None


class TestZettelRelationships:
    def test_defaults_empty(self) -> None:
        rels = ZettelRelationships()
        assert rels.backlinks == []
        assert rels.moc_parents == []
        assert rels.unlinked_mentions == []
        assert rels.suggested_links == []
        assert rels.sequence_parent is None
        assert rels.sequence_children == []
        assert rels.sequence_breadcrumb == []
        assert rels.sequence_tree == []

    def test_mutable_list_append(self) -> None:
        rels = ZettelRelationships()
        rels.backlinks.append({"url": "a/", "title": "A", "snippet": None})
        assert len(rels.backlinks) == 1

    def test_sequence_parent_assignable(self) -> None:
        rels = ZettelRelationships()
        rels.sequence_parent = {"url": "p/", "title": "Parent"}
        assert rels.sequence_parent is not None


class TestZettelFacade:
    def test_from_parts(self, sample_meta: ZettelMeta) -> None:
        zettel = Zettel.from_parts(sample_meta)
        assert zettel.id == sample_meta.id
        assert zettel.title == sample_meta.title
        assert zettel.backlinks == []
        assert zettel.is_moc is True

    def test_from_parts_with_rels(self, sample_meta: ZettelMeta) -> None:
        rels = ZettelRelationships(
            backlinks=[{"url": "a/", "title": "A", "snippet": None}],
        )
        zettel = Zettel.from_parts(sample_meta, rels)
        assert len(zettel.backlinks) == 1

    def test_meta_properties_read_only(self, sample_meta: ZettelMeta) -> None:
        zettel = Zettel.from_parts(sample_meta)
        with pytest.raises(AttributeError):
            zettel.id = 99  # type: ignore[misc]
        with pytest.raises(AttributeError):
            zettel.title = "Changed"  # type: ignore[misc]

    def test_relationship_properties_writable(self, sample_meta: ZettelMeta) -> None:
        zettel = Zettel.from_parts(sample_meta)

        # List mutation via append
        zettel.backlinks.append({"url": "b/", "title": "B", "snippet": None})
        assert len(zettel.backlinks) == 1

        # Direct assignment
        zettel.sequence_parent = {"url": "p/", "title": "P"}
        assert zettel.sequence_parent is not None

        # List reassignment
        zettel.sequence_children = [{"url": "c/", "title": "C"}]
        assert len(zettel.sequence_children) == 1

    def test_hash_and_equality(self, sample_meta: ZettelMeta) -> None:
        z1 = Zettel.from_parts(sample_meta)
        z2 = Zettel.from_parts(sample_meta)
        assert z1 == z2
        assert hash(z1) == hash(z2)

    def test_internal_meta_accessible(self, sample_meta: ZettelMeta) -> None:
        zettel = Zettel.from_parts(sample_meta)
        assert zettel._meta is sample_meta
        assert isinstance(zettel._rels, ZettelRelationships)
