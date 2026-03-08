from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.services.tags_service import TagsService
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


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
        svc.process_metadata(files)

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
        svc.process_metadata(files)

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
        svc.process_metadata(files)
        svc.generate_tags_file()

        output = tmp_path / "tags.md"
        assert output.exists()
        content = output.read_text()
        assert "demo" in content

    def test_configure_creates_folder(self, tmp_path: Path) -> None:
        target = tmp_path / "build_output"
        config = MagicMock()
        config.get = lambda key, default=None: {
            "tags_filename": "tags.md",
            "tags_folder": str(target),
            "tags_template": None,
        }.get(key, default)
        config.__getitem__ = lambda self, key: {
            "docs_dir": str(tmp_path),
            "site_dir": str(tmp_path / "site"),
        }[key]

        svc = TagsService()
        svc.configure(config)

        assert target.exists()
        assert target.is_dir()

    def test_configure_resolves_relative_folder(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir()
        config = MagicMock()
        config.get = lambda key, default=None: {
            "tags_filename": "tags.md",
            "tags_folder": ".build",
            "tags_template": None,
        }.get(key, default)
        config.__getitem__ = lambda self, key: {
            "docs_dir": str(docs),
            "site_dir": str(tmp_path / "site"),
        }[key]

        svc = TagsService()
        svc.configure(config)

        assert svc.tags_folder == tmp_path / ".build"

    def test_process_files_chains_metadata_and_tags(self, tmp_path: Path) -> None:
        md = tmp_path / "note.md"
        md.write_text("---\nid: 1\ntags:\n  - alpha\n---\nBody\n")

        f = MagicMock()
        f.src_path = "note.md"

        files = MagicMock()
        files.__iter__ = lambda self: iter([f])
        files.__len__ = lambda self: 1

        svc = TagsService()
        config = self._make_config(str(tmp_path))
        svc.configure(config)
        svc.process_files(files)

        # metadata extracted
        assert len(svc.metadata) == 1
        assert svc.metadata[0]["tags"] == ["alpha"]

        # tags file generated
        output = tmp_path / "tags.md"
        assert output.exists()
        assert "alpha" in output.read_text()

        # tags file added to build via files.append
        files.append.assert_called_once()

    def test_moc_featured_as_entry_points(self, tmp_path: Path) -> None:
        svc = TagsService()
        config = self._make_config(str(tmp_path))
        svc.configure(config, role_key="role")
        svc.metadata = [
            {
                "id": 1,
                "title": "MOC Note",
                "tags": ["python"],
                "role": "moc",
                "src_path": "moc.md",
            },
            {
                "id": 2,
                "title": "Regular Note",
                "tags": ["python"],
                "src_path": "regular.md",
            },
        ]
        svc.generate_tags_file()

        content = (tmp_path / "tags.md").read_text()
        assert "Entry points" in content
        assert "[MOC Note]" in content
        # MOC should only appear in entry points, not in the regular list
        assert content.count("MOC Note") == 1
        # Regular note should appear in the regular list
        assert "[Regular Note]" in content

    def test_process_metadata_uses_configured_suffix_for_store_lookup(
        self, tmp_path: Path
    ) -> None:
        z = _make_zettel_mock(
            1, title="Note", rel_path="note.txt",
            path=Path("/docs/note.txt"),
        )
        z.meta = {"id": 1, "title": "Note", "tags": ["demo"]}
        store = ZettelStore([z])

        f = MagicMock()
        f.src_path = "note.txt"

        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        svc = TagsService()
        config = self._make_config(str(tmp_path))
        svc.configure(config, file_suffix=".txt")
        svc.process_metadata(files, store)

        assert len(svc.metadata) == 1
        assert svc.metadata[0]["title"] == "Note"
