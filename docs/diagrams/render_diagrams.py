#!/usr/bin/env python3
"""Render Mermaid .mmd files to SVG (primary) and PNG (fallback) via Chrome headless."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

DIAGRAMS_DIR = Path(__file__).parent
TEMPLATE = DIAGRAMS_DIR / "render-template.html"
SVG_DIR = DIAGRAMS_DIR / "svg"
PNG_DIR = DIAGRAMS_DIR / "png"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MIN_SVG_WIDTH = 500


def parse_viewbox(svg_text: str) -> tuple[float, float]:
    """Return rendered width/height from SVG attributes or viewBox."""
    width_match = re.search(r'\bwidth="([\d.]+)', svg_text)
    height_match = re.search(r'\bheight="([\d.]+)', svg_text)
    if width_match and height_match:
        return float(width_match.group(1)), float(height_match.group(1))

    viewbox_match = re.search(r'viewBox="[\d.\s-]+?\s+([\d.]+)\s+([\d.]+)"', svg_text)
    if viewbox_match:
        return float(viewbox_match.group(1)), float(viewbox_match.group(2))

    raise ValueError("Could not determine SVG dimensions")


def extract_svg(dump_html: str) -> str:
    match = re.search(r'(<svg[\s\S]*?</svg>)', dump_html)
    if not match:
        raise ValueError("No SVG found in rendered DOM")
    return match.group(1)


def normalize_svg(svg_text: str) -> str:
    """Set explicit pixel dimensions from viewBox so PDF embeds scale correctly."""
    viewbox_match = re.search(r'viewBox="\s*[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)\s*"', svg_text)
    if not viewbox_match:
        return svg_text

    width, height = viewbox_match.group(1), viewbox_match.group(2)
    svg_text = re.sub(r'\sstyle="[^"]*"', "", svg_text, count=1)
    if re.search(r'\bwidth="', svg_text):
        svg_text = re.sub(r'\bwidth="[^"]*"', f'width="{width}"', svg_text, count=1)
    else:
        svg_text = svg_text.replace("<svg ", f'<svg width="{width}" ', 1)
    if re.search(r'\bheight="', svg_text):
        svg_text = re.sub(r'\bheight="[^"]*"', f'height="{height}"', svg_text, count=1)
    else:
        svg_text = svg_text.replace("<svg ", f'<svg height="{height}" ', 1)
    return svg_text


def render_one(name: str, source: str) -> tuple[Path, Path]:
    page = TEMPLATE.read_text(encoding="utf-8").replace("DIAGRAM_PLACEHOLDER", source.strip())

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tmp:
        tmp.write(page)
        html_path = Path(tmp.name)

    svg_out = SVG_DIR / f"{name}.svg"
    png_out = PNG_DIR / f"{name}.png"

    dump_cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--virtual-time-budget=20000",
        "--dump-dom",
        html_path.as_uri(),
    ]
    dump_result = subprocess.run(dump_cmd, capture_output=True, text=True, timeout=90)
    html_path.unlink(missing_ok=True)

    if dump_result.returncode != 0:
        raise RuntimeError(dump_result.stderr.strip() or dump_result.stdout.strip())
    if not dump_result.stdout.strip():
        raise RuntimeError("Chrome dump-dom produced no output")

    svg_text = normalize_svg(extract_svg(dump_result.stdout))
    svg_out.write_text(svg_text, encoding="utf-8")

    width, height = parse_viewbox(svg_text)
    if width < MIN_SVG_WIDTH:
        raise ValueError(f"SVG too narrow ({width:.0f}px) — likely failed render")

    pad = 48
    win_w = min(int(width) + pad, 4000)
    win_h = min(int(height) + pad, 4000)

    shot_cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={win_w},{win_h}",
        "--force-device-scale-factor=2",
        "--virtual-time-budget=20000",
        f"--screenshot={png_out}",
        svg_out.as_uri(),
    ]
    shot_result = subprocess.run(shot_cmd, capture_output=True, text=True, timeout=90)
    if shot_result.returncode != 0 or not png_out.exists():
        # PNG is optional; SVG is the PDF source of truth
        png_out = svg_out

    return svg_out, png_out


def verify_outputs() -> list[str]:
    issues: list[str] = []
    for svg_path in sorted(SVG_DIR.glob("*.svg")):
        text = svg_path.read_text(encoding="utf-8")
        try:
            width, height = parse_viewbox(text)
        except ValueError as exc:
            issues.append(f"{svg_path.name}: {exc}")
            continue
        if width < MIN_SVG_WIDTH or height < 120:
            issues.append(f"{svg_path.name}: dimensions {width:.0f}x{height:.0f} too small")
    return issues


def main() -> int:
    if not Path(CHROME).exists():
        print("Chrome not found", file=sys.stderr)
        return 1

    SVG_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)

    mmd_files = sorted(DIAGRAMS_DIR.glob("*.mmd"))
    failed = 0
    manifest: dict[str, dict[str, str | float]] = {}

    for path in mmd_files:
        name = path.stem
        try:
            svg_out, png_out = render_one(name, path.read_text(encoding="utf-8"))
            w, h = parse_viewbox(svg_out.read_text(encoding="utf-8"))
            manifest[name] = {
                "svg": svg_out.name,
                "png": png_out.name,
                "width": w,
                "height": h,
            }
            print(f"OK  {name} -> {svg_out.name} ({w:.0f}x{h:.0f}px)")
        except Exception as exc:  # noqa: BLE001
            print(f"ERR {name}: {exc}", file=sys.stderr)
            failed += 1

    (SVG_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    issues = verify_outputs()
    for issue in issues:
        print(f"VERIFY {issue}", file=sys.stderr)
        failed += 1

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
