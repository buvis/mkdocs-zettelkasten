"""Unit tests for dev/scripts/check_contrast.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make dev/scripts importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dev" / "scripts"))

from check_contrast import (
    contrast_ratio,
    parse_color,
    parse_scheme_file,
    relative_luminance,
)

# ── parse_color ──────────────────────────────────────────────────────────


class TestParseColor:
    def test_hex6(self):
        assert parse_color("#ff0000") == (255, 0, 0)

    def test_hex6_upper(self):
        assert parse_color("#00FF00") == (0, 255, 0)

    def test_hex3(self):
        assert parse_color("#f00") == (255, 0, 0)

    def test_hex3_mixed_case(self):
        assert parse_color("#0Af") == (0, 170, 255)

    def test_named_black(self):
        assert parse_color("black") == (0, 0, 0)

    def test_named_white(self):
        assert parse_color("white") == (255, 255, 255)

    def test_named_gray(self):
        assert parse_color("gray") == (128, 128, 128)

    def test_named_lightgray(self):
        assert parse_color("lightgray") == (211, 211, 211)

    def test_strips_whitespace(self):
        assert parse_color("  #abc  ") == (170, 187, 204)

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="cannot parse color"):
            parse_color("not-a-color")

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="cannot parse color"):
            parse_color("")


# ── relative_luminance ───────────────────────────────────────────────────


class TestRelativeLuminance:
    def test_black(self):
        assert relative_luminance(0, 0, 0) == pytest.approx(0.0)

    def test_white(self):
        assert relative_luminance(255, 255, 255) == pytest.approx(1.0)

    def test_red(self):
        assert relative_luminance(255, 0, 0) == pytest.approx(0.2126, abs=1e-4)

    def test_green(self):
        assert relative_luminance(0, 255, 0) == pytest.approx(0.7152, abs=1e-4)

    def test_blue(self):
        assert relative_luminance(0, 0, 255) == pytest.approx(0.0722, abs=1e-4)

    def test_mid_gray(self):
        # sRGB #808080 -> each channel = 128 -> linear ~0.2159
        lum = relative_luminance(128, 128, 128)
        assert 0.2 < lum < 0.25


# ── contrast_ratio ───────────────────────────────────────────────────────


class TestContrastRatio:
    def test_black_on_white(self):
        assert contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0)

    def test_white_on_black(self):
        # order shouldn't matter
        assert contrast_ratio((255, 255, 255), (0, 0, 0)) == pytest.approx(21.0)

    def test_same_color(self):
        assert contrast_ratio((100, 100, 100), (100, 100, 100)) == pytest.approx(1.0)

    def test_known_pair(self):
        # #767676 on white is the WCAG threshold for 4.5:1
        ratio = contrast_ratio((118, 118, 118), (255, 255, 255))
        assert ratio == pytest.approx(4.54, abs=0.05)


# ── parse_scheme_file ────────────────────────────────────────────────────


class TestParseSchemeFile:
    def test_light_only(self, tmp_path):
        css = tmp_path / "test.css"
        css.write_text("""
[data-color-scheme="test"] {
  --bg-zettel: #fff;
  --text-primary: #000;
}
""")
        result = parse_scheme_file(css)
        assert "test" in result
        assert result["test"]["--bg-zettel"] == "#fff"
        assert result["test"]["--text-primary"] == "#000"

    def test_light_and_dark(self, tmp_path):
        css = tmp_path / "test.css"
        css.write_text("""
[data-color-scheme="duo"] {
  --bg-zettel: #fff;
  --text-primary: #333;
}
[data-color-scheme="duo"][data-theme="dark"] {
  --bg-zettel: #111;
  --text-primary: #eee;
}
""")
        result = parse_scheme_file(css)
        assert "duo" in result
        assert "duo__dark" in result
        assert result["duo"]["--bg-zettel"] == "#fff"
        assert result["duo__dark"]["--bg-zettel"] == "#111"

    def test_ignores_non_variable_lines(self, tmp_path):
        css = tmp_path / "test.css"
        css.write_text("""
/* comment */
[data-color-scheme="x"] {
  color-scheme: light;
  --bg-page: #abc;
}
""")
        result = parse_scheme_file(css)
        assert list(result["x"].keys()) == ["--bg-page"]

    def test_real_scheme_file(self):
        """Parse an actual scheme file from the repo."""
        real = (
            Path(__file__).resolve().parents[2]
            / "mkdocs_zettelkasten"
            / "themes"
            / "zettelkasten"
            / "css"
            / "schemes"
            / "vesper.css"
        )
        if not real.exists():
            pytest.skip("vesper.css not in worktree")
        result = parse_scheme_file(real)
        assert "vesper" in result
        assert "vesper__dark" in result
        assert result["vesper"]["--text-primary"] == "#3b3228"
        assert result["vesper__dark"]["--text-primary"] == "#b2b2b2"
