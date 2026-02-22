---
id: 20260222000001
title: Configuration Reference
tags: [reference, configuration]
---

# Configuration Reference

All options go in `mkdocs.yml`.

## Minimal example

```yaml
theme:
  name: zettelkasten

plugins:
  - search
  - zettelkasten
```

## Full example

```yaml
theme:
  name: zettelkasten
  color_scheme: solarized      # see Color Schemes page
  highlightjs: true
  hljs_style: github           # light mode code theme
  hljs_style_dark: github-dark # dark mode code theme
  hljs_languages: []           # extra languages beyond the common bundle

plugins:
  - search
  - zettelkasten:
      log_level: INFO
      id_key: id
      date_key: date
      last_update_key: last_update
      tags_key: tags
      id_format: '^\d{14}$'
      date_format: '%Y-%m-%d'
      timezone: ''
      file_suffix: .md
      validation_enabled: true
      icon_references: fa fa-book
      icon_backlinks: fa fa-link
      editor_enabled: false
      editor_repo: ''
      editor_branch: main
      editor_docs_prefix: docs
```

## Plugin options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `log_level` | string | `INFO` | Logging verbosity: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `id_key` | string | `id` | YAML frontmatter key for zettel ID |
| `date_key` | string | `date` | Frontmatter key for creation date |
| `last_update_key` | string | `last_update` | Frontmatter key for last update date |
| `tags_key` | string | `tags` | Frontmatter key for tags |
| `id_format` | regex | `^\d{14}$` | Pattern for valid zettel IDs (default: 14-digit timestamp) |
| `date_format` | string | `%Y-%m-%d` | Python strftime format for displayed dates |
| `timezone` | string | *(system)* | Timezone for dates. Falls back to env `ZETTELKASTEN_TZ`, then system timezone |
| `file_suffix` | string | `.md` | File extension for zettel documents |
| `validation_enabled` | bool | `true` | Show validation warnings for malformed zettels |
| `icon_references` | string | `fa fa-book` | FontAwesome class for references icon |
| `icon_backlinks` | string | `fa fa-link` | FontAwesome class for backlinks icon |
| `editor_enabled` | bool | `false` | Show in-browser edit button on zettels |
| `editor_repo` | string | *(empty)* | GitHub repo in `owner/repo` format (required if editor enabled) |
| `editor_branch` | string | `main` | Branch for editor commits |
| `editor_docs_prefix` | string | `docs` | Path prefix to docs directory in repo |

## Theme options

Set under `theme:` in `mkdocs.yml`.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `color_scheme` | string | `solarized` | Color scheme name (see [Color Schemes](color-schemes.md)) |
| `highlightjs` | bool | `true` | Enable syntax highlighting |
| `hljs_style` | string | `github` | Highlight.js theme for light mode |
| `hljs_style_dark` | string | `github-dark` | Highlight.js theme for dark mode |
| `hljs_languages` | list | `[]` | Extra highlight.js language packs to load |
| `navigation_depth` | int | `2` | Max depth of nav menu |
| `nav_style` | string | `primary` | Navbar color style: `primary`, `light`, `dark` |
| `locale` | string | `en` | Language locale |
| `analytics.gtag` | string | *(null)* | Google Analytics 4 measurement ID |
| `shortcuts.help` | int | `191` | Keycode for help shortcut (default: ?) |
| `shortcuts.next` | int | `78` | Keycode for next page (default: n) |
| `shortcuts.previous` | int | `80` | Keycode for previous page (default: p) |
| `shortcuts.search` | int | `83` | Keycode for search (default: s) |

## Zettel frontmatter

Each zettel needs YAML frontmatter between `---` delimiters:

```markdown
---
id: 20211122194827
title: My zettel title
tags: [topic-a, topic-b]
date: 2021-11-22
---

Your content here.
```

- `id` *(required)* — unique identifier matching `id_format`
- `title` *(optional)* — falls back to first H1 heading, then filename
- `tags` *(optional)* — list of tags for the tag index
- `date` *(optional)* — creation date
- `last_update` *(optional)* — if set, overrides git/filesystem date
