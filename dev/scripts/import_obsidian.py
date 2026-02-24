"""Convert an Obsidian vault to mkdocs-zettelkasten format."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------


def slugify_filename(name: str) -> str:
    """Turn a human filename into a slug: lowercase, spaces to hyphens."""
    return re.sub(r"\s+", "-", name.strip()).lower()


# ---------------------------------------------------------------------------
# Wikilink conversion
# ---------------------------------------------------------------------------

_EMBED_LINK = re.compile(
    r"!\[\[(?P<target>[^\]#|]+)(?:#(?P<section>[^\]|]+))?(?:\|(?P<alias>[^\]]+))?\]\]"
)

_WIKI_LINK = re.compile(r"\[\[(?P<target>[^\]|]+)(?:\|(?P<alias>[^\]]+))?\]\]")


def convert_embed_link(m: re.Match) -> str:
    """``![[target]]`` -> ``![target](target.md)``."""
    target = m.group("target").strip()
    section = m.group("section")
    alias = m.group("alias")

    slug = slugify_filename(target) + ".md"
    if section:
        slug += "#" + section.strip().lower().replace(" ", "-")

    display = alias or target
    return f"![{display}]({slug})"


def convert_wiki_link(m: re.Match) -> str:
    """``[[target]]`` -> ``[target](target.md)``."""
    target = m.group("target").strip()
    alias = m.group("alias")

    slug = slugify_filename(target) + ".md"
    display = alias or target
    return f"[{display}]({slug})"


def convert_links(text: str) -> str:
    """Replace all Obsidian wiki/embed links with markdown equivalents."""
    # Embeds first so ``![[`` is not partially matched by ``[[``
    text = _EMBED_LINK.sub(convert_embed_link, text)
    return _WIKI_LINK.sub(convert_wiki_link, text)


# ---------------------------------------------------------------------------
# Frontmatter mapping
# ---------------------------------------------------------------------------

DEFAULT_FRONTMATTER_MAP: dict[str, str | None] = {
    "aliases": None,  # strip
    "cssclass": None,  # strip
    "cssclasses": None,  # strip
    "publish": None,  # strip
    "alias": None,  # strip
}


def map_frontmatter(
    fm: dict,
    mapping: dict[str, str | None] | None = None,
) -> dict:
    """Remap or strip Obsidian-specific frontmatter keys.

    ``mapping`` values:
    - ``None`` -> strip the key
    - ``"new_key"`` -> rename
    """
    mapping = mapping or DEFAULT_FRONTMATTER_MAP
    out: dict = {}
    for key, value in fm.items():
        if key in mapping:
            new_key = mapping[key]
            if new_key is not None:
                out[new_key] = value
        else:
            out[key] = value
    return out


# ---------------------------------------------------------------------------
# Full-file conversion
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"\A---\n(.+?)\n---\n?", re.DOTALL)


def convert_file_content(
    text: str,
    frontmatter_map: dict[str, str | None] | None = None,
) -> str:
    """Convert a single Obsidian markdown file's content."""
    fm_match = _FRONTMATTER_RE.match(text)
    if fm_match:
        raw_fm = fm_match.group(1)
        fm = yaml.safe_load(raw_fm)
        if isinstance(fm, dict):
            fm = map_frontmatter(fm, frontmatter_map)
            body = text[fm_match.end() :]
            fm_str = yaml.dump(
                fm, default_flow_style=False, allow_unicode=True
            ).rstrip()
            return f"---\n{fm_str}\n---\n{convert_links(body)}"

    return convert_links(text)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def process_vault(input_dir: Path, output_dir: Path) -> int:
    """Walk input_dir, convert .md files, copy everything else. Returns file count."""
    count = 0
    for src in input_dir.rglob("*"):
        if src.is_dir():
            continue

        rel = src.relative_to(input_dir)

        # Slugify each path component for .md files
        if src.suffix == ".md":
            parts = list(rel.parts)
            parts[-1] = slugify_filename(rel.stem) + ".md"
            dest = output_dir / Path(*parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            text = src.read_text(encoding="utf-8-sig")
            dest.write_text(convert_file_content(text), encoding="utf-8")
            count += 1
        else:
            dest = output_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)

    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert an Obsidian vault to mkdocs-zettelkasten format.",
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        help="Path to Obsidian vault",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Path to output directory",
    )
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        parser.error(f"Input directory does not exist: {args.input_dir}")

    count = process_vault(args.input_dir, args.output_dir)
    print(f"Converted {count} markdown files")


if __name__ == "__main__":
    main()
