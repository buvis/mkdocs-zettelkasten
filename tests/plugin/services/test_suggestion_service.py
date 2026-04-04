from mkdocs_zettelkasten.plugin.services.link_resolver import LinkResolver
from mkdocs_zettelkasten.plugin.services.suggestion_service import SuggestionService
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


def _resolve(store):
    return LinkResolver.resolve(store).resolved


class TestSharedLinkSuggestions:
    def setup_method(self):
        self.service = SuggestionService()

    def test_no_suggestions_for_isolated_note(self):
        z = _make_zettel_mock(1, title="A", rel_path="a.md")
        store = ZettelStore([z])
        result = self.service.compute(store, [], _resolve(store))
        assert result.get(1, []) == []

    def test_shared_link_produces_suggestion(self):
        """A links to C, B links to C -> suggest A<->B."""
        a = _make_zettel_mock(1, title="A", rel_path="a.md", links=["c.md"])
        b = _make_zettel_mock(2, title="B", rel_path="b.md", links=["c.md"])
        c = _make_zettel_mock(3, title="C", rel_path="c.md")
        store = ZettelStore([a, b, c])
        result = self.service.compute(store, [], _resolve(store))
        sugg_for_a = result.get(1, [])
        assert any(s["target_id"] == 2 for s in sugg_for_a)

    def test_shared_link_reason_format(self):
        a = _make_zettel_mock(1, title="A", rel_path="a.md", links=["c.md"])
        b = _make_zettel_mock(2, title="B", rel_path="b.md", links=["c.md"])
        c = _make_zettel_mock(3, title="C", rel_path="c.md")
        store = ZettelStore([a, b, c])
        result = self.service.compute(store, [], _resolve(store))
        sugg = next(s for s in result.get(1, []) if s["target_id"] == 2)
        assert "shared link" in sugg["reason"]
        assert sugg["confidence"] > 0

    def test_already_linked_excluded(self):
        """A links to B and C, B links to C -> no suggestion A<->B (already linked)."""
        a = _make_zettel_mock(1, title="A", rel_path="a.md", links=["b.md", "c.md"])
        b = _make_zettel_mock(2, title="B", rel_path="b.md", links=["c.md"])
        c = _make_zettel_mock(3, title="C", rel_path="c.md")
        store = ZettelStore([a, b, c])
        result = self.service.compute(store, [], _resolve(store))
        sugg_for_a = result.get(1, [])
        assert not any(s["target_id"] == 2 for s in sugg_for_a)

    def test_reverse_link_excluded(self):
        """B links to A and C, A links to C -> no suggestion A<->B (B already links to A)."""
        a = _make_zettel_mock(1, title="A", rel_path="a.md", links=["c.md"])
        b = _make_zettel_mock(2, title="B", rel_path="b.md", links=["a.md", "c.md"])
        c = _make_zettel_mock(3, title="C", rel_path="c.md")
        store = ZettelStore([a, b, c])
        result = self.service.compute(store, [], _resolve(store))
        sugg_for_a = result.get(1, [])
        assert not any(s["target_id"] == 2 for s in sugg_for_a)


