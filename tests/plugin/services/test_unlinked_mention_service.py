from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.services.unlinked_mention_service import (
    UnlinkedMentionService,
)
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


def _make_store(zettels):
    store = MagicMock()
    store.zettels = zettels
    return store


class TestUnlinkedMentionDetection:
    def test_finds_title_mention(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body of target.")
        source = _make_zettel_mock(
            2, title="Knowledge", body="The study of epistemology is ancient."
        )
        store = _make_store([target, source])

        service = UnlinkedMentionService()
        mentions = service.find_unlinked_mentions(store)

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

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 in mentions

    def test_skips_self_mention(self) -> None:
        z = _make_zettel_mock(
            1, title="Epistemology", body="This note about epistemology."
        )
        store = _make_store([z])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_skips_already_linked(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="Epistemology is discussed.", links=["1"]
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
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

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
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

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_skips_mention_inside_inline_code(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="The variable `epistemology` is set."
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_skips_mention_inside_fenced_code(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="```\nepistemology\n```\nSome other text."
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_finds_id_mention(self) -> None:
        target = _make_zettel_mock(20240101120000, title="My Note", body="Body.")
        source = _make_zettel_mock(
            20240102120000,
            title="Other",
            body="Refer to 20240101120000 for details.",
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 20240101120000 in mentions

    def test_skips_short_title(self) -> None:
        target = _make_zettel_mock(1, title="AI", body="Body.")
        source = _make_zettel_mock(2, title="Other", body="AI is discussed here.")
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_snippet_has_mark_tag(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="The study of epistemology is ancient."
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        _, snippet = mentions[1][0]
        assert "<mark>" in snippet

    def test_snippet_escapes_html_special_chars(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="If x < y & z > w then epistemology matters."
        )
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
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

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert len(mentions[1]) == 2

    def test_no_mentions_returns_empty(self) -> None:
        z1 = _make_zettel_mock(1, title="Alpha", body="Body one.")
        z2 = _make_zettel_mock(2, title="Beta", body="Body two.")
        store = _make_store([z1, z2])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 not in mentions
        assert 2 not in mentions

    def test_exactly_three_char_title_matches(self) -> None:
        target = _make_zettel_mock(1, title="API", body="Body.")
        source = _make_zettel_mock(2, title="Other", body="The API is fast.")
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 in mentions

    def test_word_boundary_matching(self) -> None:
        """'Install' should not match inside 'Installation'."""
        target = _make_zettel_mock(1, title="Install", body="Body.")
        source = _make_zettel_mock(2, title="Other", body="Installation is easy.")
        store = _make_store([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_skips_already_linked_by_wiki_path(self) -> None:
        target = _make_zettel_mock(
            1, title="Epistemology", rel_path="folder/note.md",
            path=Path("/docs/folder/note.md"), body="Body.",
        )
        source = _make_zettel_mock(
            2, title="Other", body="Epistemology is discussed.",
            links=["folder/note"],
        )
        store = ZettelStore([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_skips_already_linked_by_path_with_suffix(self) -> None:
        target = _make_zettel_mock(
            1, title="Epistemology", rel_path="folder/note.md",
            path=Path("/docs/folder/note.md"), body="Body.",
        )
        source = _make_zettel_mock(
            2, title="Other", body="Epistemology is discussed.",
            links=["folder/note.md"],
        )
        store = ZettelStore([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_path_link_to_different_target_still_reports_mention(self) -> None:
        target = _make_zettel_mock(
            1, title="Epistemology", rel_path="folder/note.md",
            path=Path("/docs/folder/note.md"), body="Body.",
        )
        source = _make_zettel_mock(
            2, title="Other", body="Epistemology is discussed.",
            rel_path="other.md", path=Path("/docs/other.md"),
            links=["folder/different"],
        )
        store = ZettelStore([target, source])

        mentions = UnlinkedMentionService().find_unlinked_mentions(store)
        assert 1 in mentions


class TestUnlinkedMentionWithResolvedLinks:
    def test_suppresses_when_resolved_links_contains_target(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="Epistemology is discussed."
        )
        store = _make_store([target, source])

        resolved = {2: {1}, 1: set()}
        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, resolved_links=resolved
        )
        assert 1 not in mentions

    def test_detects_when_resolved_links_missing_target(self) -> None:
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="Epistemology is discussed."
        )
        store = _make_store([target, source])

        resolved = {2: set(), 1: set()}
        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, resolved_links=resolved
        )
        assert 1 in mentions

    def test_resolved_links_skips_store_lookup(self) -> None:
        """Even with links=['1'], if resolved_links says no link, detect mention."""
        target = _make_zettel_mock(1, title="Epistemology", body="Body.")
        source = _make_zettel_mock(
            2, title="Other", body="Epistemology is discussed.", links=["1"]
        )
        store = _make_store([target, source])

        # resolved_links says source doesn't link to target
        resolved = {2: set(), 1: set()}
        mentions = UnlinkedMentionService().find_unlinked_mentions(
            store, resolved_links=resolved
        )
        # resolved_links takes precedence over _already_links_to
        assert 1 in mentions
