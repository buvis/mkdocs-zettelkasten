import datetime
from typing import Callable
from zoneinfo import ZoneInfo

import pytest
import tzlocal

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel, ZettelFormatError

local_tz = ZoneInfo(tzlocal.get_localzone_name())

LAST_UPDATE_CONTENT = """---
id: 2020-05-20
title: Test with last update in meta
last_update: 2022-12-31
---
# Test content"""

DATE_CONTENT = """---
id: 2020-05-20
title: Test with date in meta
date: 2022-11-30
---
# Test content"""

ID_CONTENT = """---
id: 2023-05-20
title: Basic test
---
# Test content"""


EMPTY_ID_CONTENT = """---
id:
title: Test with no ID
---
# Test content"""


def test_last_update_from_frontmatter(
    zettel_factory: Callable[[str, datetime.datetime], Zettel],
) -> None:
    zettel = zettel_factory(
        LAST_UPDATE_CONTENT,
        datetime.datetime(2022, 1, 1, tzinfo=local_tz),
    )
    assert zettel.last_update_date == "2022-12-31"


def test_last_update_from_date(
    zettel_factory: Callable[[str, datetime.datetime], Zettel],
) -> None:
    zettel = zettel_factory(
        DATE_CONTENT,
        datetime.datetime(2022, 1, 1, tzinfo=local_tz),
    )
    assert zettel.last_update_date == "2022-11-30"


def test_last_update_from_id(
    zettel_factory: Callable[[str, datetime.datetime], Zettel],
) -> None:
    zettel = zettel_factory(ID_CONTENT, datetime.datetime(2022, 1, 1, tzinfo=local_tz))
    assert zettel.last_update_date == "2023-05-20"


def test_last_update_fail_on_missing_id(
    zettel_factory: Callable[[str, datetime.datetime], Zettel],
) -> None:
    with pytest.raises(ZettelFormatError, match="Missing zettel ID"):
        zettel_factory(EMPTY_ID_CONTENT, datetime.datetime(2022, 1, 1, tzinfo=local_tz))


def test_override_by_modification_date(
    zettel_factory: Callable[[str, datetime.datetime], Zettel],
) -> None:
    zettel = zettel_factory(
        LAST_UPDATE_CONTENT,
        datetime.datetime(2024, 1, 1, tzinfo=local_tz),
    )
    assert (
        zettel.last_update_date == "2022-12-31"
    )  # CORRECT: last_update date always wins

    zettel = zettel_factory(
        DATE_CONTENT,
        datetime.datetime(2024, 1, 1, tzinfo=local_tz),
    )
    assert zettel.last_update_date == "2024-01-01"

    zettel = zettel_factory(ID_CONTENT, datetime.datetime(2024, 1, 1, tzinfo=local_tz))
    assert zettel.last_update_date == "2024-01-01"
