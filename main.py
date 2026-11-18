#!/usr/bin/env python3
"""news-image-20261118 -- one-day world news front page, drawn from scratch.

Pure Python 3.13 standard library only (os, sys, zlib, struct, binascii).
No network, no third-party imports, no image files: the PNG is encoded
by hand and every glyph is drawn from a 5x7 bitmap font defined below.

Output: /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png), 1024x1024,
deterministic -- two runs write byte-identical files.
"""
import binascii
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font: 5x7
# Each glyph is 7 rows of 5 pixels, "#" = ink. All text is upper-cased
# before drawing, so only capitals, digits and punctuation are needed.
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
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "|": ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    "•": ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
}
FALLBACK = FONT["?"]


def glyph(ch):
    return FONT.get(ch, FALLBACK)


# ---------------------------------------------------------------- canvas
PAPER = (247, 243, 232)
INK = (26, 26, 26)
GREY = (74, 74, 74)
RED = (185, 28, 28)
NAVY = (20, 33, 61)
NAVY2 = (29, 45, 80)
BLUE = (29, 78, 216)
OCEAN = (214, 231, 242)
LAND = (168, 185, 127)
LAND2 = (150, 170, 108)
RULE = (180, 172, 150)
GOLD = (180, 130, 30)

px = bytearray(W * H * 3)


