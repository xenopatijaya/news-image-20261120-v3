#!/usr/bin/env python3
"""THE WORLD IN ONE DAY - Friday 20 November 2026 (edition v3).

Build-time drawing program: draws a single-image front page
(1024x1024 PNG) summing up the world's news of Friday 20 November
2026, and writes it as entry.png inside the make.fun output
directory (MAKEFUN_OUTPUT_DIR, default /output). This file is NOT
run by the grader; the runtime entrypoint is main.py, which simply
copies the entry.png produced by this program and committed in the
repo.

Edition v3 keeps the v2 page structure and every story identical;
what changes is the drawing itself: textured paper, layered and
shaded lead illustrations, illustrated mini-scenes on every feature
card, and a denser dot-matrix world map.

Python standard library + Pillow only. No network, no clock, and no
unseeded randomness (a fixed-seed LCG and integer hashes only): two
runs produce a byte-identical entry.png. The output directory
itself is never deleted; only entry.png inside it is written.
"""
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

W, H = 1024, 1024
M = 24                      # page margin
CW = W - 2 * M              # content width = 976

PAPER = (247, 241, 227)
CARD = (253, 250, 242)
SHADOW = (233, 225, 203)
INK = (26, 23, 20)
GRAY = (102, 95, 86)
LINE = (70, 62, 52)
RED = (179, 0, 27)
DARKRED = (128, 0, 20)
NAVY = (15, 25, 48)
TEAL = (10, 74, 84)
GOLD = (176, 124, 32)
GREEN = (46, 110, 52)
WHITE = (255, 255, 255)

FD = "/usr/share/fonts/truetype/dejavu"
SERIF = FD + "/DejaVuSerif.ttf"
SERIFB = FD + "/DejaVuSerif-Bold.ttf"
SANS = FD + "/DejaVuSans.ttf"
SANSB = FD + "/DejaVuSans-Bold.ttf"

_fonts = {}


def F(path, size):
    key = (path, size)
    if key not in _fonts:
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]


# ---------------------------------------------------------------- data

STATS = [
    ("300,000+", "EVACUATED BEFORE AKVAN"),
    ("~30", "MISSILES AT KYIV IN ONE NIGHT"),
    ("-4.9%", "NIKKEI 225 FALL IN TOKYO"),
    ("2.2%", "JAPAN CORE CPI, YEAR ON YEAR"),
    ("118", "PHILLIPS CENTURY, NZ v INDIA"),
    ("8 yrs", "BEPICOLOMBO VOYAGE TO MERCURY"),
]

CHIPS = [
    "ASIA-PACIFIC 11", "EUROPE 5", "MIDDLE EAST 2", "AFRICA 3",
    "AMERICAS 7", "OCEANIA 2", "WORLD & SPACE 6",
]

KICKER = ("AKVAN MAKES LANDFALL - 300,000+ EVACUATED   ///   "
          "KYIV UNDER FIRE - ~30 MISSILES   ///   "
          "ASIA STOCKS ROUT - NIKKEI -4.9%")

LEADS = [
    {
        "tag": "1 - GOPALPUR, INDIA - BAY OF BENGAL",
        "head": "Cyclone Akvan slams ashore",
        "body": ("Landfall near Gopalpur with gusts to 110 km/h. More "
                 "than 300,000 people were evacuated ahead of the storm."),
        "src": "Source: Reuters, IMD",
        "art": "akvan",
        "chip": "LANDFALL - GUSTS 110 KM/H",
    },
    {
        "tag": "2 - KYIV, UKRAINE",
        "head": "Kyiv under heaviest fire in weeks",
        "body": ("About 30 missiles in a single night; three people "
                 "killed as strikes hit homes and power sites."),
        "src": "Sources: Reuters, AP",
        "art": "kyiv",
        "chip": "~30 MISSILES - 3 KILLED",
    },
    {
        "tag": "3 - TOKYO - ASIA MARKETS",
        "head": "AI sell-off sweeps Asia",
        "body": ("Nikkei -4.9%, Kospi -5.4% and Taiex -6.8% as chip "
                 "shares lead a global technology rout."),
        "src": "Source: Reuters",
        "art": "chart",
        "chip": "",
    },
]

FEATURES = [
    {"n": 4, "tag": "SPACE - DEEP SPACE", "icon": "mercury",
     "head": "BepiColombo reaches Mercury",
     "body": "ESA-JAXA probe ends an 8-year cruise; orbit capture is set for Saturday.",
     "src": "ESA"},
    {"n": 5, "tag": "TOKYO, JAPAN", "icon": "yen",
     "head": "Japan core CPI holds at 2.2%",
     "body": "Core prices rose 2.2% in a year, matching forecasts; the BOJ watches on.",
     "src": "Reuters"},
    {"n": 6, "tag": "BEIJING, CHINA", "icon": "bank",
     "head": "China holds LPR steady",
     "body": "One-year LPR kept at 3.0% and five-year at 3.5% as policy stays put.",
     "src": "Reuters"},
    {"n": 7, "tag": "COP31 - FINAL DAY", "icon": "globe",
     "head": "Climate talks deadlocked",
     "body": "Fossil-fuel wording stalls the draft deal as the summit overruns.",
     "src": "Reuters"},
    {"n": 8, "tag": "DAKAR, SENEGAL", "icon": "boat",
     "head": "Migrant boat sinks: 4 dead",
     "body": "A pirogue capsized off the coast; rescuers search for survivors.",
     "src": "AFP"},
    {"n": 9, "tag": "ROME, ITALY", "icon": "placard",
     "head": "General strike grips Italy",
     "body": "CGIL walkout halts trains and flights in protest at the budget.",
     "src": "ANSA"},
    {"n": 10, "tag": "NEW ZEALAND", "icon": "cricket",
     "head": "Phillips smashes 118",
     "body": "Glenn Phillips' century puts New Zealand on top against India.",
     "src": "AP"},
    {"n": 11, "tag": "SAN SALVADOR", "icon": "ballot",
     "head": "Bukele files for third term",
     "body": "El Salvador's president registers to run again; assembly debates.",
     "src": "Reuters"},
    {"n": 12, "tag": "STRAIT OF HORMUZ", "icon": "tanker",
     "head": "Hormuz shut, Brent $92.50",
     "body": "Tanker traffic halted and insurers pull cover as oil jumps.",
     "src": "Bloomberg"},
    {"n": 13, "tag": "BOSTON - HEALTH", "icon": "pill",
     "head": "Cancer pill cuts tumours 60.7% [CLAIM]",
     "body": "Early trial reports pancreatic tumours shrinking by 60.7%; wider tests to come.",
     "src": "Reuters"},
]

