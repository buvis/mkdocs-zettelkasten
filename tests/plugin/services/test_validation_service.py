from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mkdocs_zettelkasten.plugin.services.validation_service import (
    ValidationService,
)
from tests.plugin.conftest import _make_zettel_mock


class TestValidationService:
    def _make_zettel(
        self,
        zettel_id: int,
        rel_path: str,
        links: list[str] | None = None,
        note_type: str | None = "permanent",
    ):
        return _make_zettel_mock(
            zettel_id,
            rel_path=rel_path,
            links=links,
            note_type=note_type,
        )

    def _make_store(self, zettels):
        store = MagicMock()
        store.zettels = zettels
        store.get_by_id.side_effect = lambda zid: next(
            (z for z in zettels if z.id == zid), None
        )
        return store

    def test_no_issues_when_all_linked(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(1, "a.md", links=["b"])
        z2 = self._make_zettel(2, "b.md", links=["a"])
        store = self._make_store([z1, z2])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {1: [z2], 2: [z1]}, [], [])

        assert vs.get_issues("a.md") == []
        assert vs.get_issues("b.md") == []

    def test_orphan_detected(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(1, "a.md", links=["b"])
        z2 = self._make_zettel(2, "b.md", links=[])
        store = self._make_store([z1, z2])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {2: [z1]}, [], [])

        a_issues = vs.get_issues("a.md")
        assert len(a_issues) == 1
        assert a_issues[0].check == "orphan"
        assert vs.get_issues("b.md") == []

    def test_broken_link_detected(self, tmp_path: Path) -> None:
        store = self._make_store([])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {}, [], [("a.md", "nonexistent")])

        issues = vs.get_issues("a.md")
        broken = [i for i in issues if i.check == "broken_link"]
        assert len(broken) == 1
        assert "nonexistent" in broken[0].message

    def test_invalid_file_reported(self, tmp_path: Path) -> None:
        invalid_f = MagicMock()
        invalid_f.src_path = "bad.md"
        store = self._make_store([])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {}, [invalid_f], [])

        issues = vs.get_issues("bad.md")
        assert len(issues) == 1
        assert issues[0].check == "invalid_file"
        assert issues[0].severity == "error"

    def test_external_links_not_flagged(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(
            1, "a.md", links=["https://example.com", "#anchor", "mailto:x@y.com"]
        )
        store = self._make_store([z1])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {}, [], [])

        broken = [i for i in vs.get_issues("a.md") if i.check == "broken_link"]
        assert len(broken) == 0

    def test_stale_fleeting_detected(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(20200101120000, "a.md", note_type="fleeting")
        store = self._make_store([z1])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {"a.md": [z1]}, [], [])

        stale = [i for i in vs.get_issues("a.md") if i.check == "stale_fleeting"]
        assert len(stale) == 1
        assert stale[0].severity == "info"

    def test_recent_fleeting_not_flagged(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(20991231120000, "a.md", note_type="fleeting")
        store = self._make_store([z1])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {"a.md": [z1]}, [], [])

        stale = [i for i in vs.get_issues("a.md") if i.check == "stale_fleeting"]
        assert len(stale) == 0

    def test_permanent_note_not_flagged_as_stale(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(20200101120000, "a.md")
        store = self._make_store([z1])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {"a.md": [z1]}, [], [])

        stale = [i for i in vs.get_issues("a.md") if i.check == "stale_fleeting"]
        assert len(stale) == 0

    def test_missing_type_detected(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(1, "a.md", note_type=None)
        store = self._make_store([z1])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {"a.md": [z1]}, [], [])

        missing = [i for i in vs.get_issues("a.md") if i.check == "missing_type"]
        assert len(missing) == 1
        assert missing[0].severity == "info"

    def test_typed_note_not_flagged_as_missing(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(1, "a.md")
        store = self._make_store([z1])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {"a.md": [z1]}, [], [])

        missing = [i for i in vs.get_issues("a.md") if i.check == "missing_type"]
        assert len(missing) == 0

    def test_broken_sequence_detected(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(1, "a.md")
        z1.sequence_parent_id = 999
        store = self._make_store([z1])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {"a.md": [z1]}, [], [])

        broken = [i for i in vs.get_issues("a.md") if i.check == "broken_sequence"]
        assert len(broken) == 1
        assert broken[0].severity == "warning"
        assert "999" in broken[0].message

    def test_valid_sequence_not_flagged(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(1, "a.md")
        z1.sequence_parent_id = 2
        z2 = self._make_zettel(2, "b.md")
        store = self._make_store([z1, z2])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {"a.md": [z1], "b.md": [z2]}, [], [])

        broken = [i for i in vs.get_issues("a.md") if i.check == "broken_sequence"]
        assert len(broken) == 0

    def test_empty_store_produces_zero_issues(self, tmp_path: Path) -> None:
        store = self._make_store([])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {}, [], [])

        assert vs.total_actionable_issues() == 0

    def test_generate_report_raises_on_missing_output_folder(self) -> None:
        store = self._make_store([])

        vs = ValidationService()
        vs.output_folder = Path("/nonexistent/path")
        vs.validate(store, {}, [], [])

        with pytest.raises(FileNotFoundError):
            vs.generate_report()

    def test_broken_link_from_precomputed_list(self, tmp_path: Path) -> None:
        store = self._make_store([])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {}, [], broken_links=[("a.md", "missing")])

        broken = [i for i in vs.get_issues("a.md") if i.check == "broken_link"]
        assert len(broken) == 1
        assert "missing" in broken[0].message

    def test_precomputed_broken_links_skips_store_lookup(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(1, "a.md", links=["nonexistent"])
        store = self._make_store([z1])

        vs = ValidationService()
        vs.output_folder = tmp_path
        # Pass empty broken_links — should produce no broken link issues
        # even though z1 has a nonexistent link (proves store lookup is skipped)
        vs.validate(store, {}, [], broken_links=[])

        broken = [i for i in vs.get_issues("a.md") if i.check == "broken_link"]
        assert len(broken) == 0

    def test_report_file_generated(self, tmp_path: Path) -> None:
        store = self._make_store([])

        vs = ValidationService()
        vs.output_folder = tmp_path
        vs.validate(store, {}, [], [])
        vs.generate_report()

        report = tmp_path / "validation.md"
        assert report.exists()
        content = report.read_text()
        assert "Validation Report" in content
