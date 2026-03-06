from __future__ import annotations

import logging
from datetime import datetime, tzinfo

import tzlocal

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


_DATE_FORMATS = ["%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M%S"]



def _try_strptime_formats(string: str, tz: tzinfo) -> datetime | None:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(string, fmt).replace(tzinfo=tz)
        except ValueError:  # noqa: PERF203
            continue
    return None


def convert_string_to_date(
    string: str,
    tz: tzinfo | None = None,
) -> datetime | None:
    if tz is None:
        tz = tzlocal.get_localzone()
    string = str(string)

    date = _try_strptime_formats(string, tz)
    if date is None:
        try:
            date = datetime.fromisoformat(string)
            if date.tzinfo is None:
                date = date.replace(tzinfo=tz)
        except ValueError:
            date = None

    logger.debug("Converted %s to datetime: %s.", string, date)
    return date
