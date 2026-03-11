#!/usr/bin/env python3
"""
Generate AuraSafe app icon (1024x1024 PNG).
Run from the project root: python scripts/generate_icon.py
Requires: Pillow
"""
import os
import math
from PIL import Image, ImageDraw, ImageFilter

SIZE = 1024
OUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_rgb(c1: tuple, c2: tuple, t: float) -> tuple:
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def main():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Background: dark navy gradient ──────────────────────────────────────
    top_col = (13, 13, 26)    # #0D0D1A
    bot_col = (20, 20, 45)
    for y in range(SIZE):
        t = y / (SIZE - 1)
        col = lerp_rgb(top_col, bot_col, t) + (255,)
        draw.line([(0, y), (SIZE - 1, y)], fill=col)

    # Rounded corner mask
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, SIZE - 1, SIZE - 1], radius=190, fill=255
    )
    img.putalpha(mask)

    # ── Shield fill: gradient blue → teal ───────────────────────────────────
    CX, CY = SIZE // 2, SIZE // 2 - 5
    SW, SH = 590, 670

    top_y = CY - SH // 2
    mid_y = CY + int(SH * 0.12)
    bot_y = CY + SH // 2
    lx    = CX - SW // 2
    rx    = CX + SW // 2

    shield_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sl_draw = ImageDraw.Draw(shield_layer)

    for row in range(top_y, bot_y + 1):
        t = (row - top_y) / max(bot_y - top_y, 1)
        # #1A237E → #00838F
        col = lerp_rgb((26, 35, 126), (0, 131, 143), t) + (245,)

        if row <= mid_y:
            xl, xr = lx, rx
        else:
            t2 = (row - mid_y) / max(bot_y - mid_y, 1)
            xl = int(lerp(lx, CX, t2))
            xr = int(lerp(rx, CX, t2))

        if xr > xl:
            sl_draw.line([(xl, row), (xr, row)], fill=col)

    shield_layer = shield_layer.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, shield_layer)

    # ── Shield highlight: top-left soft white glow ──────────────────────────
    hl = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse(
        [lx + 20, top_y + 20, CX + 60, CY - 50],
        fill=(255, 255, 255, 22),
    )
    hl = hl.filter(ImageFilter.GaussianBlur(35))
    img = Image.alpha_composite(img, hl)

    # ── Cyan glow halo behind cross ──────────────────────────────────────────
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gr = 185
    ImageDraw.Draw(glow).ellipse(
        [CX - gr, CY - gr - 15, CX + gr, CY + gr - 15],
        fill=(0, 188, 212, 60),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img = Image.alpha_composite(img, glow)

    # ── Shield outline: cyan border ──────────────────────────────────────────
    outline_poly = [
        (lx + 25, top_y),
        (rx - 25, top_y),
        (rx,      top_y + 25),
        (rx,      mid_y),
        (CX,      bot_y),
        (lx,      mid_y),
        (lx,      top_y + 25),
    ]
    for thickness, alpha in [(6, 200), (12, 80), (20, 30)]:
        ol = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        ol_draw = ImageDraw.Draw(ol)
        # Expand polygon outward by `thickness`
        expanded = []
        for px, py in outline_poly:
            dx = px - CX
            dy = py - CY
            dist = math.hypot(dx, dy) or 1
            expanded.append((px + dx / dist * thickness, py + dy / dist * thickness))
        ol_draw.polygon(expanded, outline=(0, 188, 212, alpha))
        img = Image.alpha_composite(img, ol)

    # ── Medical cross (white) ────────────────────────────────────────────────
    cross_layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    cl = ImageDraw.Draw(cross_layer)
    ccx, ccy = CX, CY - 20   # cross center
    arm = 125   # arm half-length
    cw  = 46    # bar half-width
    # Horizontal bar
    cl.rectangle([ccx - arm, ccy - cw, ccx + arm, ccy + cw], fill=(255, 255, 255, 255))
    # Vertical bar
    cl.rectangle([ccx - cw, ccy - arm, ccx + cw, ccy + arm], fill=(255, 255, 255, 255))
    img = Image.alpha_composite(img, cross_layer)

    # ── Small cyan dot at bottom of shield ───────────────────────────────────
    dot = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(dot).ellipse(
        [CX - 22, bot_y - 70, CX + 22, bot_y - 26],
        fill=(0, 188, 212, 220),
    )
    img = Image.alpha_composite(img, dot)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    img.save(OUT_PATH, "PNG")
    print(f"Icon saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
