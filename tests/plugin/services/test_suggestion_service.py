from pathlib import PurePosixPath
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.services.suggestion_service import SuggestionService
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


def _make_zettel(zettel_id, title, rel_path, links=None):
    z = MagicMock()
    z.id = zettel_id
    z.title = title
    z.path = PurePosixPath(rel_path)
    z.rel_path = rel_path
    z.links = links or []
    z.__hash__ = lambda self: hash(zettel_id)
    z.__eq__ = lambda self, other: getattr(other, "id", None) == zettel_id
    return z


def _make_store(zettels):
    store = ZettelStore(zettels)
    return store


class TestSharedLinkSuggestions:
    def setup_method(self):
        self.service = SuggestionService()

    def test_no_suggestions_for_isolated_note(self):
        z = _make_zettel(1, "A", "a.md")
        store = _make_store([z])
        result = self.service.compute(store, [])
        assert result.get(1, []) == []

    def test_shared_link_produces_suggestion(self):
        """A links to C, B links to C -> suggest A<->B."""
        a = _make_zettel(1, "A", "a.md", ["c.md"])
        b = _make_zettel(2, "B", "b.md", ["c.md"])
        c = _make_zettel(3, "C", "c.md")
        store = _make_store([a, b, c])
        result = self.service.compute(store, [])
        sugg_for_a = result.get(1, [])
        assert any(s["target_id"] == 2 for s in sugg_for_a)

    def test_shared_link_reason_format(self):
        a = _make_zettel(1, "A", "a.md", ["c.md"])
        b = _make_zettel(2, "B", "b.md", ["c.md"])
        c = _make_zettel(3, "C", "c.md")
        store = _make_store([a, b, c])
        result = self.service.compute(store, [])
        sugg = [s for s in result.get(1, []) if s["target_id"] == 2][0]
        assert "shared link" in sugg["reason"]
        assert sugg["confidence"] > 0

    def test_already_linked_excluded(self):
        """A links to B and C, B links to C -> no suggestion A<->B (already linked)."""
        a = _make_zettel(1, "A", "a.md", ["b.md", "c.md"])
        b = _make_zettel(2, "B", "b.md", ["c.md"])
        c = _make_zettel(3, "C", "c.md")
        store = _make_store([a, b, c])
        result = self.service.compute(store, [])
        sugg_for_a = result.get(1, [])
        assert not any(s["target_id"] == 2 for s in sugg_for_a)

    def test_reverse_link_excluded(self):
        """B links to A and C, A links to C -> no suggestion A<->B (B already links to A)."""
        a = _make_zettel(1, "A", "a.md", ["c.md"])
        b = _make_zettel(2, "B", "b.md", ["a.md", "c.md"])
        c = _make_zettel(3, "C", "c.md")
        store = _make_store([a, b, c])
        result = self.service.compute(store, [])
        sugg_for_a = result.get(1, [])
        assert not any(s["target_id"] == 2 for s in sugg_for_a)


class TestSharedTagSuggestions:
    def setup_method(self):
        self.service = SuggestionService()

    def test_shared_tags_produce_suggestion(self):
        a = _make_zettel(1, "A", "a.md")
        b = _make_zettel(2, "B", "b.md")
        store = _make_store([a, b])
        tags_meta = [
            {"src_path": "a.md", "tags": ["philosophy", "epistemology"]},
            {"src_path": "b.md", "tags": ["philosophy", "science"]},
        ]
        result = self.service.compute(store, tags_meta)
        sugg_for_a = result.get(1, [])
        assert any(s["target_id"] == 2 for s in sugg_for_a)

    def test_shared_tag_reason_format(self):
        a = _make_zettel(1, "A", "a.md")
        b = _make_zettel(2, "B", "b.md")
        store = _make_store([a, b])
        tags_meta = [
            {"src_path": "a.md", "tags": ["philosophy", "epistemology"]},
            {"src_path": "b.md", "tags": ["philosophy", "science"]},
        ]
        result = self.service.compute(store, tags_meta)
        sugg = [s for s in result.get(1, []) if s["target_id"] == 2][0]
        assert "shared tag" in sugg["reason"]

    def test_no_shared_tags_no_suggestion(self):
        a = _make_zettel(1, "A", "a.md")
        b = _make_zettel(2, "B", "b.md")
        store = _make_store([a, b])
        tags_meta = [
            {"src_path": "a.md", "tags": ["philosophy"]},
            {"src_path": "b.md", "tags": ["science"]},
        ]
        result = self.service.compute(store, tags_meta)
        sugg_for_a = result.get(1, [])
        assert not any(s["target_id"] == 2 for s in sugg_for_a)


class TestMergeAndLimits:
    def setup_method(self):
        self.service = SuggestionService()

    def test_below_threshold_excluded(self):
        """Two notes share 1 link target but also have 5 non-shared targets -> low Jaccard."""
        a = _make_zettel(1, "A", "a.md", ["shared.md", "x1.md", "x2.md", "x3.md", "x4.md"])
        b = _make_zettel(2, "B", "b.md", ["shared.md", "y1.md", "y2.md", "y3.md", "y4.md"])
        # Create all target zettels
        targets = [_make_zettel(i, f"T{i}", f"{name}.md")
                   for i, name in enumerate(
                       ["shared", "x1", "x2", "x3", "x4", "y1", "y2", "y3", "y4"],
                       start=10)]
        store = _make_store([a, b] + targets)
        result = self.service.compute(store, [])
        sugg_for_a = result.get(1, [])
        # Jaccard = 1/9 ~ 0.11 < 0.3 threshold
        assert not any(s["target_id"] == 2 for s in sugg_for_a)

    def test_max_five_suggestions(self):
        """A note with many tag matches should only get top 5."""
        main = _make_zettel(1, "Main", "main.md")
        others = [_make_zettel(i, f"Other{i}", f"other{i}.md") for i in range(2, 9)]
        store = _make_store([main] + others)
        tags_meta = [{"src_path": "main.md", "tags": ["a", "b"]}]
        tags_meta += [{"src_path": f"other{i}.md", "tags": ["a", "b"]} for i in range(2, 9)]
        result = self.service.compute(store, tags_meta)
        assert len(result.get(1, [])) <= 5

    def test_highest_confidence_kept_on_duplicate(self):
        """If both strategies suggest same pair, keep higher confidence."""
        a = _make_zettel(1, "A", "a.md", ["c.md"])
        b = _make_zettel(2, "B", "b.md", ["c.md"])
        c = _make_zettel(3, "C", "c.md")
        store = _make_store([a, b, c])
        tags_meta = [
            {"src_path": "a.md", "tags": ["x", "y"]},
            {"src_path": "b.md", "tags": ["x", "y"]},
        ]
        result = self.service.compute(store, tags_meta)
        sugg_for_a = [s for s in result.get(1, []) if s["target_id"] == 2]
        assert len(sugg_for_a) == 1  # no duplicates

    def test_suggestions_sorted_by_confidence(self):
        main = _make_zettel(1, "Main", "main.md")
        high = _make_zettel(2, "High", "high.md")
        low = _make_zettel(3, "Low", "low.md")
        store = _make_store([main, high, low])
        tags_meta = [
            {"src_path": "main.md", "tags": ["a", "b", "c"]},
            {"src_path": "high.md", "tags": ["a", "b", "c"]},
            {"src_path": "low.md", "tags": ["a", "b"]},
        ]
        result = self.service.compute(store, tags_meta)
        suggs = result.get(1, [])
        assert len(suggs) >= 2
        assert suggs[0]["confidence"] >= suggs[1]["confidence"]
