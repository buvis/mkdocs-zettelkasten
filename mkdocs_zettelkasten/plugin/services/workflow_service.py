from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


class WorkflowService:
    """Computes workflow dashboard data from zettel store."""

    FLEETING_STALE_DAYS = 7
    REVIEW_STALE_DAYS = 30
    MAX_HOTSPOTS = 10

    def compute(
        self,
        store: ZettelStore,
        backlinks: dict[str, list],
        mentions: dict[int, list[tuple[int, str]]],
        file_suffix: str = ".md",
        today: date | None = None,
    ) -> dict[str, Any]:
        today = today or date.today()
        backlinked_ids = self._backlinked_ids(store, backlinks, file_suffix)
        backlink_counts = self._backlink_counts(store, backlinks, file_suffix)
        return {
            "stats": self._stats(store, backlinks, mentions),
            "inbox": self._inbox(store, today),
            "needs_connection": self._needs_connection(store),
            "review_queue": self._review_queue(store, today),
            "orphans": self._orphans(store, backlinked_ids),
            "mention_hotspots": self._mention_hotspots(
                store, mentions, backlink_counts
            ),
        }

    def _id_to_date(self, zettel_id: int) -> date:
        s = str(zettel_id)
        return date(int(s[:4]), int(s[4:6]), int(s[6:8]))

    def _backlinked_ids(self, store, backlinks, file_suffix):
        ids: set[int] = set()
        for key, linkers in backlinks.items():
            if linkers:
                target = store.get_by_partial_path(key, file_suffix)
                if target:
                    ids.add(target.id)
        return ids

    def _backlink_counts(self, store, backlinks, file_suffix):
        counts: dict[int, int] = {}
        for key, linkers in backlinks.items():
            target = store.get_by_partial_path(key, file_suffix)
            if target:
                counts[target.id] = counts.get(target.id, 0) + len(linkers)
        return counts

    def _stats(self, store, backlinks, mentions):
        zettels = store.zettels
        by_type = {"fleeting": 0, "literature": 0, "permanent": 0, "unset": 0}
        by_maturity = {"draft": 0, "developing": 0, "evergreen": 0, "unset": 0}
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
            "total_mentions": sum(len(v) for v in mentions.values()),
        }

    def _inbox(self, store, today):
        items = []
        for z in store.zettels:
            if z.note_type != "fleeting":
                continue
            created = self._id_to_date(z.id)
            age = (today - created).days
            items.append({
                "id": z.id,
                "title": z.title,
                "rel_path": z.rel_path,
                "age_days": age,
                "stale": age > self.FLEETING_STALE_DAYS,
            })
        return sorted(items, key=lambda x: x["id"], reverse=True)

    def _needs_connection(self, store):
        items = []
        for z in store.zettels:
            if z.note_type != "permanent":
                continue
            if len(z.links) > 1:
                continue
            items.append({
                "id": z.id,
                "title": z.title,
                "rel_path": z.rel_path,
                "link_count": len(z.links),
            })
        return sorted(items, key=lambda x: x["link_count"])

    def _review_queue(self, store, today):
        items = []
        for z in store.zettels:
            if z.maturity != "developing":
                continue
            created = self._id_to_date(z.id)
            age = (today - created).days
            if age <= self.REVIEW_STALE_DAYS:
                continue
            items.append({
                "id": z.id,
                "title": z.title,
                "rel_path": z.rel_path,
                "days_since_update": age,
            })
        return sorted(items, key=lambda x: x["days_since_update"], reverse=True)

    def _orphans(self, store, backlinked_ids):
        items = []
        for z in store.zettels:
            if z.id in backlinked_ids:
                continue
            if z.sequence_parent_id is not None:
                continue
            items.append({
                "id": z.id,
                "title": z.title,
                "rel_path": z.rel_path,
            })
        return sorted(items, key=lambda x: x["title"])

    def _mention_hotspots(self, store, mentions, backlink_counts):
        items = []
        for zid, mention_list in mentions.items():
            if not mention_list:
                continue
            z = store.get_by_id(zid)
            if not z:
                continue
            items.append({
                "id": z.id,
                "title": z.title,
                "rel_path": z.rel_path,
                "mention_count": len(mention_list),
                "backlink_count": backlink_counts.get(z.id, 0),
            })
        items.sort(key=lambda x: x["mention_count"], reverse=True)
        return items[: self.MAX_HOTSPOTS]
