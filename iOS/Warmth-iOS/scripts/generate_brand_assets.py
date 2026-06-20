#!/usr/bin/env python3
"""Generate Warmth brand PNGs by recoloring the original sun-runner artwork."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Install Pillow: python3 -m venv .venv-brand && .venv-brand/bin/pip install pillow", file=sys.stderr)
    sys.exit(1)

REPO = Path(__file__).resolve().parent.parent
ROOT = REPO / "Warmth-iOS" / "Warmth" / "Resources"
BRAND = ROOT / "Brand"
REFERENCE = BRAND / "reference" / "original-monochrome.png"
ASSETS = ROOT / "Assets.xcassets"
WATCH_ASSETS = REPO / "Warmth-iOS" / "WarmthWatch" / "Resources" / "Assets.xcassets"

# Warmth palette (matches WarmthColor.swift)
WARM_WHITE = (0xFB, 0xF8, 0xF5)
INK = (0x0B, 0x0B, 0x0C)
EMBER_RED = (0xFF, 0x2D, 0x1A)
EMBER_ORANGE = (0xFF, 0x5A, 0x2C)
AMBER = (0xFF, 0x9A, 0x3D)


def _lerp(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    return tuple(int(c1[i] + t * (c2[i] - c1[i])) for i in range(3))


def _ember_gradient(y: int, height: int) -> tuple[int, int, int]:
    """Top-leading ember red → bottom-trailing amber, like WarmthColor.emberGradient."""
    t = y / max(height - 1, 1)
    if t <= 0.5:
        return _lerp(EMBER_RED, EMBER_ORANGE, t * 2)
    return _lerp(EMBER_ORANGE, AMBER, (t - 0.5) * 2)


def _character_mask(source: Image.Image, radius: int = 4, feature_radius: int = 14) -> tuple[list[list[bool]], list[list[bool]]]:
    """Stroke mask (for white character) and wider feature mask (for eyes/mouth)."""
    width, height = source.size
    pixels = source.load()
    white = [[False] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a and r + g + b > 620:
                white[y][x] = True

    def dilate(source_mask: list[list[bool]], r: int) -> list[list[bool]]:
        out = [[False] * width for _ in range(height)]
        for y in range(height):
            for x in range(width):
                if not source_mask[y][x]:
                    continue
                for dy in range(-r, r + 1):
                    ny = y + dy
                    if ny < 0 or ny >= height:
                        continue
                    for dx in range(-r, r + 1):
                        nx = x + dx
                        if 0 <= nx < width:
                            out[ny][nx] = True
        return out

    return dilate(white, radius), dilate(white, feature_radius)


def _near_white_stroke(pixels, x: int, y: int, width: int, height: int, radius: int = 6) -> bool:
    """True if pixel is part of the stroke or its anti-aliased halo."""
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                r, g, b, _ = pixels[nx, ny]
                if r + g + b > 480:
                    return True
    return False
def _is_face_feature(pixels, x: int, y: int, width: int, height: int, radius: int = 4) -> bool:
    """Eyes/mouth sit inside white fill — more white than dark neighbors, unlike the outer contour."""
    white_neighbors = 0
    dark_neighbors = 0
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                r, g, b, _ = pixels[nx, ny]
                total = r + g + b
                if total > 500:
                    white_neighbors += 1
                elif total < 40:
                    dark_neighbors += 1
    return white_neighbors >= 10 and white_neighbors > dark_neighbors * 2


def recolor_original(source: Path) -> Image.Image:
    """Map original black/white artwork to Warmth app colours, preserving exact edges."""
    img = Image.open(source).convert("RGBA")
    pixels = img.load()
    width, height = img.size
    output = Image.new("RGBA", (width, height))
    out_pixels = output.load()

    # Sun face region — restrict ink to eyes/mouth only, not stroke edges
    face_y0, face_y1 = int(height * 0.10), int(height * 0.36)
    face_x0, face_x1 = int(width * 0.20), int(width * 0.80)

    for y in range(height):
        ember = _ember_gradient(y, height)
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                out_pixels[x, y] = (0, 0, 0, 0)
                continue

            luminance = (r + g + b) / (3 * 255)
            near_stroke = _near_white_stroke(pixels, x, y, width, height)
            in_sun_face = face_y0 <= y <= face_y1 and face_x0 <= x <= face_x1

            if (
                in_sun_face
                and luminance <= 0.08
                and _is_face_feature(pixels, x, y, width, height)
            ):
                strength = min(1.0, max(0.0, (0.08 - luminance) / 0.08))
                color = _lerp(WARM_WHITE, INK, strength)
            elif near_stroke:
                color = WARM_WHITE
            else:
                color = ember

            out_pixels[x, y] = (*color, a)

    return output


def save_png(img: Image.Image, size: int, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    resized = img.resize((size, size), Image.Resampling.LANCZOS)
    resized.save(out_path, format="PNG", optimize=True)


def write_svg_wrapper(png_path: Path, svg_path: Path) -> None:
    """Embed the recolored raster in SVG for design-tool compatibility."""
    import base64

    data = base64.b64encode(png_path.read_bytes()).decode("ascii")
    svg_path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 736 736">
  <title>Warmth sun-runner (Warmth palette recolor of original artwork)</title>
  <image width="736" height="736" xlink:href="data:image/png;base64,{data}"/>
</svg>
""",
        encoding="utf-8",
    )


