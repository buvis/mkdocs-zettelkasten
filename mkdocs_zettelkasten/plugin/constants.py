"""Shared constants for the zettelkasten plugin."""

from __future__ import annotations

# -- Staleness thresholds (days) -----------------------------------------------

FLEETING_STALE_DAYS = 7
REVIEW_STALE_DAYS = 30

# -- Note types ----------------------------------------------------------------

TYPE_FLEETING = "fleeting"
TYPE_LITERATURE = "literature"
TYPE_PERMANENT = "permanent"

# -- Maturity levels -----------------------------------------------------------

MATURITY_DRAFT = "draft"
MATURITY_DEVELOPING = "developing"
MATURITY_EVERGREEN = "evergreen"

# -- MOC (Map of Content) roles ------------------------------------------------
# A zettel is considered a MOC if its role matches one of these values.
# MOCs serve as structural navigation hubs that organize other zettels.

MOC_ROLES: frozenset[str] = frozenset({"moc", "index", "hub", "structure"})
