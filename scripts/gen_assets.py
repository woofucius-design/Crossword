"""
Generates every app icon / splash asset from one vector-ish definition,
so the brand mark lives in version control as code rather than as opaque
binaries.

The mark: a 3x3 crossword fragment in the app's own palette — cream
cells, two black squares placed with real 180-degree crossword symmetry,
and one gold "selected" cell matching colors.cellSelected in the app.

  python3 scripts/gen_assets.py

Outputs to assets/:
  icon.png              1024  iOS + fallback app icon (opaque navy)
  adaptive-icon.png     1024  Android adaptive FOREGROUND (transparent,
                              art kept inside the 66% mask safe zone)
  monochrome-icon.png   1024  Android 13+ themed icon (white silhouette)
  splash-icon.png       1024  expo-splash-screen mark (transparent)
  notification-icon.png   96  Android status-bar icon (white silhouette)
  favicon.png             48  web
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

# Palette mirrors src/theme/tokens.ts
NAVY = (13, 27, 42, 255)        # colors.bg        #0D1B2A
CREAM = (248, 245, 238, 255)    # colors.cellBg    #F8F5EE
GOLD = (255, 216, 76, 255)      # colors.cellSelected #FFD84C
BLACK_SQ = (26, 26, 26, 255)    # colors.cellBlack #1a1a1a
WHITE = (255, 255, 255, 255)

# 3x3 crossword fragment. '#' = black square, '*' = selected (gold).
# The two black squares are 180-degree rotationally symmetric, the way a
# real crossword grid must be.
PATTERN = [
    "..#",
    ".*.",
    "#..",
]

SS = 4  # supersample factor for antialiasing


def draw_mark(size: int, *, scale: float, background, cell_colors) -> Image.Image:
    """Render the mark on a `size` square. `scale` is the fraction of the
    canvas the grid occupies — smaller for adaptive icons, whose corners
    get masked away by the launcher."""
    S = size * SS
    img = Image.new("RGBA", (S, S), background)
    d = ImageDraw.Draw(img)

    grid = S * scale
    gap = grid * 0.055
    cell = (grid - gap * 2) / 3
    radius = cell * 0.16
    x0 = (S - grid) / 2
    y0 = (S - grid) / 2

    for r, row in enumerate(PATTERN):
        for c, ch in enumerate(row):
            color = cell_colors[ch]
            if color is None:
                continue
            left = x0 + c * (cell + gap)
            top = y0 + r * (cell + gap)
            d.rounded_rectangle(
                [left, top, left + cell, top + cell],
                radius=radius,
                fill=color,
            )
    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(exist_ok=True)

    full_colors = {".": CREAM, "#": BLACK_SQ, "*": GOLD}
    # On a themed/monochrome icon everything is one colour, so the black
    # squares must become holes or the mark reads as a solid block.
    mono_colors = {".": WHITE, "#": None, "*": WHITE}

    # iOS / general icon: opaque navy, art fills more of the tile because
    # only the corners get rounded.
    draw_mark(1024, scale=0.62, background=NAVY,
              cell_colors=full_colors).save(OUT / "icon.png")

    # Android adaptive foreground: transparent, and the art must survive
    # an aggressive circular mask, so it sits well inside the safe zone.
    draw_mark(1024, scale=0.46, background=(0, 0, 0, 0),
              cell_colors=full_colors).save(OUT / "adaptive-icon.png")

    draw_mark(1024, scale=0.46, background=(0, 0, 0, 0),
              cell_colors=mono_colors).save(OUT / "monochrome-icon.png")

    draw_mark(1024, scale=0.55, background=(0, 0, 0, 0),
              cell_colors=full_colors).save(OUT / "splash-icon.png")

    # Android notification icons are drawn as a white-on-transparent
    # silhouette; anything else shows up as a grey blob.
    draw_mark(96, scale=0.82, background=(0, 0, 0, 0),
              cell_colors=mono_colors).save(OUT / "notification-icon.png")

    draw_mark(48, scale=0.72, background=NAVY,
              cell_colors=full_colors).save(OUT / "favicon.png")

    for p in sorted(OUT.glob("*.png")):
        with Image.open(p) as im:
            print(f"  {p.name:<24} {im.size[0]}x{im.size[1]} {im.mode}")


if __name__ == "__main__":
    main()
