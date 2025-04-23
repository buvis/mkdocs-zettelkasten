import pytest
from pathlib import Path
from unittest.mock import patch
import datetime

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel


@pytest.fixture
def zettel_factory(tmp_path):
    """
    Factory fixture to create a Zettel instance with custom file content and mtime.

    Args:
        file_content (str): The content of the markdown file (including YAML frontmatter).
        mtime (datetime.datetime): The modification time to mock for the file.

    Returns:
        Zettel: The initialized Zettel instance.
    """

    def _factory(file_content: str, mtime: datetime.datetime):
        file_path = tmp_path / "test.md"
        file_path.write_text(file_content)
        with patch(
            "mkdocs_zettelkasten.plugin.entities.zettel.os.path.getmtime",
            return_value=mtime.timestamp(),
        ):
            return Zettel(str(file_path))

    return _factory
