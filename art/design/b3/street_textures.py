# B3-1b 街道的像素貼圖（32 像素＝1 m；共用的水泥、金屬、玻璃、輪胎等在 assets/textures/common/，這裡只畫街道專屬的）。
# 用法：python3 art/design/b3/street_textures.py 輸出資料夾 → 每張的 .txt、.png 與 preview.png
import sys
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/tools")
from pix import Grid
from texlib import h, shade, noise_fill, blob, crack, export

OUTDIR = sys.argv[1]
SHEETS = {}


def sheet(name, w, h_, kind):
    g = Grid(w, h_)
    SHEETS[name] = (g, kind)
    return g


# ---- 柏油路（2 m 一格）：暖灰、補過的色塊、裂縫、碎石亮點 ----
g = sheet("asphalt", 64, 64, "tile 2m")
noise_fill(g, "#4a443c", 0.08, 31)
for cx, cy, r in ((16, 44, 7), (50, 14, 5)):
    blob(g, cx, cy, r, "#3e3832", cx + cy)
crack(g, 8, 4, 30, 41, "#2a2622")
crack(g, 38, 30, 28, 47, "#2a2622")
crack(g, 52, 40, 16, 53, "#302b26")
for i in range(26):
    g.put(int(h(i, 1, 33) * 64), int(h(i, 2, 33) * 64), "#5a544a")

# ---- 人行道（2 m 一格）：50 cm 的方磚、磚縫、缺角 ----
g = sheet("sidewalk", 64, 64, "tile 2m")
for ty in range(4):
    for tx in range(4):
        base = shade("#6a5e50", 0.92 + h(tx, ty, 34) * 0.16)
        noise_fill(g, base, 0.05, 35 + tx * 4 + ty, rect=(tx * 16, ty * 16, tx * 16 + 15, ty * 16 + 15))
for k in range(0, 64, 16):
    g.hline(0, 63, k, "#4e463c")
    g.vline(k, 0, 63, "#4e463c")
for cx, cy in ((22, 37), (45, 9), (7, 55)):
    blob(g, cx, cy, 2, "#544a40", cx * cy, density=0.9)
crack(g, 34, 18, 12, 36, "#463e34")

# ---- 磚牆（2 m 一格）：一塊磚 25×12.5 cm（8×4 像素含灰縫），每排錯開半塊，煙燻 ----
g = sheet("brick", 64, 64, "tile 2m")
for y in range(64):
    row = y // 4
    for x in range(64):
        xx = (x + (4 if row % 2 else 0)) % 64
        bx = xx // 8
        if y % 4 == 3 or xx % 8 == 7:
            c = "#4e3a2c"
        else:
            c = shade("#6e4a36", 0.88 + h(bx, row, 37) * 0.22 + (h(x, y, 38) - 0.5) * 0.08)
        g.put(x, y, c)
for cx, cy, r in ((12, 10, 6), (44, 40, 8)):
    blob(g, cx, cy, r, "#3e2c22", cx + cy * 3, density=0.5)

# ---- 鐵捲門（1 m 一格）：橫向的板條、鏽 ----
g = sheet("shutter", 32, 32, "tile 1m")
for y in range(32):
    c = "#6a6a62" if y % 3 != 2 else "#4e4e48"
    for x in range(32):
        g.put(x, y, shade(c, 0.95 + (h(x, y, 39) - 0.5) * 0.12))
for i in range(6):
    blob(g, int(h(i, 1, 40) * 32), int(h(i, 2, 40) * 32), 2, "#6a3a2a", i, density=0.7)

# ---- 窗戶（1 × 1.5 m，fit）：木框、十字窗格、暗玻璃與反光，右上一格破掉 ----
g = sheet("window", 32, 48, "fit")
noise_fill(g, "#1e2224", 0.10, 41)
for x0, y0 in ((3, 3), (17, 3), (3, 25), (17, 25)):
    g.line(x0 + 2, y0 + 16, x0 + 10, y0 + 2, "#2e3438")
for k in (0, 1, 30, 31):
    g.vline(k, 0, 47, "#4a3a2c"); g.hline(0, 31, k if k < 2 else k + 16, "#4a3a2c")
g.vline(15, 0, 47, "#4a3a2c"); g.vline(16, 0, 47, "#4a3a2c")
g.hline(0, 31, 23, "#4a3a2c"); g.hline(0, 31, 24, "#4a3a2c")
for y in range(4, 20):                             # 破掉的那格：黑洞＋鋸齒邊
    for x in range(19, 29):
        if h(x, y, 42) < 0.85 - abs(x - 24) * 0.04 - abs(y - 11) * 0.03:
            g.put(x, y, "#0c0a08")

