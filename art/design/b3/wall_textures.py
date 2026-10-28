# B3-6b 牆前的像素貼圖（32 像素＝1 m；炭筆字用 2 倍密度 64 像素＝1 m）。
# 借用：地板 common/floor（水泥）、木頭 common/wood、磚 common/brick、天花板 home/ceiling_home、隔壁房間的窗 ruins/window_lit。
# 這裡畫牆前專屬的（輸出到 assets/textures/wall/）。牆上的字照原插畫寫成全大寫、沒有句點的「I'M STILL HERE」（作者 2026-10-28）。
# 用法：python3 art/design/b3/wall_textures.py 輸出資料夾 → 每張的 .txt、.png 與 preview.png
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


# ---- 舊牆（寬 2 m 一格、高 2.8 m 整面，64×90）：髒的灰褐色灰泥、從天花板流下來的水漬、下面一圈髒污、細裂縫 ----
g = sheet("wall_old", 64, 90, "tile 2m × 2.8m")
for y in range(90):
    for x in range(64):
        z = 2.8 - (y + 0.5) / 32
        stain = 0.10 * h(x // 3, 1, 801) * max(0.0, (z - 1.8) / 1.0)      # 越上面越髒
        dirt = 0.14 * max(0.0, (0.4 - z) / 0.4)                            # 牆腳的髒污
        c = shade("#6e6858", 0.95 + (h(x // 2, y // 2, 802) - 0.5) * 0.08 + (h(x, y, 803) - 0.5) * 0.05 - stain - dirt)
        g.put(x, y, c)
for i in range(4):                                                        # 水漬
    x = int(h(i, 1, 804) * 64)
    for k in range(12 + int(h(i, 2, 804) * 30)):
        g.put((x + (1 if h(i, k, 805) < 0.2 else 0)) % 64, k, shade("#5a5446", 0.95 + h(i, k, 806) * 0.1))
for i in range(5):
    blob(g, int(h(i, 3, 807) * 64), int(20 + h(i, 4, 807) * 60), 2 + int(h(i, 5, 807) * 2), "#625c4e", i + 810, density=0.55)
crack(g, 18, 8, 26, 808, "#4e4a3e"); crack(g, 50, 40, 20, 809, "#4e4a3e")

# ---- 灰泥剝落露出磚（貼花，兩塊各 1 m 見方，fit 64×32，透明）：不規則的洞、裡面是磚、邊上碎掉的灰泥 ----
g = sheet("brick_patch", 64, 32, "fit alpha")
for i, (cx, cy, rx, ry) in enumerate(((16, 16, 12, 9), (48, 16, 9, 12))):
    for dy in range(-ry - 2, ry + 3):
        for dx in range(-rx - 2, rx + 3):
            x, y = cx + dx, cy + dy
            if not (0 <= x < 64 and 0 <= y < 32):
                continue
            d = math.hypot(dx / rx, dy / ry) + (h(cx + dx // 2, cy + dy // 2, 811 + i) - 0.5) * 0.3
            if d <= 0.84:
                row = y // 3
                mortar = y % 3 == 0 or (x + (row % 2) * 3) % 6 == 0
                g.put(x, y, "#4a3a30" if mortar else shade("#7a4634", 0.88 + h(x, y, 812) * 0.18))
            elif d <= 1.0:
                g.put(x, y, "#8a8474" if dy < 0 else "#3e3a30")             # 碎掉的灰泥邊（上亮下暗）

# ---- 補過的灰泥（3.1 × 2.3 m，fit 100×74，透明邊）：比舊牆亮一點（太亮會像貼了一張紙）、抹刀的弧形紋路、邊緣不規則；字的附近有灰灰的手印 ----
g = sheet("plaster_patch", 100, 74, "fit alpha")


def wobble(t, seed, amp):
    """沿著邊緣平滑起伏的位移（幾個不同頻率的正弦相加，相位用固定亂數）"""
    return amp * sum(math.sin(t * f + h(k, 1, seed) * 6.28) * w for k, (f, w) in enumerate(((0.11, 0.5), (0.27, 0.3), (0.63, 0.2))))


for y in range(74):
    for x in range(100):
        if not (3 + wobble(y, 821, 3) < x < 96 + wobble(y, 822, 3) and 3 + wobble(x, 823, 3) < y < 70 + wobble(x, 824, 3)):
            continue                                                      # 不規則的邊
        edge = min(x - 3 - wobble(y, 821, 3), 96 + wobble(y, 822, 3) - x, y - 3 - wobble(x, 823, 3), 70 + wobble(x, 824, 3) - y)
        trowel = 0.04 * math.sin((x * 0.21 + y * 0.13) + 2 * math.sin(y * 0.09))  # 抹刀的弧形紋路
        c = shade("#8e8674", 0.95 + trowel + (h(x, y, 829) - 0.5) * 0.06 - (0.07 if edge < 1.5 else 0))
        g.put(x, y, c)
for i in range(3):
    crack(g, 10 + int(h(i, 1, 824) * 80), 4 + int(h(i, 2, 824) * 20), 12 + int(h(i, 3, 824) * 14), 825 + i, "#7e7666", wrap=False)
for k, (hx, hy) in enumerate(((70, 30), (74, 34), (28, 40))):              # 手指抹過的灰痕（炭筆的灰）
    for t in range(9):
        for f in range(4):
            x, y = hx + f * 2 + t // 3, hy + t
            if g.get(x, y) and h(x, y, 826 + k) < 0.7:
                g.put(x, y, shade(g.get(x, y), 0.82))

# ---- 炭筆字（2.6 × 0.8 m，2 倍密度 fit 166×52，透明）：照原插畫兩行「I'M STILL／HERE」，筆畫粗細不一、有斷續、往下拖的炭粉 ----
GLYPH = {
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"], "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"], "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"], "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."], "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "'": ["#", "#", ".", ".", ".", ".", "."],
}
g = sheet("charcoal_words", 166, 52, "fit 2x alpha")


def charcoal_line(y, s, x0, seed):
    """一行炭筆字：每個字 3 倍大，上下晃一點；筆畫深淺不一、偶爾斷掉，下面拖一點炭粉"""
    x = x0
    for i, c in enumerate(s):
        if c == " ":
            x += 8
            continue
        dy = int(round((h(i, 1, seed) - 0.5) * 3))
        for gy, row in enumerate(GLYPH[c]):
            for gx, v in enumerate(row):
                if v != "#":
                    continue
                for sy in range(3):
                    for sx in range(3):
                        if (sx == 2 or sy == 2) and h(x + gx * 3 + sx, gy * 3 + sy, seed + 3) < 0.18:
                            continue                                      # 筆畫邊緣不整齊（粗細不一）
                        px, py = x + gx * 3 + sx, y + dy + gy * 3 + sy
                        r = h(px, py, seed + 7)
                        if r < 0.03:
                            continue                                      # 炭筆沒畫到
                        g.put(px, py, "#3a3836" if r > 0.85 else ("#121110" if r < 0.3 else "#1e1d1b"))
                if gy == 6 and h(x + gx, i, seed + 9) < 0.3:              # 往下拖的炭粉
                    g.put(x + gx * 3 + 1, y + dy + 21, "#4a4844"); g.put(x + gx * 3 + 1, y + dy + 22, "#5a5854")
        x += len(GLYPH[c][0]) * 3 + 3


charcoal_line(2, "I'M STILL", 19, 831)
charcoal_line(28, "HERE", 40, 832)

export(SHEETS, OUTDIR)
