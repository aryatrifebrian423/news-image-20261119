#!/usr/bin/env python3
"""Entry program for news-image-20261119 (make.fun).

Draws a one-page editorial poster summing up the world news of
Thursday 19 November 2026 and writes it to $MAKEFUN_OUTPUT_DIR/entry.png
(default /output). Pure Python 3 standard library: a small pixel canvas,
an embedded 5x7 bitmap font, flat pictograms drawn from rectangles,
circles and lines, and a zlib/struct PNG encoder. No network, no time,
no randomness: every run writes the same bytes.
"""
import os
import struct
import sys
import zlib
from pathlib import Path

W = H = 1024
PAPER = (247, 242, 232)
CARD = (255, 255, 255)
INK = (24, 24, 24)
NAVY = (28, 52, 88)
NAVY_DARK = (18, 36, 62)
RED = (178, 34, 28)
GOLD = (198, 158, 38)
GREY = (110, 108, 100)
LIGHT_GREY = (224, 219, 205)
SKY = (158, 198, 220)
SEA = (58, 104, 148)
TEAL = (18, 128, 122)
GREEN = (46, 139, 64)
ORANGE = (214, 110, 32)
PURPLE = (94, 64, 140)

# ------------------------------------------------------------------ font --
# 5x7 bitmap font, uppercase + digits + punctuation. Each glyph is 7 rows
# of 5 characters ('#' on, '.' off). All poster text is rendered uppercase.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..##.", "..##.", "..##.", "..##.", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "\u2014": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#.##", "#..##"),
    "$": ("..#..", ".####", "#...#", ".###.", "....#", "####.", "..#.."),
    "+": (".....", "..#..", "#####", "..#..", ".....", ".....", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
}


def text_width(text, scale):
    """Pixel width of text rendered at the given scale."""
    return len(text) * 6 * scale


