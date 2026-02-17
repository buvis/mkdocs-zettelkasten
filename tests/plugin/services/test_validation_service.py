from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.services.validation_service import (
    ValidationService,
)


class TestValidationService:
    def _make_zettel(
        self, zettel_id: int, rel_path: str, links: list[str] | None = None
    ):
        z = MagicMock()
        z.id = zettel_id
        z.rel_path = rel_path
        z.links = links or []
        return z

    def _make_zettel_service(self, zettels, backlinks=None, invalid_files=None):
        svc = MagicMock()
        svc.get_zettels.return_value = zettels
        svc.store.get_by_partial_path = self._make_partial_path_lookup(zettels)
        svc.backlinks = backlinks or {}
        svc.invalid_files = invalid_files or []
        return svc

    def _make_partial_path_lookup(self, zettels):
        def lookup(partial, _file_suffix=".md"):
            for z in zettels:
                if partial in z.rel_path:
                    return z
            return None

        return lookup

    def test_no_issues_when_all_linked(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(1, "a.md", links=["b"])
        z2 = self._make_zettel(2, "b.md", links=["a"])

        svc = self._make_zettel_service(
            [z1, z2], backlinks={"a.md": [z2], "b.md": [z1]}
        )

        vs = ValidationService()
        vs.output_folder = tmp_path
        config = MagicMock()
        config.__getitem__ = lambda self, k: str(tmp_path) if k == "site_dir" else ""
        files = MagicMock()

        vs.validate(svc, files, config)

        assert vs.get_issues("a.md") == []
        assert vs.get_issues("b.md") == []

    def test_orphan_detected(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(1, "a.md", links=["b"])
        z2 = self._make_zettel(2, "b.md", links=[])

        svc = self._make_zettel_service([z1, z2], backlinks={"b.md": [z1]})

        vs = ValidationService()
        vs.output_folder = tmp_path
        config = MagicMock()
        config.__getitem__ = lambda self, k: str(tmp_path) if k == "site_dir" else ""
        files = MagicMock()

        vs.validate(svc, files, config)

        a_issues = vs.get_issues("a.md")
        assert len(a_issues) == 1
        assert a_issues[0].check == "orphan"
        assert vs.get_issues("b.md") == []

    def test_broken_link_detected(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(1, "a.md", links=["nonexistent"])

        svc = self._make_zettel_service([z1], backlinks={})

        vs = ValidationService()
        vs.output_folder = tmp_path
        config = MagicMock()
        config.__getitem__ = lambda self, k: str(tmp_path) if k == "site_dir" else ""
        files = MagicMock()

        vs.validate(svc, files, config)

        issues = vs.get_issues("a.md")
        broken = [i for i in issues if i.check == "broken_link"]
        assert len(broken) == 1
        assert "nonexistent" in broken[0].message

    def test_invalid_file_reported(self, tmp_path: Path) -> None:
        invalid_f = MagicMock()
        invalid_f.src_path = "bad.md"

        svc = self._make_zettel_service([], invalid_files=[invalid_f])

        vs = ValidationService()
        vs.output_folder = tmp_path
        config = MagicMock()
        config.__getitem__ = lambda self, k: str(tmp_path) if k == "site_dir" else ""
        files = MagicMock()

        vs.validate(svc, files, config)

        issues = vs.get_issues("bad.md")
        assert len(issues) == 1
        assert issues[0].check == "invalid_file"
        assert issues[0].severity == "error"

    def test_external_links_not_flagged(self, tmp_path: Path) -> None:
        z1 = self._make_zettel(
            1, "a.md", links=["https://example.com", "#anchor", "mailto:x@y.com"]
        )

        svc = self._make_zettel_service([z1], backlinks={})

        vs = ValidationService()
        vs.output_folder = tmp_path
        config = MagicMock()
        config.__getitem__ = lambda self, k: str(tmp_path) if k == "site_dir" else ""
        files = MagicMock()

        vs.validate(svc, files, config)

        broken = [i for i in vs.get_issues("a.md") if i.check == "broken_link"]
        assert len(broken) == 0

    def test_report_file_generated(self, tmp_path: Path) -> None:
        svc = self._make_zettel_service([])

        vs = ValidationService()
        vs.output_folder = tmp_path
        config = MagicMock()
        config.__getitem__ = lambda self, k: str(tmp_path) if k == "site_dir" else ""
        files = MagicMock()

        vs.validate(svc, files, config)

        report = tmp_path / "validation.md"
        assert report.exists()
        content = report.read_text()
        assert "Validation Report" in content
