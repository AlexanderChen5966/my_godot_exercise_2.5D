# B3-2b 診所的像素貼圖（32 像素＝1 m；牌子、圖卡、海報用 2 倍密度 64 像素＝1 m）。
# 共用的水泥、金屬、木板、碎布、輪胎、血跡在 assets/textures/common/；出口牌借停車場的 parking/sign、正門的鐵捲門借街道的 street/shutter。
# 這裡畫診所專屬的（輸出到 assets/textures/clinic/）與共用的落葉 leaves（輸出到 common/）。
# 用法：python3 art/design/b3/clinic_textures.py 輸出資料夾 → 每張的 .txt、.png 與 preview.png
import math, sys
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/tools")
from pix import Grid
from texlib import h, shade, noise_fill, blob, crack, export

OUTDIR = sys.argv[1]
SHEETS = {}


def sheet(name, w, h_, kind):
    g = Grid(w, h_)
    SHEETS[name] = (g, kind)
    return g


def leaf(g, cx, cy, ang, size, c, seed):
    """一片葉子（菱形＋中間的葉脈），ang 是方向（弧度）"""
    dx, dy = math.cos(ang), math.sin(ang)
    for t in range(-size, size + 1):
        w = int((size - abs(t)) * 0.6 + 0.5)
        for s in range(-w, w + 1):
            x, y = int(round(cx + dx * t - dy * s)), int(round(cy + dy * t + dx * s))
            g.put(x, y, shade(c, 0.9 + h(x, y, seed) * 0.2) if s else shade(c, 0.75))