class TestSharedTagSuggestions:
    def setup_method(self):
        self.service = SuggestionService()

    def test_shared_tags_produce_suggestion(self):
        a = _make_zettel_mock(1, title="A", rel_path="a.md")
        b = _make_zettel_mock(2, title="B", rel_path="b.md")
        store = ZettelStore([a, b])
        tags_meta = [
            {"src_path": "a.md", "tags": ["philosophy", "epistemology"]},
            {"src_path": "b.md", "tags": ["philosophy", "science"]},
        ]
        result = self.service.compute(store, tags_meta, _resolve(store))
        sugg_for_a = result.get(1, [])
        assert any(s["target_id"] == 2 for s in sugg_for_a)

    def test_shared_tag_reason_format(self):
        a = _make_zettel_mock(1, title="A", rel_path="a.md")
        b = _make_zettel_mock(2, title="B", rel_path="b.md")
        store = ZettelStore([a, b])
        tags_meta = [
            {"src_path": "a.md", "tags": ["philosophy", "epistemology"]},
            {"src_path": "b.md", "tags": ["philosophy", "science"]},
        ]
        result = self.service.compute(store, tags_meta, _resolve(store))
        sugg = next(s for s in result.get(1, []) if s["target_id"] == 2)
        assert "shared tag" in sugg["reason"]

    def test_no_shared_tags_no_suggestion(self):
        a = _make_zettel_mock(1, title="A", rel_path="a.md")
        b = _make_zettel_mock(2, title="B", rel_path="b.md")
        store = ZettelStore([a, b])
        tags_meta = [
            {"src_path": "a.md", "tags": ["philosophy"]},
            {"src_path": "b.md", "tags": ["science"]},
        ]
        result = self.service.compute(store, tags_meta, _resolve(store))
        sugg_for_a = result.get(1, [])
        assert not any(s["target_id"] == 2 for s in sugg_for_a)


class TestMergeAndLimits:
    def setup_method(self):
        self.service = SuggestionService()

    def test_below_threshold_excluded(self):
        """Two notes share 1 link target but also have 5 non-shared targets -> low Jaccard."""
        a = _make_zettel_mock(
            1,
            title="A",
            rel_path="a.md",
            links=["shared.md", "x1.md", "x2.md", "x3.md", "x4.md"],
        )
        b = _make_zettel_mock(
            2,
            title="B",
            rel_path="b.md",
            links=["shared.md", "y1.md", "y2.md", "y3.md", "y4.md"],
        )
        # Create all target zettels
        targets = [
            _make_zettel_mock(i, title=f"T{i}", rel_path=f"{name}.md")
            for i, name in enumerate(
                ["shared", "x1", "x2", "x3", "x4", "y1", "y2", "y3", "y4"], start=10
            )
        ]
        store = ZettelStore([a, b, *targets])
        result = self.service.compute(store, [], _resolve(store))
        sugg_for_a = result.get(1, [])
        # Jaccard = 1/9 ~ 0.11 < 0.3 threshold
        assert not any(s["target_id"] == 2 for s in sugg_for_a)

    def test_max_five_suggestions(self):
        """A note with many tag matches should only get top 5."""
        main = _make_zettel_mock(1, title="Main", rel_path="main.md")
        others = [
            _make_zettel_mock(i, title=f"Other{i}", rel_path=f"other{i}.md")
            for i in range(2, 9)
        ]
        store = ZettelStore([main, *others])
        tags_meta = [{"src_path": "main.md", "tags": ["a", "b"]}]
        tags_meta += [
            {"src_path": f"other{i}.md", "tags": ["a", "b"]} for i in range(2, 9)
        ]
        result = self.service.compute(store, tags_meta, _resolve(store))
        assert len(result.get(1, [])) <= 5

    def test_highest_confidence_kept_on_duplicate(self):
        """If both strategies suggest same pair, keep higher confidence."""
        a = _make_zettel_mock(1, title="A", rel_path="a.md", links=["c.md"])
        b = _make_zettel_mock(2, title="B", rel_path="b.md", links=["c.md"])
        c = _make_zettel_mock(3, title="C", rel_path="c.md")
        store = ZettelStore([a, b, c])
        tags_meta = [
            {"src_path": "a.md", "tags": ["x", "y"]},
            {"src_path": "b.md", "tags": ["x", "y"]},
        ]
        result = self.service.compute(store, tags_meta, _resolve(store))
        sugg_for_a = [s for s in result.get(1, []) if s["target_id"] == 2]
        assert len(sugg_for_a) == 1  # no duplicates

    def test_suggestions_sorted_by_confidence(self):
        main = _make_zettel_mock(1, title="Main", rel_path="main.md")
        high = _make_zettel_mock(2, title="High", rel_path="high.md")
        low = _make_zettel_mock(3, title="Low", rel_path="low.md")
        store = ZettelStore([main, high, low])
        tags_meta = [
            {"src_path": "main.md", "tags": ["a", "b", "c"]},
            {"src_path": "high.md", "tags": ["a", "b", "c"]},
            {"src_path": "low.md", "tags": ["a", "b"]},
        ]
        result = self.service.compute(store, tags_meta, _resolve(store))
        suggs = result.get(1, [])
        assert len(suggs) >= 2
        assert suggs[0]["confidence"] >= suggs[1]["confidence"]


