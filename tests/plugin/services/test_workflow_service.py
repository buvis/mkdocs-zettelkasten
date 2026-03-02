from datetime import date

from mkdocs_zettelkasten.plugin.services.workflow_service import WorkflowService
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock

TODAY = date(2026, 2, 27)


def _make_zettel(
    zettel_id,
    title,
    rel_path,
    note_type=None,
    maturity=None,
    links=None,
    sequence_parent_id=None,
):
    return _make_zettel_mock(
        zettel_id,
        title=title,
        rel_path=rel_path,
        note_type=note_type,
        maturity=maturity,
        links=links,
        sequence_parent_id=sequence_parent_id,
    )


class TestStats:
    def setup_method(self):
        self.service = WorkflowService()

    def test_counts_by_type(self):
        zettels = [
            _make_zettel(20260227000001, "A", "a.md", note_type="fleeting"),
            _make_zettel(20260227000002, "B", "b.md", note_type="permanent"),
            _make_zettel(20260227000003, "C", "c.md"),
        ]
        store = ZettelStore(zettels)
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["stats"]["by_type"] == {
            "fleeting": 1,
            "literature": 0,
            "permanent": 1,
            "unset": 1,
        }

    def test_counts_by_maturity(self):
        zettels = [
            _make_zettel(20260227000001, "A", "a.md", maturity="draft"),
            _make_zettel(20260227000002, "B", "b.md", maturity="evergreen"),
            _make_zettel(20260227000003, "C", "c.md"),
        ]
        store = ZettelStore(zettels)
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["stats"]["by_maturity"] == {
            "draft": 1,
            "developing": 0,
            "evergreen": 1,
            "unset": 1,
        }

    def test_total_and_connection_counts(self):
        z1 = _make_zettel(20260227000001, "A", "a.md", links=["b.md", "c.md"])
        z2 = _make_zettel(20260227000002, "B", "b.md")
        store = ZettelStore([z1, z2])
        backlinks = {"b.md": [z1]}
        mentions = {2: [(1, "snip")]}
        result = self.service.compute(store, backlinks, mentions, today=TODAY)
        assert result["stats"]["total"] == 2
        assert result["stats"]["total_links"] == 2
        assert result["stats"]["total_backlinks"] == 1
        assert result["stats"]["total_unlinked_mentions"] == 1


class TestInbox:
    def setup_method(self):
        self.service = WorkflowService()

    def test_includes_fleeting(self):
        z = _make_zettel(20260227000000, "Quick", "q.md", note_type="fleeting")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["inbox"]) == 1
        assert result["inbox"][0]["title"] == "Quick"

    def test_excludes_non_fleeting(self):
        z = _make_zettel(20260227000000, "Perm", "p.md", note_type="permanent")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["inbox"]) == 0

    def test_stale_flag(self):
        old = _make_zettel(20260201000000, "Old", "o.md", note_type="fleeting")
        new = _make_zettel(20260226000000, "New", "n.md", note_type="fleeting")
        store = ZettelStore([old, new])
        result = self.service.compute(store, {}, {}, today=TODAY)
        by_title = {i["title"]: i for i in result["inbox"]}
        assert by_title["Old"]["stale"] is True
        assert by_title["New"]["stale"] is False

    def test_sorted_newest_first(self):
        old = _make_zettel(20260201000000, "Old", "o.md", note_type="fleeting")
        new = _make_zettel(20260227000000, "New", "n.md", note_type="fleeting")
        store = ZettelStore([old, new])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["inbox"][0]["title"] == "New"


class TestNeedsConnection:
    def setup_method(self):
        self.service = WorkflowService()

    def test_permanent_no_links(self):
        z = _make_zettel(20260227000000, "Lonely", "l.md", note_type="permanent")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["needs_connection"]) == 1

    def test_permanent_one_link(self):
        z = _make_zettel(
            20260227000000, "One", "o.md", note_type="permanent", links=["x.md"]
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["needs_connection"]) == 1

    def test_excludes_well_connected(self):
        z = _make_zettel(
            20260227000000,
            "Connected",
            "c.md",
            note_type="permanent",
            links=["x.md", "y.md"],
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["needs_connection"]) == 0

    def test_excludes_non_permanent(self):
        z = _make_zettel(20260227000000, "Fleeting", "f.md", note_type="fleeting")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["needs_connection"]) == 0