def put(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        px[i], px[i + 1], px[i + 2] = color


def rect(x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            px[i], px[i + 1], px[i + 2] = color


def hline(x, y, w, color):
    rect(x, y, w, 1, color)


def vline(x, y, h, color):
    rect(x, y, 1, h, color)


def circle(cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int((r * r - dy * dy) ** 0.5)
        rect(cx - dx, cy + dy, dx * 2 + 1, 1, color)


def disc_outline(cx, cy, r, color):
    for a in range(360):
        import math
        rad = a * 3.141592653589793 / 180.0
        put(int(cx + r * math.cos(rad)), int(cy + r * math.sin(rad)), color)


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, color):
    """Draw upper-cased text; returns the x just past the last glyph."""
    s = s.upper()
    cx = x
    for ch in s:
        g = glyph(ch)
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == "1":
                    rect(cx + col * scale, y + row * scale, scale, scale, color)
        cx += 6 * scale
    return cx


def draw_centered(y, s, scale, color, cx=W // 2):
    w = text_width(s, scale)
    draw_text(cx - w // 2, y, s, scale, color)


def wrap(s, scale, max_w):
    """Greedy word wrap; returns a list of lines fitting max_w pixels."""
    max_chars = max(1, (max_w + scale) // (6 * scale))
    words = s.upper().split(" ")
    lines = []
    cur = ""
    for wrd in words:
        trial = wrd if not cur else cur + " " + wrd
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            # a single over-long word is hard-split
            while len(wrd) > max_chars:
                lines.append(wrd[:max_chars])
                wrd = wrd[max_chars:]
            cur = wrd
    if cur:
        lines.append(cur)
    return lines


def draw_para(x, y, s, scale, max_w, color, line_h=None):
    if line_h is None:
        line_h = 7 * scale + 2
    lines = wrap(s, scale, max_w)
    for i, ln in enumerate(lines):
        draw_text(x, y + i * line_h, ln, scale, color)
    return y + len(lines) * line_h

# ---------------------------------------------------------------- world map
# Stylised equirectangular continents, drawn as filled polygons in
# lon/lat space. Rough coastlines, recognisable at a glance.
NORTH_AMERICA = [(-168, 66), (-150, 70), (-140, 70), (-128, 71), (-115, 69),
                 (-100, 69), (-90, 68), (-85, 66), (-80, 73), (-72, 62),
                 (-64, 60), (-56, 52), (-60, 47), (-65, 44), (-70, 42),
                 (-74, 39), (-76, 35), (-80, 32), (-81, 26), (-84, 30),
                 (-89, 30), (-91, 19), (-97, 16), (-102, 18), (-106, 23),
                 (-112, 29), (-117, 33), (-124, 40), (-124, 48), (-130, 54),
                 (-140, 60), (-152, 58), (-158, 58), (-165, 60)]
GREENLAND = [(-58, 64), (-52, 60), (-43, 60), (-32, 68), (-40, 76),
             (-55, 77), (-62, 76), (-68, 70)]
SOUTH_AMERICA = [(-80, 9), (-77, 8), (-72, 12), (-64, 10), (-59, 9),
                 (-52, 5), (-51, 0), (-44, -3), (-35, -8), (-38, -15),
                 (-40, -21), (-48, -28), (-53, -33), (-58, -38), (-63, -41),
                 (-66, -45), (-68, -50), (-70, -54), (-73, -50), (-73, -40),
                 (-72, -30), (-70, -20), (-75, -15), (-79, -8), (-81, -4),
                 (-80, 1), (-80, 6)]
AFRICA = [(-17, 15), (-16, 21), (-10, 31), (-6, 34), (0, 36), (10, 37),
          (11, 34), (19, 32), (25, 32), (32, 31), (34, 28), (37, 22),
          (39, 18), (43, 12), (48, 11), (51, 11), (48, 4), (42, -1),
          (40, -8), (40, -15), (36, -20), (33, -26), (28, -33), (20, -35),
          (17, -32), (15, -27), (13, -21), (12, -17), (13, -12), (9, -1),
          (9, 4), (4, 6), (-4, 5), (-8, 4), (-13, 8), (-16, 12)]
EURASIA = [(-10, 36), (-9, 38), (-9, 43), (-4, 44), (-2, 48), (-5, 50),
           (-1, 51), (2, 51), (5, 53), (8, 55), (8, 57), (10, 59),
           (6, 60), (5, 62), (11, 62), (16, 58), (18, 56), (21, 55),
           (24, 59), (28, 60), (30, 62), (35, 65), (40, 68), (50, 68),
           (60, 69), (68, 73), (75, 73), (85, 75), (100, 76), (110, 74),
           (120, 73), (130, 72), (140, 72), (150, 70), (160, 69), (170, 67),
           (178, 65), (173, 64), (170, 60), (162, 56), (158, 52), (156, 51),
           (150, 59), (142, 55), (141, 50), (140, 45), (135, 43), (131, 42),
           (127, 40), (126, 38), (122, 38), (120, 34), (121, 30), (118, 25),
           (112, 22), (108, 19), (106, 10), (104, 9), (100, 7), (98, 10),
           (98, 14), (94, 16), (91, 22), (89, 22), (86, 20), (82, 16),
           (80, 13), (77, 8), (76, 10), (75, 15), (73, 18), (72, 20),
           (69, 22), (66, 25), (62, 25), (58, 25), (56, 26), (52, 26),
           (50, 29), (48, 30), (44, 29), (42, 29), (39, 30), (36, 36),
           (33, 36), (30, 36), (27, 37), (26, 39), (23, 36), (22, 38),
           (19, 40), (16, 40), (14, 44), (12, 44), (9, 44), (6, 43),
           (3, 43), (0, 40), (-1, 38), (-2, 37), (-6, 36), (-9, 37)]
UK = [(-5, 50), (-4, 52), (-5, 54), (-4, 56), (-3, 58), (-2, 57),
      (0, 53), (1, 51), (-1, 51), (-3, 50)]
JAPAN = [(130, 31), (131, 33), (133, 34), (135, 34), (137, 35), (139, 35),
         (140, 37), (141, 39), (141, 41), (142, 43), (144, 44), (142, 45),
         (141, 42), (140, 39), (139, 37), (137, 36), (134, 35), (131, 33)]
AUSTRALIA = [(113, -22), (114, -28), (115, -32), (115, -35), (118, -35),
             (124, -33), (129, -32), (132, -32), (135, -35), (138, -35),
             (140, -38), (144, -38), (147, -39), (150, -37), (153, -32),
             (153, -27), (151, -24), (148, -20), (146, -19), (142, -11),
             (142, -14), (137, -12), (135, -15), (132, -12), (130, -13),
             (127, -14), (124, -15), (122, -17), (118, -20)]
SE_ASIA = [(95, 5), (98, 8), (100, 7), (101, 3), (103, 1), (105, -2),
           (108, -4), (110, -6), (112, -7), (114, -8), (116, -9), (119, -10),
           (122, -10), (121, -7), (119, -4), (116, -2), (113, 0), (110, 1),
           (107, 0), (104, 1), (101, 3), (98, 6), (96, 8)]
MADAGASCAR = [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24),
              (45, -25), (44, -21), (43, -18)]
NEW_ZEALAND = [(167, -45), (170, -43), (173, -41), (175, -38), (177, -38),
               (175, -40), (173, -42), (170, -44), (167, -46)]
CONTINENTS = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EURASIA,
              UK, JAPAN, AUSTRALIA, SE_ASIA, MADAGASCAR, NEW_ZEALAND]

MAP_X, MAP_Y, MAP_W, MAP_H = 16, 192, 640, 124
MAP_LON0, MAP_LON1 = -170, 190
MAP_LAT0, MAP_LAT1 = -58, 84


def map_xy(lon, lat):
    x = MAP_X + (lon - MAP_LON0) / (MAP_LON1 - MAP_LON0) * MAP_W
    y = MAP_Y + (MAP_LAT1 - lat) / (MAP_LAT1 - MAP_LAT0) * MAP_H
    return int(x), int(y)


def fill_poly(points, color):
    pts = [map_xy(lon, lat) for lon, lat in points]
    ys = [p[1] for p in pts]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        xs = []
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 <= y < y2) or (y2 <= y < y1):
                t = (y - y1) / (y2 - y1)
                xs.append(x1 + t * (x2 - x1))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            xa, xb = int(xs[k]), int(xs[k + 1])
            if xb >= xa:
                rect(xa, y, xb - xa + 1, 1, color)


# Numbered map markers: (story number, lon, lat)
MARKERS = [(1, 114, 22), (2, 121, 15), (5, 36, 45), (6, 30, 50),
           (7, 50, 26), (8, 56, 27), (9, 127, 39), (13, 80, 16),
           (15, -74, 41), (22, 7, 9), (24, 28, -26), (12, 0, 51)]


def draw_marker(num, lon, lat):
    cx, cy = map_xy(lon, lat)
    circle(cx, cy, 8, RED)
    disc_outline(cx, cy, 8, PAPER)
    label = str(num)
    tw = text_width(label, 1)
    draw_text(cx - tw // 2, cy - 3, label, 1, PAPER)


# ---------------------------------------------------------------- the news
# 34 stories, all events of Wednesday 18 November 2026 as reported that day.
# (tag, headline, one-line summary) -- headlines and summaries are kept
# short so each block fits two lines of headline + two of summary.
STORIES = [
    ("CHINA", "APEC OPENS IN SHENZHEN",
     "21 leaders meet on trade and AI."),
    ("PHILIPPINES", "TRUMP LANDS IN MANILA FOR QUAD",
     "Meets Modi, Albanese, Takaichi."),
    ("CHINA", "TRUMP, XI AND PUTIN TO MEET",
     "First trilateral summit, 19 Nov."),
    ("RUSSIA", "PUTIN ARRIVES IN SHENZHEN",
     "May also meet N. Korea's leader."),
    ("UKRAINE", "UKRAINE HITS CRIMEA BRIDGE AGAIN",
     "A span drops into Kerch Strait."),
    ("UKRAINE", "RUSSIA POUNDS KYIV BRIDGES",
     "Water and power cut in Kyiv."),
    ("BAHRAIN", "IRAN DRONES HIT US RADAR IN BAHRAIN",
     "Third strike on the base in 5 days."),
    ("IRAN", "US STRIKES IRAN'S QESHM ISLAND",
     "Oil routes in Hormuz on watch."),
    ("N. KOREA", "NORTH KOREA FIRES MISSILE TO SEA",
     "Fired from Wonsan after US drills."),
    ("TAIWAN", "US PRESSES UN OVER TAIWAN FLIGHTS",
     "US asks ICAO to oppose curbs."),
    ("CANADA", "CANADA AND CHINA EXTEND TRADE DEALS",
     "Xi meets Carney ahead of APEC."),
    ("UK", "BRITAIN SANCTIONS SETTLEMENT FIRMS",
     "London defends two-state solution."),
    ("INDIA", "CYCLONE AKVAN BEARS DOWN ON ANDHRA",
     "Landfall 20 Nov; winds to 145 km/h."),
    ("INDIA", "DHONI RETIRES FROM THE IPL",
     "CSK great, 45, to mentor in 2027."),
    ("USA", "DOW PLUNGES 1,000 POINTS IN A DAY",
     "Tech sell-off; VIX jumps."),
    ("USA", "NVIDIA PROBES CEO SPY-LINK CLAIMS",
     "Trump backs the Nvidia chief."),
    ("WORLD", "CYBER-ATTACK HITS APPLE, ZOOM, BBC",
     "Outages across 200 sites."),
    ("IRAN", "IRAN REFUSES UN NUCLEAR INSPECTION",
     "Tehran bars IAEA until war ends."),
    ("YEMEN", "HOUTHIS ADVANCE ON YEMEN'S COAST",
     "Ground seized 100 km west of Aden."),
    ("GAZA", "GAZA CEASEFIRE 'NEAR COLLAPSE'",
     "Aid must flow before winter."),
    ("CONGO", "CONGO PEACE EFFORTS FAIL TO STOP WAR",
     "Rival talks stall; war rages on."),
    ("NIGERIA", "US INTEL BACKS NIGERIA RAIDS",
     "Missions backed before 2027 vote."),
    ("NIGERIA", "POLICE FREE 20 ABDUCTED IN ZAMFARA",
     "Held 22 days; families reunited."),
    ("S. AFRICA", "17 DEAD IN TWO SOUTH AFRICA SHOOTINGS",
     "Two cities probed by police."),
    ("EGYPT", "EGYPT AND INDIA PLAN TRADE DEAL",
     "Pharma, farm and tech on agenda."),
    ("AFRICA", "AFRICAN UNION PUSHES SUDAN PEACE",
     "Bloc seeks African-led talks."),
    ("S. SUDAN", "SOUTH SUDAN VOTE DELAY DRAGS ON",
     "AU, UN want a clear election date."),
    ("RWANDA", "RWANDA TALKS EU RETURN HUB IN VIENNA",
     "Migrant returns discussed from 2027."),
    ("FRANCE", "FRANCE DENIES TROOPS IN UKRAINE",
     "Paris calls Moscow claim propaganda."),
    ("SERBIA", "SERBIAN MIG-29 CRASH KILLS PILOT",
     "Jet down near Belgrade."),
    ("RUSSIA", "RUSSIAN PLANE CRASH KILLS 13 IN SIBERIA",
     "An-12 down in Kemerovo region."),
    ("SPAIN", "SPAIN RAISES MINIMUM WAGE 5.3%",
     "Pay to 1,286 euros; vote 29 Nov."),
    ("GERMANY", "GERMANY BUILDS NEW DRONE REGIMENT",
     "Bundeswehr boosts surveillance."),
    ("GERMANY", "GERMANY WINS FIRST CHESS MEDAL",
     "First medal for Germany since 2000."),
]

# ---------------------------------------------------------------- layout
COLS = 4
COL_W = 239
COL_X = [16, 267, 518, 769]
GRID_TOP = 350
ROW_H = 72


def draw_masthead():
    rect(0, 0, W, 74, NAVY)
    rect(0, 74, W, 3, RED)
    draw_centered(10, "THE WORLD IN ONE DAY", 4, PAPER)
    draw_centered(48, "WEDNESDAY 18 NOVEMBER 2026  •  34 STORIES  •  ONE DAY",
                  2, (200, 205, 220))


def draw_hero():
    rect(16, 80, 992, 104, (255, 255, 255))
    rect(16, 80, 992, 1, RULE)
    rect(16, 183, 992, 1, RULE)
    rect(16, 80, 1, 104, RULE)
    rect(1007, 80, 1, 104, RULE)
    draw_centered(88, "ASIA HOSTS THE WORLD", 3, RED)
    draw_centered(114, "APEC OPENS IN SHENZHEN AS QUAD MEETS IN MANILA", 2, INK)
    draw_centered(138,
                  "TRUMP, XI AND PUTIN SET FOR FIRST TRILATERAL SUMMIT ON 19 NOV",
                  2, INK)
    draw_centered(162,
                  "WAR IN UKRAINE, GULF STRIKES AND A CYCLONE FILL THE REST OF THE DAY",
                  1, GREY)


def draw_map_panel():
    rect(16, 192, 640, 124, OCEAN)
    rect(16, 192, 640, 1, RULE)
    rect(16, 315, 640, 1, RULE)
    rect(16, 192, 1, 124, RULE)
    rect(655, 192, 1, 124, RULE)
    for poly in CONTINENTS:
        fill_poly(poly, LAND)
    # equator + graticule hint
    ex0, ey0 = map_xy(-170, 0)
    ex1, _ = map_xy(190, 0)
    for x in range(ex0, ex1, 4):
        put(x, ey0, (150, 180, 200))
    for num, lon, lat in MARKERS:
        draw_marker(num, lon, lat)
    draw_text(22, 197, "THE WORLD TODAY", 1, NAVY)
    # right-hand stats panel
    rect(672, 192, 336, 124, NAVY2)
    draw_text(690, 202, "THE DAY IN NUMBERS", 2, GOLD)
    stats = [("34", "STORIES FROM EVERY CONTINENT"),
             ("3", "SUMMITS IN ASIA IN 48 HOURS"),
             ("21", "APEC LEADERS IN SHENZHEN"),
             ("2", "BRIDGES HIT IN THE UKRAINE WAR")]
    y = 226
    for big, small in stats:
        draw_text(690, y, big, 2, PAPER)
        draw_text(726, y + 3, small, 1, (200, 205, 220))
        y += 21
    draw_text(690, 308, "MAP: NUMBERED STORIES MARKED IN RED", 1, (160, 170, 190))


def draw_section_head():
    hline(16, 330, 992, INK)
    draw_text(16, 336, "THE DAY IN BRIEF - 34 STORIES", 2, INK)
    right = "EVERY EVENT REPORTED ON 18 NOVEMBER 2026"
    draw_text(W - 16 - text_width(right, 1), 340, right, 1, GREY)


def draw_stories():
    # 4 columns; column 0 and 1 hold 9 stories, columns 2 and 3 hold 8.
    counts = [9, 9, 8, 8]
    idx = 0
    for col in range(COLS):
        x = COL_X[col]
        y = GRID_TOP
        for _ in range(counts[col]):
            tag, head, summ = STORIES[idx]
            idx += 1
            # number chip
            rect(x, y, 20, 14, RED)
            lab = "%02d" % (idx)
            draw_text(x + 10 - text_width(lab, 1) // 2, y + 3, lab, 1, PAPER)
            draw_text(x + 24, y + 1, tag, 1, RED)
            # headline, up to 2 lines
            hy = draw_para(x, y + 15, head, 2, COL_W, INK, line_h=14)
            # summary, up to 2 lines
            draw_para(x, hy + 1, summ, 2, COL_W, GREY, line_h=14)
            y += ROW_H
            if col < COLS - 1:
                vline(x + COL_W + 6, GRID_TOP, 9 * ROW_H - 8, (220, 214, 196))


def draw_footer():
    rect(0, 1000, W, 24, NAVY)
    draw_centered(1007, "SOURCES: REUTERS, AP, NDTV, XINHUA, IMD, QUAD JOINT STATEMENT  •  "
                         "ALL EVENTS REPORTED ON WEDNESDAY 18 NOVEMBER 2026",
                  1, (200, 205, 220))


# ---------------------------------------------------------------- PNG encode
def png_chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png():
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw += px[y * W * 3:(y + 1) * W * 3]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr)
            + png_chunk(b"IDAT", idat) + png_chunk(b"IEND", b""))


def main():
    rect(0, 0, W, H, PAPER)
    draw_masthead()
    draw_hero()
    draw_map_panel()
    draw_section_head()
    draw_stories()
    draw_footer()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(encode_png())
    print("wrote", path)


if __name__ == "__main__":
    main()
