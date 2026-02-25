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

ZETTEL_WITH_CONTEXT = """---
id: 20240101120000
title: My Zettel
date: 2024-01-01
---
# Heading

First paragraph has no links at all.

Second paragraph discusses the concept of knowledge and links to [[20240102120000|other note]] as an example of justified true belief.

Third paragraph is unrelated content.
"""

ZETTEL_MD_LINK_CONTEXT = """---
id: 20240101120000
title: My Zettel
date: 2024-01-01
---
# Heading

This paragraph references [another note](other.md) with context around it.
"""

ZETTEL_LINK_AT_START = """---
id: 20240101120000
title: My Zettel
date: 2024-01-01
---
[[20240102120000|Note]] is the first word in this paragraph with some more text.
"""

ZETTEL_LINK_AT_END = """---
id: 20240101120000
title: My Zettel
date: 2024-01-01
---
This paragraph ends with a reference to [[20240102120000|another note]].
"""

ZETTEL_LONG_PARAGRAPH = """---
id: 20240101120000
title: My Zettel
date: 2024-01-01
---
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Here we link to [[20240102120000|important note]] which is very relevant. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
"""

ZETTEL_DUPLICATE_LINKS = """---
id: 20240101120000
title: My Zettel
date: 2024-01-01
---
First mention of [[20240102120000|note]] in this paragraph.

Second mention of [[20240102120000|note]] in another paragraph.
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


class TestNoteTypeAndMaturity:
    def test_note_type_from_frontmatter(self, tmp_path: Path) -> None:
        content = "---\nid: 1\ntype: permanent\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content)
        assert z.note_type == "permanent"

    def test_maturity_from_frontmatter(self, tmp_path: Path) -> None:
        content = "---\nid: 1\nmaturity: developing\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content)
        assert z.maturity == "developing"

    def test_source_from_frontmatter(self, tmp_path: Path) -> None:
        content = '---\nid: 1\nsource: "Ahrens 2017"\ndate: 2024-01-01\n---\n# Title\n'
        z = _make_zettel(tmp_path, content)
        assert z.source == "Ahrens 2017"

    def test_missing_type_is_none(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert z.note_type is None

    def test_missing_maturity_is_none(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert z.maturity is None

    def test_missing_source_is_none(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert z.source is None

    def test_custom_type_key(self, tmp_path: Path) -> None:
        content = "---\nid: 1\nkind: literature\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content, zettel_config={"type_key": "kind"})
        assert z.note_type == "literature"

    def test_custom_maturity_key(self, tmp_path: Path) -> None:
        content = "---\nid: 1\nstatus: evergreen\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content, zettel_config={"maturity_key": "status"})
        assert z.maturity == "evergreen"

    def test_arbitrary_type_value(self, tmp_path: Path) -> None:
        content = "---\nid: 1\ntype: custom_type\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content)
        assert z.note_type == "custom_type"


class TestRole:
    def test_role_from_frontmatter(self, tmp_path: Path) -> None:
        content = "---\nid: 1\nrole: moc\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content)
        assert z.role == "moc"

    def test_missing_role_is_none(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert z.role is None

    def test_custom_role_key(self, tmp_path: Path) -> None:
        content = "---\nid: 1\nnote_role: index\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content, zettel_config={"role_key": "note_role"})
        assert z.role == "index"

    def test_is_moc_true_for_moc(self, tmp_path: Path) -> None:
        content = "---\nid: 1\nrole: moc\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content)
        assert z.is_moc is True

    def test_is_moc_true_for_index(self, tmp_path: Path) -> None:
        content = "---\nid: 1\nrole: index\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content)
        assert z.is_moc is True

    def test_is_moc_true_for_hub(self, tmp_path: Path) -> None:
        content = "---\nid: 1\nrole: hub\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content)
        assert z.is_moc is True

    def test_is_moc_true_for_structure(self, tmp_path: Path) -> None:
        content = "---\nid: 1\nrole: structure\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content)
        assert z.is_moc is True

    def test_is_moc_false_for_other(self, tmp_path: Path) -> None:
        content = "---\nid: 1\nrole: reference\ndate: 2024-01-01\n---\n# Title\n"
        z = _make_zettel(tmp_path, content)
        assert z.is_moc is False

    def test_is_moc_false_when_no_role(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert z.is_moc is False

    def test_moc_parents_initialized_empty(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert z.moc_parents == []


class TestLinkSnippets:
    def test_wiki_link_snippet_extracted(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, ZETTEL_WITH_CONTEXT)
        assert "20240102120000" in z.link_snippets
        snippet = z.link_snippets["20240102120000"]
        assert "justified true belief" in snippet

    def test_md_link_snippet_extracted(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, ZETTEL_MD_LINK_CONTEXT)
        assert "other.md" in z.link_snippets
        assert "references" in z.link_snippets["other.md"]

    def test_link_at_paragraph_start(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, ZETTEL_LINK_AT_START)
        assert "20240102120000" in z.link_snippets

    def test_link_at_paragraph_end(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, ZETTEL_LINK_AT_END)
        assert "20240102120000" in z.link_snippets
        assert "reference to" in z.link_snippets["20240102120000"]

    def test_long_paragraph_trimmed(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, ZETTEL_LONG_PARAGRAPH)
        snippet = z.link_snippets["20240102120000"]
        assert len(snippet) <= 250
        assert "..." in snippet

    def test_duplicate_link_keeps_first(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, ZETTEL_DUPLICATE_LINKS)
        snippet = z.link_snippets["20240102120000"]
        assert "First mention" in snippet

    def test_no_links_empty_snippets(self, tmp_path: Path) -> None:
        content = "---\nid: 1\ndate: 2024-01-01\n---\nNo links here.\n"
        z = _make_zettel(tmp_path, content)
        assert z.link_snippets == {}

    def test_snippet_highlights_link_text(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, ZETTEL_WITH_CONTEXT)
        snippet = z.link_snippets["20240102120000"]
        assert "<mark>" in snippet
        assert "other note</mark>" in snippet

    def test_snippet_does_not_include_link_syntax(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, ZETTEL_WITH_CONTEXT)
        snippet = z.link_snippets["20240102120000"]
        assert "[[" not in snippet
        assert "]]" not in snippet


class TestBody:
    def test_body_stored(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert "Some body text" in z.body

    def test_body_excludes_frontmatter(self, tmp_path: Path) -> None:
        z = _make_zettel(tmp_path, VALID_ZETTEL)
        assert "id:" not in z.body
