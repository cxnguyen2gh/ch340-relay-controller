#-----------------------------------------------------------------------------
#                        Proprietary - Export Controlled
#
# Descriptions:
#   Generates relay_icon.png and relay_icon.ico.
#   Requires: Pillow  (pip install pillow)
#
# Author: Chinh Nguyen
#-----------------------------------------------------------------------------

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Pillow not found. Run:  pip install pillow")
    sys.exit(1)

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

ICON_SIZE   = 512
BG_COLOR    = (30,  30,  30)
PANEL_COLOR = (54,  54,  54)
LED_ON      = (214, 34,  34)
LED_DARK    = (125, 18,  18)
LED_HIGH    = (255, 92,  92)
SWITCH_CLR  = (248, 248, 248)
SWITCH_SHA  = (205, 205, 205)
BORDER_CLR  = (90,  90,  90)

OUT_FILE    = Path(__file__).parent / "relay_icon.png"
ICO_FILE    = Path(__file__).parent / "relay_icon.ico"


#-----------------------------------------------------------------------------
# Draw a filled anti-aliased circle on the given draw context
#-----------------------------------------------------------------------------
def draw_circle(draw, cx, cy, radius, color):
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=color,
    )


#-----------------------------------------------------------------------------
# Build and save the relay icon PNG
#-----------------------------------------------------------------------------
def build_icon():
    scale   = 2                          # 2x for anti-alias downsample
    sz      = ICON_SIZE * scale
    img     = Image.new("RGB", (sz, sz), BG_COLOR)
    draw    = ImageDraw.Draw(img)

    margin  = int(0.06 * sz)
    corner  = int(0.12 * sz)
    draw.rounded_rectangle(
        [margin, margin, sz - margin, sz - margin],
        radius=corner,
        fill=PANEL_COLOR,
        outline=BORDER_CLR,
        width=int(0.01 * sz),
    )

    cx = sz // 2
    cy = sz // 2
    led_r = int(0.31 * sz)

    for glow_r, alpha in [(led_r + 58, 34), (led_r + 30, 62)]:
        glow_img = Image.new("RGB", (sz, sz), PANEL_COLOR)
        glow_draw = ImageDraw.Draw(glow_img)
        draw_circle(glow_draw, cx, cy, glow_r, LED_ON)
        img = Image.blend(img, glow_img, alpha / 255)
        draw = ImageDraw.Draw(img)

    draw_circle(draw, cx, cy, led_r, LED_DARK)
    draw_circle(draw, cx, cy, int(led_r * 0.88), LED_ON)

    draw_circle(
        draw,
        cx - int(led_r * 0.28),
        cy - int(led_r * 0.30),
        int(led_r * 0.28),
        LED_HIGH,
    )

    sw_w = int(0.16 * sz)
    sw_h = int(0.46 * sz)
    sw_rad = int(0.06 * sz)
    draw.rounded_rectangle(
        [cx - sw_w // 2, cy - sw_h // 2,
         cx + sw_w // 2, cy + sw_h // 2],
        radius=sw_rad,
        fill=SWITCH_SHA,
    )
    draw.rounded_rectangle(
        [cx - sw_w // 2, cy - sw_h // 2 - int(0.012 * sz),
         cx + sw_w // 2, cy + sw_h // 2 - int(0.012 * sz)],
        radius=sw_rad,
        fill=SWITCH_CLR,
    )

    # Downsample for anti-aliasing
    img = img.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
    img.save(OUT_FILE)
    img.save(ICO_FILE, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    print(f"Icon saved: {OUT_FILE}")
    print(f"Icon saved: {ICO_FILE}")


if __name__ == "__main__":
    build_icon()
