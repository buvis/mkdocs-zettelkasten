---
id: 20260222000002
title: Color Schemes
tags: [reference, theme]
---

# Color Schemes

Set your color scheme in `mkdocs.yml`:

```yaml
theme:
  name: zettelkasten
  color_scheme: solarized
```

Users can also switch schemes at runtime via the settings modal (gear icon in the navbar).

## Available schemes

acme, atom-one-monokai, ayu, catppuccin, dracula, everforest, flexoki, github, gruvbox, horizon, kanagawa, material, modus, monokai, night-owl, nord, one, palenight, papercolor, poimandres, rose-pine, selenized, solarized, tokyo-night, zenburn

All schemes support both light and dark modes. Use the dark mode toggle in the settings modal to switch.

## Code highlighting themes

Code block syntax highlighting uses highlight.js. Set defaults in `mkdocs.yml`:

```yaml
theme:
  hljs_style: github           # light mode
  hljs_style_dark: github-dark # dark mode
```

Users can pick from 27 code themes in the settings modal. The preview pane shows a live sample.
