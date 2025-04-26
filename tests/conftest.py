import datetime
from pathlib import Path
from typing import Callable
from unittest.mock import Mock, patch

import pytest

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel


@pytest.fixture
def zettel_factory(tmp_path: Path) -> Callable[[str, datetime.datetime], Zettel]:
    """
    Factory fixture to create a Zettel instance with custom file content and mtime.

    Args:
        file_content (str): The content of the markdown file (including YAML frontmatter).
        mtime (datetime.datetime): The modification time to mock for the file.

    Returns:
        Zettel: The initialized Zettel instance.
    """

    def _factory(file_content: str, mtime: datetime.datetime) -> Zettel:
        file_path = tmp_path / "test.md"
        file_path.write_text(file_content)
        mock_stat = Mock()
        mock_stat.st_mtime = mtime

        with patch.object(Path, "stat", return_value=mock_stat):
            return Zettel(file_path)

    return _factory
