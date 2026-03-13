from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext


def _make_ctx(**kwargs):
    defaults = {
        "config": MagicMock(),
        "store": MagicMock(),
        "link_map": MagicMock(),
        "invalid_files": [],
        "tags_metadata": [],
        "tags_folder": Path(),
        "site_dir": "/tmp",
    }
    defaults.update(kwargs)
    return PipelineContext(**defaults)


class TestPipelineContext:
    def test_backlinks_defaults_to_empty(self) -> None:
        assert _make_ctx().backlinks == {}

    def test_backlinks_from_init(self) -> None:
        assert _make_ctx(backlinks={1: ["a"]}).backlinks == {1: ["a"]}

    def test_unlinked_mentions_defaults_to_empty(self) -> None:
        assert _make_ctx().unlinked_mentions == {}

    def test_unlinked_mentions_from_init(self) -> None:
        ctx = _make_ctx(unlinked_mentions={1: [(2, "snip")]})
        assert ctx.unlinked_mentions == {1: [(2, "snip")]}

    def test_sequence_children_defaults_to_empty(self) -> None:
        assert _make_ctx().sequence_children == {}

    def test_sequence_children_from_init(self) -> None:
        assert _make_ctx(sequence_children={1: [2, 3]}).sequence_children == {1: [2, 3]}
