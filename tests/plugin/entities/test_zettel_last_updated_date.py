import datetime
from collections.abc import Callable
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
from mkdocs_zettelkasten.plugin.entities.zettel import Zettel, ZettelFormatError

UTC = ZoneInfo("UTC")

LAST_UPDATE_CONTENT = """---
id: 20200520120000
title: Test with last update in meta
last_update: 2022-12-31
---
# Test content"""

DATE_CONTENT = """---
id: 20200520120000
title: Test with date in meta
date: 2022-11-30
---
# Test content"""

ID_CONTENT = """---
id: 20230520120000
title: Basic test
---
# Test content"""


EMPTY_ID_CONTENT = """---
id:
title: Test with no ID
---
# Test content"""


def _ts(year: int, month: int = 1, day: int = 1) -> float:
    """Helper to create a UTC timestamp from a date."""
    return datetime.datetime(year, month, day, tzinfo=UTC).timestamp()


def test_last_update_from_frontmatter(
    zettel_factory: Callable[[str, float], Zettel],
) -> None:
    zettel = zettel_factory(LAST_UPDATE_CONTENT, _ts(2022))
    assert zettel.last_update_date == "2022-12-31"


def test_last_update_from_date(
    zettel_factory: Callable[[str, float], Zettel],
) -> None:
    zettel = zettel_factory(DATE_CONTENT, _ts(2022))
    assert zettel.last_update_date == "2022-11-30"


def test_last_update_from_id(
    zettel_factory: Callable[[str, float], Zettel],
) -> None:
    zettel = zettel_factory(ID_CONTENT, _ts(2022))
    assert zettel.last_update_date == "2023-05-20"


def test_last_update_fail_on_missing_id(
    zettel_factory: Callable[[str, float], Zettel],
) -> None:
    with pytest.raises(ZettelFormatError, match="Missing zettel ID"):
        zettel_factory(EMPTY_ID_CONTENT, _ts(2022))


def test_override_by_modification_date(
    zettel_factory: Callable[[str, float], Zettel],
) -> None:
    zettel = zettel_factory(LAST_UPDATE_CONTENT, _ts(2024))
    assert zettel.last_update_date == "2022-12-31"  # last_update always wins

    zettel = zettel_factory(DATE_CONTENT, _ts(2024))
    assert zettel.last_update_date == "2024-01-01"

    zettel = zettel_factory(ID_CONTENT, _ts(2024))
    assert zettel.last_update_date == "2024-01-01"


def test_custom_date_format(
    zettel_factory: Callable[..., Zettel],
) -> None:
    zettel = zettel_factory(
        LAST_UPDATE_CONTENT,
        _ts(2022),
        zettel_config=ZettelkastenConfig(date_format="%d/%m/%Y"),
    )
    assert zettel.last_update_date == "31/12/2022"


def test_uses_git_revision_date_when_tracked(tmp_path: Path) -> None:
    file_path = tmp_path / "test.md"
    file_path.write_text(ID_CONTENT)
    git_date = datetime.datetime(2025, 6, 15, 12, 0, 0, tzinfo=datetime.timezone.utc)

    with (
        patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
            return_value=True,
        ),
        patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.get_revision_date_for_file",
            return_value=git_date,
        ),
    ):
        zettel = Zettel(file_path, str(file_path.relative_to(tmp_path)))

    assert zettel.last_update_date == "2025-06-15"


def test_falls_back_to_mtime_when_git_returns_none(tmp_path: Path) -> None:
    file_path = tmp_path / "test.md"
    file_path.write_text(ID_CONTENT)

    with (
        patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
            return_value=True,
        ),
        patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.get_revision_date_for_file",
            return_value=None,
        ),
    ):
        zettel = Zettel(file_path, str(file_path.relative_to(tmp_path)))

    # falls back to real file mtime — verify it's a valid date string
    import re

    assert re.match(r"\d{4}-\d{2}-\d{2}", zettel.last_update_date)
