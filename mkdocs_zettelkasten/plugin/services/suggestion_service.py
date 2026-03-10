from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


class SuggestionService:
    """Computes link suggestions based on shared links and shared tags."""

    CONFIDENCE_THRESHOLD = 0.3
    MAX_SUGGESTIONS = 5

    def compute(
        self,
        store: ZettelStore,
        tags_metadata: list[dict[str, Any]],
        file_suffix: str = ".md",
        resolved_links: dict[int, set[int]] | None = None,
    ) -> dict[int, list[dict]]:
        """Return {zettel_id: [{target_id, reason, confidence}, ...]}."""
        if resolved_links is not None:
            # Filter out self-links since _build_link_sets excludes them
            link_sets = {
                zid: {tid for tid in targets if tid != zid}
                for zid, targets in resolved_links.items()
            }
        else:
            link_sets = self._build_link_sets(store, file_suffix)
        tag_sets = self._build_tag_sets(store, tags_metadata)
        linked_pairs = self._build_linked_pairs(link_sets)

        link_suggs = self._shared_link_suggestions(store, link_sets, linked_pairs)
        tag_suggs = self._shared_tag_suggestions(store, tag_sets, linked_pairs)

        return self._merge(link_suggs, tag_suggs)

    def _build_link_sets(self, store, file_suffix):
        """Map each zettel ID to set of target IDs it links to."""
        link_sets: dict[int, set[int]] = {}
        for z in store.zettels:
            targets = set()
            for link in z.links:
                target = store.get_by_partial_path(link, file_suffix)
                if target and target.id != z.id:
                    targets.add(target.id)
            link_sets[z.id] = targets
        return link_sets

    def _build_tag_sets(self, store, tags_metadata):
        """Map each zettel ID to its set of tags."""
        tags_by_path = {m["src_path"]: set(m.get("tags", [])) for m in tags_metadata}
        tag_sets: dict[int, set[str]] = {}
        for z in store.zettels:
            tag_sets[z.id] = tags_by_path.get(z.rel_path, set())
        return tag_sets

    def _build_linked_pairs(self, link_sets):
        """Set of (a, b) pairs where a links to b (directional)."""
        pairs: set[tuple[int, int]] = set()
        for src_id, targets in link_sets.items():
            for tgt_id in targets:
                pairs.add((src_id, tgt_id))
        return pairs

    def _already_linked(self, a_id, b_id, linked_pairs):
        return (a_id, b_id) in linked_pairs or (b_id, a_id) in linked_pairs

    def _shared_link_suggestions(self, store, link_sets, linked_pairs):
        """Jaccard similarity on outgoing link sets."""
        sets = {zid: frozenset(s) for zid, s in link_sets.items() if s}
        return self._jaccard_suggestions(store, sets, linked_pairs, "shared link")

    def _shared_tag_suggestions(self, store, tag_sets, linked_pairs):
        """Jaccard similarity on tag sets."""
        sets = {zid: frozenset(s) for zid, s in tag_sets.items() if s}
        return self._jaccard_suggestions(store, sets, linked_pairs, "shared tag")

    def _jaccard_suggestions(
        self,
        store,
        sets: dict[int, frozenset],
        linked_pairs: set,
        reason_label: str,
    ) -> dict[int, list[dict]]:
        """Compute Jaccard similarity over arbitrary sets and return suggestions."""
        suggestions: dict[int, list[dict]] = {}
        zettels = store.zettels
        for i, z in enumerate(zettels):
            z_set = sets.get(z.id)
            if not z_set:
                continue
            candidates = []
            for j, other in enumerate(zettels):
                if i >= j:
                    continue
                other_set = sets.get(other.id)
                if not other_set:
                    continue
                if self._already_linked(z.id, other.id, linked_pairs):
                    continue
                intersection = z_set & other_set
                if not intersection:
                    continue
                union = z_set | other_set
                jaccard = len(intersection) / len(union)
                if jaccard < self.CONFIDENCE_THRESHOLD:
                    continue
                n = len(intersection)
                reason = f"{n} {reason_label}{'s' if n != 1 else ''}"
                entry = {
                    "target_id": other.id,
                    "reason": reason,
                    "confidence": round(jaccard, 2),
                }
                candidates.append(entry)
                suggestions.setdefault(other.id, []).append(
                    {
                        "target_id": z.id,
                        "reason": reason,
                        "confidence": round(jaccard, 2),
                    }
                )
            suggestions.setdefault(z.id, []).extend(candidates)
        return suggestions

    def _merge(self, link_suggs, tag_suggs):
        """Merge both strategy results, dedup by target, keep highest confidence, sort, limit."""
        merged: dict[int, list[dict]] = {}
        for zid in link_suggs.keys() | tag_suggs.keys():
            all_suggs = link_suggs.get(zid, []) + tag_suggs.get(zid, [])
            # Dedup: keep highest confidence per target
            best: dict[int, dict] = {}
            for s in all_suggs:
                tid = s["target_id"]
                if tid not in best or s["confidence"] > best[tid]["confidence"]:
                    best[tid] = s
            # Sort by confidence desc, limit
            sorted_suggs = sorted(
                best.values(), key=lambda x: x["confidence"], reverse=True
            )
            merged[zid] = sorted_suggs[: self.MAX_SUGGESTIONS]
        return merged
