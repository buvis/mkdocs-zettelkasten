from __future__ import annotations

import logging
from datetime import datetime

import tzlocal

local_tz = tzlocal.get_localzone()
logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


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

    logger.debug("Converted %s to datetime: %s.", string, date)

    return date
