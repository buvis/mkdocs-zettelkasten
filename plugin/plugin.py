from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, Optional

import jinja2
import yaml
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File
from mkdocs.structure.nav import Section
from mkdocs.config.config_options import Type
from mkdocs.structure.pages import Page

from plugin.fix_page_links_to_zettels import fix_page_links_to_zettels
from plugin.fix_page_title import fix_page_title
from plugin.get_page_ref import get_page_ref
from plugin.get_prev_next_page import get_prev_next_page
from plugin.get_zettels import get_zettels


class ZettelkastenPlugin(BasePlugin):
    config_scheme = (
        ("tags_folder", Type(str, default=".build")),
        ("tags_template", Type(str)),
    )

    def __init__(self) -> None:
        super().__init__()
        # Tags configuration
        self.tags_filename: Path = Path("tags.md")
        self.tags_folder: Path = Path(".build")
        self.tags_template: Optional[Path] = None
        self.metadata: List[Dict[str, Any]] = []

        # Zettelkasten store
        self.zettels: Set[str] = set()

    def on_config(self, config: Dict[str, Any]) -> None:
        self._configure_tags_paths(config)
        self._ensure_tags_directory_exists()
        self._load_template_configuration()

    def on_files(self, files: List[File], config: Dict[str, Any]) -> None:
        self._process_zettelkasten_files(files, config)
        self._process_tags_metadata(files, config)
        self._generate_tags_file()
        self._add_tags_file_to_build(files, config)

    def on_page_markdown(
        self, markdown: str, page: Page, config: Dict[str, Any], files: List[File]
    ) -> str:
        return self._apply_zettelkasten_transformations(markdown, page, config, files)

    def _configure_tags_paths(self, config: Dict[str, Any]) -> None:
        """Configure paths for tags generation"""
        self.tags_filename = Path(self.config.get("tags_filename", "tags.md"))
        self.tags_folder = Path(self.config.get("tags_folder", ".build"))

        if not self.tags_folder.is_absolute():
            self.tags_folder = Path(config["docs_dir"]).parent / self.tags_folder

    def _ensure_tags_directory_exists(self) -> None:
        """Create tags directory if needed"""
        if not self.tags_folder.exists():
            self.tags_folder.mkdir(parents=True)

    def _load_template_configuration(self) -> None:
        """Handle template loading configuration"""
        if self.config.get("tags_template"):
            self.tags_template = Path(self.config["tags_template"])

    def _process_tags_metadata(self, files: List[File], config: Dict[str, Any]) -> None:
        """Extract metadata from Markdown files"""
        for file in files:
            if file.src_path.endswith(".md"):
                self.metadata.append(
                    self._extract_file_metadata(file.src_path, config["docs_dir"])
                )

    def _generate_tags_file(self) -> None:
        """Generate tags.md content"""
        tag_map = self._create_tag_map()
        rendered_content = self._render_tags_template(tag_map)
        self._write_tags_file(rendered_content)

    def _create_tag_map(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create structured data for template rendering"""
        tag_map: defaultdict[str, List[Dict[str, Any]]] = defaultdict(list)
        sorted_meta = sorted(self.metadata, key=lambda x: x.get("year", 5000))

        for meta in sorted_meta:
            if not meta:
                continue

            meta.setdefault("title", "Untitled")
            if tags := meta.get("tags"):
                for tag in tags:
                    tag_map[tag].append(meta)

        return dict(tag_map)

    def _render_tags_template(self, tag_map: Dict[str, List[Dict[str, Any]]]) -> str:
        """Render Jinja2 template for tags page"""
        environment = self._create_jinja_environment()
        template = environment.get_template(self._get_template_name())
        return template.render(tags=sorted(tag_map.items(), key=lambda t: t[0].lower()))

    def _create_jinja_environment(self) -> jinja2.Environment:
        """Configure Jinja2 environment based on settings"""
        if self.tags_template:
            return jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(self.tags_template.parent))
            )

        template_path = Path(__file__).parent / "templates"
        return jinja2.Environment(loader=jinja2.FileSystemLoader(str(template_path)))

    def _get_template_name(self) -> str:
        """Determine appropriate template name"""
        return self.tags_template.name if self.tags_template else "tags.md.j2"

    def _write_tags_file(self, content: str) -> None:
        """Write generated content to tags file"""
        output_path = self.tags_folder / self.tags_filename
        output_path.write_text(content, encoding="utf-8")

    def _add_tags_file_to_build(
        self, files: List[File], config: Dict[str, Any]
    ) -> None:
        """Register generated tags file in build process"""
        new_file = File(
            path=str(self.tags_filename),
            src_dir=str(self.tags_folder),
            dest_dir=config["site_dir"],
            use_directory_urls=False,
        )
        files.append(new_file)

    @staticmethod
    def _extract_file_metadata(filename: str, docs_dir: str) -> Dict[str, Any]:
        """Extract YAML metadata from Markdown files"""
        file_path = Path(docs_dir) / filename
        with file_path.open(encoding="utf-8") as f:
            yaml_content = ZettelkastenPlugin._read_yaml_frontmatter(f)

        if yaml_content:
            yaml_content["filename"] = filename
            return yaml_content
        return {}

    @staticmethod
    def _read_yaml_frontmatter(file_handler) -> Optional[Dict[str, Any]]:
        """Read YAML frontmatter from file"""
        yaml_lines = []
        delimiter_count = 0

        for line in file_handler:
            stripped = line.strip()
            if stripped == "---":
                delimiter_count += 1
                if delimiter_count == 2:
                    break
                continue

            if delimiter_count == 1:
                yaml_lines.append(line)

        if yaml_lines:
            try:
                return yaml.safe_load("".join(yaml_lines))
            except yaml.scanner.ScannerError:
                return None
        else:
            return None

    def _process_zettelkasten_files(
        self, files: List[File], config: Dict[str, Any]
    ) -> None:
        """Initialize Zettelkasten store"""
        self.zettels = get_zettels(files, config)

    def _apply_zettelkasten_transformations(
        self, markdown: str, page: Page, config: Dict[str, Any], files: List[File]
    ) -> str:
        """Process page Markdown for Zettelkasten features"""
        markdown = fix_page_title(markdown, page, config, files)
        markdown = fix_page_links_to_zettels(
            markdown, page, config, files, self.zettels
        )

        # Store navigation references
        page.previous_page, page.next_page = get_prev_next_page(
            markdown, page, config, files, self.zettels
        )

        # Add page reference
        processed_md, page.ref = get_page_ref(markdown, page, config, files)
        return processed_md
