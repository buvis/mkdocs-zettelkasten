from pathlib import Path
from unittest.mock import MagicMock, patch

from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService

VALID_MD = "---\nid: 1\ndate: 2024-01-01\n---\n# Title\nBody\n"
PERMISSIVE_CONFIG = {"id_format": r"^\d+$"}


class TestZettelService:
    def test_configure_stores_config(self) -> None:
        svc = ZettelService()
        cfg = {"id_key": "myid"}
        svc.configure(cfg)
        assert svc.zettel_config == cfg

    def test_process_files(self, tmp_path: Path) -> None:
        fp = tmp_path / "note.md"
        fp.write_text(VALID_MD)

        f = MagicMock()
        f.src_path = "note.md"
        f.abs_src_path = str(fp)
        f.is_documentation_page.return_value = True

        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        config = MagicMock()
        config.__getitem__ = lambda self, key: {"docs_dir": str(tmp_path)}[key]

        svc = ZettelService()
        svc.configure(PERMISSIVE_CONFIG)
        with patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
            return_value=False,
        ):
            svc.process_files(files, config)

        assert len(svc.get_zettels()) == 1

    def test_add_zettel_to_page(self, tmp_path: Path) -> None:
        fp = tmp_path / "note.md"
        fp.write_text(VALID_MD)

        f = MagicMock()
        f.src_path = "note.md"
        f.abs_src_path = str(fp)
        f.is_documentation_page.return_value = True

        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        config = MagicMock()
        config.__getitem__ = lambda self, key: {"docs_dir": str(tmp_path)}[key]

        svc = ZettelService()
        svc.configure(PERMISSIVE_CONFIG)
        with patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
            return_value=False,
        ):
            svc.process_files(files, config)

        page = MagicMock()
        page.file.abs_src_path = str(fp)
        page.meta = {}

        result = svc.add_zettel_to_page(page)
        assert result.meta["is_zettel"] is True
        assert result.meta["zettel"].id == 1

    def test_get_zettel_by_id_existing(self, tmp_path: Path) -> None:
        fp = tmp_path / "note.md"
        fp.write_text(VALID_MD)

        f = MagicMock()
        f.src_path = "note.md"
        f.abs_src_path = str(fp)
        f.is_documentation_page.return_value = True

        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        config = MagicMock()
        config.__getitem__ = lambda self, key: {"docs_dir": str(tmp_path)}[key]

        svc = ZettelService()
        svc.configure(PERMISSIVE_CONFIG)
        with patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
            return_value=False,
        ):
            svc.process_files(files, config)

        result = svc.get_zettel_by_id(1)
        assert result is not None
        assert result.id == 1

    def test_get_zettel_by_id_nonexistent(self) -> None:
        svc = ZettelService()
        assert svc.get_zettel_by_id(999) is None

    def test_add_zettel_non_zettel_page(self) -> None:
        svc = ZettelService()
        page = MagicMock()
        page.file.abs_src_path = None
        page.meta = {}

        result = svc.add_zettel_to_page(page)
        assert result.meta["is_zettel"] is False
