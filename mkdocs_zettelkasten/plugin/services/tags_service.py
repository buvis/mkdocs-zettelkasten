from pathlib import Path
from typing import Any, Dict, List, Optional

from mkdocs_zettelkasten.plugin.utils.metadata_utils import extract_file_metadata
from mkdocs_zettelkasten.plugin.utils.jinja_utils import create_jinja_environment


class TagsService:
    """
    Handles tag extraction, template rendering, and tags file generation.
    """

    def __init__(self) -> None:
        self.tags_filename: Path = Path("tags.md")
        self.tags_folder: Path = Path(".build")
        self.tags_template: Optional[Path] = None
        self.metadata: List[Dict[str, Any]] = []

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure paths and template from MkDocs config.
        """
        self.tags_filename = Path(config.get("tags_filename", "tags.md"))
        self.tags_folder = Path(config.get("tags_folder", ".build"))
        if not self.tags_folder.is_absolute():
            self.tags_folder = Path(config["docs_dir"]).parent / self.tags_folder
        if config.get("tags_template"):
            self.tags_template = Path(config["tags_template"])
        if not self.tags_folder.exists():
            self.tags_folder.mkdir(parents=True)

    def process_metadata(self, files: List[Any], config: Dict[str, Any]) -> None:
        """
        Extract metadata from Markdown files.
        """
        self.metadata.clear()
        for file in files:
            if file.src_path.endswith(".md"):
                meta = extract_file_metadata(file.src_path, config["docs_dir"])
                if meta:
                    self.metadata.append(meta)

    def generate_tags_file(self) -> None:
        """
        Render and write the tags file.
        """
        tag_map = self._create_tag_map()
        rendered = self._render_tags_template(tag_map)
        self._write_tags_file(rendered)

    def add_tags_file_to_build(self, files: List[Any], config: Dict[str, Any]) -> None:
        """
        Add the generated tags file to the MkDocs build list.
        """
        from mkdocs.structure.files import File  # Local import for plugin compatibility

        new_file = File(
            path=str(self.tags_filename),
            src_dir=str(self.tags_folder),
            dest_dir=config["site_dir"],
            use_directory_urls=False,
        )
        files.append(new_file)

    def _create_tag_map(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Create a mapping of tags to metadata entries.
        """
        from collections import defaultdict

        tag_map = defaultdict(list)
        for meta in sorted(self.metadata, key=lambda x: x.get("year", 5000)):
            if tags := meta.get("tags"):
                for tag in tags:
                    tag_map[tag].append(meta)
        return dict(tag_map)

    def _render_tags_template(self, tag_map: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Render the tags page using a Jinja2 template.
        """
        env = create_jinja_environment(self.tags_template)
        template_name = self.tags_template.name if self.tags_template else "tags.md.j2"
        template = env.get_template(template_name)
        return template.render(tags=sorted(tag_map.items(), key=lambda t: t[0].lower()))

    def _write_tags_file(self, content: str) -> None:
        """
        Write the rendered tags content to the output file.
        """
        output_path = self.tags_folder / self.tags_filename
        output_path.write_text(content, encoding="utf-8")