BRIEFS = [
    "Malawi fuel crisis deepens, queues grow (Reuters)",
    "Rohingya camps react to ICJ verdict (AP)",
    "Fiona the hippo dies, Cincinnati Zoo (AP)",
    "Russell fastest in Vegas F1 practice (Reuters)",
    "Seoul: opposition files impeachment bid (Reuters)",
    "Gold closes at record $3,526 an ounce (Reuters)",
    "EU calls emergency talks on Kyiv strikes (Reuters)",
    "Aid convoys reach Akvan-hit coast (AFP)",
    "Kyiv blackouts after missile wave (AP)",
    "UN chief urges COP31 compromise (AFP)",
    "BepiColombo: capture burn due Saturday (ESA)",
    "Wall Street opens lower in AI rout (AP)",
    "Chip shares lead Asia sell-off (Bloomberg)",
    "Italy strike cancels flights, trains (ANSA)",
    "Senegal boat survivors tell of capsize (AFP)",
    "El Salvador assembly debates term bill (Reuters)",
    "Insurers halt Hormuz tanker cover (Bloomberg)",
    "Phillips 118 puts NZ on top v India (AP)",
    "BOJ watches as core CPI holds 2.2% (Reuters)",
    "LPR hold signals steady China policy (Reuters)",
    "Cancer-pill patients await wider trial (Reuters)",
    "Akvan floods displace thousands inland (AFP)",
    "COP31 talks run past midnight deadline (Reuters)",
]

DATE_CHECK = ("First reported Thursday 19 Nov, so NOT shown as Friday's "
              "news: the Shenzhen summit itself - Anthropic's IPO pricing "
              "and Nasdaq debut - the ICJ Rohingya verdict itself - GTA "
              "VI's midnight launch - the Riyadh tower attack - Voyager "
              "1's light-day (18 Nov).")

FOOTER1 = ("Every story here happened, or was first reported, on Friday "
           "20 November 2026 in at least one time zone. Claims are "
           "attributed, not stated as fact.")
FOOTER2 = ("Sources: Reuters, AP, AFP, Bloomberg, ANSA, ESA. All "
           "illustrations are original vector drawings made with Python "
           "and Pillow for this page.")
FOOTER3 = "THE WORLD IN ONE DAY - news-image-20261120-v3 - Built for make.fun"


# ------------------------------------------------------------- helpers

def tw(d, text, font):
    return d.textlength(text, font=font)


