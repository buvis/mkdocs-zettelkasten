from typing import Any, Dict, List, Set

from mkdocs_zettelkasten.plugin.adapters.zettels import get_zettels


class ZettelService:
    """
    Handles Zettelkasten file discovery and storage.
    """

    def __init__(self) -> None:
        self.zettels: Set[str] = set()

    def process_files(self, files: List[Any], config: Dict[str, Any]) -> None:
        """
        Populate the zettels set using adapters.zettels.get_zettels.
        """
        self.zettels = get_zettels(files, config)
