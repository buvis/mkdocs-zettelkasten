from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.services.tags_service import TagsService


class TestTagsService:
    def _make_config(self, docs_dir: str, site_dir: str = "/tmp/site") -> MagicMock:
        config = MagicMock()
        config.get = lambda key, default=None: {
            "tags_filename": "tags.md",
            "tags_folder": docs_dir,
            "tags_template": None,
        }.get(key, default)
        config.__getitem__ = lambda self, key: {
            "docs_dir": docs_dir,
            "site_dir": site_dir,
        }[key]
        return config

    def test_process_metadata(self, tmp_path: Path) -> None:
        md = tmp_path / "note.md"
        md.write_text("---\nid: 1\ntags:\n  - python\n  - testing\n---\nBody\n")

        f = MagicMock()
        f.src_path = "note.md"

        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        svc = TagsService()
        config = self._make_config(str(tmp_path))
        svc.configure(config)
        svc.process_metadata(files, config)

        assert len(svc.metadata) == 1
        assert svc.metadata[0]["tags"] == ["python", "testing"]

    def test_custom_tags_key(self, tmp_path: Path) -> None:
        md = tmp_path / "note.md"
        md.write_text("---\nid: 1\nlabels:\n  - alpha\n---\nBody\n")

        f = MagicMock()
        f.src_path = "note.md"

        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        svc = TagsService()
        config = self._make_config(str(tmp_path))
        svc.configure(config, tags_key="labels")
        svc.process_metadata(files, config)

        tag_map = svc._create_tag_map()
        assert "alpha" in tag_map

    def test_generate_tags_file(self, tmp_path: Path) -> None:
        md = tmp_path / "note.md"
        md.write_text("---\nid: 1\ntags:\n  - demo\n---\nBody\n")

        f = MagicMock()
        f.src_path = "note.md"

        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        svc = TagsService()
        config = self._make_config(str(tmp_path))
        svc.configure(config)
        svc.process_metadata(files, config)
        svc.generate_tags_file()

        output = tmp_path / "tags.md"
        assert output.exists()
        content = output.read_text()
        assert "demo" in content