# ---- 黃色標線（0.5 m 一格）：舊漆、露出柏油 ----
g = sheet("lane", 16, 16, "tile 0.5m")
for y in range(16):
    for x in range(16):
        r = h(x, y, 43)
        g.put(x, y, "#b8963c" if r < 0.68 else ("#8e763a" if r < 0.88 else "#4a443c"))

# ---- 燒焦的車體（1 m 一格）：焦黑、鏽、殘餘的火星 ----
g = sheet("burnt", 32, 32, "tile 1m")
noise_fill(g, "#2a2420", 0.12, 44)
for i in range(7):
    blob(g, int(h(i, 1, 45) * 32), int(h(i, 2, 45) * 32), 3, "#5a3a28", i + 3, density=0.55)
for i in range(9):
    g.put(int(h(i, 3, 46) * 32), int(h(i, 4, 46) * 32), "#8a4a20")

# ---- 木板（1 × 0.5 m 一格）：木紋 ----
g = sheet("wood", 32, 16, "tile 1m")
for y in range(16):
    for x in range(32):
        k = 0.9 + 0.14 * ((y + int(h(x // 6, y, 47) * 2)) % 4 == 0) + (h(x, y, 48) - 0.5) * 0.08
        g.put(x, y, shade("#6a4e34", k))
g.hline(0, 31, 7, "#4a3424")

# ---- 停車場招牌（0.5 m 見方，2 倍密度 32×32）：藍底白「P」 ----
g = sheet("sign_p", 32, 32, "fit")
g.rect(0, 0, 31, 31, "#2a4a7a"); g.rect(1, 1, 30, 30, "#e0e4e8"); g.rect(3, 3, 28, 28, "#2a4a7a")
for y in range(8, 25):
    g.rect(10, y, 12, y, "#e0e4e8")
g.rect(10, 8, 19, 9, "#e0e4e8"); g.rect(10, 16, 19, 17, "#e0e4e8"); g.rect(19, 9, 21, 16, "#e0e4e8")
blob(g, 25, 26, 3, "#4a3a2a", 49, wrap=False, density=0.6)

# ---- 診所招牌（0.5 m 見方，32×32）：白底綠十字 ----
g = sheet("sign_clinic", 32, 32, "fit")
noise_fill(g, "#d8d4c8", 0.06, 50)
g.rect(0, 0, 31, 1, "#8a8a80"); g.rect(0, 30, 31, 31, "#8a8a80"); g.rect(0, 0, 1, 31, "#8a8a80"); g.rect(30, 0, 31, 31, "#8a8a80")
g.rect(12, 6, 19, 25, "#2a8a4a"); g.rect(6, 12, 25, 19, "#2a8a4a")
blob(g, 6, 26, 3, "#6a5a48", 51, wrap=False, density=0.6)

# ---- 店面招牌（2 × 0.5 m，fit）：褪色的底＋看不清的字塊 ----
g = sheet("shopsign", 64, 16, "fit")
noise_fill(g, "#7a3a2a", 0.10, 52)
g.rect(0, 0, 63, 0, "#4a2a20"); g.rect(0, 15, 63, 15, "#4a2a20")
for i, x0 in enumerate((8, 20, 32, 44)):           # 四個褪色的大字（只看得出筆畫）
    for y in range(4, 12):
        for x in range(x0, x0 + 9):
            if h(x, y, 53 + i) < 0.42 and (y in (4, 7, 11) or x in (x0, x0 + 4, x0 + 8)):
                g.put(x, y, "#c8b89a")

# ---- 遠處的建築（2 m 一格，較低密度）：暗、少數亮著的窗 ----
g = sheet("far", 32, 32, "tile 2m")
noise_fill(g, "#5a3826", 0.06, 54)
for wy in range(2, 32, 8):
    for wx in range(2, 32, 6):
        c = "#d08a3a" if h(wx, wy, 55) < 0.12 else "#3e2618"
        g.rect(wx, wy, wx + 2, wy + 3, c)

# ---- 三角錐（fit）：橘白相間 ----
g = sheet("cone", 16, 32, "fit")
for y in range(32):
    band = y in range(8, 12) or y in range(18, 22)
    for x in range(16):
        g.put(x, y, shade("#e0e0d8" if band else "#c8602a", 0.92 + (h(x, y, 56) - 0.5) * 0.12))

# ---- 舊報紙（0.5 m 一格）：米色、一行行的字 ----
g = sheet("paper", 16, 16, "tile 0.5m")
noise_fill(g, "#b8b0a0", 0.06, 57)
for y in range(2, 16, 3):
    for x in range(1, 15):
        if h(x, y, 58) < 0.7:
            g.put(x, y, "#7a7468")

export(SHEETS, OUTDIR)