# ---- 牆（寬 2 m 一格、高 3 m 整面，64×96）：下面 1 m 漆成淡綠的護牆、木條、上面米黃灰泥；剝落、水漬、靠天花板的黴 ----
g = sheet("wall", 64, 96, "tile 2m × 3m")
for y in range(96):
    for x in range(64):
        z = 3.0 - (y + 0.5) / 32
        if z < 1.0:
            c = shade("#7a8a6e", 0.92 + (h(x, y, 101) - 0.5) * 0.10 - (0.1 if z < 0.12 else 0))
        else:
            c = shade("#a0946e", 0.92 + (h(x, y, 102) - 0.5) * 0.10 + (0.04 if h(x // 3, y // 3, 103) < 0.3 else 0))
        g.put(x, y, c)
g.hline(0, 63, 63, "#5a4630"); g.hline(0, 63, 64, "#4a3a28")             # 護牆上緣的木條（z 1.0）
for i in range(5):                                                       # 剝落的灰泥，露出底下的水泥
    blob(g, int(h(i, 1, 104) * 64), int(8 + h(i, 2, 104) * 50), 3 + int(h(i, 3, 104) * 3), "#8a8478", i * 11 + 2, density=0.7)
for i in range(4):                                                       # 護牆上的漆掉了
    blob(g, int(h(i, 1, 105) * 64), int(70 + h(i, 2, 105) * 20), 2, "#9a9a88", i * 7 + 5, density=0.7)
for i in range(6):                                                       # 由上往下流的水漬
    x0 = int(h(i, 1, 106) * 64)
    for y in range(0, 10 + int(h(i, 2, 106) * 40)):
        if h(x0, y, 107) < 0.8:
            g.put(x0, y, shade(g.get(x0, y), 0.82))
for y in range(8):                                                       # 靠天花板的黴
    for x in range(64):
        if h(x, y, 108) < 0.5 - y * 0.06:
            g.put(x, y, "#5a5a3e")
crack(g, 20, 14, 26, 109, "#7a6e52"); crack(g, 50, 30, 18, 110, "#7a6e52")

# ---- 地磚（2 m 一格）：50 cm 的米色地磚，深淺交錯、縫裡的髒污、碎掉的一塊 ----
g = sheet("floor_tile", 64, 64, "tile 2m")
for ty in range(4):
    for tx in range(4):
        base = "#8a7e64" if (tx + ty) % 2 == 0 else "#968a6e"
        noise_fill(g, shade(base, 0.95 + h(tx, ty, 111) * 0.1), 0.06, 112 + tx * 4 + ty, rect=(tx * 16, ty * 16, tx * 16 + 15, ty * 16 + 15))
for k in range(0, 64, 16):
    g.hline(0, 63, k, "#5e5444"); g.vline(k, 0, 63, "#5e5444")
crack(g, 36, 34, 14, 113, "#5e5444"); crack(g, 40, 33, 10, 114, "#5e5444")
for i in range(3):
    blob(g, int(h(i, 1, 115) * 64), int(h(i, 2, 115) * 64), 4, "#6e6450", i * 13 + 1, density=0.45)

# ---- 天花板（2 m 一格）：50 cm 的輕鋼架天花板、金屬條、水漬 ----
g = sheet("ceiling", 64, 64, "tile 2m")
for ty in range(4):
    for tx in range(4):
        noise_fill(g, shade("#8a8270", 0.95 + h(tx, ty, 116) * 0.1), 0.07, 117 + tx + ty * 4, rect=(tx * 16, ty * 16, tx * 16 + 15, ty * 16 + 15))
for k in range(0, 64, 16):
    g.hline(0, 63, k, "#6a665a"); g.vline(k, 0, 63, "#6a665a")
for cx, cy, r in ((22, 40, 6), (50, 12, 4)):
    blob(g, cx, cy, r, "#6e6248", cx + cy, density=0.6)
    blob(g, cx, cy, r - 2, "#5e5440", cx * cy, density=0.6)

# ---- 布簾（1 m 一格）：淡青灰的布、直的皺褶、污漬 ----
g = sheet("curtain", 32, 32, "tile 1m")
for y in range(32):
    for x in range(32):
        fold = 0.12 * math.cos(x / 32 * math.pi * 4)
        g.put(x, y, shade("#7a8a7a", 0.95 + fold + (h(x, y, 118) - 0.5) * 0.06))
blob(g, 9, 22, 4, "#6a6a52", 119, density=0.5); blob(g, 25, 6, 2, "#5a3a2a", 120, density=0.6)

# ---- 皮面（0.5 m 一格）：青綠色的人造皮、裂紋 ----
g = sheet("leather", 16, 16, "tile 0.5m")
noise_fill(g, "#5a7a7a", 0.08, 121)
crack(g, 3, 2, 9, 122, "#3e5656"); crack(g, 11, 8, 7, 123, "#3e5656")
g.put(6, 12, "#c8c0a8"); g.put(7, 12, "#c8c0a8")                         # 裂開露出的海綿

# ---- 窗戶（2 × 1.4 m，fit 64×45）：金屬窗框、3×2 片玻璃（髒、有兩片破了）、外面是夕陽和爬藤 ----
g = sheet("window_clinic", 64, 45, "fit")
for y in range(45):
    for x in range(64):
        k = 1.0 - y / 45 * 0.35
        g.put(x, y, shade("#e0b060", k + (h(x, y, 124) - 0.5) * 0.06))   # 外面的夕陽
for i in range(14):                                                       # 窗外的爬藤（剪影）
    leaf(g, int(h(i, 1, 125) * 64), int(h(i, 2, 125) * 18), h(i, 3, 125) * 6.28, 3, "#3e4a2a", i)
for py in range(45):                                                      # 髒玻璃（沒破的那幾片蓋一層灰）
    for px in range(64):
        col, row = px * 3 // 64, py * 2 // 45
        if (col, row) not in ((1, 0), (2, 1)):
            k = 0.62 if (px + py * 2) % 19 not in (0, 1) else 0.8           # 灰濛的玻璃＋擦過的痕跡
            g.put(px, py, shade(g.get(px, py), k))
for (col, row) in ((1, 0), (2, 1)):                                       # 破的那兩片：鋸齒邊上留著碎玻璃
    x0, y0 = col * 21 + 2, row * 22 + 2
    for py in range(y0, y0 + 20):
        for px in range(x0, x0 + 19):
            e = min(px - x0, x0 + 18 - px, py - y0, y0 + 19 - py)
            if e < 3 and h(px, py, 127) < 0.55:
                g.put(px, py, "#9aa8a4")
for x in (0, 1, 21, 42, 62, 63):
    g.vline(x, 0, 44, "#4a4a44")
for y in (0, 1, 22, 43, 44):
    g.hline(0, 63, y, "#4a4a44")

# ---- 外面（2 × 1.5 m，fit 64×48）：從正門看出去的黃昏街道（天空、遠處的樓、柏油） ----
g = sheet("outside", 64, 48, "fit")
for y in range(48):
    for x in range(64):
        g.put(x, y, shade("#d0803a", 1.05 - y / 48 * 0.4))
for x0, x1, top in ((0, 14, 12), (16, 30, 20), (34, 50, 8), (52, 64, 16)):
    for y in range(top, 36):
        for x in range(x0, x1):
            g.put(x, y, "#5a3826" if h(x, y, 128) < 0.92 else "#d08a3a")
for y in range(36, 48):
    for x in range(64):
        g.put(x, y, shade("#4a443c", 0.9 + h(x, y, 129) * 0.2))
g.hline(0, 63, 40, "#8a7a3a")

# ---- 後門（1 × 2.1 m，fit 32×67）：木門、上方有鐵絲網的小窗、門把、下緣的踢板、掉漆 ----
g = sheet("door_wood", 32, 67, "fit")
for y in range(67):
    for x in range(32):
        g.put(x, y, shade("#6a4e34", 0.92 + 0.1 * ((x + int(h(x // 4, y, 130) * 3)) % 5 == 0) + (h(x, y, 131) - 0.5) * 0.08))
g.rect(10, 8, 21, 21, "#3a3226")
for y in range(9, 21):
    for x in range(11, 21):
        g.put(x, y, "#c0904a" if (x + y) % 3 else "#5a5448")             # 鐵絲網＋外面的光
g.rect(1, 56, 30, 64, "#7a7a70")                                          # 踢板
g.rect(25, 36, 27, 37, "#b8b0a0"); g.put(26, 38, "#6a6a60")               # 門把
for x in (0, 31):
    g.vline(x, 0, 66, "#3a2a1c")
g.hline(0, 31, 0, "#3a2a1c")
for i in range(5):
    blob(g, int(h(i, 1, 132) * 32), int(10 + h(i, 2, 132) * 50), 2, "#8a7a5e", i * 3 + 7, wrap=False, density=0.7)

# ---- 圖卡（每張 0.5 m 見方，2 倍密度 32×32；6 張排成 96×64）----
# 照 2D 版圖卡（props/cards.png）的感覺：舊圖卡的配色（紙 #D8D2BC、近黑的粗框、暗紅、灰綠衣服）、沒有表情、泛黃水漬、膠帶、捲角。
# 上排：蘋果、媽媽、房子（回家）；下排：水杯、手、被撕掉只剩膠帶和一角的一張（主角不是華人，不用注音；作者 B3-2b 決定）
g = sheet("cards", 96, 64, "fit 2x")
INK = "#16181c"


def card(i):
    x0, y0 = (i % 3) * 32, (i // 3) * 32
    P = lambda x, y, c: g.put(x0 + x, y0 + y, c)
    R = lambda xa, ya, xb, yb, c: g.rect(x0 + xa, y0 + ya, x0 + xb, y0 + yb, c)
    E = lambda cx, cy, rx, ry, c: g.ellipse(x0 + cx, y0 + cy, rx, ry, c)
    if i == 5:                                                            # 撕掉了：牆面＋比較乾淨的一塊＋膠帶上的紙角
        for y in range(32):
            for x in range(32):
                clean = 3 <= x <= 28 and 2 <= y <= 29
                P(x, y, shade("#aca07a" if clean else "#a0946e", 0.92 + (h(x0 + x, y0 + y, 102) - 0.5) * 0.10))
        R(2, 1, 7, 3, "#c8c0a0"); R(24, 1, 29, 3, "#c8c0a0")
        for t in range(5):
            g.hline(x0 + 3, x0 + 8 - t, y0 + 4 + t, "#b3ab90")            # 左上角留下的三角形紙片
        blob(g, x0 + 16, y0 + 20, 3, "#8a7e5e", 171, wrap=False, density=0.5)
        return
    for y in range(32):                                                   # 紙：邊緣比較暗、泛黃
        for x in range(32):
            e = min(x, y, 31 - x, 31 - y)
            P(x, y, shade("#d8d2bc", 0.88 + h(x0 + x, y0 + y, 170) * 0.07 - (0.10 if e < 3 else 0.04 if e < 5 else 0)))
    if i == 0:                                                            # 蘋果
        E(16, 17, 10, 9, INK); E(16, 17, 9, 8, "#9c3a2e")
        for y in range(10, 26):
            for x in range(17, 26):
                if (x - 16) ** 2 / 81 + (y - 17) ** 2 / 64 <= 1 and (x - 14) ** 2 / 64 + (y - 15) ** 2 / 56 > 1:
                    P(x, y, "#5f2a22")
        P(12, 13, "#b0564a"); P(13, 13, "#b0564a"); P(12, 14, "#b0564a")
        g.vline(x0 + 16, y0 + 4, y0 + 9, INK); g.vline(x0 + 17, y0 + 5, y0 + 8, "#2b2622")
        R(18, 5, 21, 6, INK); R(19, 6, 22, 7, "#5c6b65")
    elif i == 1:                                                          # 媽媽（頭和肩膀、長頭髮、沒有表情）
        E(16, 31, 12, 7, INK); E(16, 31, 11, 6, "#5c6b65")
        R(14, 21, 18, 25, "#a8826a")
        E(16, 13, 9, 9, INK); R(7, 13, 25, 24, INK)
        E(16, 15, 6, 7, "#c49a7c")
        for y in range(9, 23):
            for x in range(18, 23):
                if (x - 16) ** 2 / 42 + (y - 15) ** 2 / 56 <= 1 and (x - 15) ** 2 / 25 + (y - 14) ** 2 / 49 > 1:
                    P(x, y, "#a8826a")
        g.hline(x0 + 10, x0 + 22, y0 + 8, INK); g.hline(x0 + 11, x0 + 21, y0 + 9, INK)
        P(13, 15, INK); P(19, 15, INK)
        g.hline(x0 + 15, x0 + 17, y0 + 19, "#7a5244")
    elif i == 2:                                                          # 房子（回家）
        for t in range(9):
            g.hline(x0 + 15 - t, x0 + 17 + t, y0 + 4 + t, INK)
            if t: g.hline(x0 + 16 - t, x0 + 16 + t, y0 + 4 + t, "#9c3a2e")
        g.hline(x0 + 7, x0 + 25, y0 + 13, INK)
        R(8, 14, 24, 26, INK); R(9, 14, 23, 25, "#b3ab90")
        R(13, 18, 17, 25, INK); R(14, 19, 16, 25, "#2b2622")
        R(19, 16, 22, 19, INK); R(20, 17, 21, 18, "#5c6b65")
        g.hline(x0 + 4, x0 + 27, y0 + 26, INK)
    elif i == 3:                                                          # 水杯
        for y in range(8, 26):
            w = 7 - (y - 8) * 2 // 17
            g.hline(x0 + 16 - w - 1, x0 + 16 + w + 1, y0 + y, INK)
            g.hline(x0 + 16 - w, x0 + 16 + w, y0 + y, "#5c6b65" if y >= 15 else "#c8c6b4")
        g.hline(x0 + 9, x0 + 23, y0 + 15, "#7a8a84")
        g.hline(x0 + 9, x0 + 23, y0 + 26, INK)
        g.vline(x0 + 11, y0 + 10, y0 + 13, "#e4e0d0")
    elif i == 4:                                                          # 手（張開的手掌）
        for k, (x, top) in enumerate(((11, 8), (14, 5), (17, 5), (20, 7))):
            R(x - 1, top - 1, x + 2, 16, INK); R(x, top, x + 1, 16, "#c49a7c")
        R(9, 14, 23, 27, INK); R(10, 15, 22, 26, "#c49a7c")
        for t in range(5):
            R(9 - t, 19 - t, 11 - t, 22 - t, INK)
        for t in range(4):
            R(9 - t, 20 - t, 10 - t, 21 - t, "#c49a7c")
        R(12, 27, 20, 30, INK); R(13, 27, 19, 30, "#c49a7c")
        g.vline(x0 + 21, y0 + 16, y0 + 25, "#a8826a"); g.hline(x0 + 13, x0 + 21, y0 + 26, "#a8826a")
        g.line(x0 + 13, y0 + 21, x0 + 18, y0 + 18, "#a8826a")
    for k in range(3):                                                    # 水漬、髒
        blob(g, x0 + 4 + int(h(i, k, 172) * 24), y0 + 4 + int(h(k, i, 172) * 24), 2, "#b3ab90", i * 7 + k, wrap=False, density=0.45)
    blob(g, x0 + 6 + int(h(i, 9, 173) * 18), y0 + 27, 3, "#a89a7c", i + 180, wrap=False, density=0.6)
    for k in (0, 31):                                                     # 粗框
        g.hline(x0, x0 + 31, y0 + k, INK); g.vline(x0 + k, y0, y0 + 31, INK)
    g.hline(x0 + 1, x0 + 30, y0 + 1, "#2b2622"); g.vline(x0 + 1, y0 + 1, y0 + 30, "#2b2622")
    R(3, 0, 8, 2, "#c8c0a0"); R(23, 0, 28, 2, "#c8c0a0")                  # 膠帶
    g.hline(x0 + 3, x0 + 8, y0 + 2, "#a89a7c"); g.hline(x0 + 23, x0 + 28, y0 + 2, "#a89a7c")
    if i in (0, 3, 4):                                                    # 右下角捲起來
        for t in range(6):
            for s in range(6 - t):
                P(31 - t, 31 - s, "#2b2622" if s + t >= 5 else "#b3ab90")
        g.line(x0 + 26, y0 + 31, x0 + 31, y0 + 26, "#8a8068")


for i in range(6):
    card(i)

# ---- 海報（2 倍密度；左：洗手〔0.5 × 0.7 m＝32×45〕、右：佈告欄上的紙〔1 × 0.7 m＝64×45〕，排成 96×45） ----
g = sheet("posters", 96, 45, "fit 2x")
noise_fill(g, "#d8d0b8", 0.06, 136, rect=(0, 0, 31, 44))
g.rect(0, 0, 31, 7, "#3a7a5a")
for x in range(4, 28, 5):
    g.rect(x, 3, x + 2, 4, "#e8f0e8")                                     # 標題（看不清的字）
g.ellipse(16, 20, 8, 7, "#e0b890"); g.ellipse(16, 20, 5, 4, "#c89870")    # 兩隻手
for t in range(6):
    g.put(10 + t * 2, 30 + (t % 2), "#6aa0c0")                            # 水滴
for y in range(34, 42, 3):
    g.hline(4, 27, y, "#7a7468")
g.rect(36, 0, 95, 44, "#6a4e34"); g.rect(38, 2, 93, 42, "#8a6e4a")        # 佈告欄（軟木）
for i in range(6):
    x0, y0 = 40 + (i % 3) * 18, 4 + (i // 3) * 19
    c = ("#e0dccc", "#d8c898", "#c8d8c8")[i % 3]
    g.rect(x0, y0, x0 + 14, y0 + 16, c)
    for y in range(y0 + 3, y0 + 15, 3):
        g.hline(x0 + 2, x0 + 12, y, "#8a8478")
    g.put(x0 + 7, y0 + 1, "#b83a30")                                      # 圖釘
g.rect(76, 23, 92, 40, "#8a6e4a")                                         # 掉了一張

# ---- 病歷櫃正面（2 × 1.6 m，fit 64×51）：4 層木架、彩色的病歷夾、空掉的格子 ----
g = sheet("files", 64, 51, "fit")
noise_fill(g, "#4a3a28", 0.06, 137)
for row in range(4):
    y0 = 2 + row * 12
    g.rect(1, y0, 62, y0 + 9, "#2a2018")
    x = 2
    while x < 61:
        w = 1 + int(h(x, row, 138) * 2)
        if h(x, row, 139) < 0.15:
            x += 4; continue                                              # 空格（被翻過）
        c = ("#c8b890", "#a05a3a", "#5a7a9a", "#c8c0a8", "#8a9a5a")[int(h(x, row, 140) * 5)]
        top = y0 + int(h(x, row, 141) * 3)
        g.rect(x, top, x + w - 1, y0 + 9, shade(c, 0.85 + h(x, row, 142) * 0.25))
        x += w + (1 if h(x, row, 143) < 0.3 else 0)
    g.hline(0, 63, y0 + 10, "#5a4630"); g.hline(0, 63, y0 + 11, "#3a2a1c")

# ---- 爬藤（透明底）：吊下來的一串（1 × 2 m，32×64）、牆上的一片（2 × 1.5 m，64×48） ----
g = sheet("ivy_hang", 32, 64, "fit alpha")
for s in range(4):
    x = 6 + s * 7
    for y in range(0, 20 + int(h(s, 1, 144) * 40)):
        x += 1 if h(s, y, 145) < 0.2 else (-1 if h(s, y, 145) > 0.8 else 0)
        g.put(x, y, "#3e3420")
        if y % 4 == 0:
            leaf(g, x + (2 if (y // 4) % 2 else -2), y + 1, (0.6 if (y // 4) % 2 else 2.5) + h(s, y, 146), 3,
                 "#56603a" if h(s, y, 147) < 0.6 else "#3e4a2a", s * 100 + y)
g = sheet("ivy_wall", 64, 48, "fit alpha")
for i in range(70):
    d = h(i, 3, 148)
    cx, cy = int(h(i, 1, 148) * 64), int(h(i, 2, 148) ** 0.7 * 46)
    if math.hypot((cx - 32) / 32, (cy - 18) / 30) < 1.0:
        leaf(g, cx, cy, d * 6.28, 2 + int(h(i, 4, 148) * 2), "#56603a" if d < 0.55 else "#3e4a2a", i)
for s in range(5):                                                       # 藤
    x = 8 + s * 12
    for y in range(4, 44):
        x += 1 if h(s, y, 149) < 0.25 else (-1 if h(s, y, 149) > 0.75 else 0)
        if g.get(x, y) is None or h(x, y, 150) < 0.3:
            g.put(x, y, "#3e3420")

# ---- 藥罐（0.5 m 一格）：褐色的塑膠罐、白色標籤 ----
g = sheet("pills", 16, 16, "tile 0.5m")
noise_fill(g, "#a0642a", 0.08, 151)
g.rect(0, 5, 15, 10, "#e0dccc")
for x in range(2, 14, 3):
    g.put(x, 7, "#7a7468"); g.put(x + 1, 8, "#7a7468")
g.hline(0, 15, 0, "#e0dccc"); g.hline(0, 15, 1, "#c8c4b4")               # 白色的蓋子

# ---- 病歷夾（2 倍密度 0.25 × 0.35 m＝16×22）：褐色板子、夾子、紙、血手印 ----
g = sheet("clipboard", 16, 22, "fit 2x")
noise_fill(g, "#7a5a3a", 0.06, 152)
g.rect(2, 3, 13, 20, "#e0dccc")
for y in range(6, 19, 2):
    g.hline(3, 12, y, "#8a8478")
g.rect(5, 0, 10, 3, "#9a9a90"); g.hline(6, 9, 1, "#6a6a60")
blob(g, 10, 15, 2, "#6a1a14", 153, wrap=False, density=0.9)

# ---- 紙箱（1 m 一格）：瓦楞紙、膠帶、受潮的深色 ----
g = sheet("box", 32, 32, "tile 1m")
noise_fill(g, "#9a7a50", 0.08, 154)
g.rect(14, 0, 17, 31, "#b89a6a")
for i in range(3):
    blob(g, int(h(i, 1, 155) * 32), int(20 + h(i, 2, 155) * 10), 3, "#7a5e3a", i + 50, density=0.6)

# ---- 花盆（0.5 m 一格）：陶土 ----
g = sheet("pot", 16, 16, "tile 0.5m")
noise_fill(g, "#9a5a3a", 0.08, 156)
g.hline(0, 15, 2, "#7a4430"); g.hline(0, 15, 3, "#b86e4a")

# ---- 藥櫃、推車的烤漆（1 m 一格）：米白、掉漆、鏽 ----
g = sheet("cabinet_paint", 32, 32, "tile 1m")
noise_fill(g, "#c8c0a8", 0.05, 157)
for i in range(6):
    blob(g, int(h(i, 1, 158) * 32), int(h(i, 2, 158) * 32), 1 + int(h(i, 3, 158) * 2), "#8a5a3a" if i % 2 else "#9a9484", i * 9, density=0.8)

# ---- 共用：落葉（1 m 見方的一片地面貼花，透明底） ----
g = sheet("leaves", 32, 32, "fit alpha")
for i in range(18):
    cx, cy = int(3 + h(i, 1, 159) * 26), int(3 + h(i, 2, 159) * 26)
    c = ("#7a5a2a", "#8a6a30", "#5a4a24", "#6a6a30")[int(h(i, 3, 159) * 4)]
    leaf(g, cx, cy, h(i, 4, 159) * 6.28, 2, c, i + 200)

export(SHEETS, OUTDIR)