def wrap(d, text, font, maxw):
    """Greedy word wrap by pixel width; returns a list of lines."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if tw(d, trial, font) <= maxw or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(d, text, font, maxw, maxlines):
    """Wrap and clamp to maxlines, ending the last line with '...'."""
    lines = wrap(d, text, font, maxw)
    if len(lines) <= maxlines:
        return lines
    lines = lines[:maxlines]
    last = lines[-1]
    while last and tw(d, last + "...", font) > maxw:
        last = last[:-1]
    lines[-1] = last.rstrip() + "..."
    return lines


def block(d, x, y, text, font, fill, maxw, maxlines, lh):
    for i, ln in enumerate(fit(d, text, font, maxw, maxlines)):
        d.text((x, y + i * lh), ln, font=font, fill=fill)
    return y + maxlines * lh


def italic(img, x, y, text, font, fill):
    """Fake-italic: render the text, shear it, paste it back."""
    probe = ImageDraw.Draw(img)
    wpx = int(probe.textlength(text, font=font)) + 8
    hpx = font.size + 6
    layer = Image.new("RGBA", (wpx + hpx // 3, hpx), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((2, 2), text, font=font, fill=fill + (255,))
    layer = layer.transform(layer.size, Image.AFFINE,
                            (1, 0.28, -0.28 * hpx, 0, 1, 0))
    img.paste(layer, (int(x), int(y)), layer)


def chip_bar(d, x, y, text, fg, bg):
    f = F(SANSB, 10)
    wpx = tw(d, text, f) + 16
    d.rectangle([x, y, x + wpx, y + 17], fill=bg)
    d.text((x + 8, y + 3), text, font=f, fill=fg)
    return wpx


def blend(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def vgrad(d, x, y, w, h, top, bot):
    """Vertical colour gradient over a rectangle, one line per row."""
    for i in range(h):
        d.line([x, y + i, x + w, y + i], fill=blend(top, bot, i / max(1, h - 1)))


def hash2(ix, iy):
    """Deterministic integer hash of a grid cell -> 0..255."""
    v = (ix * 374761393 + iy * 668265263) & 0xFFFFFFFF
    v = ((v ^ (v >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((v ^ (v >> 16)) & 0xFF)


class LCG:
    """Fixed-seed linear congruential generator (deterministic)."""

    def __init__(self, seed):
        self.state = seed & 0x7FFFFFFF

    def next(self, mod):
        self.state = (self.state * 1103515245 + 12345) & 0x7FFFFFFF
        return self.state % mod


def glow(img, cx, cy, r, color, peak=110):
    """Soft radial glow: a blurred disc pasted with its own alpha."""
    if r <= 2:
        return
    tile = Image.new("RGBA", (2 * r, 2 * r), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    td.ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=color + (peak,))
    tile = tile.filter(ImageFilter.GaussianBlur(r / 2.0))
    img.paste(tile, (int(cx - r), int(cy - r)), tile)


def halftone(d, x0, y0, x1, y1, color, step=5, r=1):
    """Regular dot grid used as cheap shading inside a rectangle."""
    yy = y0
    row = 0
    while yy <= y1:
        xx = x0 + (step // 2 if row % 2 else 0)
        while xx <= x1:
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=color)
            xx += step
        yy += step
        row += 1


def paper_texture(img):
    """Grain, soft blotches and a thin vignette over the whole page."""
    d = ImageDraw.Draw(img, "RGBA")
    rng = LCG(20261120)
    # large, very soft tonal blotches so the paper is not flat
    for _ in range(26):
        bx = rng.next(W - 240)
        by = rng.next(H - 240)
        br = 60 + rng.next(120)
        tone = (214, 200, 168, 10) if rng.next(2) else (255, 252, 240, 10)
        d.ellipse([bx, by, bx + br, by + br], fill=tone)
    # fine deterministic grain: speckles a touch darker / lighter
    for _ in range(5200):
        gx = rng.next(W)
        gy = rng.next(H)
        if rng.next(2):
            d.point((gx, gy), fill=(196, 182, 148, 90))
        else:
            d.point((gx, gy), fill=(255, 254, 246, 90))
    for _ in range(700):
        gx = rng.next(W)
        gy = rng.next(H)
        d.line([gx, gy, gx + 1, gy], fill=(188, 172, 136, 70))
    # thin vignette: darkened corners from a blurred ellipse mask
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([-260, -200, W + 260, H + 200], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(180))
    dark = Image.new("RGB", (W, H), (206, 192, 158))
    img.paste(dark, (0, 0), mask.point(lambda v: (255 - v) // 5))


# ------------------------------------------------------------ masthead

def masthead(img, d):
    f_eye = F(SANSB, 12)
    eye = "T H E   W O R L D   I N   O N E   D A Y"
    d.text(((W - tw(d, eye, f_eye)) / 2, 14), eye, font=f_eye, fill=INK)
    d.text((M, 14), "No. 47", font=f_eye, fill=GRAY)
    r = "ONE IMAGE - ONE DAY"
    d.text((W - M - tw(d, r, f_eye), 14), r, font=f_eye, fill=GRAY)
    d.line([M, 36, W - M, 36], fill=LINE, width=1)
    for cx in (M + 2, W - M - 2):
        d.polygon([(cx - 4, 41), (cx, 37), (cx + 4, 41), (cx, 45)],
                  fill=RED)

    f_title = F(SERIFB, 57)
    title = "Friday 20 November 2026"
    d.text(((W - tw(d, title, f_title)) / 2, 44), title,
           font=f_title, fill=INK)
    d.line([M, 112, W - M, 112], fill=INK, width=3)
    d.line([M, 117, W - M, 117], fill=INK, width=1)

    d.rectangle([M, 123, W - M, 151], fill=RED)
    d.rectangle([M, 123, W - M, 126], fill=DARKRED)
    d.rectangle([M, 148, W - M, 151], fill=DARKRED)
    f_k = F(SANSB, 13)
    d.text(((W - tw(d, KICKER, f_k)) / 2, 130), KICKER, font=f_k,
           fill=(255, 255, 255))


def stats(d):
    d.rectangle([M, 156, W - M, 220], fill=(253, 248, 236))
    halftone(d, M + 4, 214, W - M - 4, 218, (226, 216, 188), step=6, r=1)
    f_num = F(SERIFB, 27)
    f_lab = F(SANSB, 9)
    cell = CW / 6.0
    for i, (num, lab) in enumerate(STATS):
        cx = M + i * cell
        if i:
            d.line([cx, 162, cx, 200], fill=LINE, width=1)
        d.text((cx + (cell - tw(d, num, f_num)) / 2, 160), num,
               font=f_num, fill=RED)
        for j, ln in enumerate(fit(d, lab, f_lab, cell - 10, 2)):
            d.text((cx + (cell - tw(d, ln, f_lab)) / 2, 196 + j * 11),
                   ln, font=f_lab, fill=INK)
    d.line([M, 222, W - M, 222], fill=LINE, width=1)


def chips(d):
    f = F(SANSB, 10)
    widths = [tw(d, c, f) + 18 for c in CHIPS]
    total = sum(widths) + 8 * (len(CHIPS) - 1)
    x = (W - total) / 2
    for c, wpx in zip(CHIPS, widths):
        d.rounded_rectangle([x + 1, 231, x + wpx + 1, 253], radius=9,
                            fill=SHADOW)
        d.rounded_rectangle([x, 230, x + wpx, 252], radius=9,
                            fill=CARD, outline=RED, width=1)
        d.ellipse([x + 6, 239, x + 9, 242], fill=RED)
        d.text((x + 13, 236), c, font=f, fill=DARKRED)
        x += wpx + 8


# --------------------------------------------------------- lead panels

def art_akvan(img, d, x, y, w, h):
    # storm sea and sky: deep teal gradient with a darker squall band
    vgrad(d, x, y, w, h, (13, 52, 74), (64, 128, 138))
    d.rectangle([x, y, x + w, y + 12], fill=(10, 38, 56))
    halftone(d, x + 4, y + h - 16, x + 196, y + h - 4,
             (30, 84, 96), step=5, r=1)
    cx, cy = x + 102, y + h // 2
    glow(img, cx, cy, 52, (190, 220, 226), peak=60)
    d = ImageDraw.Draw(img)
    # layered spiral: many arcs, alternating cloud shades, tight pitch
    for r in range(47, 5, -3):
        start = (r * 53) % 360
        shade = (228, 234, 236) if (r // 3) % 2 else (164, 194, 206)
        if r < 14:
            shade = (240, 244, 244) if (r // 3) % 2 else (188, 208, 216)
        d.arc([cx - r, cy - r * 0.76, cx + r, cy + r * 0.76],
              start=start, end=start + 248, fill=shade, width=3)
        d.arc([cx - r, cy - r * 0.76, cx + r, cy + r * 0.76],
              start=start + 252, end=start + 292,
              fill=blend(shade, (90, 120, 130), 0.45), width=3)
    # storm eye: dark core, gold ring, bright rim
    d.ellipse([cx - 8, cy - 7, cx + 8, cy + 7], fill=(24, 44, 54))
    d.ellipse([cx - 8, cy - 7, cx + 8, cy + 7], outline=GOLD, width=2)
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(240, 226, 170))
    # wind arrows curving around the spiral
    for ax, ay, a0, a1 in [(58, 16, 200, 320), (150, 74, 20, 130),
                           (66, 78, 300, 60)]:
        d.arc([x + ax - 15, y + ay - 11, x + ax + 15, y + ay + 11],
              a0, a1, fill=(250, 226, 150), width=2)
        ex = x + ax + 15 * math.cos(math.radians(a1))
        ey = y + ay + 11 * math.sin(math.radians(a1))
        tx = -math.sin(math.radians(a1))
        ty = math.cos(math.radians(a1))
        d.polygon([(ex, ey), (ex - 7 * tx + 3 * math.cos(math.radians(a1)),
                              ey - 7 * ty + 3 * math.sin(math.radians(a1))),
                   (ex - 7 * tx - 3 * math.cos(math.radians(a1)),
                    ey - 7 * ty - 3 * math.sin(math.radians(a1)))],
                  fill=(250, 226, 150))
    # coastline: layered sand bands with a darker wet edge
    land = [(x + 214, y + h), (x + 228, y + 46), (x + 250, y + 31),
            (x + 274, y + 39), (x + w, y + 27), (x + w, y + h)]
    d.polygon(land, fill=(206, 176, 110))
    inner = [(x + 226, y + h), (x + 238, y + 50), (x + 256, y + 38),
             (x + 276, y + 45), (x + w, y + 36), (x + w, y + h)]
    d.polygon(inner, fill=(188, 152, 88))
    d.line([(x + 228, y + 46), (x + 250, y + 31), (x + 274, y + 39),
            (x + w, y + 27)], fill=(110, 84, 42), width=2)
    # surf: white foam arcs where sea meets sand
    for fx, fy in [(222, 62), (238, 52), (258, 46), (282, 50), (300, 44)]:
        d.arc([x + fx - 8, y + fy - 4, x + fx + 8, y + fy + 5],
              200, 340, fill=(240, 248, 248), width=2)
    # palm trees: curved trunks and five fronds each
    for gx in range(x + 240, x + w - 10, 25):
        gy = y + 56 + (gx // 7) % 12
        d.line([gx, gy, gx - 4, gy - 12], fill=(74, 54, 30), width=2)
        top = (gx - 4, gy - 12)
        for ang in (170, 205, 245, 290, 335):
            ex = top[0] + int(10 * math.cos(math.radians(ang)))
            ey = top[1] + int(7 * math.sin(math.radians(ang))) + 3
            d.line([top[0], top[1], ex, ey], fill=(52, 92, 40), width=2)
        d.ellipse([top[0] - 2, top[1] - 1, top[0] + 2, top[1] + 3],
                  fill=(90, 64, 32))
    # driving rain: two densities of slanted streaks
    rng = LCG(4211)
    for _ in range(90):
        rx = x + 6 + rng.next(196)
        ry = y + 4 + rng.next(h - 26)
        ln = 5 + rng.next(6)
        col = (176, 208, 222) if rng.next(3) else (140, 178, 196)
        d.line([rx, ry, rx - ln // 2, ry + ln], fill=col, width=1)
    # whitecaps on the sea
    for wx, wy in [(30, 74), (66, 82), (120, 84), (168, 70), (196, 84)]:
        d.arc([x + wx - 7, y + wy - 3, x + wx + 7, y + wy + 4],
              190, 330, fill=(226, 240, 242), width=1)
    d.rectangle([x, y + h - 19, x + 168, y + h], fill=RED)
    d.rectangle([x, y + h - 19, x + 168, y + h - 16], fill=DARKRED)
    d.text((x + 7, y + h - 15), "LANDFALL - GUSTS 110 KM/H",
           font=F(SANSB, 10), fill=(255, 255, 255))


def art_kyiv(img, d, x, y, w, h):
    # night sky gradient, near-black zenith to smoky horizon
    vgrad(d, x, y, w, h, (6, 9, 24), (34, 38, 62))
    d.rectangle([x, y + h - 14, x + w, y + h], fill=(16, 14, 22))
    # stars: hash-placed, two brightness levels
    for sx in range(6, w - 4, 7):
        for sy in range(3, 34, 7):
            v = hash2(sx, sy)
            if v > 216:
                d.point((x + sx, y + sy), fill=(235, 235, 224))
            elif v > 205:
                d.point((x + sx, y + sy), fill=(150, 152, 170))
    # moon with shaded craters and a soft halo
    glow(img, x + 287, y + 17, 20, (232, 226, 200), peak=80)
    d = ImageDraw.Draw(img)
    d.ellipse([x + 278, y + 8, x + 296, y + 26], fill=(233, 227, 201))
    d.ellipse([x + 290, y + 10, x + 296, y + 20], fill=(214, 207, 182))
    for mx, my, mr in [(283, 13, 2), (288, 20, 1), (281, 19, 1)]:
        d.ellipse([x + mx - mr, y + my - mr, x + mx + mr, y + my + mr],
                  fill=(205, 198, 172))
    # searchlight beams sweeping up from the rooftops (translucent)
    beams = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(beams)
    bd.polygon([(40, h), (86, h), (150, 6), (138, 6)], fill=(240, 240, 210, 34))
    bd.polygon([(250, h), (292, h), (196, 4), (186, 4)], fill=(240, 240, 210, 30))
    bd.polygon([(150, h), (176, h), (238, 10), (228, 10)], fill=(240, 240, 210, 22))
    base_rgba = img.crop((x, y, x + w, y + h)).convert("RGBA")
    img.paste(Image.alpha_composite(base_rgba, beams).convert("RGB"),
              (x, y))
    d = ImageDraw.Draw(img)
    # skyline: varied blocks, shaded sides, rows of lit windows
    base = y + h
    blocks = [(0, 34), (24, 50), (50, 30), (72, 58), (104, 38),
              (128, 52), (156, 32), (180, 60), (212, 40), (238, 54),
              (268, 36), (292, 46)]
    for bi, (bx, bh) in enumerate(blocks):
        d.rectangle([x + bx, base - bh, x + bx + 22, base],
                    fill=(4, 6, 13))
        d.rectangle([x + bx, base - bh, x + bx + 3, base],
                    fill=(10, 12, 24))
        for wy in range(base - bh + 5, base - 6, 8):
            for wx in range(x + bx + 5, x + bx + 19, 6):
                if hash2(wx, wy + bi) > 150:
                    d.rectangle([wx, wy, wx + 3, wy + 4],
                                fill=(250, 205, 90))
                elif hash2(wx, wy) > 235:
                    d.rectangle([wx, wy, wx + 3, wy + 4],
                                fill=(190, 120, 60))
    # dome and spire landmark, centre-left
    d.pieslice([x + 80, base - 76, x + 104, base - 46], 180, 360,
               fill=(4, 6, 13))
    d.rectangle([x + 90, base - 80, x + 94, base - 60], fill=(4, 6, 13))
    d.point((x + 92, base - 82), fill=(250, 205, 90))
    d.rectangle([x + 196, base - 68, x + 198, base - 58], fill=(4, 6, 13))
    # missile trails: wide glow, hot core, burst at the head
    trails = [((x + 300, y + 2), (x + 210, y + 60)),
              ((x + 262, y + 0), (x + 148, y + 56)),
              ((x + 316, y + 20), (x + 262, y + 64))]
    for (ax, ay), (bx2, by2) in trails:
        glow(img, bx2, by2, 16, (255, 140, 50), peak=120)
        d = ImageDraw.Draw(img)
        d.line([ax, ay, bx2, by2], fill=(196, 74, 26), width=6)
        d.line([ax, ay, bx2, by2], fill=(255, 120, 50), width=3)
        d.line([ax, ay, bx2, by2], fill=(255, 230, 175), width=1)
        d.ellipse([bx2 - 8, by2 - 8, bx2 + 8, by2 + 8],
                  fill=(255, 140, 50))
        d.ellipse([bx2 - 4, by2 - 4, bx2 + 4, by2 + 4],
                  fill=(255, 208, 112))
        for k in range(12):
            ang = k * 0.5236
            r1 = 11 + (k % 3) * 3
            px = bx2 + int(r1 * math.cos(ang))
            py = by2 + int(r1 * math.sin(ang))
            d.line([bx2, by2, px, py], fill=(255, 172, 84), width=2)
        # smoke puffs drifting from each burst
        for s in range(3):
            sx = bx2 + 12 + s * 9
            sy = by2 - 8 - s * 5
            d.ellipse([sx - 5, sy - 3, sx + 5, sy + 3],
                      fill=(88, 84, 96))
    d.rectangle([x, y + h - 19, x + 148, y + h], fill=RED)
    d.rectangle([x, y + h - 19, x + 148, y + h - 16], fill=DARKRED)
    d.text((x + 7, y + h - 15), "~30 MISSILES - 3 KILLED",
           font=F(SANSB, 10), fill=(255, 255, 255))


def art_chart(img, d, x, y, w, h):
    # dealing-room paper with a faint red wash under the fall
    vgrad(d, x, y, w, h, (252, 248, 238), (244, 234, 218))
    # grid: horizontal rules plus vertical day divisions
    for gy in range(10, h - 6, 13):
        d.line([x + 8, y + gy, x + w - 8, y + gy],
               fill=(216, 208, 190), width=1)
    for gx in range(28, w - 8, 36):
        d.line([x + gx, y + 8, x + gx, y + h - 16],
               fill=(226, 218, 198), width=1)
    # candlesticks: firm open, then the rout (o, c, hi, lo per candle)
    candles = [(30, 34, 26, 38), (36, 40, 32, 43), (33, 30, 28, 36),
               (38, 42, 35, 45), (40, 37, 34, 43), (44, 50, 41, 53),
               (48, 44, 42, 51), (55, 62, 52, 65), (60, 57, 55, 64),
               (66, 73, 63, 76), (71, 68, 66, 75), (78, 84, 75, 87)]
    cw_step = (w - 90) / len(candles)
    for i, (o, c, hi, lo) in enumerate(candles):
        cxp = x + 58 + i * cw_step + cw_step / 2
        col = GREEN if c < o else RED
        d.line([cxp, y + hi - 22, cxp, y + lo - 22], fill=col, width=1)
        d.rectangle([cxp - 4, y + min(o, c) - 22, cxp + 4,
                     y + max(o, c) - 22], fill=col)
    # the index line diving through the candles, area filled beneath
    pts = [(8, 14), (48, 18), (88, 13), (124, 24), (158, 22),
           (192, 38), (224, 50), (254, 66), (288, 80), (306, 86)]
    xy = [(x + px, y + py) for px, py in pts]
    fill_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fill_layer)
    fd.polygon([(px - x, py - y) for px, py in xy] +
               [(306, h - 14), (8, h - 14)], fill=(179, 0, 27, 46))
    base_rgba = img.crop((x, y, x + w, y + h)).convert("RGBA")
    img.paste(Image.alpha_composite(base_rgba,
                                    fill_layer).convert("RGB"), (x, y))
    d = ImageDraw.Draw(img)
    d.line(xy, fill=RED, width=3)
    d.line(xy, fill=(255, 120, 110), width=1)
    for px, py in xy[::3]:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=WHITE,
                  outline=RED, width=1)
    ex, ey = xy[-1]
    d.polygon([(ex, ey), (ex - 12, ey - 4), (ex - 5, ey - 13)],
              fill=RED)
    # exchange skyline silhouette along the bottom edge
    base = y + h
    for bx, bh in [(0, 16), (26, 22), (54, 14), (80, 24), (112, 17),
                   (140, 21), (170, 13), (196, 20), (228, 15),
                   (256, 19), (284, 14)]:
        d.rectangle([x + bx, base - bh, x + bx + 22, base],
                    fill=(24, 26, 38))
        for wx in range(x + bx + 4, x + bx + 18, 6):
            if hash2(wx, bh) > 140:
                d.rectangle([wx, base - bh + 4, wx + 3, base - bh + 7],
                            fill=(250, 205, 90))
    d.rectangle([x, base - 1, x + w, base], fill=(24, 26, 38))
    # index labels, kept from the v2 panel
    f = F(SANSB, 11)
    d.text((x + 12, y + 28), "NIKKEI -4.9%", font=f, fill=RED)
    d.text((x + 12, y + 46), "KOSPI -5.4%", font=f, fill=DARKRED)
    d.text((x + 12, y + 64), "TAIEX -6.8%", font=f, fill=(90, 20, 20))
    d.text((x + w - 92, y + 6), "FRI 20 NOV", font=F(SANSB, 9),
           fill=GRAY)


ARTS = {"akvan": art_akvan, "kyiv": art_kyiv, "chart": art_chart}


def lead_panels(img, d):
    pw, ph, gap, y0 = 317, 224, 12, 262
    f_tag, f_head = F(SANSB, 9), F(SERIFB, 16)
    f_body, f_src = F(SANS, 10), F(SERIF, 9)
    for i, lead in enumerate(LEADS):
        x = M + i * (pw + gap)
        d.rectangle([x + 3, y0 + 3, x + pw + 3, y0 + ph + 3],
                    fill=SHADOW)
        d.rectangle([x, y0, x + pw, y0 + ph], fill=CARD, outline=LINE,
                    width=1)
        ARTS[lead["art"]](img, d, x + 1, y0 + 1, pw - 2, 94)
        d = ImageDraw.Draw(img)
        d.line([x + 1, y0 + 95, x + pw - 1, y0 + 95], fill=LINE, width=1)
        d.text((x + 10, y0 + 104), lead["tag"], font=f_tag, fill=RED)
        block(d, x + 10, y0 + 120, lead["head"], f_head, INK,
              pw - 20, 2, 20)
        block(d, x + 10, y0 + 164, lead["body"], f_body, INK,
              pw - 20, 3, 13)
        italic(img, x + 10, y0 + 206, lead["src"], f_src, GRAY)
        d = ImageDraw.Draw(img)


# ------------------------------------------------------- feature cards

def scene_mercury(d, x, y):
    # deep-space backdrop with stars, shaded planet, probe on approach
    d.rectangle([x, y, x + 44, y + 40], fill=(10, 12, 28))
    for sx, sy in [(4, 5), (38, 4), (8, 33), (40, 30), (20, 3), (33, 36)]:
        d.point((x + sx, y + sy), fill=(220, 220, 210))
    d.arc([x + 2, y + 4, x + 42, y + 30], 200, 330, fill=GOLD, width=1)
    d.ellipse([x + 8, y + 10, x + 34, y + 36], fill=(168, 160, 148),
              outline=INK, width=1)
    d.ellipse([x + 11, y + 12, x + 24, y + 25], fill=(186, 179, 166))
    d.pieslice([x + 8, y + 10, x + 34, y + 36], 300, 120,
               fill=(128, 121, 108))
    for cx, cy, r in [(16, 18, 3), (26, 26, 4), (20, 30, 2)]:
        d.ellipse([x + cx - r, y + cy - r, x + cx + r, y + cy + r],
                  fill=(140, 132, 118), outline=(110, 103, 90))
    d.rectangle([x + 30, y + 3, x + 38, y + 10], fill=(70, 90, 160),
                outline=(200, 200, 220))
    d.rectangle([x + 33, y + 10, x + 35, y + 14], fill=(200, 190, 170))
    d.line([x + 34, y + 14, x + 28, y + 19], fill=(220, 220, 220),
           width=1)


def scene_yen(d, x, y):
    # two gold coins with radial shading, sparkles, tiny rising bars
    d.rectangle([x, y + 30, x + 44, y + 40], fill=(238, 228, 200))
    for bx, bh in [(4, 8), (10, 12), (16, 10)]:
        d.rectangle([x + bx, y + 30 - bh, x + bx + 4, y + 30],
                    fill=(196, 84, 60))
    d.ellipse([x + 20, y + 12, x + 40, y + 32], fill=(214, 172, 70),
              outline=(146, 110, 30), width=1)
    d.ellipse([x + 6, y + 5, x + 34, y + 33], fill=(238, 204, 100),
              outline=(146, 110, 30), width=2)
    d.ellipse([x + 9, y + 8, x + 24, y + 22], fill=(246, 220, 130))
    d.ellipse([x + 10, y + 9, x + 31, y + 30], outline=(190, 148, 52),
              width=1)
    d.text((x + 15, y + 10), "Y", font=F(SANSB, 15), fill=(120, 88, 20))
    d.line([x + 14, y + 21, x + 26, y + 21], fill=(120, 88, 20),
           width=2)
    d.line([x + 14, y + 25, x + 26, y + 25], fill=(120, 88, 20),
           width=2)
    for sx, sy in [(36, 6), (5, 26), (38, 24)]:
        d.line([x + sx - 2, y + sy, x + sx + 2, y + sy],
               fill=(250, 230, 150), width=1)
        d.line([x + sx, y + sy - 2, x + sx, y + sy + 2],
               fill=(250, 230, 150), width=1)


def scene_bank(d, x, y):
    # shaded bank facade: pediment, lit columns, steps, coin stacks
    d.rectangle([x, y, x + 44, y + 40], fill=(228, 220, 198))
    d.polygon([(x + 3, y + 12), (x + 33, y + 12), (x + 18, y + 3)],
              fill=RED)
    d.polygon([(x + 18, y + 3), (x + 33, y + 12), (x + 18, y + 12)],
              fill=DARKRED)
    d.ellipse([x + 15, y + 6, x + 21, y + 11], fill=(255, 235, 200))
    for cx in (7, 14, 21):
        d.rectangle([x + cx, y + 15, x + cx + 4, y + 30], fill=NAVY)
        d.rectangle([x + cx, y + 15, x + cx + 1, y + 30],
                    fill=(70, 84, 120))
    d.rectangle([x + 3, y + 30, x + 33, y + 33], fill=(90, 80, 66))
    d.rectangle([x + 3, y + 34, x + 33, y + 37], fill=(120, 108, 88))
    d.text((x + 13, y + 16), "%", font=F(SANSB, 11), fill=(255, 255, 255))
    for i, ch in enumerate((6, 9, 4)):
        for j in range(ch // 2):
            d.ellipse([x + 36, y + 34 - j * 3, x + 43, y + 37 - j * 3],
                      fill=(232, 196, 92), outline=(146, 110, 30))


def scene_globe(d, x, y):
    # shaded earth: atmosphere ring, graticule, two-tone continents
    d.rectangle([x, y, x + 44, y + 40], fill=(16, 34, 54))
    for sx, sy in [(5, 4), (39, 6), (36, 34), (6, 35)]:
        d.point((x + sx, y + sy), fill=(210, 220, 230))
    d.ellipse([x + 5, y + 4, x + 37, y + 36], fill=(52, 110, 150),
              outline=(140, 190, 220), width=1)
    d.ellipse([x + 8, y + 6, x + 22, y + 20], fill=(86, 142, 178))
    d.ellipse([x + 14, y + 4, x + 28, y + 36], outline=(30, 70, 105),
              width=1)
    d.line([x + 5, y + 20, x + 37, y + 20], fill=(30, 70, 105), width=1)
    d.polygon([(x + 10, y + 10), (x + 18, y + 8), (x + 19, y + 15),
               (x + 12, y + 16)], fill=GREEN)
    d.polygon([(x + 24, y + 22), (x + 33, y + 27), (x + 26, y + 33),
               (x + 22, y + 28)], fill=GREEN)
    d.polygon([(x + 24, y + 22), (x + 33, y + 27), (x + 27, y + 28)],
              fill=(70, 140, 74))
    d.polygon([(x + 28, y + 12), (x + 34, y + 15), (x + 29, y + 19)],
              fill=(96, 150, 80))
    d.arc([x + 2, y + 1, x + 42, y + 24], 300, 60, fill=GOLD, width=1)


def scene_boat(d, x, y):
    # pirogue on a banded sea under a low sun, foam and birds
    vgrad(d, x, y, 44, 16, (250, 214, 150), (252, 236, 200))
    vgrad(d, x, y + 16, 44, 24, (38, 110, 128), (16, 64, 84))
    d.ellipse([x + 30, y + 2, x + 40, y + 12], fill=(250, 190, 80))
    d.ellipse([x + 32, y + 4, x + 38, y + 10], fill=(252, 210, 120))
    for bx, by in [(6, 5), (13, 8)]:
        d.arc([x + bx - 3, y + by - 2, x + bx, y + by + 2], 200, 330,
              fill=INK, width=1)
        d.arc([x + bx, y + by - 2, x + bx + 3, y + by + 2], 210, 340,
              fill=INK, width=1)
    d.polygon([(x + 5, y + 22), (x + 35, y + 22), (x + 30, y + 30),
               (x + 10, y + 30)], fill=(122, 78, 40))
    d.polygon([(x + 5, y + 22), (x + 35, y + 22), (x + 33, y + 25),
               (x + 8, y + 25)], fill=(150, 104, 56))
    d.line([x + 20, y + 22, x + 20, y + 6], fill=INK, width=2)
    d.polygon([(x + 21, y + 7), (x + 21, y + 21), (x + 31, y + 21)],
              fill=(240, 236, 224), outline=INK)
    d.polygon([(x + 21, y + 7), (x + 21, y + 21), (x + 26, y + 21)],
              fill=(214, 208, 192))
    for wx in (4, 16, 28):
        d.arc([x + wx, y + 31, x + wx + 10, y + 39], 0, 180,
              fill=(170, 216, 224), width=2)
    d.arc([x + 8, y + 33, x + 18, y + 39], 0, 180,
          fill=(240, 248, 248), width=1)


def scene_placard(d, x, y):
    # strike scene: raised placard, red flag, crowd silhouettes
    d.rectangle([x, y, x + 44, y + 40], fill=(240, 232, 214))
    d.rectangle([x + 6, y + 3, x + 32, y + 19], fill=(255, 255, 255),
                outline=RED, width=2)
    d.rectangle([x + 6, y + 3, x + 32, y + 7], fill=RED)
    d.line([x + 10, y + 11, x + 28, y + 11], fill=INK, width=2)
    d.line([x + 10, y + 15, x + 24, y + 15], fill=GRAY, width=1)
    d.line([x + 19, y + 19, x + 19, y + 30], fill=(122, 78, 40),
           width=3)
    d.line([x + 36, y + 6, x + 36, y + 28], fill=INK, width=1)
    d.polygon([(x + 36, y + 6), (x + 43, y + 8), (x + 36, y + 11)],
              fill=RED)
    for hx in (6, 16, 27, 37):
        d.ellipse([x + hx - 4, y + 28, x + hx + 4, y + 36],
                  fill=(40, 36, 34))
        d.pieslice([x + hx - 6, y + 33, x + hx + 6, y + 43], 180, 360,
                   fill=(40, 36, 34))
    d.rectangle([x, y + 38, x + 44, y + 40], fill=(200, 188, 164))


def scene_cricket(d, x, y):
    # pitch strip, stumps, angled bat, seamed ball with motion arcs
    vgrad(d, x, y, 44, 40, (120, 168, 92), (84, 128, 62))
    d.rectangle([x, y + 26, x + 44, y + 40], fill=(104, 148, 78))
    d.polygon([(x + 14, y + 8), (x + 30, y + 8), (x + 34, y + 38),
               (x + 10, y + 38)], fill=(216, 196, 150))
    d.line([x + 12, y + 30, x + 32, y + 30], fill=(240, 236, 220),
           width=1)
    for sx in (16, 20, 24):
        d.rectangle([x + sx, y + 12, x + sx + 2, y + 22], fill=GOLD)
    d.rectangle([x + 15, y + 11, x + 26, y + 13], fill=(140, 100, 40))
    d.polygon([(x + 30, y + 16), (x + 36, y + 19), (x + 24, y + 36),
               (x + 19, y + 33)], fill=(206, 170, 105), outline=INK)
    d.rectangle([x + 31, y + 13, x + 35, y + 18], fill=(90, 60, 30))
    d.ellipse([x + 3, y + 20, x + 13, y + 30], fill=RED, outline=INK)
    d.arc([x + 5, y + 22, x + 11, y + 28], 100, 260,
          fill=(255, 255, 255), width=1)
    d.arc([x + 1, y + 17, x + 15, y + 33], 300, 60,
          fill=(240, 240, 230), width=1)


def scene_ballot(d, x, y):
    # ballot box with shaded slot, checked paper, gold third-term badge
    d.rectangle([x, y, x + 44, y + 40], fill=(232, 224, 204))
    halftone(d, x + 2, y + 34, x + 42, y + 39, (206, 194, 168),
             step=5, r=1)
    d.rectangle([x + 6, y + 18, x + 34, y + 37], fill=NAVY)
    d.rectangle([x + 6, y + 18, x + 34, y + 22], fill=(40, 56, 96))
    d.rectangle([x + 13, y + 20, x + 27, y + 23], fill=(8, 12, 24))
    d.rectangle([x + 13, y + 2, x + 27, y + 20], fill=(255, 255, 255),
                outline=INK, width=1)
    d.rectangle([x + 13, y + 2, x + 27, y + 6], fill=(226, 220, 204))
    d.line([x + 16, y + 11, x + 19, y + 15], fill=GREEN, width=2)
    d.line([x + 19, y + 15, x + 25, y + 7], fill=GREEN, width=2)
    d.ellipse([x + 29, y + 24, x + 41, y + 36], fill=GOLD,
              outline=(120, 84, 20), width=1)
    d.text((x + 32, y + 26), "3", font=F(SANSB, 11), fill=(255, 255, 255))
    for cx, cy in [(4, 6), (38, 10), (8, 14)]:
        d.point((x + cx, y + cy), fill=RED)
        d.point((x + cx + 2, y + cy + 2), fill=TEAL)


def scene_tanker(d, x, y):
    # laden tanker: shaded hull, container stacks, bridge, smoke, sea
    vgrad(d, x, y, 44, 14, (206, 222, 232), (240, 242, 240))
    vgrad(d, x, y + 14, 44, 26, (44, 106, 128), (20, 66, 86))
    d.ellipse([x + 33, y + 6, x + 38, y + 11], fill=(120, 116, 110))
    d.ellipse([x + 36, y + 3, x + 42, y + 8], fill=(150, 146, 140))
    d.polygon([(x + 3, y + 24), (x + 39, y + 24), (x + 35, y + 32),
               (x + 8, y + 32)], fill=(52, 52, 60))
    d.rectangle([x + 5, y + 21, x + 39, y + 24], fill=RED)
    d.rectangle([x + 5, y + 23, x + 39, y + 24], fill=DARKRED)
    stacks = [(9, (176, 90, 40)), (16, (52, 96, 140)), (23, (70, 120, 70))]
    for sx, col in stacks:
        d.rectangle([x + sx, y + 14, x + sx + 6, y + 21], fill=col)
        d.rectangle([x + sx, y + 14, x + sx + 6, y + 16],
                    fill=blend(col, (255, 255, 255), 0.25))
    d.rectangle([x + 31, y + 9, x + 36, y + 21], fill=(226, 226, 230),
                outline=INK)
    d.rectangle([x + 32, y + 11, x + 35, y + 14], fill=(90, 130, 160))
    for wx in (4, 16, 28):
        d.arc([x + wx, y + 32, x + wx + 10, y + 39], 0, 180,
              fill=(170, 216, 224), width=2)


def scene_pill(d, x, y):
    # two-tone capsule with highlight, tumour cluster shrinking away
    d.rectangle([x, y, x + 44, y + 40], fill=(238, 240, 244))
    halftone(d, x + 26, y + 2, x + 42, y + 14, (214, 218, 226),
             step=4, r=1)
    d.rounded_rectangle([x + 2, y + 6, x + 28, y + 19], radius=6,
                        fill=(246, 244, 240), outline=INK, width=1)
    d.rounded_rectangle([x + 15, y + 6, x + 28, y + 19], radius=6,
                        fill=RED)
    d.rectangle([x + 15, y + 7, x + 21, y + 18], fill=RED)
    d.rectangle([x + 15, y + 6, x + 28, y + 10], fill=(216, 60, 70))
    d.line([x + 5, y + 9, x + 12, y + 9], fill=(255, 255, 255), width=2)
    d.rounded_rectangle([x + 8, y + 24, x + 20, y + 31], radius=3,
                        fill=(240, 200, 90), outline=(146, 110, 30))
    d.line([x + 14, y + 24, x + 14, y + 31], fill=(146, 110, 30),
           width=1)
    for cx, cy, r in [(32, 26, 6), (38, 32, 4), (39, 36, 2)]:
        d.ellipse([x + cx - r, y + cy - r, x + cx + r, y + cy + r],
                  fill=(214, 120, 110), outline=DARKRED, width=1)
        d.ellipse([x + cx - r // 2, y + cy - r // 2,
                   x + cx, y + cy], fill=(228, 150, 140))
    d.line([x + 24, y + 34, x + 29, y + 30], fill=GREEN, width=2)
    d.polygon([(x + 29, y + 30), (x + 25, y + 30), (x + 29, y + 34)],
              fill=GREEN)


ICONS = {"mercury": scene_mercury, "yen": scene_yen, "bank": scene_bank,
         "globe": scene_globe, "boat": scene_boat,
         "placard": scene_placard, "cricket": scene_cricket,
         "ballot": scene_ballot, "tanker": scene_tanker,
         "pill": scene_pill}


def feature_cards(img, d):
    cw2, ch2, gap = 188, 122, 9
    f_tag, f_head = F(SANSB, 8), F(SANSB, 11)
    f_body, f_src = F(SANS, 9), F(SERIF, 8)
    for idx, feat in enumerate(FEATURES):
        row, col = divmod(idx, 5)
        x = M + col * (cw2 + gap)
        y = 494 + row * 128
        d.rectangle([x + 2, y + 2, x + cw2 + 2, y + ch2 + 2],
                    fill=SHADOW)
        d.rectangle([x, y, x + cw2, y + ch2], fill=CARD, outline=LINE,
                    width=1)
        d.rectangle([x + 7, y + 7, x + 23, y + 23], fill=RED)
        d.rectangle([x + 7, y + 7, x + 23, y + 11], fill=DARKRED)
        d.text((x + 10 if feat["n"] < 10 else x + 8, y + 10),
               str(feat["n"]), font=F(SANSB, 10), fill=(255, 255, 255))
        d.text((x + 28, y + 10), feat["tag"], font=f_tag, fill=RED)
        ICONS[feat["icon"]](d, x + 7, y + 28)
        block(d, x + 56, y + 29, feat["head"], f_head, INK,
              cw2 - 63, 3, 13)
        block(d, x + 7, y + 74, feat["body"], f_body, INK,
              cw2 - 14, 3, 11)
        italic(img, x + 7, y + 108, feat["src"], f_src, GRAY)
        d = ImageDraw.Draw(img)


# ------------------------------------------------------------- map etc

LAND = [
    (-100, 52, 42, 13), (-95, 33, 26, 9), (-42, 74, 12, 5),
    (-62, -8, 13, 9), (-64, -24, 8, 11),
    (16, 50, 22, 8), (18, 12, 24, 11), (24, -14, 13, 9),
    (88, 54, 58, 10), (80, 22, 12, 9), (103, 16, 9, 8),
    (138, 37, 5, 4), (134, -25, 15, 6), (172, -42, 4, 4),
]

PINS = [
    (1, 86.4, 19.3), (2, 30.5, 50.4), (3, 139.7, 35.7),
    (5, 128.0, 32.5), (6, 116.4, 39.9), (7, 30.7, 36.9),
    (8, -17.4, 14.7), (9, 12.5, 41.9), (10, 172.6, -40.5),
    (11, -89.2, 13.7), (12, 56.3, 26.5), (13, -71.1, 42.3),
]


def world_map(d):
    d.text((M, 752), "WHERE FRIDAY HAPPENED", font=F(SANSB, 11),
           fill=INK)
    x0, y0, w, h = 28, 770, 372, 114
    # pale sea panel with graticule lines every 30 lon / 20 lat
    d.rectangle([x0 - 4, y0 - 4, x0 + w + 4, y0 + h + 4],
                fill=(240, 234, 216), outline=(206, 196, 168), width=1)
    for glon in range(-150, 180, 30):
        gx = x0 + (glon + 180) / 360.0 * w
        d.line([gx, y0, gx, y0 + h], fill=(222, 214, 192), width=1)
    for glat in range(-60, 80, 20):
        gy = y0 + (80 - glat) / 140.0 * h
        d.line([x0, gy, x0 + w, gy], fill=(222, 214, 192), width=1)
    d.line([x0, y0 + 80 / 140.0 * h, x0 + w, y0 + 80 / 140.0 * h],
           fill=(206, 196, 168), width=1)
    # dense dot-matrix landmass, two-tone hash shading for texture
    cols, rows = 124, 34
    for r in range(rows):
        lat = 80 - (r + 0.5) * 140.0 / rows
        for c in range(cols):
            lon = -180 + (c + 0.5) * 360.0 / cols
            land = False
            for cx, cy, rx, ry in LAND:
                if ((lon - cx) / rx) ** 2 + ((lat - cy) / ry) ** 2 <= 1:
                    land = True
                    break
            if not land and -4 < lat < 4 and 95 < lon < 140:
                land = (c + r) % 3 != 0
            if land:
                px = x0 + (c + 0.5) * w / cols
                py = y0 + (r + 0.5) * h / rows
                col = (110, 94, 64) if hash2(c, r) > 168 else (134, 118, 84)
                d.ellipse([px - 1.3, py - 1.3, px + 1.3, py + 1.3],
                          fill=col)
    f_pin = F(SANSB, 8)
    for n, lon, lat in PINS:
        px = x0 + (lon + 180) / 360.0 * w
        py = y0 + (80 - lat) / 140.0 * h
        d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=(120, 0, 18))
        d.ellipse([px - 6, py - 6, px + 6, py + 6], fill=RED,
                  outline=(255, 255, 255), width=1)
        s = str(n)
        d.text((px - tw(d, s, f_pin) / 2, py - 4), s, font=f_pin,
               fill=(255, 255, 255))
    mx, my = x0 + w - 12, y0 - 8
    d.ellipse([mx - 7, my - 7, mx + 7, my + 7], fill=(120, 96, 40))
    d.ellipse([mx - 6, my - 6, mx + 6, my + 6], fill=(168, 160, 148),
              outline=GOLD, width=2)
    d.text((mx - tw(d, "4", f_pin) / 2, my - 4), "4", font=f_pin,
           fill=INK)
    d.text((M, 890), "Pins 1-13 = pictured stories. 4 = BepiColombo "
           "at Mercury (space).", font=F(SANS, 8), fill=GRAY)


def briefs(d):
    d.text((416, 752), "ALSO ON FRIDAY", font=F(SANSB, 12), fill=RED)
    note = "23 more stories"
    d.text((W - M - tw(d, note, F(SANS, 9)), 755), note,
           font=F(SANS, 9), fill=GRAY)
    d.line([416, 770, W - M, 770], fill=LINE, width=1)
    f_num, f_txt = F(SANSB, 9), F(SANS, 9)
    for i, item in enumerate(BRIEFS):
        col, row = divmod(i, 12)
        x = 416 + col * 298
        y = 778 + row * 11
        if row % 2 == 0:
            d.rectangle([x - 3, y - 1, x + 292, y + 10],
                        fill=(250, 245, 231))
        num = "%d." % (14 + i)
        d.text((x, y), num, font=f_num, fill=RED)
        d.text((x + tw(d, num, f_num) + 4, y), item, font=f_txt,
               fill=INK)


def date_check(d):
    y0 = 912
    d.rectangle([M + 3, y0 + 3, W - M + 3, y0 + 51], fill=SHADOW)
    d.rectangle([M, y0, W - M, y0 + 48], fill=(250, 238, 228),
                outline=RED, width=2)
    halftone(d, M + CW - 60, y0 + 4, W - M - 6, y0 + 14,
             (238, 208, 190), step=5, r=1)
    d.text((M + 10, y0 + 6), "DATE CHECK", font=F(SANSB, 10), fill=RED)
    block(d, M + 10, y0 + 22, DATE_CHECK, F(SANS, 9), INK, CW - 20, 2,
          12)


def footer(d):
    d.line([M, 970, W - M, 970], fill=LINE, width=1)
    f1, f2, f3 = F(SERIF, 9), F(SERIF, 9), F(SANSB, 8)
    for y, txt, f in ((978, FOOTER1, f1), (991, FOOTER2, f2),
                      (1005, FOOTER3, f3)):
        d.text(((W - tw(d, txt, f)) / 2, y), txt, font=f,
               fill=GRAY if f is f3 else INK)


def print_grain(img):
    """Fine print grain over the finished page: a deterministic
    hash-noise field at 2x2 blocks, applied as a +/-2 brightness
    wobble so flat areas gain real texture without hiding text."""
    gw, gh = W // 2, H // 2
    noise = Image.new("L", (gw, gh))
    px = noise.load()
    for yy in range(gh):
        for xx in range(gw):
            px[xx, yy] = hash2(xx, yy) % 5
    noise = noise.resize((W, H), Image.NEAREST).convert("RGB")
    return ImageChops.add(img, noise, 1.0, -2)


# ---------------------------------------------------------------- main

def build():
    img = Image.new("RGB", (W, H), PAPER)
    paper_texture(img)
    d = ImageDraw.Draw(img)
    masthead(img, d)
    stats(d)
    chips(d)
    lead_panels(img, d)
    d = ImageDraw.Draw(img)
    feature_cards(img, d)
    d = ImageDraw.Draw(img)
    world_map(d)
    briefs(d)
    date_check(d)
    footer(d)
    img = print_grain(img)
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, "entry.png"), format="PNG", optimize=True)


if __name__ == "__main__":
    build()
