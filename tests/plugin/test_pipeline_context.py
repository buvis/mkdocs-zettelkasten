from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext


def _make_ctx(**results):
    return PipelineContext(
        config=MagicMock(),
        store=MagicMock(),
        link_map=MagicMock(),
        invalid_files=[],
        tags_metadata=[],
        tags_folder=Path("."),
        site_dir="/tmp",
        results=results,
    )


class TestPipelineContext:
    def test_backlinks_defaults_to_empty(self) -> None:
        assert _make_ctx().backlinks == {}

    def test_backlinks_from_results(self) -> None:
        assert _make_ctx(backlinks={1: ["a"]}).backlinks == {1: ["a"]}

    def test_unlinked_mentions_defaults_to_empty(self) -> None:
        assert _make_ctx().unlinked_mentions == {}

    def test_unlinked_mentions_from_results(self) -> None:
        ctx = _make_ctx(unlinked_mentions={1: [(2, "snip")]})
        assert ctx.unlinked_mentions == {1: [(2, "snip")]}

    def test_sequence_children_defaults_to_empty(self) -> None:
        assert _make_ctx().sequence_children == {}

    def test_sequence_children_from_results(self) -> None:
        assert _make_ctx(sequence_children={1: [2, 3]}).sequence_children == {1: [2, 3]}

    def test_suggestions_defaults_to_empty(self) -> None:
        assert _make_ctx().suggestions == {}

    def test_suggestions_from_results(self) -> None:
        ctx = _make_ctx(suggestions={1: [{"target_id": 2}]})
        assert ctx.suggestions == {1: [{"target_id": 2}]}

    def test_results_default_factory(self) -> None:
        ctx = PipelineContext(
            config=MagicMock(),
            store=MagicMock(),
            link_map=MagicMock(),
            invalid_files=[],
            tags_metadata=[],
            tags_folder=Path("."),
            site_dir="/tmp",
        )
        assert ctx.results == {}
