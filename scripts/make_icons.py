"""Generate favicons from the navbar's seismograph mark, so tab icon and header match.

Run: uv run --with pillow python scripts/make_icons.py

Writes app/static/img/: favicon.svg, favicon.ico (16/32/48), favicon-16x16.png,
favicon-32x32.png, apple-touch-icon.png (180), android-chrome-192x192.png,
android-chrome-512x512.png.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parent.parent / "app" / "static" / "img"
CLAY = (231, 225, 216)
HI = (255, 252, 246)
LO = (170, 152, 128)
ACCENT = (194, 65, 12)

# Same polyline as the header brand: <path d="M1 9h6l2-5 3 12 3-15 3 11 2-3h7"> in a 28x18 box.
MARK = [(1, 9), (7, 9), (9, 4), (12, 16), (15, 1), (18, 12), (20, 9), (27, 9)]


def _mark_points(size: float, pad: float) -> tuple[list[tuple[float, float]], float]:
    scale = (size - 2 * pad) / 26  # mark spans x 1..27
    height = 15 * scale  # mark spans y 1..16
    top = (size - height) / 2
    return [(pad + (x - 1) * scale, top + (y - 1) * scale) for x, y in MARK], scale


def svg() -> str:
    points, scale = _mark_points(64, 9)
    d = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in points)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" rx="16" fill="#e7e1d8"/>'
        f'<path d="{d}" fill="none" stroke="#c2410c" stroke-width="{2.4 * scale:.2f}" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>\n'
    )


def raster(
    size: int, *, rounded: bool = True, stroke: float = 2.4, raised: bool = False
) -> Image.Image:
    """Render at 8x size and downsample for smooth edges."""
    big = size * 8
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    radius = big // 4 if rounded else 0
    if raised:
        # Soft neumorphic disc behind the mark on large icons.
        img.paste((*CLAY, 255), (0, 0, big, big))
        for colour, dx in ((LO, big // 40), (HI, -big // 40)):
            layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            inset = big // 6
            ImageDraw.Draw(layer).ellipse(
                (inset + dx, inset + dx, big - inset + dx, big - inset + dx), fill=(*colour, 150)
            )
            img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(big // 30)))
        ImageDraw.Draw(img).ellipse((big // 6, big // 6, big - big // 6, big - big // 6), fill=CLAY)
        pad = big * 0.27
    else:
        ImageDraw.Draw(img).rounded_rectangle((0, 0, big - 1, big - 1), radius, fill=(*CLAY, 255))
        pad = big * 0.14
    points, scale = _mark_points(big, pad)
    width = max(1, round(stroke * scale))
    draw = ImageDraw.Draw(img)
    draw.line(points, fill=ACCENT, width=width, joint="curve")
    r = width / 2
    for x, y in (points[0], points[-1]):
        draw.ellipse((x - r, y - r, x + r, y + r), fill=ACCENT)
    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "favicon.svg").write_text(svg(), encoding="utf-8")
    # Tiny sizes get a thicker stroke so the mark survives downscaling.
    raster(16, stroke=3.4).save(OUT / "favicon-16x16.png")
    raster(32, stroke=3).save(OUT / "favicon-32x32.png")
    raster(48, stroke=2.8).save(
        OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)],
        append_images=[raster(16, stroke=3.4), raster(32, stroke=3)],
    )  # fmt: skip
    raster(180, rounded=False, raised=True).convert("RGB").save(OUT / "apple-touch-icon.png")
    for size in (192, 512):
        raster(size, rounded=False, raised=True).convert("RGB").save(
            OUT / f"android-chrome-{size}x{size}.png"
        )
    print("icons written to", OUT)


if __name__ == "__main__":
    main()
