from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files

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

    def configure(self, config: MkDocsConfig) -> None:
        self.output_folder = Path(config.get("tags_folder", ".build"))
        if not self.output_folder.is_absolute():
            self.output_folder = Path(config["docs_dir"]).parent / self.output_folder
        if not self.output_folder.exists():
            self.output_folder.mkdir(parents=True)

    def validate(self, zettel_service: Any, files: Files, config: MkDocsConfig) -> None:
        from .backlink_processor import BacklinkProcessor

        self.issues.clear()
        self._check_invalid_files(zettel_service)
        self._check_orphans(zettel_service)
        self._check_broken_links(zettel_service, BacklinkProcessor)
        self._generate_report()
        self._add_to_build(files, config)

        total = sum(len(v) for v in self.issues.values())
        logger.info("Validation complete: %d issues found.", total)

    def get_issues(self, rel_path: str) -> list[ValidationIssue]:
        return self.issues.get(rel_path, [])

    def _check_invalid_files(self, zettel_service: Any) -> None:
        for f in zettel_service.invalid_files:
            self.issues[f.src_path].append(
                ValidationIssue(
                    path=f.src_path,
                    check="invalid_file",
                    severity="error",
                    message="Invalid zettel (missing ID or malformed YAML)",
                )
            )

    def _check_orphans(self, zettel_service: Any) -> None:
        targeted_ids: set[int] = set()
        for link_path in zettel_service.backlinks:
            target = zettel_service.store.get_by_partial_path(link_path)
            if target:
                targeted_ids.add(target.id)

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
        self, zettel_service: Any, backlink_processor_cls: type
    ) -> None:
        for zettel in zettel_service.get_zettels():
            internal_links = [
                link
                for link in zettel.links
                if not link.startswith(("http://", "https://", "#", "mailto:"))
            ]
            for link in backlink_processor_cls._normalize_links(internal_links):
                target = zettel_service.store.get_by_partial_path(link)
                if not target:
                    self.issues[zettel.rel_path].append(
                        ValidationIssue(
                            path=zettel.rel_path,
                            check="broken_link",
                            severity="warning",
                            message=f"Broken link: {link}",
                        )
                    )

    def _generate_report(self) -> None:
        env = create_jinja_environment(None)
        template = env.get_template("validation.md.j2")

        all_issues: list[ValidationIssue] = []
        for path_issues in self.issues.values():
            all_issues.extend(path_issues)

        content = template.render(
            errors=[i for i in all_issues if i.severity == "error"],
            warnings=[i for i in all_issues if i.severity == "warning"],
            info=[i for i in all_issues if i.severity == "info"],
            total=len(all_issues),
        )

        output_path = self.output_folder / self.output_filename
        output_path.write_text(content, encoding="utf-8")

    def _add_to_build(self, files: Files, config: MkDocsConfig) -> None:
        from mkdocs.structure.files import File

        new_file = File(
            path=str(self.output_filename),
            src_dir=str(self.output_folder),
            dest_dir=config["site_dir"],
            use_directory_urls=False,
        )
        files.append(new_file)
        logger.info("Validation report added as %s", new_file.src_path)
