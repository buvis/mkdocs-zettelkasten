from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.entities.zettel import Zettel


import logging

from mkdocs.structure.files import File, Files

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def get_prev_next_page(
    page: Page,
    files: Files,
    zettels: list[Zettel],
) -> tuple[Page | None, Page | None]:
    """Determine previous and next pages for navigation with zettelkasten support."""
    if _is_special_page(page):
        return _handle_special_page(page, files, zettels)

    homepage_file = _find_homepage(files)

    if not page.meta.get("is_zettel"):
        return (None, None)

    current_index = _find_zettel_index(page, zettels)

    if current_index is None:
        return (None, None)

    prev_zettel, next_zettel = _get_adjacent_zettels(zettels, current_index)
    prev_file = _resolve_zettel_file(prev_zettel, files) or homepage_file
    next_file = _resolve_zettel_file(next_zettel, files)
    prev_page = (
        prev_file.page if isinstance(prev_file, File) and prev_file.page else None
    )
    next_page = (
        next_file.page if isinstance(next_file, File) and next_file.page else None
    )
    log_prev_page = prev_page.file.src_path if prev_page is not None else "none"
    log_next_page = next_page.file.src_path if next_page is not None else "none"

    logger.debug(
        "Setting %s as previous and %s as next page for %s",
        log_prev_page,
        log_next_page,
        page.file.src_path,
    )
    return (prev_page, next_page)


def _is_special_page(page: Page) -> bool:
    return page.file.src_path in {"index.md", "tags.md"}


def _handle_special_page(
    page: Page,
    files: Files,
    zettels: list[Zettel],
) -> tuple[Page | None, Page | None]:
    if page.file.src_path == "index.md" and zettels:
        first_zettel_file = _find_file_by_path(files, str(zettels[0].path))
        next_page = (
            first_zettel_file.page
            if isinstance(first_zettel_file, File) and first_zettel_file.page
            else None
        )

        return (None, next_page)
    return (None, None)


def _find_homepage(files: Files) -> File | str:
    return next((f for f in files if f.src_path == "index.md"), "")


def _find_zettel_index(page: Page, zettels: list[Zettel]) -> int | None:
    if not page.meta.get("zettel"):
        return None

    zettel_id = page.meta["zettel"].id

    return (
        next((i for i, z in enumerate(zettels) if z.id == zettel_id), None)
        if zettel_id
        else None
    )


def _get_adjacent_zettels(
    zettels: list[Zettel],
    current_index: int,
) -> tuple[Zettel | None, Zettel | None]:
    return (
        zettels[current_index - 1] if current_index > 0 else None,
        zettels[current_index + 1] if current_index < len(zettels) - 1 else None,
    )


def _resolve_zettel_file(zettel: Zettel | None, files: Files) -> File | str:
    return _find_file_by_path(files, str(zettel.path)) if zettel else ""


def _find_file_by_path(files: Files, path: str) -> File | str:
    return next((f for f in files if f.abs_src_path == path), "")
