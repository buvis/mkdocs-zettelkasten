from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any

from mkdocs_zettelkasten.plugin.constants import (
    FLEETING_STALE_DAYS,
    MATURITY_DEVELOPING,
    MATURITY_DRAFT,
    MATURITY_EVERGREEN,
    REVIEW_STALE_DAYS,
    TYPE_FLEETING,
    TYPE_LITERATURE,
    TYPE_PERMANENT,
)
from mkdocs_zettelkasten.plugin.utils.date_utils import convert_string_to_date
from mkdocs_zettelkasten.plugin.utils.jinja_utils import create_jinja_environment

if TYPE_CHECKING:
    from pathlib import Path

    from mkdocs.structure.files import Files

    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class WorkflowService:
    """Computes workflow dashboard data from zettel store."""

    MAX_HOTSPOTS = 10

    def __init__(self) -> None:
        self.output_folder: Path | None = None
        self._site_dir: str | None = None

    def compute(
        self,
        store: ZettelStore,
        backlinks: dict[str, list],
        unlinked_mentions: dict[int, list[tuple[int, str]]],
        file_suffix: str = ".md",
        today: date | None = None,
    ) -> dict[str, Any]:
        today = today or datetime.now(tz=timezone.utc).date()
        backlinked_ids, backlink_counts = self._resolve_backlinks(
            store, backlinks, file_suffix
        )
        return {
            "stats": self._stats(store, backlinks, unlinked_mentions),
            "inbox": self._inbox(store, today),
            "needs_connection": self._needs_connection(store),
            "review_queue": self._review_queue(store, today),
            "orphans": self._orphans(store, backlinked_ids),
            "mention_hotspots": self._unlinked_mention_hotspots(
                store, unlinked_mentions, backlink_counts
            ),
        }

    def configure(self, output_folder: Path, site_dir: str) -> None:
        self.output_folder = output_folder
        self._site_dir = site_dir

    def generate(self, dashboard: dict[str, Any]) -> None:
        """Render workflow template to output folder."""
        if self.output_folder is None:
            msg = "configure() must be called before generate()"
            raise RuntimeError(msg)
        env = create_jinja_environment(None)
        template = env.get_template("workflow.md.j2")
        content = template.render(**dashboard)
        output_path = self.output_folder / "workflow.md"
        output_path.write_text(content, encoding="utf-8")
        logger.info("Generated workflow dashboard.")

    def add_to_build(self, files: Files) -> None:
        """Add generated workflow.md to MkDocs file collection."""
        if self.output_folder is None or self._site_dir is None:
            msg = "configure() must be called before add_to_build()"
            raise RuntimeError(msg)
        # deferred: avoid import-time mkdocs coupling
        from mkdocs.structure.files import File

        new_file = File(
            path="workflow.md",
            src_dir=str(self.output_folder),
            dest_dir=self._site_dir,
            use_directory_urls=False,
        )
        files.append(new_file)

    def _resolve_backlinks(self, store, backlinks, file_suffix):
        ids: set[int] = set()
        counts: dict[int, int] = {}
        for key, linkers in backlinks.items():
            target = store.get_by_partial_path(key, file_suffix)
            if not target:
                continue
            if linkers:
                ids.add(target.id)
            counts[target.id] = counts.get(target.id, 0) + len(linkers)
        return ids, counts

    def _stats(self, store, backlinks, unlinked_mentions):
        zettels = store.zettels
        by_type = {TYPE_FLEETING: 0, TYPE_LITERATURE: 0, TYPE_PERMANENT: 0, "unset": 0}
        by_maturity = {MATURITY_DRAFT: 0, MATURITY_DEVELOPING: 0, MATURITY_EVERGREEN: 0, "unset": 0}
        total_links = 0
        for z in zettels:
            t_key = z.note_type if z.note_type in by_type else "unset"
            by_type[t_key] += 1
            m_key = z.maturity if z.maturity in by_maturity else "unset"
            by_maturity[m_key] += 1
            total_links += len(z.links)
        return {
            "total": len(zettels),
            "by_type": by_type,
            "by_maturity": by_maturity,
            "total_links": total_links,
            "total_backlinks": sum(len(v) for v in backlinks.values()),
            "total_unlinked_mentions": sum(len(v) for v in unlinked_mentions.values()),
        }

    def _inbox(self, store, today):
        items = []
        for z in store.zettels:
            if z.note_type != TYPE_FLEETING:
                continue
            dt = convert_string_to_date(str(z.id))
            created = dt.date() if dt else None
            if not created:
                continue
            age = (today - created).days
            items.append(
                {
                    "id": z.id,
                    "title": z.title,
                    "rel_path": z.rel_path,
                    "age_days": age,
                    "stale": age > FLEETING_STALE_DAYS,
                }
            )
        return sorted(items, key=lambda x: x["id"], reverse=True)

    def _needs_connection(self, store):
        items = []
        for z in store.zettels:
            if z.note_type != TYPE_PERMANENT:
                continue
            if len(z.links) > 1:
                continue
            items.append(
                {
                    "id": z.id,
                    "title": z.title,
                    "rel_path": z.rel_path,
                    "link_count": len(z.links),
                }
            )
        return sorted(items, key=lambda x: x["link_count"])

    def _review_queue(self, store, today):
        items = []
        for z in store.zettels:
            if z.maturity != MATURITY_DEVELOPING:
                continue
            dt = convert_string_to_date(str(z.id))
            created = dt.date() if dt else None
            if not created:
                continue
            age = (today - created).days
            if age <= REVIEW_STALE_DAYS:
                continue
            items.append(
                {
                    "id": z.id,
                    "title": z.title,
                    "rel_path": z.rel_path,
                    "days_since_creation": age,
                }
            )
        return sorted(items, key=lambda x: x["days_since_creation"], reverse=True)

    def _orphans(self, store, backlinked_ids):
        items = []
        for z in store.zettels:
            if z.id in backlinked_ids:
                continue
            if z.sequence_parent_id is not None:
                continue
            items.append(
                {
                    "id": z.id,
                    "title": z.title,
                    "rel_path": z.rel_path,
                }
            )
        return sorted(items, key=lambda x: x["title"])

    def _unlinked_mention_hotspots(self, store, unlinked_mentions, backlink_counts):
        items = []
        for zid, mention_list in unlinked_mentions.items():
            if not mention_list:
                continue
            z = store.get_by_id(zid)
            if not z:
                continue
            items.append(
                {
                    "id": z.id,
                    "title": z.title,
                    "rel_path": z.rel_path,
                    "mention_count": len(mention_list),
                    "backlink_count": backlink_counts.get(z.id, 0),
                }
            )
        items.sort(key=lambda x: x["mention_count"], reverse=True)
        return items[: self.MAX_HOTSPOTS]
