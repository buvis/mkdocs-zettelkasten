from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mkdocs_zettelkasten.plugin.entities.zettel import (
    ReadState,
    Zettel,
    ZettelFormatError,
)

VALID_ZETTEL = """---
id: 20240101120000
title: My Zettel
tags:
  - test
date: 2024-01-01
---
# Heading

Some body text with [[20240102120000]] and [link](other.md).
"""

NO_TITLE_ZETTEL = """---
id: 20240101120000
date: 2024-01-01
---
# Alt Title From Heading

Body text.
"""

NO_TITLE_NO_HEADING = """---
id: 20240101120000
date: 2024-01-01
---
Body without heading.
"""

MISSING_ID_ZETTEL = """---
title: No ID Here
---
# Content
"""

UNCLOSED_HEADER = """---
id: 123
title: Unclosed
# Missing closing divider
"""

BOM_CONTENT = (
    "\ufeff---\nid: 20240101120000\ntitle: BOM Test\ndate: 2024-01-01\n---\nBody\n"
)

INVALID_YAML = '---\nkey: "unclosed string\n---\nBody\n'

EXTRA_DIVIDER = """---
id: 20240101120000
title: Extra divider
date: 2024-01-01
---
Body before third divider
---
Content after third divider
"""


def _make_zettel(tmp_path: Path, content: str, **kwargs) -> Zettel:
    fp = tmp_path / "test.md"
    fp.write_text(content)
    mock_stat = Mock()
    mock_stat.st_mtime = 1704067200.0  # 2024-01-01
    with (
        patch.object(Path, "stat", return_value=mock_stat),
        patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
            return_value=False,
        ),
    ):
        return Zettel(fp, str(fp.relative_to(tmp_path)), **kwargs)


class TestZettelInit:
    def test_valid_zettel(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert z.id == 20240101120000
        assert z.title == "My Zettel"
        assert z.last_update_date

    def test_missing_id_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ZettelFormatError, match="Missing zettel ID"):
            _make_zettel(tmp_path, MISSING_ID_ZETTEL)

    def test_unclosed_header_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ZettelFormatError, match="Unclosed YAML header"):
            _make_zettel(tmp_path, UNCLOSED_HEADER)

    def test_invalid_yaml_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ZettelFormatError):
            _make_zettel(tmp_path, INVALID_YAML)

    def test_bom_encoding(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, BOM_CONTENT)
        assert z.id == 20240101120000
        assert z.title == "BOM Test"


class TestTitleFallback:
    def test_title_from_frontmatter(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert z.title == "My Zettel"

    def test_title_from_heading(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, NO_TITLE_ZETTEL)
        assert z.title == "Alt Title From Heading"

    def test_title_from_filename(self, tmp_path: Path) -> None:
        fp = tmp_path / "20240101120000_my_note.md"
        fp.write_text(NO_TITLE_NO_HEADING)
        mock_stat = Mock()
        mock_stat.st_mtime = 1704067200.0
        with (
            patch.object(Path, "stat", return_value=mock_stat),
            patch(
                "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
                return_value=False,
            ),
        ):
            z = Zettel(fp, str(fp.relative_to(tmp_path)))
        assert z.title == "My note"


class TestExtractLinks:
    def test_extracts_wiki_links(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert "20240102120000" in z.links

    def test_extracts_md_links(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert "other.md" in z.links

    def test_no_links(self, tmp_path: Path) -> None:
        content = "---\nid: 1\ndate: 2024-01-01\n---\nNo links here.\n"
        z = _make_zettel(tmp_path, content)
        assert z.links == []


class TestExtraDivider:
    def test_third_divider_stops_body(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, EXTRA_DIVIDER)
        assert z.id == 20240101120000


class TestHashAndEquality:
    def test_hash(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert hash(z) == hash(20240101120000)

    def test_eq_same_id(self, tmp_path: Path) -> None:
        z1 = _make_zettel(tmp_path, VALID_ZETTEL)
        z2 = _make_zettel(tmp_path, VALID_ZETTEL)
        assert z1 == z2

    def test_neq_different_type(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert z != "not a zettel"


class TestReadState:
    def test_initial_state(self) -> None:
        rs = ReadState()
        assert not rs.is_reading_header
        assert not rs.is_reading_body
        assert rs.divider_count == 0

    def test_first_divider_starts_header(self) -> None:
        rs = ReadState()
        rs.handle_divider()
        assert rs.is_reading_header
        assert not rs.is_reading_body

    def test_second_divider_starts_body(self) -> None:
        rs = ReadState()
        rs.handle_divider()
        rs.handle_divider()
        assert not rs.is_reading_header
        assert rs.is_reading_body

    def test_third_divider_keeps_reading_body(self) -> None:
        rs = ReadState()
        rs.handle_divider()
        rs.handle_divider()
        rs.handle_divider()
        assert not rs.is_reading_header
        assert rs.is_reading_body


class TestConfigurableKeys:
    def test_custom_id_key(self, tmp_path: Path) -> None:
        content = "---\nzettel_id: 99\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content, zettel_config={"id_key": "zettel_id"})
        assert z.id == 99

    def test_custom_date_key(self, tmp_path: Path) -> None:
        content = "---\nid: 1\ncreated: 2025-06-15\n---\n# Title\n"
        z = _make_zettel(tmp_path, content, zettel_config={"date_key": "created"})
        assert z.last_update_date == "2025-06-15"

    def test_custom_last_update_key(self, tmp_path: Path) -> None:
        content = "---\nid: 1\nmodified: 2025-06-15\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(
            tmp_path, content, zettel_config={"last_update_key": "modified"}
        )
        assert z.last_update_date == "2025-06-15"
