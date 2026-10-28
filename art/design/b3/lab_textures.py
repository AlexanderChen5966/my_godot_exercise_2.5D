# B3-3b 設施走廊的像素貼圖（32 像素＝1 m）。
# 共用的金屬、木板、玻璃、燒焦、碎布、舊報紙在 assets/textures/common/；天花板借診所的 clinic/ceiling、出口牌借停車場的 parking/sign、
# 地上的病歷夾借 clinic/clipboard。這裡畫設施走廊專屬的（輸出到 assets/textures/lab/）。
# 不畫可讀的字（主角不是華人；作者 B3-2b）：標示用圖形、色塊、看不清的線。
# 用法：python3 art/design/b3/lab_textures.py 輸出資料夾 → 每張的 .txt、.png 與 preview.png
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


# ---- 牆（寬 2 m 一格、高 3 m 整面，64×96）：下面 1 m 深色木板護牆（直條）、木條，上面灰白漆；從天花板流下來的髒污、水漬 ----
g = sheet("wall_lab", 64, 96, "tile 2m × 3m")
for y in range(96):
    for x in range(64):
        z = 3.0 - (y + 0.5) / 32
        if z < 1.0:
            c = shade("#5a4a3a", 0.9 + (h(x, y, 201) - 0.5) * 0.12 - (0.18 if x % 8 == 0 else 0) - (0.08 if z < 0.1 else 0))
        else:
            streak = 0.10 * h(x // 2, 0, 202) * max(0.0, (z - 1.6) / 1.4)     # 越上面越髒
            c = shade("#8a8676", 0.94 + (h(x, y, 203) - 0.5) * 0.08 - streak)
        g.put(x, y, c)
g.hline(0, 63, 63, "#3a2e22"); g.hline(0, 63, 64, "#6e5a44"); g.hline(0, 63, 65, "#2e241a")   # 木條（z 1.0）
for i in range(5):                                                        # 從上面流下來的水漬
    x = int(h(i, 1, 204) * 64)
    n = 10 + int(h(i, 2, 204) * 24)
    for k in range(n):
        g.put((x + (1 if h(i, k, 205) < 0.2 else 0)) % 64, k, shade("#6e6a5c", 0.95 + h(i, k, 206) * 0.1))
for i in range(4):
    blob(g, int(h(i, 3, 207) * 64), int(14 + h(i, 4, 207) * 40), 2 + int(h(i, 5, 207) * 2), "#7a7668", i + 30, density=0.6)
crack(g, 40, 20, 18, 208, "#5e5a4e")

# ---- 地板（1 m 一格，32×32）：50 cm 塑膠地磚，兩種灰褐交錯、接縫、刮痕、髒污 ----
g = sheet("floor_lab", 32, 32, "tile 1m")
for y in range(32):
    for x in range(32):
        c = "#6e6a60" if ((x // 16) + (y // 16)) % 2 == 0 else "#625e56"
        c = shade(c, 0.94 + (h(x, y, 210) - 0.5) * 0.08)
        if x % 16 == 0 or y % 16 == 0:
            c = shade(c, 0.78)
        g.put(x, y, c)
for i in range(3):
    x0, y0 = int(h(i, 1, 211) * 32), int(h(i, 2, 211) * 32)
    for k in range(5 + int(h(i, 3, 211) * 5)):
        g.put((x0 + k) % 32, (y0 + k // 3) % 32, "#7a766c")              # 刮痕
blob(g, 22, 8, 3, "#55524a", 212, density=0.55)

# ---- 觀察窗（2 × 1.2 m，fit 64×38，透明）：金屬窗框＋中間的直框，玻璃大多破了，只剩邊上的碎片 ----
g = sheet("window_lab", 64, 38, "fit alpha")
F = "#5a5e60"
for x in range(64):
    for y in (0, 1, 36, 37):
        g.put(x, y, shade(F, 0.8 if y in (1, 36) else 1.0))
for y in range(38):
    for x in (0, 1, 31, 32, 62, 63):
        g.put(x, y, shade(F, 0.85 if x in (1, 32, 62) else 1.0))
def shard(x0, y0, dx, dy, n, seed):
    """從窗框長出來的一塊三角形碎玻璃"""
    for k in range(n):
        w = n - k
        for s in range(w):
            x, y = x0 + dx * k + (s if dy else 0), y0 + dy * k + (s if dx else 0)
            if 2 <= x <= 61 and 2 <= y <= 35 and x not in (31, 32):
                g.put(x, y, shade("#7a9aa8", 0.9 + h(x, y, seed) * 0.15) if (x + y) % 7 else "#b8d0d8")
shard(2, 2, 1, 0, 9, 213); shard(2, 30, 0, -1, 7, 214); shard(25, 2, 0, 1, 6, 215)
shard(33, 2, 0, 1, 12, 216); shard(52, 2, 1, 0, 8, 217); shard(55, 35, 0, -1, 5, 218); shard(33, 35, 0, -1, 4, 219)
for y in range(20, 36):                                                   # 右半邊下面還有一大塊有裂痕的玻璃
    for x in range(44, 62):
        if x - 44 > (36 - y) * 0.9:
            g.put(x, y, "#5a6e78" if (x * 3 + y * 5) % 23 == 0 else shade("#7a9aa8", 0.88 + h(x, y, 220) * 0.12))

# ---- 螢幕（0.5 × 0.375 m，16×12）：黑框、暗青綠的畫面、波形 ----
g = sheet("monitor", 16, 12, "fit")
g.rect(0, 0, 15, 11, "#2a2c2e")
g.rect(1, 1, 14, 9, "#0e2a26")
for x in range(2, 14):
    y = 5 + int(round(2.2 * math.sin(x * 0.9) * (1 if x % 5 else 0.3)))
    g.put(x, y, "#4ac8a0")
g.hline(2, 6, 2, "#2a7a64"); g.hline(9, 12, 8, "#2a7a64")
g.hline(5, 10, 10, "#3a3c3e")

# ---- 實驗架上的瓶罐（1 × 0.5 m，fit 32×16）：一層的正面；燒杯、試劑瓶（暗綠、琥珀、混濁），後面是暗的 ----
g = sheet("jars", 32, 16, "fit")
g.rect(0, 0, 31, 15, "#1e2022")
x = 1
i = 0
while x < 30:
    w = 3 + int(h(i, 1, 221) * 3)
    hh = 6 + int(h(i, 2, 221) * 7)
    if h(i, 3, 221) < 0.18:                                               # 空出來的位置
        x += w + 1; i += 1; continue
    c = ("#4a6a4a", "#8a6a2a", "#7a8a8a", "#5a3a2a", "#6a7a5a")[int(h(i, 4, 221) * 5)]
    top = 15 - hh
    g.rect(x, top + 2, x + w - 1, 15, shade("#8a9aa0", 0.7))             # 玻璃
    lvl = top + 2 + int((hh - 2) * h(i, 5, 221) * 0.6)
    g.rect(x, lvl, x + w - 1, 15, shade(c, 0.9))                         # 液體
    g.rect(x + w // 2 - 1 if w > 3 else x, top, x + w // 2 if w > 3 else x + 1, top + 1, "#4a4a48")   # 瓶口
    g.vline(x, top + 2, 15, shade("#b8c8c8", 0.8))                        # 反光
    x += w + 1; i += 1

# ---- 木箱（1 m 一格，32×32）：橫的木板、外框、釘子、噴漆的箭頭與方塊標記（沒有字） ----
g = sheet("crate", 32, 32, "tile 1m")
for y in range(32):
    for x in range(32):
        c = shade("#8a6a40", 0.9 + (h(x, y, 222) - 0.5) * 0.14 + (0.06 if (y // 6) % 2 else 0))
        if y % 6 == 0:
            c = shade(c, 0.7)
        g.put(x, y, c)
for k in (0, 1, 30, 31):
    g.hline(0, 31, k, "#6a4e2e"); g.vline(k, 0, 31, "#6a4e2e")
for x, y in ((3, 3), (28, 3), (3, 28), (28, 28)):
    g.put(x, y, "#3a3a38")
for t in range(5):                                                        # 噴漆的箭頭（朝上）
    g.hline(8 - t, 8 + t, 9 + t, "#2a2622")
g.rect(7, 14, 9, 21, "#2a2622")
g.rect(17, 11, 25, 19, "#2a2622"); g.rect(19, 13, 23, 17, "#8a6a40")       # 方塊標記
blob(g, 24, 25, 3, "#5a4428", 223, density=0.5)

# ---- 檔案櫃（0.5 × 1.3 m，fit 16×42）：灰綠烤漆、4 個抽屜、把手、標籤框、凹痕 ----
g = sheet("filecab", 16, 42, "fit")
noise_fill(g, "#6a7068", 0.06, 224)
for d in range(4):
    y0 = 1 + d * 10
    g.rect(1, y0, 14, y0 + 8, shade("#6a7068", 1.05))
    g.hline(1, 14, y0 + 8, "#4a4e48"); g.vline(14, y0, y0 + 8, "#4a4e48")
    g.rect(5, y0 + 2, 10, y0 + 3, "#c8c4b0"); g.hline(6, 9, y0 + 2, "#9a9688")   # 標籤框（看不清的字）
    g.rect(6, y0 + 5, 9, y0 + 6, "#3a3c38")                              # 把手
blob(g, 11, 25, 2, "#4e5450", 225, wrap=False, density=0.7)
blob(g, 3, 36, 2, "#7a5a3a", 226, wrap=False, density=0.6)

# ---- 散落的紀錄（1 × 0.5 m，fit 32×16，透明）：牛皮紙夾、藍色夾子、一張張的紙（地上的貼花） ----
g = sheet("folders", 32, 16, "fit alpha")
items = [(2, 3, 9, 6, "#c8a870", 1), (12, 1, 8, 6, "#d8d4c4", 0), (20, 5, 9, 7, "#5a6a8a", 1), (6, 9, 8, 6, "#d8d4c4", 0),
         (15, 9, 9, 6, "#c8a870", 1), (25, 1, 6, 5, "#d8d4c4", 0)]
for i, (x0, y0, w, hh, c, folder) in enumerate(items):
    sk = 1 if i % 2 else 0
    for y in range(hh):
        for x in range(w):
            g.put(x0 + x + (y // 3) * sk, y0 + y, shade(c, 0.92 + h(x, y, 227 + i) * 0.1))
    if folder:
        g.hline(x0, x0 + w - 1, y0, shade(c, 0.75))
    else:
        for y in range(y0 + 1, y0 + hh - 1, 2):
            g.hline(x0 + 1, x0 + w - 3, y, "#8a8678")                     # 看不清的字

# ---- 通風管口（0.75 m 見方，24×24）：金屬外框、橫的百葉、暗的縫 ----
g = sheet("vent", 24, 24, "fit")
g.rect(0, 0, 23, 23, "#6a6e70")
g.rect(2, 2, 21, 21, "#141618")
for y in range(3, 21, 3):
    g.hline(2, 21, y, "#7a7e80"); g.hline(2, 21, y + 1, "#5a5e60")
for x, y in ((1, 1), (22, 1), (1, 22), (22, 22)):
    g.put(x, y, "#3a3c3e")
blob(g, 18, 6, 2, "#7a5a3a", 228, wrap=False, density=0.5)

# ---- 出口的鐵門（1.4 × 2.1 m，fit 45×67）：灰綠鐵板、凹痕、推桿、上面的鐵絲網玻璃小窗、焦痕 ----
g = sheet("door_metal", 45, 67, "fit")
noise_fill(g, "#5e6a62", 0.06, 229)
for k in (0, 44):
    g.vline(k, 0, 66, "#3e4842")
g.hline(0, 44, 0, "#3e4842"); g.hline(0, 44, 66, "#3e4842")
g.rect(14, 8, 30, 22, "#3e4842"); g.rect(15, 9, 29, 21, "#c8c0a0")        # 小窗（外面的光）
for y in range(9, 22, 3):
    g.hline(15, 29, y, "#9a9070")
for x in range(15, 30, 3):
    g.vline(x, 9, 21, "#9a9070")
g.rect(4, 34, 40, 36, "#8a8e90"); g.hline(4, 40, 37, "#4a4e50")           # 推桿
g.rect(36, 30, 38, 40, "#6a6e70")
for i in range(3):
    blob(g, 8 + int(h(i, 1, 230) * 28), 44 + int(h(i, 2, 230) * 18), 3, "#4a5450", i + 60, wrap=False, density=0.6)   # 凹痕
blob(g, 6, 60, 5, "#2a2622", 231, wrap=False, density=0.55)               # 焦痕

# ---- 燒焦的痕跡（2 m 見方，fit 64×64，透明）：起火的門口周圍，中間最黑、往外淡出 ----
g = sheet("soot", 64, 64, "fit alpha")
for by in range(32):                                                      # 2×2 一格（1 像素一格會像撒胡椒，B3-1d 的教訓）
    for bx in range(32):
        x, y = bx * 2, by * 2
        dx, dy = (x - 31) / 30, (y - 40) / 36
        d = math.hypot(dx * (1.0 + 0.25 * h(by, 0, 233)), dy * (0.75 if y < 40 else 1.6))
        if d < 0.55 or (d < 1 and h(bx, by, 232) < 1.35 - d * 1.2):
            c = shade("#1a1612", 0.8 + d * 0.9 + (h(bx, by, 234) - 0.5) * 0.15)
            g.rect(x, y, x + 1, y + 1, c)

# ---- 出口牌（0.7 × 0.25 m，2 倍密度 fit 45×16）：綠底、白色的逃生人形＋門＋箭頭（國際通用的圖形，不用字；停車場的 parking/sign 有中文「出口」） ----
g = sheet("exit_sign", 45, 16, "fit 2x")
g.rect(0, 0, 44, 15, "#1e7a4a")
g.rect(1, 1, 43, 14, "#2a9a5a")
W_ = "#e8f0e8"
g.rect(4, 3, 11, 13, W_); g.rect(5, 4, 10, 13, "#2a9a5a")                # 門
RUN = ["......##.", "......##.", "....####.", "...#.###.", "..#..####", ".....##..", "....###..", "...##.##.", "..##...#.", ".##....##"]
for dy, row in enumerate(RUN):                                            # 跑向門口的人（逐格的圖案）
    for dx, v in enumerate(row):
        if v == "#":
            g.put(13 + dx, 3 + dy, W_)
for t in range(4):                                                        # 箭頭（往右）
    g.vline(36 + t, 8 - (3 - t), 8 + (3 - t), W_)
g.rect(26, 7, 35, 9, W_)

export(SHEETS, OUTDIR)
