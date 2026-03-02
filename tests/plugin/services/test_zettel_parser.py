from pathlib import Path
from unittest.mock import MagicMock, patch

from mkdocs.structure.files import File

from mkdocs_zettelkasten.plugin.services.zettel_parser import ZettelParser

VALID_CONTENT = "---\nid: 1\ndate: 2024-01-01\n---\n# Title\nBody\n"
INVALID_CONTENT = "---\ntitle: No ID\n---\n# Title\n"
PERMISSIVE_CONFIG = {"id_format": r"^\d+$"}


def _make_file(src_path: str, abs_src_path: str, is_doc: bool = True) -> MagicMock:
    f = MagicMock(spec=File)
    f.src_path = src_path
    f.abs_src_path = abs_src_path
    f.is_documentation_page.return_value = is_doc
    return f


class TestZettelParser:
    def test_parses_valid_zettel(self, tmp_path: Path) -> None:
        fp = tmp_path / "valid.md"
        fp.write_text(VALID_CONTENT)
        f = _make_file("valid.md", str(fp))

        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        with patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
            return_value=False,
        ):
            valid, invalid = ZettelParser.parse_files(
                files, zettel_config=PERMISSIVE_CONFIG
            )

        assert len(valid) == 1
        assert len(invalid) == 0
        assert valid[0].id == 1

    def test_invalid_zettel_goes_to_invalid(self, tmp_path: Path) -> None:
        fp = tmp_path / "bad.md"
        fp.write_text(INVALID_CONTENT)
        f = _make_file("bad.md", str(fp))

        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        with patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
            return_value=False,
        ):
            valid, invalid = ZettelParser.parse_files(
                files, zettel_config=PERMISSIVE_CONFIG
            )

        assert len(valid) == 0
        assert len(invalid) == 1

    def test_skips_non_documentation_pages(self) -> None:
        f = _make_file("image.png", "/docs/image.png", is_doc=False)
        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        valid, invalid = ZettelParser.parse_files(files)
        assert len(valid) == 0
        assert len(invalid) == 0

    def test_passes_zettel_config(self, tmp_path: Path) -> None:
        content = "---\nzettel_id: 99\ndate: 2024-01-01\n---\n# Title\n"
        fp = tmp_path / "custom.md"
        fp.write_text(content)
        f = _make_file("custom.md", str(fp))

        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        with patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
            return_value=False,
        ):
            valid, _ = ZettelParser.parse_files(
                files,
                zettel_config={"id_key": "zettel_id", "id_format": r"^\d+$"},
            )

        assert len(valid) == 1
        assert valid[0].id == 99
