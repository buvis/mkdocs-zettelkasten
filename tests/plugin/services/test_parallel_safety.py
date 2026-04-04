"""Tests verifying on_page_markdown makes no writes to shared Zettel state.

Phase 4d of #128: confirm relationships are fully populated before
rendering and that page transformation is read-only.
"""

from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import MagicMock, patch

from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
from mkdocs_zettelkasten.plugin.entities.zettel import (
    Zettel,
    ZettelMeta,
    ZettelRelationships,
)
from mkdocs_zettelkasten.plugin.features.backlink_feature import BacklinkFeature
from mkdocs_zettelkasten.plugin.features.sequence_feature import SequenceFeature
from mkdocs_zettelkasten.plugin.features.unlinked_mention_feature import (
    UnlinkedMentionFeature,
)
from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext
from mkdocs_zettelkasten.plugin.services.page_transformer import PageTransformer
from mkdocs_zettelkasten.plugin.services.relationship_materializer import (
    RelationshipMaterializer,
)
from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService

ZETTEL_A = """---
id: 1
title: Note A
---
Links to [[2]]
"""

ZETTEL_B = """---
id: 2
title: Note B
---
Body of note B
"""


def _build_service(tmp_path: Path, file_map: dict[str, str]) -> ZettelService:
    cfg = ZettelkastenConfig(id_format=r"^\d+$")
    svc = ZettelService()
    svc.configure(cfg)
    for name, content in file_map.items():
        (tmp_path / name).write_text(content)
    from mkdocs.structure.files import File, Files

    files = Files(
        [
            File(name, str(tmp_path), str(tmp_path / "site"), use_directory_urls=True)
            for name in file_map
        ]
    )
    with patch(
        "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
        return_value=False,
    ):
        svc.process_files(files, MagicMock(spec=dict))
    return svc


def _build_ctx(svc: ZettelService) -> PipelineContext:
    ctx = PipelineContext(
        config=svc.zettel_config,
        store=svc.store,
        link_map=svc.link_map,
        invalid_files=svc.invalid_files,
        tags_metadata=[],
        tags_folder=Path(),
        site_dir="/tmp",
    )
    features = [BacklinkFeature(), UnlinkedMentionFeature(), SequenceFeature()]
    for f in features:
        f.compute(ctx)
    RelationshipMaterializer.materialize_all(ctx)
    return ctx


def _make_full_config(tmp_path: Path) -> dict:
    return {
        "site_url": "http://localhost/",
        "site_dir": str(tmp_path / "site"),
        "extra": {},
        "markdown_extensions": [],
        "mdx_configs": {},
    }


class TestParallelSafety:
    def test_transform_does_not_mutate_rels(self, tmp_path: Path) -> None:
        """on_page_markdown must not modify any Zettel._rels fields."""
        file_map = {"1.md": ZETTEL_A, "2.md": ZETTEL_B}
        svc = _build_service(tmp_path, file_map)
        ctx = _build_ctx(svc)
        features = [BacklinkFeature(), UnlinkedMentionFeature(), SequenceFeature()]
        from mkdocs.structure.files import File, Files

        files = Files(
            [
                File(
                    name,
                    str(tmp_path),
                    str(tmp_path / "site"),
                    use_directory_urls=True,
                )
                for name in file_map
            ]
        )
        config = _make_full_config(tmp_path)

        # Snapshot all rels before transform
        rels_before: dict[int, ZettelRelationships] = {}
        for z in svc.store.zettels:
            rels_before[z.id] = copy.deepcopy(z._rels)

        # Transform each page
        transformer = PageTransformer()
        for name, content in file_map.items():
            page = MagicMock()
            page.file.src_path = name
            page.file.abs_src_path = str(tmp_path / name)
            page.url = name.removesuffix(".md") + "/"
            page.meta = {}
            page.previous_page = None
            page.next_page = None
            transformer.transform(content, page, config, files, svc, features, ctx)

        # Verify rels unchanged
        for z in svc.store.zettels:
            before = rels_before[z.id]
            after = z._rels
            assert before.backlinks == after.backlinks, f"backlinks changed for {z.id}"
            assert before.moc_parents == after.moc_parents
            assert before.unlinked_mentions == after.unlinked_mentions
            assert before.suggested_links == after.suggested_links
            assert before.sequence_parent == after.sequence_parent
            assert before.sequence_children == after.sequence_children

    def test_relationships_populated_before_rendering(self, tmp_path: Path) -> None:
        """After materialize_all, relationships must be populated."""
        file_map = {"1.md": ZETTEL_A, "2.md": ZETTEL_B}
        svc = _build_service(tmp_path, file_map)
        _build_ctx(svc)  # triggers compute + materialize

        # Zettel 2 should have a backlink from zettel 1
        z2 = svc.store.get_by_id(2)
        assert z2 is not None
        assert len(z2.backlinks) > 0, (
            "backlinks should be populated after materialization"
        )

    def test_meta_fields_frozen_during_transform(self) -> None:
        """ZettelMeta fields cannot be modified at any point."""
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
        zettel = Zettel.from_parts(meta)

        with __import__("pytest").raises(FrozenInstanceError):
            meta.id = 99  # type: ignore[misc]

        with __import__("pytest").raises(AttributeError):
            zettel.id = 99  # type: ignore[misc]
