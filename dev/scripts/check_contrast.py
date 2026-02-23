#!/usr/bin/env python3
"""WCAG 2.1 contrast-ratio checker for color-scheme CSS files."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Named CSS colors used in scheme files
# ---------------------------------------------------------------------------
NAMED_COLORS: dict[str, str] = {
    "black": "#000000",
    "white": "#ffffff",
    "gray": "#808080",
    "grey": "#808080",
    "lightgray": "#d3d3d3",
    "lightgrey": "#d3d3d3",
    "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9",
    "silver": "#c0c0c0",
    "red": "#ff0000",
    "green": "#008000",
    "blue": "#0000ff",
    "yellow": "#ffff00",
    "orange": "#ffa500",
}

# ---------------------------------------------------------------------------
# Contrast pairs: (foreground var, background var, required ratio, label)
# ---------------------------------------------------------------------------
CONTRAST_PAIRS: list[tuple[str, str, float, str]] = [
    ("--text-primary", "--bg-zettel", 4.5, "body text"),
    ("--text-link", "--bg-zettel", 4.5, "links"),
    ("--text-header", "--bg-zettel", 3.0, "headings (large)"),
    ("--text-primary", "--bg-accent", 4.5, "text on accent bg"),
    ("--text-code", "--bg-code", 4.5, "code blocks"),
]

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

_HEX3 = re.compile(r"^#([0-9a-fA-F]{3})$")
_HEX6 = re.compile(r"^#([0-9a-fA-F]{6})$")


def parse_color(raw: str) -> tuple[int, int, int]:
    """Return (R, G, B) 0-255 from a hex string or named color."""
    value = raw.strip().lower()
    if value in NAMED_COLORS:
        value = NAMED_COLORS[value]

    m6 = _HEX6.match(value)
    if m6:
        h = m6.group(1)
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    m3 = _HEX3.match(value)
    if m3:
        h = m3.group(1)
        return int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16)

    msg = f"cannot parse color: {raw!r}"
    raise ValueError(msg)


def _linearize(c8: int) -> float:
    """sRGB channel (0-255) -> linear value per WCAG 2.1."""
    s = c8 / 255.0
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def relative_luminance(r: int, g: int, b: int) -> float:
    """WCAG 2.1 relative luminance (0-1)."""
    return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


def contrast_ratio(fg: tuple[int, int, int], bg: tuple[int, int, int]) -> float:
    """WCAG contrast ratio (1-21)."""
    l1 = relative_luminance(*fg)
    l2 = relative_luminance(*bg)
    if l1 < l2:
        l1, l2 = l2, l1
    return (l1 + 0.05) / (l2 + 0.05)


# ---------------------------------------------------------------------------
# CSS parsing
# ---------------------------------------------------------------------------

_SELECTOR_RE = re.compile(
    r'\[data-color-scheme="([^"]+)"\]'
    r'(?:\[data-theme="dark"\])?'
)
_VAR_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")


def parse_scheme_file(path: Path) -> dict[str, dict[str, str]]:
    """Parse a scheme CSS file into {variant: {var: value}}.

    Returns a dict keyed by "<scheme_id>" for light and
    "<scheme_id>__dark" for the dark variant.
    """
    text = path.read_text()
    result: dict[str, dict[str, str]] = {}

    # Split on top-level selectors while keeping the selector text.
    # Strategy: find each selector block via brace matching.
    pos = 0
    while pos < len(text):
        sel_match = _SELECTOR_RE.search(text, pos)
        if not sel_match:
            break
        scheme_id = sel_match.group(1)
        is_dark = '[data-theme="dark"]' in sel_match.group(0)
        key = f"{scheme_id}__dark" if is_dark else scheme_id

        # Find the opening brace after the selector
        brace_start = text.index("{", sel_match.end())
        depth = 1
        i = brace_start + 1
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        block = text[brace_start + 1 : i - 1]

        variables: dict[str, str] = {}
        for vm in _VAR_RE.finditer(block):
            variables[vm.group(1)] = vm.group(2).strip()
        result[key] = variables
        pos = i

    return result


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------


def check_schemes(schemes_dir: Path) -> list[dict]:
    """Run contrast checks on all CSS files.  Returns list of result dicts."""
    results: list[dict] = []
    for css_file in sorted(schemes_dir.glob("*.css")):
        variants = parse_scheme_file(css_file)
        for variant_key, variables in sorted(variants.items()):
            is_dark = variant_key.endswith("__dark")
            scheme_name = variant_key.removesuffix("__dark") if is_dark else variant_key
            mode = "dark" if is_dark else "light"

            for fg_var, bg_var, required, label in CONTRAST_PAIRS:
                fg_raw = variables.get(fg_var)
                bg_raw = variables.get(bg_var)
                if fg_raw is None or bg_raw is None:
                    results.append({
                        "scheme": scheme_name,
                        "mode": mode,
                        "pair": label,
                        "fg_var": fg_var,
                        "bg_var": bg_var,
                        "ratio": None,
                        "required": required,
                        "pass": False,
                        "note": "missing variable",
                    })
                    continue

                try:
                    fg = parse_color(fg_raw)
                    bg = parse_color(bg_raw)
                except ValueError as exc:
                    results.append({
                        "scheme": scheme_name,
                        "mode": mode,
                        "pair": label,
                        "fg_var": fg_var,
                        "bg_var": bg_var,
                        "ratio": None,
                        "required": required,
                        "pass": False,
                        "note": str(exc),
                    })
                    continue

                ratio = contrast_ratio(fg, bg)
                results.append({
                    "scheme": scheme_name,
                    "mode": mode,
                    "pair": label,
                    "fg_var": fg_var,
                    "bg_var": bg_var,
                    "ratio": ratio,
                    "required": required,
                    "pass": ratio >= required,
                    "note": "",
                })

    return results


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _print_report(results: list[dict]) -> int:
    """Print a table and return exit code (0 = all pass, 1 = failures)."""
    failures = [r for r in results if not r["pass"]]

    # Print all results grouped by scheme+mode
    current = ""
    for r in results:
        header = f"{r['scheme']} ({r['mode']})"
        if header != current:
            current = header
            print(f"\n  {header}")
            print(f"  {'─' * 60}")

        status = "PASS" if r["pass"] else "FAIL"
        ratio_str = f"{r['ratio']:.2f}" if r["ratio"] is not None else "N/A"
        note = f"  ({r['note']})" if r["note"] else ""
        print(
            f"    [{status}] {r['pair']:<22} "
            f"{ratio_str:>6}:1  (need {r['required']:.1f}:1){note}"
        )

    # Summary
    total = len(results)
    passed = total - len(failures)
    print(f"\n  {passed}/{total} checks passed")

    if failures:
        print(f"\n  {len(failures)} failure(s):")
        for r in failures:
            ratio_str = f"{r['ratio']:.2f}" if r["ratio"] is not None else "N/A"
            note = f" ({r['note']})" if r["note"] else ""
            print(
                f"    - {r['scheme']} {r['mode']}: {r['pair']} "
                f"= {ratio_str}:1 < {r['required']:.1f}:1{note}"
            )
        return 1

    print("\n  All checks passed.")
    return 0


def main(schemes_dir: Path | None = None) -> int:
    if schemes_dir is None:
        schemes_dir = (
            Path(__file__).resolve().parents[2]
            / "mkdocs_zettelkasten"
            / "themes"
            / "zettelkasten"
            / "css"
            / "schemes"
        )
    if not schemes_dir.is_dir():
        print(f"error: schemes dir not found: {schemes_dir}", file=sys.stderr)
        return 1

    results = check_schemes(schemes_dir)
    return _print_report(results)


if __name__ == "__main__":
    raise SystemExit(main())
