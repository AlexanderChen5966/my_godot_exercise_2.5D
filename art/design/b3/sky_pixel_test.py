# B3-4 廢墟的像素天空（B 版，作者 2026-10-28 採用；漸層天空 A 版當備案，見 docs/2.5D_天空與陽光.md）。
# B3-4c 起是正式素材：Pixelorama 存成 art/textures/ruins/sky.pxo、匯出 assets/textures/ruins/sky.png。
# 左右無縫（網點 2 格一循環、雲帶用 % W 繞回、太陽與煙不碰兩端），之後改 HD-2D 時可以包成 360° 的地平線帶。
# 平面 96 × 40 m、放在 z −45，4 像素＝1 m（從鏡頭看過去，一格天空像素和人物的像素差不多大）。
# 用法：python3 art/design/b3/sky_pixel_test.py 輸出.png
import math, sys
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/tools")
from pix import Grid
from texlib import h, shade

W, H = 384, 160
g = Grid(W, H)
BANDS = ["#2a1e22", "#3a2828", "#4e3430", "#6a4230", "#8a5430", "#ab6a32", "#c8843a", "#dc9e4a", "#e8b860"]   # 上 → 地平線
SUN_X, SUN_Y = 270, 132
for y in range(H):
    t = y / (H - 1)                                        # 0＝上、1＝地平線
    f = t ** 1.6 * (len(BANDS) - 1)
    i = int(f)
    frac = f - i
    for x in range(W):
        k = i + (1 if i + 1 < len(BANDS) and ((x + y) % 2 == 0 and frac > 0.66 or (x % 2 == 0 and y % 2 == 0 and frac > 0.33 and frac <= 0.66)) else 0)
        c = BANDS[min(k, len(BANDS) - 1)]
        d = math.hypot((x - SUN_X) / 1.6, y - SUN_Y)       # 太陽附近的光暈（一圈圈的色帶）
        if d < 60:
            c = shade(c, 1.0 + 0.12 * (3 - int(d // 20)))
        g.put(x, y, c)
for y in range(H):                                         # 太陽（低、被煙遮住一半）
    for x in range(W):
        if math.hypot(x - SUN_X, y - SUN_Y) <= 9:
            g.put(x, y, "#f8e0a0" if math.hypot(x - SUN_X, y - SUN_Y) <= 7 else "#f0c878")
smoke = {}                                                 # 兩股往右上飄、越高越散的煙：先記下每格要多暗，最後每格只調暗一次
for p, (x0, drift) in enumerate(((70, 1.3), (200, 0.9))):
    for s in range(90):
        cx = x0 + s * drift + 8 * math.sin(s * 0.08 + p * 2)
        cy = 156 - s * 1.5
        r = 5 + s * 0.35
        for dy in range(-int(r), int(r) + 1):
            for dx in range(-int(r), int(r) + 1):
                d = math.hypot(dx, dy) / r
                x, y = int(cx + dx), int(cy + dy)
                if d <= 1 and h(x // 3, y // 3, 500 + p) < (1.15 - d) * (1.0 - s / 120):
                    k = 0.62 + 0.25 * d + 0.12 * s / 90                 # 中間、下面比較濃
                    smoke[(x, y)] = min(smoke.get((x, y), 1.0), k)
for (x, y), k in smoke.items():
    col = g.get(x, y)
    if col:
        g.put(x, y, shade(col, k))
for c in range(7):                                         # 橫向的雲帶（比天空暗一點）
    y = 30 + c * 14 + int(h(c, 1, 520) * 6)
    x = int(h(c, 2, 520) * W)
    L = 40 + int(h(c, 3, 520) * 80)
    for k in range(L):
        for t in range(2 + (k % 7 == 0)):
            xx = (x + k) % W
            col = g.get(xx, y + t)
            if col:
                g.put(xx, y + t, shade(col, 0.82))
g.save_txt(sys.argv[1] + ".txt", outline=False)
import subprocess
subprocess.run(["magick", sys.argv[1] + ".txt", "PNG32:" + sys.argv[1]], check=True)
