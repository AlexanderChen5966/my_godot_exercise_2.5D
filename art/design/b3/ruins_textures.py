# B3-4b 廢墟的像素貼圖（32 像素＝1 m；牌子用 2 倍密度 64 像素＝1 m）。
# 借用：街道的柏油 street/asphalt、標線 street/lane、人行道 street/sidewalk；共用的磚、燒焦、木板、金屬、碎布在 common/。
# 這裡畫廢墟專屬的（輸出到 assets/textures/ruins/）。不畫可讀的字（主角不是華人）：路牌用圖形。
# 用法：python3 art/design/b3/ruins_textures.py 輸出資料夾 → 每張的 .txt、.png 與 preview.png
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


# ---- 斷牆的水泥（2 m 一格，64×64）：灰褐水泥、模板的接縫、從上往下的煙燻、剝落露出的磚、裂縫 ----
g = sheet("concrete_ruin", 64, 64, "tile 2m")
for y in range(64):
    for x in range(64):
        soot = 0.10 * h(x // 3, 1, 301)                                   # 一條條往下的煙燻（2×2 以上一塊，不要像撒胡椒）
        c = shade("#6a6258", 0.92 + (h(x // 2, y // 2, 302) - 0.5) * 0.10 - soot)
        if y % 32 == 0 or x % 32 == 0:
            c = shade(c, 0.82)                                            # 模板接縫
        g.put(x, y, c)
for i in range(3):                                                        # 剝落露出的磚
    cx, cy = int(h(i, 1, 303) * 64), int(h(i, 2, 303) * 64)
    for dy in range(-3, 4):
        for dx in range(-5, 6):
            if (dx / 5.5) ** 2 + (dy / 3.5) ** 2 <= 1 and h(cx + dx, cy + dy, 304) < 0.85:
                x, y = (cx + dx) % 64, (cy + dy) % 64
                g.put(x, y, "#4a3a30" if (y % 3 == 0 or (x + (y // 3) * 3) % 6 == 0) else shade("#6e4a36", 0.9 + h(x, y, 305) * 0.15))
for i in range(4):
    blob(g, int(h(i, 3, 306) * 64), int(h(i, 4, 306) * 64), 3, "#3e3a34", i + 40, density=0.55)
crack(g, 12, 6, 30, 307, "#3a342e"); crack(g, 44, 30, 22, 308, "#3a342e")

# ---- 沙包（1 × 0.5 m 一格，32×16）：兩排交錯的布袋，袋口的縫、陰影 ----
g = sheet("sandbag", 32, 16, "tile 1m × 0.5m")
for y in range(16):
    for x in range(32):
        row = y // 8
        xx = (x + (8 if row else 0)) % 16
        yy = y % 8
        edge = min(xx, 15 - xx) / 8 + min(yy, 7 - yy) / 4
        c = shade("#8a7a5a", 0.62 + min(edge, 1.0) * 0.4 + (h(x, y, 310) - 0.5) * 0.08)
        g.put(x, y, c)
    for xs in (4, 20):
        g.put((xs + (8 if y // 8 else 0)) % 32, y, shade("#6a5c40", 0.9))   # 布袋的縫線

# ---- 鐵絲網（1 m 一格，32×32，透明）：菱形的網目、鏽 ----
g = sheet("fence", 32, 32, "tile 1m alpha")
for y in range(32):
    for x in range(32):
        if (x + y) % 8 == 0 or (x - y) % 8 == 0:
            g.put(x, y, "#7a5a40" if h(x, y, 311) < 0.12 else shade("#8a8e90", 0.85 + h(x, y, 312) * 0.25))

# ---- 刺網（1 m × 0.25 m 一格，32×8，透明）：一圈圈的鐵絲＋刺 ----
g = sheet("barbed", 32, 8, "tile 1m alpha")
for x in range(32):
    y = 4 + int(round(2.6 * math.sin(x * math.pi / 4)))
    g.put(x, y, "#9a9ea0")
    y2 = 4 - int(round(2.6 * math.sin(x * math.pi / 4 + 0.8)))
    g.put(x, y2, "#7a7e80")
for x in range(2, 32, 6):
    g.put(x, 3, "#b8bcbe"); g.put(x + 1, 4, "#b8bcbe"); g.put(x, 5, "#b8bcbe")

# ---- 鐵皮（1 m 一格，32×32）：直的波浪起伏、鏽斑、釘子 ----
g = sheet("corrugated", 32, 32, "tile 1m")
for y in range(32):
    for x in range(32):
        k = 0.8 + 0.25 * math.cos(x * math.pi / 2)                       # 每 4 像素一個起伏
        g.put(x, y, shade("#6a5a48", k + (h(x, y, 313) - 0.5) * 0.08))
for i in range(6):
    blob(g, int(h(i, 1, 314) * 32), int(h(i, 2, 314) * 32), 2 + int(h(i, 3, 314) * 2), "#8a4a28", i + 50, density=0.6)
for x in (2, 18):
    g.put(x, 2, "#3a3430"); g.put(x, 29, "#3a3430")

# ---- 亮著的窗（0.75 × 0.6 m，fit 24×20，會發光）：木窗框、暖黃的光、半拉的布簾 ----
g = sheet("window_lit", 24, 20, "fit emissive")
g.rect(0, 0, 23, 19, "#3a2e22")
g.rect(2, 2, 21, 17, "#ffc070")
for y in range(2, 18):
    for x in range(2, 22):
        d = math.hypot((x - 11) / 10, (y - 11) / 8)
        g.put(x, y, shade("#ffc070", 1.05 - d * 0.25))
g.vline(11, 2, 17, "#3a2e22"); g.hline(2, 21, 9, "#3a2e22")
for y in range(2, 18):                                                    # 左邊半拉的布簾
    w = 5 - abs(y - 9) // 3
    g.hline(2, 2 + w, y, shade("#a0603a", 0.9 + (y % 3) * 0.05))

# ---- 回家的路牌（0.75 × 0.375 m，2 倍密度 fit 48×24）：綠底白框、房子＋箭頭的圖形（2D 的 sign_home） ----
g = sheet("sign_home", 48, 24, "fit 2x")
g.rect(0, 0, 47, 23, "#e8ece8")
g.rect(1, 1, 46, 22, "#2a6a4a")
g.rect(2, 2, 45, 21, "#e8ece8"); g.rect(3, 3, 44, 20, "#2a6a4a")
W_ = "#e8ece8"
for t in range(6):                                                        # 房子：屋頂
    g.hline(13 - t - 1, 13 + t + 1, 6 + t, W_)
g.rect(8, 12, 18, 18, W_); g.rect(12, 14, 14, 18, "#2a6a4a")               # 牆、門
g.rect(24, 11, 36, 13, W_)                                                # 箭頭
for t in range(5):
    g.vline(37 + t, 12 - (4 - t), 12 + (4 - t), W_)
for i in range(3):
    blob(g, 6 + int(h(i, 1, 315) * 36), 4 + int(h(i, 2, 315) * 16), 1, "#7a5a3a", i + 60, wrap=False, density=0.8)

# ---- 紅十字牌（0.3 m 見方，2 倍密度 fit 20×20）：白底、紅十字、鏽 ----
g = sheet("red_cross", 20, 20, "fit 2x")
g.rect(0, 0, 19, 19, "#8a8478")
g.rect(1, 1, 18, 18, "#e0dcd0")
g.rect(8, 3, 11, 16, "#b02a22"); g.rect(3, 8, 16, 11, "#b02a22")
blob(g, 15, 15, 2, "#8a5a3a", 316, wrap=False, density=0.7)

# ---- 禁止進入的牌子（0.4 m 圓牌，2 倍密度 fit 26×26，透明）：紅圓、白橫條、邊上的凹痕 ----
g = sheet("no_entry", 26, 26, "fit 2x alpha")
for y in range(26):
    for x in range(26):
        d = math.hypot(x - 12.5, y - 12.5)
        if d <= 12.5:
            c = "#e0dcd0" if d > 11.2 else ("#e8ece8" if 5 <= x <= 20 and 10 <= y <= 15 else shade("#b02a22", 0.92 + h(x, y, 317) * 0.12))
            g.put(x, y, c)
blob(g, 18, 6, 2, "#6a4a30", 318, wrap=False, density=0.7)

# ---- 路面的裂縫（2 × 1 m，fit 64×32，透明）：主裂縫分岔＋碎塊（貼在柏油上） ----
g = sheet("cracks", 64, 32, "fit alpha")
def walk(x, y, n, dx, seed):
    for i in range(n):
        g.put(x, y, "#1e1c1a")
        if h(i, seed, 1) < 0.35:
            g.put(x, y + 1, "#2e2a26")
        x += dx
        r = h(i, seed, 2)
        y += -1 if r < 0.3 else (1 if r > 0.7 else 0)
        y = max(1, min(30, y))
walk(1, 16, 62, 1, 319); walk(20, 16, 14, 1, 320); walk(38, 15, 12, 1, 321)
for x0, y0, dy in ((14, 16, -1), (30, 17, 1), (46, 14, -1)):              # 分岔
    for k in range(8):
        g.put(x0 + k // 2, y0 + dy * k, "#1e1c1a")
for i in range(5):                                                        # 翹起來的碎塊
    cx, cy = 6 + int(h(i, 1, 322) * 52), 10 + int(h(i, 2, 322) * 12)
    g.rect(cx, cy, cx + 1, cy + 1, "#5a544a")

# ---- 火桶（周長 1.8 m × 高 0.9 m，fit 32×16，包在圓柱上）：鏽鐵桶、兩圈箍、燒黑的上緣 ----
g = sheet("drum", 32, 16, "fit wrap")
for y in range(16):
    for x in range(32):
        k = 0.85 + 0.2 * math.cos(x * math.pi / 16)
        c = shade("#5a4a3c", k + (h(x, y, 323) - 0.5) * 0.1)
        if y in (5, 11):
            c = shade("#3e342a", k)
        if y < 3:
            c = shade("#241e1a", 0.9 + h(x, y, 324) * 0.2)
        g.put(x, y, c)
for i in range(5):
    blob(g, int(h(i, 1, 325) * 32), 6 + int(h(i, 2, 325) * 9), 2, "#8a4a28", i + 70, density=0.6)

export(SHEETS, OUTDIR)