IOS_ICON_SIZES = [
    ("ios-marketing", "1024x1024", "1x", 1024),
    ("iphone", "60x60", "2x", 120),
    ("iphone", "60x60", "3x", 180),
    ("iphone", "40x40", "2x", 80),
    ("iphone", "40x40", "3x", 120),
    ("iphone", "29x29", "2x", 58),
    ("iphone", "29x29", "3x", 87),
    ("iphone", "20x20", "2x", 40),
    ("iphone", "20x20", "3x", 60),
    ("ipad", "76x76", "1x", 76),
    ("ipad", "76x76", "2x", 152),
    ("ipad", "83.5x83.5", "2x", 167),
    ("ipad", "40x40", "1x", 40),
    ("ipad", "40x40", "2x", 80),
    ("ipad", "29x29", "1x", 29),
    ("ipad", "29x29", "2x", 58),
    ("ipad", "20x20", "1x", 20),
    ("ipad", "20x20", "2x", 40),
]

WATCH_ICON_SIZES = [
    ("watchos-marketing", "1024x1024", "1x", 1024),
    ("watch", "46x46", "2x", 92),
    ("watch", "45x45", "2x", 90),
    ("watch", "44x44", "2x", 88),
    ("watch", "42x42", "2x", 84),
    ("watch", "41x41", "2x", 82),
    ("watch", "40x40", "2x", 80),
    ("watch", "38x38", "2x", 76),
    ("watch", "24x24", "2x", 48),
    ("watch", "27.5x27.5", "2x", 55),
    ("watch", "33x33", "2x", 66),
    ("watch", "29x29", "2x", 58),
]


def write_appiconset(base: Path, sizes: list[tuple[str, str, str, int]], master: Image.Image) -> None:
    iconset = base / "AppIcon.appiconset"
    iconset.mkdir(parents=True, exist_ok=True)
    images: list[dict[str, str]] = []

    for idiom, size, scale, px in sizes:
        if idiom in {"ios-marketing", "watchos-marketing"}:
            filename = f"AppIcon-{idiom}.png"
        else:
            filename = f"AppIcon-{size}@{scale}.png"
        save_png(master, px, iconset / filename)
        images.append({"filename": filename, "idiom": idiom, "scale": scale, "size": size})

    (iconset / "Contents.json").write_text(json.dumps({"images": images, "info": {"author": "xcode", "version": 1}}, indent=2) + "\n", encoding="utf-8")


def write_accent_color() -> None:
    colorset = ASSETS / "AccentColor.colorset"
    colorset.mkdir(parents=True, exist_ok=True)
    contents = {
        "colors": [
            {
                "color": {
                    "color-space": "srgb",
                    "components": {"alpha": "1.000", "blue": "0.102", "green": "0.176", "red": "1.000"},
                },
                "idiom": "universal",
            }
        ],
        "info": {"author": "xcode", "version": 1},
    }
    (colorset / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n", encoding="utf-8")


def write_assets_catalog(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "Contents.json").write_text(
        json.dumps({"info": {"author": "xcode", "version": 1}}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    if not REFERENCE.exists():
        print(f"Missing reference artwork: {REFERENCE}", file=sys.stderr)
        return 1

    master = recolor_original(REFERENCE)

    exports = BRAND / "exports"
    master_1024 = exports / "warmth-app-icon-1024.png"
    master_512 = exports / "warmth-app-icon-512.png"
    master_source = BRAND / "warmth-sun-runner.png"

    save_png(master, 1024, master_1024)
    save_png(master, 512, master_512)
    save_png(master, 736, master_source)
    write_svg_wrapper(master_source, BRAND / "warmth-sun-runner.svg")

    write_assets_catalog(ASSETS)
    write_accent_color()
    write_appiconset(ASSETS, IOS_ICON_SIZES, master)

    write_assets_catalog(WATCH_ASSETS)
    write_appiconset(WATCH_ASSETS, WATCH_ICON_SIZES, master)

    print("Recolored original artwork → ember background, warm white character, ink eyes")
    print(f"Exports: {exports}")
    print(f"iOS AppIcon: {ASSETS / 'AppIcon.appiconset'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
