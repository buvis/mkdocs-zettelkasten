from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.services.link_resolver import LinkResolver
from mkdocs_zettelkasten.plugin.services.unlinked_mention_service import (
    UnlinkedMentionService,
)
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


def _make_store(zettels):
    store = MagicMock()
    store.zettels = zettels
    return store


def _empty_resolved(zettels):
    """Build a resolved_links map with empty sets for all zettels."""
    return {z.id: set() for z in zettels}


class TestUnlinkedMentionDetection:
    def test_finds_title_mention(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body of target.")
        source = _make_zettel_mock(
            2, title="Knowledge", body="The study of epistemology is ancient."
        )
        store = _make_store([target, source])

        service = UnlinkedMentionService()
        mentions = service.find_unlinked_mentions(
            store, _empty_resolved([target, source])
        )

        assert 1 in mentions
        assert len(mentions[1]) == 1
        src_id, snippet = mentions[1][0]
        assert src_id == 2
        assert "epistemology" in snippet.lower()

    def test_case_insensitive(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="EPISTEMOLOGY is discussed here."
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source])
        )
        assert 1 in mentions

    def test_skips_self_mention(self) -> None:
        z = _make_zettel_mock(
            1, title="Epistemology", body="This note about epistemology."
        )
        store = _make_store([z])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([z])
        )
        assert 1 not in mentions

    def test_skips_already_linked(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="Epistemology is discussed.", links=["1"]
        )
        store = _make_store([target, source])

        # source links to target via resolved map
        resolved = {1: set(), 2: {1}}
        mentions = UnlinkedMentionService().find_unlinked_mentions(store, resolved)
        assert 1 not in mentions

    def test_skips_mention_inside_wiki_link(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2,
            title="Other",
            body="See [[1|Epistemology]] for details.",
            links=["1"],
        )
        store = _make_store([target, source])

        resolved = {1: set(), 2: {1}}
        mentions = UnlinkedMentionService().find_unlinked_mentions(store, resolved)
        assert 1 not in mentions

    def test_skips_mention_inside_md_link(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2,
            title="Other",
            body="See [Epistemology](1.md) for details.",
            links=["1"],
        )
        store = _make_store([target, source])

        resolved = {1: set(), 2: {1}}
        mentions = UnlinkedMentionService().find_unlinked_mentions(store, resolved)
        assert 1 not in mentions

    def test_skips_mention_inside_inline_code(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="The variable `epistemology` is set."
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source])
        )
        assert 1 not in mentions

    def test_skips_mention_inside_fenced_code(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="```\nepistemology\n```\nSome other text."
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source])
        )
        assert 1 not in mentions

    def test_finds_id_mention(self) -> None:
        target = _make_zettel_mock(20240101120000, title="My Note", body="Body.")
        source = _make_zettel_mock(
            20240102120000,
            title="Other",
            body="Refer to 20240101120000 for details.",
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source])
        )
        assert 20240101120000 in mentions

    def test_skips_short_title(self) -> None:
        target = _make_zettel_mock(1, title="AI", body="Body.")
        source = _make_zettel_mock(2, title="Other", body="AI is discussed here.")
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source])
        )
        assert 1 not in mentions

    def test_snippet_has_mark_tag(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="The study of epistemology is ancient."
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source])
        )
        _, snippet = mentions[1][0]
        assert "<mark>" in snippet

    def test_snippet_escapes_html_special_chars(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="If x < y & z > w then epistemology matters."
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source])
        )
        _, snippet = mentions[1][0]
        assert "&lt;" in snippet
        assert "&amp;" in snippet
        assert "&gt;" in snippet
        assert "<mark>" in snippet

    def test_multiple_sources_for_same_target(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source_a = _make_zettel_mock(2, title="A", body="Epistemology matters.")
        source_b = _make_zettel_mock(3, title="B", body="Epistemology again.")
        store = _make_store([target, source_a, source_b])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source_a, source_b])
        )
        assert len(mentions[1]) == 2

    def test_no_mentions_returns_empty(self) -> None:
        z1 = _make_zettel_mock(1, title="Alpha", body="Body one.")
        z2 = _make_zettel_mock(2, title="Beta", body="Body two.")
        store = _make_store([z1, z2])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([z1, z2])
        )
        assert 1 not in mentions
        assert 2 not in mentions

    def test_exactly_three_char_title_matches(self) -> None:
        target = _make_zettel_mock(1, title="API", body="Body.")
        source = _make_zettel_mock(2, title="Other", body="The API is fast.")
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source])
        )
        assert 1 in mentions

    def test_word_boundary_matching(self) -> None:
        """'Install' should not match inside 'Installation'."""
        target = _make_zettel_mock(1, title="Install", body="Body.")
        source = _make_zettel_mock(2, title="Other", body="Installation is easy.")
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source])
        )
        assert 1 not in mentions

    def test_skips_already_linked_by_wiki_path(self) -> None:
        target = _make_zettel_mock(
            1,
            title="Epistemology",
            rel_path="folder/note.md",
            path=Path("/docs/folder/note.md"),
            body="Body.",
        )
        source = _make_zettel_mock(
            2,
            title="Other",
            body="Epistemology is discussed.",
            links=["folder/note"],
        )
        store = ZettelStore([target, source])
        link_map = LinkResolver.resolve(store)

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, link_map.resolved
        )
        assert 1 not in mentions

    def test_skips_already_linked_by_path_with_suffix(self) -> None:
        target = _make_zettel_mock(
            1,
            title="Epistemology",
            rel_path="folder/note.md",
            path=Path("/docs/folder/note.md"),
            body="Body.",
        )
        source = _make_zettel_mock(
            2,
            title="Other",
            body="Epistemology is discussed.",
            links=["folder/note.md"],
        )
        store = ZettelStore([target, source])
        link_map = LinkResolver.resolve(store)

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, link_map.resolved
        )
        assert 1 not in mentions

    def test_path_link_to_different_target_still_reports_mention(self) -> None:
        target = _make_zettel_mock(
            1,
            title="Epistemology",
            rel_path="folder/note.md",
            path=Path("/docs/folder/note.md"),
            body="Body.",
        )
        source = _make_zettel_mock(
            2,
            title="Other",
            body="Epistemology is discussed.",
            rel_path="other.md",
            path=Path("/docs/other.md"),
            links=["folder/different"],
        )
        store = ZettelStore([target, source])
        link_map = LinkResolver.resolve(store)

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, link_map.resolved
        )
        assert 1 in mentions

    def test_custom_min_title_length(self) -> None:
        """With min_title_len=5, a 3-char title 'API' should be skipped."""
        target = _make_zettel_mock(1, title="API", body="Body.")
        source = _make_zettel_mock(2, title="Other", body="The API is fast.")
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source]), min_title_len=5
        )
        assert 1 not in mentions

    def test_custom_min_title_length_includes_short(self) -> None:
        """With min_title_len=2, a 2-char title 'AI' should be matched."""
        target = _make_zettel_mock(1, title="AI", body="Body.")
        source = _make_zettel_mock(2, title="Other", body="AI is discussed here.")
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, _empty_resolved([target, source]), min_title_len=2
        )
        assert 1 in mentions
