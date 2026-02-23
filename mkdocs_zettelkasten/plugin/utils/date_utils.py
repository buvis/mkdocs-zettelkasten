from __future__ import annotations

import logging
from datetime import datetime, tzinfo

import tzlocal

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def convert_string_to_date(
    string: str,
    tz: tzinfo | None = None,
) -> datetime | None:
    if tz is None:
        tz = tzlocal.get_localzone()
    string = str(string)
    try:
        date = datetime.strptime(string, "%Y-%m-%d %H:%M:%S").replace(tzinfo=tz)
    except ValueError:
        try:
            date = datetime.strptime(string, "%Y%m%d%H%M%S").replace(tzinfo=tz)
        except ValueError:
            try:
                date = datetime.fromisoformat(string)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=tz)
            except ValueError:
                date = None

    logger.debug("Converted %s to datetime: %s.", string, date)

    return date
