from pathlib import Path
from typing import Callable
from unittest.mock import Mock, patch

import pytest

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel


@pytest.fixture
def zettel_factory(tmp_path: Path) -> Callable[[str, float], Zettel]:
    def _factory(file_content: str, mtime: float) -> Zettel:
        file_path = tmp_path / "test.md"
        file_path.write_text(file_content)
        mock_stat = Mock()
        mock_stat.st_mtime = mtime

        with (
            patch.object(Path, "stat", return_value=mock_stat),
            patch(
                "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
                return_value=False,
            ),
        ):
            return Zettel(file_path, str(file_path.relative_to(tmp_path)))

    return _factory