def wrap_text(text, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ---------------------------------------------------------------- canvas --
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def border(self, x, y, w, h, color, t=2):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def hline(self, x, y, length, color, t=1):
        self.rect(x, y, length, t, color)

    def vline(self, x, y, length, color, t=1):
        self.rect(x, y, t, length, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.rect(x - t // 2, y - t // 2, t, t, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color, t=2):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d2 <= r * r:
                    self.set(xx, yy, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1:
                    self.set(xx, yy, color)

    def text(self, x, y, s, color, scale):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale

    def text_center(self, cx, y, s, color, scale):
        self.text(cx - text_width(s, scale) // 2, y, s, color, scale)

    def paragraph(self, x, y, s, color, scale, max_chars, leading=None):
        if leading is None:
            leading = 9 * scale
        for i, line in enumerate(wrap_text(s, max_chars)):
            self.text(x, y + i * leading, line, color, scale)
        return y + len(wrap_text(s, max_chars)) * leading


def png_bytes(canvas):
    """Encode the canvas as a PNG (filter 0 rows, zlib level 9)."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * stride:(y + 1) * stride]

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# ------------------------------------------------------------- pictograms --
def draw_summit_table(cv, x, y, w, h):
    """Round table with three small flags: US, China, Russia."""
    cx, cy = x + w // 2, y + h // 2 + 18
    cv.ellipse(cx, cy, 118, 26, NAVY_DARK)
    cv.ellipse(cx, cy - 6, 118, 26, NAVY)
    cv.rect(cx - 8, cy + 12, 16, 34, NAVY_DARK)
    # Three flag poles behind the table.
    poles = [cx - 88, cx, cx + 88]
    heads = [RED, GOLD, TEAL]
    for px, hc in zip(poles, heads):
        cv.vline(px, y + 8, 92, INK, 3)
        cv.disc(px, y + 6, 9, hc)
    # US flag: red/white stripes, blue corner.
    fx, fy = cx - 118, y + 12
    for i in range(5):
        cv.rect(fx, fy + i * 6, 60, 6, RED if i % 2 == 0 else CARD)
    cv.rect(fx, fy, 26, 18, NAVY)
    for dx, dy in ((5, 4), (15, 4), (5, 11), (15, 11)):
        cv.disc(fx + dx, fy + dy, 2, CARD)
    # China flag: red field, gold stars.
    fx = cx - 30
    cv.rect(fx, fy, 60, 30, RED)
    cv.disc(fx + 12, fy + 10, 5, GOLD)
    for dx, dy in ((26, 6), (32, 12), (26, 18), (20, 14)):
        cv.disc(fx + dx, fy + dy, 2, GOLD)
    # Russia flag: white, blue, red bands.
    fx = cx + 58
    cv.rect(fx, fy, 60, 10, CARD)
    cv.rect(fx, fy + 10, 60, 10, SEA)
    cv.rect(fx, fy + 20, 60, 10, RED)
    cv.border(fx, fy, 60, 30, INK, 1)


def draw_bridge(cv, x, y, w, h):
    """A long bridge with its middle span broken and fallen."""
    base = y + h - 26
    cv.rect(x, base, w, 8, INK)  # water line
    for i in range(0, w, 26):
        cv.rect(x + i, base + 10, 14, 4, SEA)
    deck = y + 34
    cv.rect(x + 6, deck, 84, 8, RED)            # left span
    cv.rect(x + w - 90, deck, 84, 8, RED)       # right span
    # Fallen middle span, tilted into the water.
    cv.line(x + 96, deck + 4, x + w // 2 + 18, base - 6, RED, 7)
    cv.line(x + w - 96, deck + 4, x + w // 2 - 6, base - 10, RED, 7)
    # Towers and cables.
    for tx in (x + 44, x + w - 50):
        cv.vline(tx, y + 6, deck - y + 4, INK, 5)
        cv.line(tx, y + 6, tx - 40, deck, INK, 2)
        cv.line(tx, y + 6, tx + 40, deck, INK, 2)
    # Smoke puffs over the gap.
    for sx, sy, r in ((x + w // 2 - 26, y + 22, 10),
                      (x + w // 2 + 4, y + 12, 13),
                      (x + w // 2 + 28, y + 24, 9)):
        cv.disc(sx, sy, r, GREY)
    # Support pillars in the water.
    for px in (x + 30, x + w - 36):
        cv.rect(px, deck + 8, 10, base - deck - 8, INK)


def draw_controller(cv, x, y, w, h):
    """A game controller over a neon city skyline."""
    base = y + h - 8
    # Skyline, heights scaled to the box.
    heights = [int(v * h / 138) for v in (46, 78, 58, 92, 66, 84, 50)]
    bx = x + (w - 7 * 30) // 2
    for hh in heights:
        cv.rect(bx, base - hh, 24, hh, NAVY_DARK)
        for wy in range(base - hh + 6, base - 6, 12):
            cv.rect(bx + 6, wy, 5, 5, GOLD)
            cv.rect(bx + 14, wy, 5, 5, GOLD)
        bx += 30
    # Sun.
    cv.disc(x + w - 30, y + 16, 11, ORANGE)
    # Controller body.
    ccx, ccy = x + w // 2, y + h - 24
    cv.ellipse(ccx, ccy, 62, 22, INK)
    cv.disc(ccx - 52, ccy + 8, 17, INK)
    cv.disc(ccx + 52, ccy + 8, 17, INK)
    cv.disc(ccx - 34, ccy - 2, 8, CARD)   # d-pad
    cv.rect(ccx - 37, ccy - 5, 6, 10, CARD)
    cv.rect(ccx - 34, ccy - 7, 10, 6, CARD)
    for dx, dy, col in ((22, -8, RED), (32, -1, GOLD),
                        (22, 6, GREEN), (12, -1, SEA)):
        cv.disc(ccx + dx, ccy + dy, 4, col)


def draw_chart(cv, x, y, w, h):
    """Rising bars with an arrow, and a big ANT ticker."""
    base = y + h - 6
    bars = [int(v * h / 150) for v in (34, 52, 44, 72, 96, 122)]
    bx = x + (w - 6 * 34) // 2
    for bh in bars:
        cv.rect(bx, base - bh, 26, bh, TEAL)
        bx += 34
    cv.line(x + 12, base - int(40 * h / 150), x + w - 26, y + 16, RED, 5)
    cv.line(x + w - 26, y + 16, x + w - 52, y + 18, RED, 5)
    cv.line(x + w - 26, y + 16, x + w - 28, y + 42, RED, 5)
    cv.text(x + 8, y + 2, "ANT", RED, 3)


def draw_cyclone(cv, x, y, w, h):
    """Spiral storm over a coastline, with rain streaks."""
    cx, cy = x + w // 2, y + h // 2 - 4
    maxr = h // 2 - 6
    for r, col in ((maxr, SEA), (int(maxr * 0.78), SKY),
                   (int(maxr * 0.55), SEA), (int(maxr * 0.32), SKY)):
        cv.ring(cx, cy, r, col, 5)
    cv.disc(cx, cy, 5, NAVY_DARK)
    # Coastline.
    cv.rect(x, y + h - 14, w, 14, GREEN)
    cv.rect(x, y + h - 14, w, 3, INK)
    # Rain streaks.
    for rx in range(x + 12, x + w - 8, 26):
        cv.line(rx, y + 4, rx - 6, y + 20, SEA, 3)
    # Wind arrow.
    cv.line(x + 14, y + 8, x + 56, y + 8, RED, 4)
    cv.line(x + 56, y + 8, x + 44, y + 2, RED, 4)
    cv.line(x + 56, y + 8, x + 44, y + 14, RED, 4)


# ------------------------------------------------------------------ layout --
def panel(cv, x, y, w, h, kicker, kcolor):
    cv.rect(x, y, w, h, CARD)
    cv.border(x, y, w, h, INK, 2)
    cv.rect(x + 2, y + 2, w - 4, 30, kcolor)
    cv.text(x + 12, y + 9, kicker, CARD, 2)


def build_poster():
    cv = Canvas(W, H, PAPER)
    # Masthead.
    cv.rect(20, 20, 984, 132, NAVY)
    cv.rect(20, 20, 984, 6, GOLD)
    cv.text(48, 42, "THE WORLD IN ONE IMAGE", CARD, 3)
    cv.text(48, 82, "19 NOVEMBER 2026", GOLD, 5)
    cv.text(816, 46, "THURSDAY", CARD, 2)
    cv.text(816, 72, "ONE DAY", CARD, 2)
    cv.text(816, 96, "ONE PICTURE", CARD, 2)
    cv.rect(20, 158, 984, 8, RED)

    # Lead panel: the Shenzhen trilateral.
    panel(cv, 28, 178, 968, 216, "SHENZHEN, CHINA  -  APEC", RED)
    draw_summit_table(cv, 44, 222, 300, 160)
    cv.text(360, 226, "THREE LEADERS,", INK, 4)
    cv.text(360, 262, "ONE TABLE", INK, 4)
    cv.paragraph(360, 306, "XI, TRUMP AND PUTIN MEET FOR THE FIRST TIME, "
                 "ON THE SIDELINES OF APEC. NUCLEAR ARMS, AI AND TRADE "
                 "ON THE TABLE. LEADERS DECLARATION DUE TODAY.",
                 INK, 2, 46)

    # Row 1: Crimea bridge + GTA VI.
    panel(cv, 28, 410, 478, 196, "UKRAINE  -  CRIMEA", NAVY)
    draw_bridge(cv, 44, 448, 446, 76)
    cv.text(44, 530, "BRIDGE HIT AGAIN", INK, 3)
    cv.paragraph(44, 560, "TRAFFIC HALTED. THIRD ATTACK THIS WEEK ON "
                 "THE BRIDGE.", INK, 2, 37)

    panel(cv, 518, 410, 478, 196, "GAMES  -  VICE CITY", PURPLE)
    draw_controller(cv, 534, 448, 446, 76)
    cv.text(534, 530, "GTA VI IS OUT", INK, 3)
    cv.paragraph(534, 560, "OUT TODAY, UNLOCKING AT MIDNIGHT IN EACH "
                 "MARKET. 13 YEARS AFTER GTA V.", INK, 2, 37)

    # Row 2: Anthropic IPO + Cyclone Akvan.
    panel(cv, 28, 622, 478, 196, "MARKETS  -  NASDAQ", TEAL)
    draw_chart(cv, 44, 660, 446, 76)
    cv.text(44, 742, "RECORD 81.3BN IPO", INK, 3)
    cv.paragraph(44, 772, "DEBUTS ON NASDAQ TODAY AS ANT, PRICED AT 83 "
                 "DOLLARS. THE BIGGEST IPO EVER.", INK, 2, 37)

    panel(cv, 518, 622, 478, 196, "WEATHER  -  BAY OF BENGAL", SEA)
    draw_cyclone(cv, 534, 660, 446, 76)
    cv.text(534, 742, "AKVAN NEARS COAST", INK, 3)
    cv.paragraph(534, 772, "SEVERE CYCLONE CLOSES ON THE INDIAN EAST "
                 "COAST. LANDFALL FRIDAY.", INK, 2, 37)

    # Also-today strip.
    cv.rect(28, 834, 968, 108, NAVY_DARK)
    cv.text(48, 848, "ALSO TODAY", GOLD, 2)
    cv.hline(48, 874, 928, GOLD, 2)
    cv.text(48, 886, "INDIA-JAPAN TALKS", CARD, 2)
    cv.text(48, 908, "TALKS OPEN IN TOKYO.", CARD, 2)
    cv.text(368, 886, "NASA BRIEFS ON", CARD, 2)
    cv.text(368, 908, "VOYAGER 1 TODAY.", CARD, 2)
    cv.text(688, 886, "APEC DECLARATION", CARD, 2)
    cv.text(688, 908, "DUE IN SHENZHEN.", CARD, 2)

    # Footer.
    cv.text_center(512, 958, "EVERY STORY FROM THURSDAY 19 NOVEMBER 2026",
                   INK, 2)
    cv.text_center(512, 982, "SOURCES: REUTERS, AP, IMD, NASDAQ FILINGS",
                   GREY, 2)
    return png_bytes(cv)


def main() -> int:
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "entry.png"
    data = build_poster()
    target.write_bytes(data)
    print(f"wrote {target} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
