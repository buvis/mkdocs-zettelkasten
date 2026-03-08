from datetime import date, datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from mkdocs_zettelkasten.plugin.services.workflow_service import WorkflowService
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock

TODAY = date(2026, 2, 27)
_UTC = ZoneInfo("UTC")


class TestStats:
    def setup_method(self):
        self.service = WorkflowService()
        self.service._timezone = _UTC

    def test_counts_by_type(self):
        zettels = [
            _make_zettel_mock(
                20260227000001, title="A", rel_path="a.md", note_type="fleeting"
            ),
            _make_zettel_mock(
                20260227000002, title="B", rel_path="b.md", note_type="permanent"
            ),
            _make_zettel_mock(20260227000003, title="C", rel_path="c.md"),
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
            _make_zettel_mock(
                20260227000001, title="A", rel_path="a.md", maturity="draft"
            ),
            _make_zettel_mock(
                20260227000002, title="B", rel_path="b.md", maturity="evergreen"
            ),
            _make_zettel_mock(20260227000003, title="C", rel_path="c.md"),
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
        z1 = _make_zettel_mock(
            20260227000001, title="A", rel_path="a.md", links=["b.md", "c.md"]
        )
        z2 = _make_zettel_mock(20260227000002, title="B", rel_path="b.md")
        store = ZettelStore([z1, z2])
        backlinks = {20260227000002: [z1]}
        mentions = {2: [(1, "snip")]}
        result = self.service.compute(store, backlinks, mentions, today=TODAY)
        assert result["stats"]["total"] == 2
        assert result["stats"]["total_links"] == 2
        assert result["stats"]["total_backlinks"] == 1
        assert result["stats"]["total_unlinked_mentions"] == 1


class TestInbox:
    def setup_method(self):
        self.service = WorkflowService()
        self.service._timezone = _UTC

    def test_includes_fleeting(self):
        z = _make_zettel_mock(
            20260227000000, title="Quick", rel_path="q.md", note_type="fleeting"
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["inbox"]) == 1
        assert result["inbox"][0]["title"] == "Quick"

    def test_excludes_non_fleeting(self):
        z = _make_zettel_mock(
            20260227000000, title="Perm", rel_path="p.md", note_type="permanent"
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["inbox"]) == 0

    def test_stale_flag(self):
        old = _make_zettel_mock(
            20260201000000, title="Old", rel_path="o.md", note_type="fleeting"
        )
        new = _make_zettel_mock(
            20260226000000, title="New", rel_path="n.md", note_type="fleeting"
        )
        store = ZettelStore([old, new])
        result = self.service.compute(store, {}, {}, today=TODAY)
        by_title = {i["title"]: i for i in result["inbox"]}
        assert by_title["Old"]["stale"] is True
        assert by_title["New"]["stale"] is False

    def test_sorted_newest_first(self):
        old = _make_zettel_mock(
            20260201000000, title="Old", rel_path="o.md", note_type="fleeting"
        )
        new = _make_zettel_mock(
            20260227000000, title="New", rel_path="n.md", note_type="fleeting"
        )
        store = ZettelStore([old, new])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["inbox"][0]["title"] == "New"


class TestNeedsConnection:
    def setup_method(self):
        self.service = WorkflowService()
        self.service._timezone = _UTC

    def test_permanent_no_links(self):
        z = _make_zettel_mock(
            20260227000000, title="Lonely", rel_path="l.md", note_type="permanent"
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["needs_connection"]) == 1

    def test_permanent_one_link(self):
        z = _make_zettel_mock(
            20260227000000,
            title="One",
            rel_path="o.md",
            note_type="permanent",
            links=["x.md"],
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["needs_connection"]) == 1

    def test_excludes_well_connected(self):
        z = _make_zettel_mock(
            20260227000000,
            title="Connected",
            rel_path="c.md",
            note_type="permanent",
            links=["x.md", "y.md"],
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["needs_connection"]) == 0

    def test_excludes_non_permanent(self):
        z = _make_zettel_mock(
            20260227000000, title="Fleeting", rel_path="f.md", note_type="fleeting"
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["needs_connection"]) == 0


class TestReviewQueue:
    def setup_method(self):
        self.service = WorkflowService()
        self.service._timezone = _UTC

    def test_stale_developing(self):
        z = _make_zettel_mock(
            20250101000000, title="Old dev", rel_path="o.md", maturity="developing"
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["review_queue"]) == 1

    def test_excludes_recent_developing(self):
        z = _make_zettel_mock(
            20260227000000, title="Recent", rel_path="r.md", maturity="developing"
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["review_queue"]) == 0

    def test_excludes_non_developing(self):
        z = _make_zettel_mock(
            20250101000000, title="Old draft", rel_path="o.md", maturity="draft"
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["review_queue"]) == 0


class TestOrphans:
    def setup_method(self):
        self.service = WorkflowService()
        self.service._timezone = _UTC

    def test_includes_unlinked(self):
        z = _make_zettel_mock(20260227000000, title="Orphan", rel_path="o.md")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["orphans"]) == 1

    def test_excludes_backlinked(self):
        z1 = _make_zettel_mock(20260227000001, title="Target", rel_path="t.md")
        z2 = _make_zettel_mock(
            20260227000002, title="Source", rel_path="s.md", links=["t.md"]
        )
        store = ZettelStore([z1, z2])
        backlinks = {20260227000001: [z2]}
        result = self.service.compute(store, backlinks, {}, today=TODAY)
        orphan_ids = [o["id"] for o in result["orphans"]]
        assert 20260227000001 not in orphan_ids

    def test_excludes_sequence_children(self):
        z = _make_zettel_mock(
            20260227000000, title="Child", rel_path="c.md", sequence_parent_id=999
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert len(result["orphans"]) == 0


class TestUnlinkedMentionHotspots:
    def setup_method(self):
        self.service = WorkflowService()
        self.service._timezone = _UTC

    def test_ranked_by_count(self):
        z1 = _make_zettel_mock(20260227000001, title="Hot", rel_path="h.md")
        z2 = _make_zettel_mock(20260227000002, title="Cold", rel_path="c.md")
        store = ZettelStore([z1, z2])
        mentions = {
            20260227000001: [(3, "s1"), (4, "s2"), (5, "s3")],
            20260227000002: [(6, "s4")],
        }
        result = self.service.compute(store, {}, mentions, today=TODAY)
        assert result["mention_hotspots"][0]["id"] == 20260227000001
        assert result["mention_hotspots"][0]["mention_count"] == 3

    def test_limited_to_max(self):
        zettels = [
            _make_zettel_mock(i, title=f"Z{i}", rel_path=f"z{i}.md")
            for i in range(1, 15)
        ]
        store = ZettelStore(zettels)
        mentions = {i: [(100 + i, "s")] for i in range(1, 15)}
        result = self.service.compute(store, {}, mentions, today=TODAY)
        assert len(result["mention_hotspots"]) <= 10

    def test_includes_backlink_count(self):
        z1 = _make_zettel_mock(20260227000001, title="Target", rel_path="t.md")
        z2 = _make_zettel_mock(
            20260227000002, title="Src", rel_path="s.md", links=["t.md"]
        )
        store = ZettelStore([z1, z2])
        backlinks = {20260227000001: [z2]}
        mentions = {20260227000001: [(20260227000002, "s")]}
        result = self.service.compute(store, backlinks, mentions, today=TODAY)
        assert result["mention_hotspots"][0]["backlink_count"] == 1


class TestEmptyStore:
    def setup_method(self):
        self.service = WorkflowService()
        self.service._timezone = _UTC

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
        self.service._timezone = _UTC

    def test_short_id_skipped_in_inbox(self):
        z = _make_zettel_mock(999, title="Short", rel_path="s.md", note_type="fleeting")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["inbox"] == []

    def test_invalid_date_id_skipped_in_inbox(self):
        """Month=13 should be skipped."""
        z = _make_zettel_mock(
            20261301000000, title="Bad month", rel_path="b.md", note_type="fleeting"
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["inbox"] == []

    def test_invalid_day_id_skipped_in_review(self):
        """Day=32 should be skipped."""
        z = _make_zettel_mock(
            20250132000000,
            title="Bad day",
            rel_path="b.md",
            maturity="developing",
        )
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["review_queue"] == []

    def test_non_numeric_prefix_skipped(self):
        """ID whose first 8 chars aren't all digits."""
        z = _make_zettel_mock(0, title="Zero", rel_path="z.md", note_type="fleeting")
        store = ZettelStore([z])
        result = self.service.compute(store, {}, {}, today=TODAY)
        assert result["inbox"] == []


class TestComputeBeforeConfigure:
    def test_raises_without_configure(self):
        svc = WorkflowService()
        store = ZettelStore([])
        with pytest.raises(RuntimeError, match="configure\\(\\) must be called"):
            svc.compute(store, {}, {})


def _patched_now(utc_instant):
    """Return a datetime.now mock that converts utc_instant to the requested tz."""

    def _now(tz=None):
        return utc_instant.astimezone(tz)

    return _now


class TestInboxTimezoneBoundary:
    """Inbox staleness respects configured timezone at day boundaries."""

    def test_fleeting_stale_in_utc_but_not_in_local(self):
        # Fleeting created Feb 27. "Now" is Mar 7 03:00 UTC.
        # UTC: today=Mar 7, age=8 → stale (>7)
        # America/New_York (UTC-5): today=Mar 6, age=7 → NOT stale
        z = _make_zettel_mock(
            20260227120000, title="Edge", rel_path="e.md", note_type="fleeting"
        )
        store = ZettelStore([z])
        utc_instant = datetime(2026, 3, 7, 3, 0, 0, tzinfo=_UTC)

        svc_ny = WorkflowService()
        svc_ny._timezone = ZoneInfo("America/New_York")
        with patch(
            "mkdocs_zettelkasten.plugin.services.workflow_service.datetime"
        ) as mock_dt:
            mock_dt.now = _patched_now(utc_instant)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result_ny = svc_ny.compute(store, {}, {})
        assert result_ny["inbox"][0]["stale"] is False

        svc_utc = WorkflowService()
        svc_utc._timezone = _UTC
        with patch(
            "mkdocs_zettelkasten.plugin.services.workflow_service.datetime"
        ) as mock_dt:
            mock_dt.now = _patched_now(utc_instant)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result_utc = svc_utc.compute(store, {}, {})
        assert result_utc["inbox"][0]["stale"] is True


class TestReviewQueueTimezoneBoundary:
    """Review queue staleness respects configured timezone at day boundaries."""

    def test_developing_stale_in_utc_but_not_in_local(self):
        # Developing created Feb 5. "Now" is Mar 8 03:00 UTC.
        # UTC: today=Mar 8, age=31 → in queue (>30)
        # America/New_York (UTC-5): today=Mar 7, age=30 → NOT in queue
        z = _make_zettel_mock(
            20260205120000, title="Dev", rel_path="d.md", maturity="developing"
        )
        store = ZettelStore([z])
        utc_instant = datetime(2026, 3, 8, 3, 0, 0, tzinfo=_UTC)

        svc_ny = WorkflowService()
        svc_ny._timezone = ZoneInfo("America/New_York")
        with patch(
            "mkdocs_zettelkasten.plugin.services.workflow_service.datetime"
        ) as mock_dt:
            mock_dt.now = _patched_now(utc_instant)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result_ny = svc_ny.compute(store, {}, {})
        assert result_ny["review_queue"] == []

        svc_utc = WorkflowService()
        svc_utc._timezone = _UTC
        with patch(
            "mkdocs_zettelkasten.plugin.services.workflow_service.datetime"
        ) as mock_dt:
            mock_dt.now = _patched_now(utc_instant)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result_utc = svc_utc.compute(store, {}, {})
        assert len(result_utc["review_queue"]) == 1