class TestReviewQueue:
    def setup_method(self):
        self.service = WorkflowService()

    def test_stale_developing(self):
        z = _make_zettel(20250101000000, "Old dev", "o.md", maturity="developing")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["review_queue"]) == 1

    def test_excludes_recent_developing(self):
        z = _make_zettel(20260227000000, "Recent", "r.md", maturity="developing")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["review_queue"]) == 0

    def test_excludes_non_developing(self):
        z = _make_zettel(20250101000000, "Old draft", "o.md", maturity="draft")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["review_queue"]) == 0


class TestOrphans:
    def setup_method(self):
        self.service = WorkflowService()

    def test_includes_unlinked(self):
        z = _make_zettel(20260227000000, "Orphan", "o.md")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["orphans"]) == 1

    def test_excludes_backlinked(self):
        z1 = _make_zettel(20260227000001, "Target", "t.md")
        z2 = _make_zettel(20260227000002, "Source", "s.md", links=["t.md"])
        store = ZettelStore([z1, z2])
        backlinks = {"t.md": [z2]}
        result = self.service.compute(store, backlinks, {}, today=TODAY)
        orphan_ids = [o["id"] for o in result["orphans"]]
        assert 20260227000001 not in orphan_ids

    def test_excludes_sequence_children(self):
        z = _make_zettel(20260227000000, "Child", "c.md", sequence_parent_id=999)
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["orphans"]) == 0


class TestUnlinkedMentionHotspots:
    def setup_method(self):
        self.service = WorkflowService()

    def test_ranked_by_count(self):
        z1 = _make_zettel(20260227000001, "Hot", "h.md")
        z2 = _make_zettel(20260227000002, "Cold", "c.md")
        store = ZettelStore([z1, z2])
        mentions = {
            20260227000001: [(3, "s1"), (4, "s2"), (5, "s3")],
            20260227000002: [(6, "s4")],
        }
        result = self.service.compute(store, {}, mentions, today=TODAY)
        assert result["mention_hotspots"][0]["id"] == 20260227000001
        assert result["mention_hotspots"][0]["mention_count"] == 3

    def test_limited_to_max(self):
        zettels = [_make_zettel(i, f"Z{i}", f"z{i}.md") for i in range(1, 15)]
        store = ZettelStore(zettels)
        mentions = {i: [(100 + i, "s")] for i in range(1, 15)}
        result = self.service.compute(store, {}, mentions, today=TODAY)
        assert len(result["mention_hotspots"]) <= 10

    def test_includes_backlink_count(self):
        z1 = _make_zettel(20260227000001, "Target", "t.md")
        z2 = _make_zettel(20260227000002, "Src", "s.md", links=["t.md"])
        store = ZettelStore([z1, z2])
        backlinks = {"t.md": [z2]}
        mentions = {20260227000001: [(20260227000002, "s")]}
        result = self.service.compute(store, backlinks, mentions, today=TODAY)
        assert result["mention_hotspots"][0]["backlink_count"] == 1


class TestEmptyStore:
    def setup_method(self):
        self.service = WorkflowService()

    def test_empty_store_returns_empty_sections(self):
        store = ZettelStore([])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["stats"]["total"] == 0
        assert result["inbox"] == []
        assert result["needs_connection"] == []
        assert result["review_queue"] == []
        assert result["orphans"] == []
        assert result["mention_hotspots"] == []


class TestMalformedIds:
    def setup_method(self):
        self.service = WorkflowService()

    def test_short_id_skipped_in_inbox(self):
        z = _make_zettel(999, "Short", "s.md", note_type="fleeting")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["inbox"] == []

    def test_invalid_date_id_skipped_in_inbox(self):
        """Month=13 should be skipped."""
        z = _make_zettel(20261301000000, "Bad month", "b.md", note_type="fleeting")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["inbox"] == []

    def test_invalid_day_id_skipped_in_review(self):
        """Day=32 should be skipped."""
        z = _make_zettel(20250132000000, "Bad day", "b.md", maturity="developing")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["review_queue"] == []

    def test_non_numeric_prefix_skipped(self):
        """ID whose first 8 chars aren't all digits."""
        z = _make_zettel(0, "Zero", "z.md", note_type="fleeting")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["inbox"] == []
