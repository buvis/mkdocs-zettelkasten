from __future__ import annotations

import datetime
import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar
from zoneinfo import ZoneInfo

from mkdocs_zettelkasten.plugin.constants import FLEETING_STALE_DAYS, TYPE_FLEETING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files

    from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService

from mkdocs_zettelkasten.plugin.utils.jinja_utils import create_jinja_environment

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


@dataclass
class ValidationIssue:
    path: str
    check: str  # invalid_file, orphan, broken_link
    severity: str  # error, warning, info
    message: str


class ValidationService:
    def __init__(self) -> None:
        self.issues: dict[str, list[ValidationIssue]] = defaultdict(list)
        self.output_folder: Path = Path(".build")
        self.output_filename: Path = Path("validation.md")
        self.file_suffix: str = ".md"
        self._timezone: ZoneInfo | None = None

    def configure(self, timezone: ZoneInfo, config: MkDocsConfig, file_suffix: str = ".md") -> None:
        self._timezone = timezone
        self.output_folder = Path(config.get("tags_folder", ".build"))
        if not self.output_folder.is_absolute():
            self.output_folder = Path(config["docs_dir"]).parent / self.output_folder
        self.file_suffix = file_suffix
        if not self.output_folder.exists():
            self.output_folder.mkdir(parents=True)

    def validate(
        self, zettel_service: ZettelService, files: Files, config: MkDocsConfig
    ) -> None:
        from .backlink_processor import BacklinkProcessor

        self.issues.clear()
        self._check_invalid_files(zettel_service)
        self._check_orphans(zettel_service)
        self._check_broken_links(zettel_service, BacklinkProcessor)
        self._check_stale_fleeting(zettel_service)
        self._check_missing_type(zettel_service)
        self._check_broken_sequences(zettel_service)
        self._generate_report()
        self._add_to_build(files, config)

        logger.info("Validation complete: %d issues found.", self.total_issues())

    def total_issues(self) -> int:
        return sum(len(v) for v in self.issues.values())

    def total_actionable_issues(self) -> int:
        return sum(
            1 for issues in self.issues.values() for i in issues if i.severity != "info"
        )

    def get_issues(self, rel_path: str) -> list[ValidationIssue]:
        return self.issues.get(rel_path, [])

    def _check_invalid_files(self, zettel_service: ZettelService) -> None:
        for f in zettel_service.invalid_files:
            self.issues[f.src_path].append(
                ValidationIssue(
                    path=f.src_path,
                    check="invalid_file",
                    severity="error",
                    message="Invalid zettel (missing ID or malformed YAML)",
                )
            )

    def _check_orphans(self, zettel_service: ZettelService) -> None:
        targeted_ids: set[int] = set(zettel_service.backlinks.keys())

        for zettel in zettel_service.get_zettels():
            if zettel.id not in targeted_ids:
                self.issues[zettel.rel_path].append(
                    ValidationIssue(
                        path=zettel.rel_path,
                        check="orphan",
                        severity="info",
                        message="No backlinks from other zettels",
                    )
                )

    def _check_broken_links(
        self, zettel_service: ZettelService, backlink_processor_cls: type
    ) -> None:
        for zettel in zettel_service.get_zettels():
            internal_links = [
                link
                for link in zettel.links
                if not link.startswith(("http://", "https://", "#", "mailto:"))
            ]
            for link in backlink_processor_cls.normalize_links(
                internal_links, self.file_suffix
            ):
                target = zettel_service.store.get_by_partial_path(
                    link, self.file_suffix
                )
                if not target:
                    logger.warning("Broken link in %s: %s", zettel.rel_path, link)
                    self.issues[zettel.rel_path].append(
                        ValidationIssue(
                            path=zettel.rel_path,
                            check="broken_link",
                            severity="warning",
                            message=f"Broken link: {link}",
                        )
                    )

    def _check_stale_fleeting(self, zettel_service: ZettelService) -> None:
        from mkdocs_zettelkasten.plugin.utils.date_utils import convert_string_to_date

        tz = self._timezone or ZoneInfo("UTC")
        cutoff = datetime.datetime.now(tz=tz) - datetime.timedelta(
            days=FLEETING_STALE_DAYS
        )
        for zettel in zettel_service.get_zettels():
            if zettel.note_type != TYPE_FLEETING:
                continue
            created = convert_string_to_date(str(zettel.id))
            if created and created < cutoff:
                self.issues[zettel.rel_path].append(
                    ValidationIssue(
                        path=zettel.rel_path,
                        check="stale_fleeting",
                        severity="info",
                        message=f"Fleeting note older than {FLEETING_STALE_DAYS} days",
                    )
                )

    def _check_missing_type(self, zettel_service: ZettelService) -> None:
        for zettel in zettel_service.get_zettels():
            if zettel.note_type is None:
                self.issues[zettel.rel_path].append(
                    ValidationIssue(
                        path=zettel.rel_path,
                        check="missing_type",
                        severity="info",
                        message="No note type metadata",
                    )
                )

    def _check_broken_sequences(self, zettel_service: ZettelService) -> None:
        for zettel in zettel_service.get_zettels():
            if zettel.sequence_parent_id is None:
                continue
            parent = zettel_service.get_zettel_by_id(zettel.sequence_parent_id)
            if not parent:
                self.issues[zettel.rel_path].append(
                    ValidationIssue(
                        path=zettel.rel_path,
                        check="broken_sequence",
                        severity="warning",
                        message=f"Sequence parent {zettel.sequence_parent_id} not found",
                    )
                )

    _CHECK_LABELS: ClassVar[dict[str, tuple[str, int]]] = {
        "invalid_file": ("Invalid files", 0),
        "broken_link": ("Broken links", 1),
        "orphan": ("Orphan zettels", 2),
        "stale_fleeting": ("Stale fleeting notes", 3),
        "missing_type": ("Missing note type", 4),
        "broken_sequence": ("Broken sequence references", 5),
    }

    def _generate_report(self) -> None:
        env = create_jinja_environment(None)
        template = env.get_template("validation.md.j2")

        all_issues: list[ValidationIssue] = []
        for path_issues in self.issues.values():
            all_issues.extend(path_issues)

        by_check: dict[str, list[ValidationIssue]] = defaultdict(list)
        for issue in all_issues:
            by_check[issue.check].append(issue)

        sections = [
            {"title": self._CHECK_LABELS.get(check, (check, 99))[0], "issues": issues}
            for check, issues in sorted(
                by_check.items(),
                key=lambda kv: self._CHECK_LABELS.get(kv[0], (kv[0], 99))[1],
            )
        ]

        content = template.render(
            sections=sections,
            total=sum(1 for i in all_issues if i.severity != "info"),
        )

        output_path = self.output_folder / self.output_filename
        output_path.write_text(content, encoding="utf-8")

    def _add_to_build(self, files: Files, config: MkDocsConfig) -> None:
        # deferred: avoid import-time mkdocs coupling
        from mkdocs.structure.files import File

        new_file = File(
            path=str(self.output_filename),
            src_dir=str(self.output_folder),
            dest_dir=config["site_dir"],
            use_directory_urls=False,
        )
        files.append(new_file)
        logger.info("Validation report added as %s", new_file.src_path)
