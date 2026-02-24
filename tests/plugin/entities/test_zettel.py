from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mkdocs_zettelkasten.plugin.entities.zettel import (
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

HR_WITH_LINKS = """---
id: 20240101120000
title: HR with links
date: 2024-01-01
---
Before the rule [[20240102120000]]
---
After the rule [[20240103120000]]
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
        assert z.last_update_date == "2024-01-01"

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
    def test_links_extracted_after_hr(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, HR_WITH_LINKS)
        assert "20240102120000" in z.links
        assert "20240103120000" in z.links


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


class TestParseFrontmatter:
    def test_splits_header_and_body(self) -> None:
        from mkdocs_zettelkasten.plugin.utils.frontmatter import parse_frontmatter

        header, body = parse_frontmatter("---\nid: 1\n---\nbody text\n")
        assert "id: 1" in header
        assert "body text" in body

    def test_no_frontmatter_returns_empty_header(self) -> None:
        from mkdocs_zettelkasten.plugin.utils.frontmatter import parse_frontmatter

        header, body = parse_frontmatter("just text\n")
        assert header == ""
        assert "just text" in body

    def test_unclosed_frontmatter_returns_empty_header(self) -> None:
        from mkdocs_zettelkasten.plugin.utils.frontmatter import parse_frontmatter

        header, _body = parse_frontmatter("---\nid: 1\n")
        assert header == ""


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
