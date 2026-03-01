from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.services.mention_service import MentionService
from tests.plugin.conftest import _make_zettel_mock


def _make_zettel(zettel_id, title, body, links=None):
    return _make_zettel_mock(zettel_id, title=title, body=body, links=links)


def _make_store(zettels):
    store = MagicMock()
    store.zettels = zettels
    return store


class TestMentionDetection:
    def test_finds_title_mention(self) -> None:
        target = _make_zettel(1, "Epistemology", "Body of target.", [])
        source = _make_zettel(
            2, "Knowledge", "The study of epistemology is ancient.", []
        )
        store = _make_store([target, source])

        service = MentionService()
        mentions = service.find_unlinked_mentions(store)

        assert 1 in mentions
        assert len(mentions[1]) == 1
        src_id, snippet = mentions[1][0]
        assert src_id == 2
        assert "epistemology" in snippet.lower()

    def test_case_insensitive(self) -> None:
        target = _make_zettel(1, "Epistemology", "Body.", [])
        source = _make_zettel(2, "Other", "EPISTEMOLOGY is discussed here.", [])
        store = _make_store([target, source])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 1 in mentions

    def test_skips_self_mention(self) -> None:
        z = _make_zettel(1, "Epistemology", "This note about epistemology.", [])
        store = _make_store([z])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_skips_already_linked(self) -> None:
        target = _make_zettel(1, "Epistemology", "Body.", [])
        source = _make_zettel(2, "Other", "Epistemology is discussed.", ["1"])
        store = _make_store([target, source])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_skips_mention_inside_wiki_link(self) -> None:
        target = _make_zettel(1, "Epistemology", "Body.", [])
        source = _make_zettel(2, "Other", "See [[1|Epistemology]] for details.", ["1"])
        store = _make_store([target, source])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_skips_mention_inside_md_link(self) -> None:
        target = _make_zettel(1, "Epistemology", "Body.", [])
        source = _make_zettel(
            2, "Other", "See [Epistemology](1.md) for details.", ["1"]
        )
        store = _make_store([target, source])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_skips_mention_inside_inline_code(self) -> None:
        target = _make_zettel(1, "Epistemology", "Body.", [])
        source = _make_zettel(2, "Other", "The variable `epistemology` is set.", [])
        store = _make_store([target, source])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_skips_mention_inside_fenced_code(self) -> None:
        target = _make_zettel(1, "Epistemology", "Body.", [])
        source = _make_zettel(
            2, "Other", "```\nepistemology\n```\nSome other text.", []
        )
        store = _make_store([target, source])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_finds_id_mention(self) -> None:
        target = _make_zettel(20240101120000, "My Note", "Body.", [])
        source = _make_zettel(
            20240102120000, "Other", "Refer to 20240101120000 for details.", []
        )
        store = _make_store([target, source])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 20240101120000 in mentions

    def test_skips_short_title(self) -> None:
        target = _make_zettel(1, "AI", "Body.", [])
        source = _make_zettel(2, "Other", "AI is discussed here.", [])
        store = _make_store([target, source])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 1 not in mentions

    def test_snippet_has_mark_tag(self) -> None:
        target = _make_zettel(1, "Epistemology", "Body.", [])
        source = _make_zettel(2, "Other", "The study of epistemology is ancient.", [])
        store = _make_store([target, source])

        mentions = MentionService().find_unlinked_mentions(store)
        _, snippet = mentions[1][0]
        assert "<mark>" in snippet

    def test_multiple_sources_for_same_target(self) -> None:
        target = _make_zettel(1, "Epistemology", "Body.", [])
        source_a = _make_zettel(2, "A", "Epistemology matters.", [])
        source_b = _make_zettel(3, "B", "Epistemology again.", [])
        store = _make_store([target, source_a, source_b])

        mentions = MentionService().find_unlinked_mentions(store)
        assert len(mentions[1]) == 2

    def test_no_mentions_returns_empty(self) -> None:
        z1 = _make_zettel(1, "Alpha", "Body one.", [])
        z2 = _make_zettel(2, "Beta", "Body two.", [])
        store = _make_store([z1, z2])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 1 not in mentions
        assert 2 not in mentions

    def test_exactly_three_char_title_matches(self) -> None:
        target = _make_zettel(1, "API", "Body.", [])
        source = _make_zettel(2, "Other", "The API is fast.", [])
        store = _make_store([target, source])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 1 in mentions

    def test_word_boundary_matching(self) -> None:
        """'Install' should not match inside 'Installation'."""
        target = _make_zettel(1, "Install", "Body.", [])
        source = _make_zettel(2, "Other", "Installation is easy.", [])
        store = _make_store([target, source])

        mentions = MentionService().find_unlinked_mentions(store)
        assert 1 not in mentions
