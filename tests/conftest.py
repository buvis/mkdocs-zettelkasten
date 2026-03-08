from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

PERMISSIVE_CONFIG = ZettelkastenConfig(id_format=r"^\d+$")


@pytest.fixture
def zettel_factory(tmp_path: Path) -> Callable[..., Zettel]:
    def _factory(
        file_content: str,
        mtime: float,
        zettel_config: ZettelkastenConfig | None = None,
    ) -> Zettel:
        file_path = tmp_path / "test.md"
        file_path.write_text(file_content)
        mock_stat = Mock()
        mock_stat.st_mtime = mtime

        cfg = zettel_config or PERMISSIVE_CONFIG

        with (
            patch.object(Path, "stat", return_value=mock_stat),
            patch(
                "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
                return_value=False,
            ),
        ):
            return Zettel(file_path, str(file_path.relative_to(tmp_path)), cfg)

    return _factory
