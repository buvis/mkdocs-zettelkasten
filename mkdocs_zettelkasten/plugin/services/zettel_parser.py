import logging
from pathlib import Path

from mkdocs.structure.files import File, Files

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


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
            if not file.is_documentation_page():
                continue
            if not file.abs_src_path:
                continue
            try:
                zettel = Zettel(Path(file.abs_src_path), file.src_path)
            except ValueError:
                invalid_files.append(file)
                logger.debug("Ignoring invalid zettel: %s", file.src_path)
            else:
                valid_zettels.append(zettel)
                logger.debug("Added zettel from %s", file.src_path)

        return valid_zettels, invalid_files
