import logging
from pathlib import Path

from mkdocs.structure.files import File, Files

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

log = logging.getLogger("mkdocs.plugins.zettelkasten")


class ZettelParser:
    """Converts Markdown files into validated Zettel instances."""

    @staticmethod
    def parse_files(files: Files) -> tuple[list[Zettel], list[File]]:
        """
        Returns:
            Tuple of (valid_zettels, invalid_files)
        """
        valid_zettels = []
        invalid_files = []

        for file in files:
            if not file.abs_src_path:
                continue
            try:
                zettel = Zettel(Path(file.abs_src_path))
            except ValueError:
                invalid_files.append(file)
                log.warning("Ignoring invalid zettel: %s", file.abs_src_path)
            else:
                valid_zettels.append(zettel)

        return valid_zettels, invalid_files