class TestSuggestionServiceWithExplicitResolvedLinks:
    def setup_method(self):
        self.service = SuggestionService()

    def test_uses_resolved_links(self):
        a = _make_zettel_mock(1, title="A", rel_path="a.md")
        b = _make_zettel_mock(2, title="B", rel_path="b.md")
        c = _make_zettel_mock(3, title="C", rel_path="c.md")
        store = ZettelStore([a, b, c])

        resolved = {1: {3}, 2: {3}, 3: set()}
        result = self.service.compute(store, [], resolved)
        sugg_for_a = result.get(1, [])
        assert any(s["target_id"] == 2 for s in sugg_for_a)

    def test_filters_self_links(self):
        a = _make_zettel_mock(1, title="A", rel_path="a.md")
        b = _make_zettel_mock(2, title="B", rel_path="b.md")
        c = _make_zettel_mock(3, title="C", rel_path="c.md")
        store = ZettelStore([a, b, c])

        resolved = {1: {1, 3}, 2: {2, 3}, 3: set()}
        result = self.service.compute(store, [], resolved)
        sugg_for_a = result.get(1, [])
        assert any(s["target_id"] == 2 for s in sugg_for_a)

    def test_empty_resolved_no_link_suggestions(self):
        a = _make_zettel_mock(1, title="A", rel_path="a.md", links=["c.md"])
        b = _make_zettel_mock(2, title="B", rel_path="b.md", links=["c.md"])
        c = _make_zettel_mock(3, title="C", rel_path="c.md")
        store = ZettelStore([a, b, c])

        resolved = {1: set(), 2: set(), 3: set()}
        result = self.service.compute(store, [], resolved)
        sugg_for_a = result.get(1, [])
        assert not any(s["target_id"] == 2 for s in sugg_for_a)


class TestCustomThresholds:
    def test_custom_confidence_threshold(self):
        """Two notes share 1 link of 3 each -> Jaccard = 1/5 = 0.2.
        Default threshold (0.3) excludes this. Lowering to 0.1 includes it."""
        a = _make_zettel_mock(
            1, title="A", rel_path="a.md", links=["shared.md", "x.md", "y.md"]
        )
        b = _make_zettel_mock(
            2, title="B", rel_path="b.md", links=["shared.md", "p.md", "q.md"]
        )
        targets = [
            _make_zettel_mock(i, title=f"T{i}", rel_path=f"{n}.md")
            for i, n in enumerate(["shared", "x", "y", "p", "q"], start=10)
        ]
        store = ZettelStore([a, b, *targets])
        service = SuggestionService()
        result_default = service.compute(store, [], _resolve(store))
        assert not any(s["target_id"] == 2 for s in result_default.get(1, []))
        result_custom = service.compute(
            store, [], _resolve(store), confidence_threshold=0.1
        )
        assert any(s["target_id"] == 2 for s in result_custom.get(1, []))

    def test_custom_max_suggestions(self):
        """With max_suggestions=2, only top 2 suggestions returned."""
        main = _make_zettel_mock(1, title="Main", rel_path="main.md")
        others = [
            _make_zettel_mock(i, title=f"Other{i}", rel_path=f"other{i}.md")
            for i in range(2, 9)
        ]
        store = ZettelStore([main, *others])
        tags_meta = [{"src_path": "main.md", "tags": ["a", "b"]}]
        tags_meta += [
            {"src_path": f"other{i}.md", "tags": ["a", "b"]} for i in range(2, 9)
        ]
        service = SuggestionService()
        result = service.compute(store, tags_meta, _resolve(store), max_suggestions=2)
        assert len(result.get(1, [])) <= 2
