"""Crop the Lightfern glyph out of the supplied wordmark and emit assets:

- lightfern.png        : white glyph on transparent (for dark UI)
- lightfern-dark.png   : original dark glyph on transparent (for light UI)

The glyph is the first cluster of dark pixels on the left, separated from the
"Lightfern" text by a whitespace gap.
"""
from PIL import Image

SRC = "/Users/nicho/.cursor/projects/Users-nicho-Documents-gtmhackathon/assets/Screenshot_2026-06-20_at_14.48.12-6948bd4a-be9c-4f12-9886-cb0fb935084f.png"
OUT_DIR = "/Users/nicho/Documents/gtmhackathon/web/public/logos"

img = Image.open(SRC).convert("RGBA")
w, h = img.size
gray = img.convert("L")
px = gray.load()

DARK = 130  # luminance threshold for "ink"

# Dark-pixel count per column
col_dark = []
for x in range(w):
    c = sum(1 for y in range(h) if px[x, y] < DARK)
    col_dark.append(c)

# First dark column
first = next((x for x in range(w) if col_dark[x] > 0), 0)
# End of the first cluster: first column after `first` with a sustained gap
end = first
gap = 0
for x in range(first, w):
    if col_dark[x] == 0:
        gap += 1
        if gap >= 6:  # whitespace between glyph and the word
            break
    else:
        gap = 0
        end = x
glyph_right = end + 1

# Vertical bounds of the glyph within [first, glyph_right]
rows = [y for y in range(h) for x in range(first, glyph_right) if px[x, y] < DARK]
top, bottom = (min(rows), max(rows) + 1) if rows else (0, h)

pad = 4
left = max(0, first - pad)
right = min(w, glyph_right + pad)
top = max(0, top - pad)
bottom = min(h, bottom + pad)

crop = img.crop((left, top, right, bottom))
cw, ch = crop.size
size = max(cw, ch)

def make(square_fill_white: bool):
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    src = crop.load()
    out = canvas.load()
    ox, oy = (size - cw) // 2, (size - ch) // 2
    for y in range(ch):
        for x in range(cw):
            r, g, b, a = src[x, y]
            lum = (r + g + b) / 3
            alpha = int(max(0, min(255, 255 - lum)))  # dark -> opaque
            if alpha < 12:
                continue
            color = (255, 255, 255) if square_fill_white else (26, 22, 18)
            out[ox + x, oy + y] = (*color, alpha)
    return canvas

make(True).save(f"{OUT_DIR}/lightfern.png")
make(False).save(f"{OUT_DIR}/lightfern-dark.png")
print(f"glyph bbox: x[{left}:{right}] y[{top}:{bottom}] -> {size}x{size}")
