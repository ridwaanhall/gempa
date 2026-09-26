"""Generate the 1200x630 Open Graph image (app/static/img/og.png).

Run: uv run --with pillow python scripts/make_og.py [--font-dir DIR]

Uses Plus Jakarta Sans / JetBrains Mono TTFs if found in --font-dir, else
falls back to system fonts. Output is committed; re-run only to change it.
"""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1200, 630
CLAY = (231, 225, 216)
WELL = (221, 214, 203)
HI = (255, 252, 246)
LO = (170, 152, 128)
INK = (42, 36, 29)
INK_3 = (98, 88, 73)
ACCENT = (194, 65, 12)
RAMP = [(232, 177, 12), (240, 140, 26), (208, 70, 26), (179, 32, 47), (110, 20, 38)]

DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVu"
WIN = "C:/Windows/Fonts/"
OUT = Path(__file__).resolve().parent.parent / "app" / "static" / "img" / "og.png"


def font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def soft_shape(
    base: Image.Image, box, radius: int, *, inset: bool = False, offset: int = 14
) -> None:
    """Draw a neumorphic raised (or inset) rounded shape onto `base`."""
    for colour, dx in ((LO, offset), (HI, -offset)):
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        shift = -dx if inset else dx
        x0, y0, x1, y1 = box
        moved = (x0 + shift, y0 + shift, x1 + shift, y1 + shift)
        d.rounded_rectangle(moved, radius, fill=(*colour, 170))
        layer = layer.filter(ImageFilter.GaussianBlur(offset))
        base.alpha_composite(layer)
    ImageDraw.Draw(base).rounded_rectangle(box, radius, fill=(*(WELL if inset else CLAY), 255))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--font-dir", default="")
    args = parser.parse_args()
    fd = Path(args.font_dir) if args.font_dir else None

    def pick(bundled: str, *system: str) -> list[str]:
        return ([str(fd / bundled)] if fd else []) + list(system)

    bold = pick("PlusJakartaSans-ExtraBold.ttf", WIN + "segoeuib.ttf", DEJAVU + "Sans-Bold.ttf")
    regular = pick("PlusJakartaSans-Medium.ttf", WIN + "segoeui.ttf", DEJAVU + "Sans.ttf")
    monos = pick("JetBrainsMono-Bold.ttf", WIN + "consolab.ttf", DEJAVU + "SansMono-Bold.ttf")
    sans_bold, sans, mono = font(bold, 88), font(regular, 34), font(monos, 30)

    img = Image.new("RGBA", (W, H), (*CLAY, 255))

    # Raised card
    soft_shape(img, (60, 60, W - 60, H - 60), 44)

    # Dial: raised disc, inset well, magnitude arc
    cx, cy, r = 920, 315, 170
    soft_shape(img, (cx - r, cy - r, cx + r, cy + r), r)
    soft_shape(img, (cx - 118, cy - 118, cx + 118, cy + 118), 118, inset=True, offset=8)
    d = ImageDraw.Draw(img)
    arc_box = (cx - 148, cy - 148, cx + 148, cy + 148)
    d.arc(arc_box, 135, 405, fill=WELL, width=18)
    # Ramp-coloured arc segments up to ~M7
    start = 135
    for colour in RAMP:
        d.arc(arc_box, start, start + 42, fill=colour, width=18)
        start += 42
    num = font(monos, 96)
    d.text((cx, cy - 6), "M7", font=num, fill=INK, anchor="mm")
    d.text((cx, cy + 62), "magnitudo", font=sans, fill=INK_3, anchor="mm")

    # Seismograph glyph + wordmark
    pts = [
        (130, 190), (165, 190), (178, 160), (196, 232),
        (214, 142), (232, 208), (246, 186), (282, 186),
    ]  # fmt: skip
    d.line(pts, fill=ACCENT, width=9, joint="curve")
    d.text((126, 250), "Gempa", font=sans_bold, fill=INK, anchor="lt")
    d.text((130, 362), "Monitor gempa bumi Indonesia", font=sans, fill=INK, anchor="lt")
    d.text((130, 408), "Realtime · dirasakan · M5+ · tsunami", font=sans, fill=INK_3, anchor="lt")
    d.text((130, 492), "Data resmi BMKG", font=mono, fill=ACCENT, anchor="lt")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
