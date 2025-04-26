from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import tzlocal

local_tz = ZoneInfo(tzlocal.get_localzone_name())


def convert_string_to_date(string: str) -> datetime | None:
    string = str(string)
    try:
        date = datetime.strptime(string, "%Y-%m-%d %H:%M:%S").replace(tzinfo=local_tz)
    except ValueError:
        try:
            date = datetime.strptime(string, "%Y%m%d%H%M%S").replace(tzinfo=local_tz)
        except ValueError:
            try:
                date = datetime.fromisoformat(string).replace(tzinfo=local_tz)
            except ValueError:
                date = None

    return date
