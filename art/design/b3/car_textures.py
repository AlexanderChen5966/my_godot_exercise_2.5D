# B3-1d 車子的貼圖集（32 像素＝1 m，照面的大小畫，不重複鋪）：青綠的廢車 car_teal、燒毀的車 car_burnt。
# 版面要和 cars.blend 的 UV 一致（art/models/common/cars.blend 的 car_build）：
#   A (0,0) 144×24 車身側面：x −2.24～2.24、z 1.0（上）～0.25（下）
#   B (0,24) 72×24 車艙側面：x −1.40～0.85、z 1.45～0.70（只用到上面 16 列）
#   C (0,48) 車頭、(64,48) 車尾 各 64×24：寬 2 m（從外面看的右方）、z 1.0～0.25
#   D (0,72) 擋風玻璃、(48,72) 後窗 各 48×24：寬 1.6 m、上緣～下緣
# 車頂、引擎蓋、後車廂用 car_teal_top（1 m 一格、無縫；和側面同色）或共用的 burnt；底盤、保險桿、輪子用共用的 metal、tire。
# 用法：python3 art/design/b3/car_textures.py 輸出資料夾 → car_teal、car_burnt 的 .txt、.png 與 preview.png
import math, sys
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/tools")
from pix import Grid
from texlib import h, shade, blob, noise_fill, export

OUTDIR = sys.argv[1]
AW, AH = 144, 96
PROFILE = [(-2.20, 0.30)]
for cx in (-1.32, 1.32):
    for a in range(180, -1, -30):
        PROFILE.append((cx + 0.40 * math.cos(math.radians(a)), 0.30 + 0.40 * math.sin(math.radians(a))))
PROFILE += [(2.18, 0.30), (2.26, 0.40), (2.27, 0.66), (2.20, 0.78), (1.70, 0.86), (0.85, 0.94),
            (-1.40, 0.96), (-1.95, 0.95), (-2.20, 0.88), (-2.25, 0.74), (-2.24, 0.38)]
CABIN = [(0.85, 0.945), (0.10, 1.40), (-0.80, 1.41), (-1.40, 0.955)]


def inside(poly, x, y):
    c = False
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i], poly[i - 1]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def edge_dist(poly, x, y):
    """點到多邊形邊的最短距離（公尺）"""
    best = 9.0
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i], poly[i - 1]
        dx, dy = x1 - x0, y1 - y0
        t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - x0 - t * dx, y - y0 - t * dy))
    return best


def side_xz(px, py):
    return (px + 0.5) / 32 - 2.24, 1.0 - (py + 0.5) / 32


def cabin_xz(px, py):
    return (px + 0.5) / 32 - 1.40, 1.45 - (py + 0.5) / 32


def window_kind(x, z):
    """車艙側面的哪一塊：frame 窗框、glass 玻璃（front／rear 前後門）、pillar 柱子、None 不在車艙裡"""
    if not inside(CABIN, x, z):
        return None
    d = edge_dist(CABIN, x, z)
    if d < 0.06 or z < 0.99:
        return "frame"
    if -0.34 < x < -0.24:
        return "pillar"                      # B 柱
    if x < -1.02:
        return "pillar"                      # C 柱（轎車後面一大塊車身）
    return "front" if x > -0.24 else "rear"


def draw(name, P):
    """P：這台車的配色與要不要破、燒"""
    g = Grid(AW, AH)
    burnt = P["burnt"]
    for py in range(AH):
        for px in range(AW):
            g.put(px, py, "#101010")
    # ---- A 車身側面 ----
    for py in range(24):
        for px in range(144):
            x, z = side_xz(px, py)
            k = 0.94 + (h(px, py, 61) - 0.5) * 0.10
            if z > 0.88:
                k += 0.12                      # 車肩的反光
            elif z < 0.45:
                k -= 0.14
            c = shade(P["paint"], k)
            if 0.69 < z < 0.72:
                c = shade(P["paint"], k + 0.10)  # 腰線
            if z < 0.37:
                c = shade(P["trim"], 0.95 + (h(px, py, 62) - 0.5) * 0.1)  # 下面的飾板
            for cx in (-1.32, 1.32):            # 輪拱的邊
                if 0.40 < math.hypot(x - cx, z - 0.30) < 0.45:
                    c = shade(P["trim"], 0.85)
            g.put(px, py, c)
    seam = P["seam"]
    for xs in (0.80, -0.28, -1.30):              # 前門、後門的門縫（碰到輪拱就停）
        px = int((xs + 2.24) * 32)
        for py in range(1, 21):
            x, z = side_xz(px, py)
            if min(math.hypot(x - cx, z - 0.30) for cx in (-1.32, 1.32)) < 0.45:
                break
            g.put(px, py, seam)
    g.hline(int((-1.30 + 2.24) * 32), int((0.80 + 2.24) * 32), 20, seam)
    g.hline(int((-2.05 + 2.24) * 32), int((-1.45 + 2.24) * 32), 2, seam)   # 後車廂邊
    if not burnt:
        for x0 in (0.02, -1.08):                 # 門把
            px = int((x0 + 2.24) * 32)
            g.hline(px - 3, px, 6, "#8a9498"); g.hline(px - 3, px, 7, shade(P["paint"], 0.6))
        g.rect(140, 10, 141, 11, "#c88a3a")      # 側邊方向燈
        g.rect(1, 4, 2, 7, "#8a2a22")             # 尾燈包過來的一小段
        fx = int((-1.80 + 2.24) * 32)            # 油箱蓋
        g.rect(fx, 5, fx + 3, 5, seam); g.rect(fx, 8, fx + 3, 8, seam); g.vline(fx, 5, 8, seam); g.vline(fx + 3, 5, 8, seam)
        for i in range(5):                        # 刮痕
            x0, y0 = int(h(i, 1, 63) * 120) + 10, int(h(i, 2, 63) * 10) + 6
            g.line(x0, y0, x0 + 6 + int(h(i, 3, 63) * 6), y0 + 1, shade(P["paint"], 1.3))
        g.line(80, 12, 86, 9, shade(P["paint"], 0.6)); g.line(86, 9, 92, 12, shade(P["paint"], 0.6))  # 凹痕
    for i in range(P["rust_n"]):                  # 鏽斑（下半部比較多）
        cx, cy = int(h(i, 1, 64) * 144), int(15 + h(i, 2, 64) * 8)
        blob(g, cx, cy, 2 + int(h(i, 3, 64) * 3), P["rust"], i * 7 + 1, wrap=False, density=0.65)
    for i in range(40):                           # 泥巴、灰塵
        px, py = int(h(i, 4, 65) * 144), int(16 + h(i, 5, 65) * 8)
        g.put(px, py, P["dust"])
    if burnt:
        for py in range(24):                      # 燻黑：上面最黑
            for px in range(144):
                if h(px // 2, py // 2, 66) < 0.62 - py * 0.025:
                    g.put(px, py, shade("#1a1614", 0.9 + h(px // 2, py // 2, 67) * 0.2))
        for i in range(10):
            g.put(int(h(i, 1, 68) * 144), int(h(i, 2, 68) * 24), "#8a4a20")   # 殘留的火星
    # ---- B 車艙側面 ----
    for py in range(24, 48):
        for px in range(72):
            x, z = cabin_xz(px, py - 24)
            kind = window_kind(x, z)
            if kind is None:
                continue
            if kind == "frame":
                c = shade(P["frame"], 0.95 + (h(px, py, 69) - 0.5) * 0.1)
            elif kind == "pillar":
                c = shade(P["paint"], 1.04 + (h(px, py, 70) - 0.5) * 0.1) if x < -1.02 else P["frame"]
            elif burnt or (kind == "front" and P["broken_front"]):
                hole = h(px, py, 71) < 0.85 or edge_dist(CABIN, x, z) > 0.10
                c = "#0c0a08" if hole else P["shard"]
                if hole and z < 1.16 and abs((x + 0.55 if x < -0.24 else x - 0.30)) < 0.20 + (1.16 - z) * 0.6:
                    c = P["seat"]                      # 破窗裡看得到的椅背
            else:
                c = shade(P["glass"], 0.95 + (h(px, py, 72) - 0.5) * 0.12)
                if (px - (py - 24) * 2) % 23 in (0, 1):
                    c = P["glass_hi"]          # 斜的反光
            g.put(px, py, c)
    if P["burnt"]:
        for py in range(24, 48):              # C 柱也燒黑
            for px in range(72):
                x, z = cabin_xz(px, py - 24)
                if window_kind(x, z) == "pillar" and x < -1.02 and h(px, py, 73) < 0.7:
                    g.put(px, py, shade("#1a1614", 0.9 + h(px, py, 74) * 0.2))
    else:
        for (x0, y0), (x1, y1) in (((24, 32), (32, 37)), ((24, 32), (18, 38)), ((24, 32), (30, 27)), ((24, 32), (15, 30))):  # 後門玻璃的裂痕
            g.line(x0, y0, x1, y1, P["crack"])
    # ---- C 車頭（0,48）、車尾（64,48） ----
    for base in (0, 64):
        for py in range(48, 72):
            for px in range(base, base + 64):
                k = 0.92 + (h(px, py, 75) - 0.5) * 0.1
                g.put(px, py, shade(P["paint"], k))
    # z → py：py = 48 + (1.0 − z) × 32；寬 y → px：(y + 1) × 32
    Y = lambda y: int((y + 1) * 32)
    Z = lambda z: 48 + int((1.0 - z) * 32)
    # 車頭：水箱護罩、大燈、方向燈
    g.rect(Y(-0.42), Z(0.64), Y(0.42) - 1, Z(0.50), "#161818")
    for zz in (0.60, 0.56, 0.52):
        g.hline(Y(-0.40), Y(0.40) - 2, Z(zz), "#1e2020" if burnt else "#3a3e3e")
    for s, broken in ((-1, P["broken_light"]), (1, False)):
        y0, y1 = (0.48, 0.80) if s > 0 else (-0.80, -0.48)
        g.rect(Y(y0), Z(0.66), Y(y1) - 1, Z(0.52), "#1a1a18")
        if burnt or broken:
            for py in range(Z(0.64), Z(0.54) + 1):
                for px in range(Y(y0) + 1, Y(y1) - 1):
                    g.put(px, py, "#0c0a08" if h(px, py, 76) < 0.8 else "#4a4c48")
        else:
            g.rect(Y(y0) + 1, Z(0.64), Y(y1) - 2, Z(0.54), "#c8c4a8")
            g.rect(Y(y0) + 2, Z(0.63), Y(y0) + 4, Z(0.62), "#e8e4d0")
        g.rect(Y(y0) + 1, Z(0.49), Y(y1) - 2, Z(0.47), "#0c0a08" if burnt else "#b87a32")
    if not burnt:
        g.rect(Y(-0.04), Z(0.70), Y(0.04), Z(0.67), "#8a9498")       # 車標
    g.hline(0, 63, Z(0.76), P["seam"])                                # 引擎蓋邊
    # 車尾：尾燈、車牌、後車廂縫
    T = lambda y: 64 + int((1 - y) * 32)    # 車尾從外面看，右方是 −y
    for y0, y1 in ((0.50, 0.82), (-0.82, -0.50)):
        a, b = sorted((T(y0), T(y1)))
        g.rect(a, Z(0.76), b - 1, Z(0.62), "#1a1a18")
        if burnt:
            for py in range(Z(0.75), Z(0.63) + 1):
                for px in range(a + 1, b - 1):
                    g.put(px, py, "#0c0a08" if h(px, py, 77) < 0.85 else "#5a2a20")
        else:
            g.rect(a + 1, Z(0.75), b - 2, Z(0.70), "#8a2020")
            g.rect(a + 1, Z(0.69), b - 2, Z(0.66), "#b83a30")
            g.rect(a + 1, Z(0.65), b - 2, Z(0.63), "#c8c0b0")
    g.rect(T(0.26), Z(0.64), T(-0.26) - 1, Z(0.50), "#1a1a18")
    if burnt:
        g.rect(T(0.24), Z(0.63), T(-0.24) - 2, Z(0.51), "#2a2420")
    else:
        g.rect(T(0.24), Z(0.63), T(-0.24) - 2, Z(0.51), "#c8c8b8")
        for i, x0 in enumerate(range(T(0.20), T(-0.20) - 3, 4)):
            g.rect(x0, Z(0.61), x0 + 1, Z(0.53), "#2a2a2a")
    g.hline(64, 127, Z(0.86), P["seam"])
    for i in range(P["rust_n"] // 2):
        blob(g, int(h(i, 1, 78) * 128), int(60 + h(i, 2, 78) * 10), 2, P["rust"], i * 5 + 3, wrap=False, density=0.6)
    if burnt:
        for py in range(48, 72):
            for px in range(128):
                if h(px // 2, py // 2, 79) < 0.55 - (py - 48) * 0.022:
                    g.put(px, py, shade("#1a1614", 0.9 + h(px // 2, py // 2, 80) * 0.2))
    # ---- D 擋風玻璃（0,72）、後窗（48,72） ----
    for base in (0, 48):
        for py in range(72, 96):
            for px in range(base, base + 48):
                u, v = px - base, py - 72
                if u < 2 or u > 45 or v < 1 or v > 22:
                    c = P["frame"]
                elif burnt:
                    hole = h(px, py, 82) < 0.88 or (u > 4 and u < 43 and v > 3 and v < 20)
                    c = "#0c0a08" if hole else P["shard"]
                else:
                    c = shade(P["glass"], 1.0 + (h(px, py, 83) - 0.5) * 0.12 + v * 0.012)
                    if (u - v) % 17 in (0, 1, 2) and v < 15:
                        c = P["glass_hi"]
                g.put(px, py, c)
    if not burnt:
        g.line(6, 94, 20, 90, "#1a1a18"); g.line(24, 94, 38, 90, "#1a1a18")       # 雨刷
        for v in range(80, 92, 3):
            g.hline(52, 91, v, shade(P["glass"], 0.8))                                # 後窗的除霧線
        if P["broken_ws"]:
            for (x0, y0), (x1, y1) in (((32, 80), (44, 74)), ((32, 80), (40, 92)), ((32, 80), (22, 84)), ((32, 80), (26, 74)), ((32, 80), (45, 86))):
                g.line(x0, y0, x1, y1, P["crack"])                                    # 擋風玻璃的蛛網狀裂痕
        for i in range(30):
            g.put(int(h(i, 1, 84) * 96), int(90 + h(i, 2, 84) * 5), P["dust"])        # 下緣的灰塵
    return g


TEAL = dict(burnt=False, paint="#4a6a6e", trim="#263234", seam="#1e2a2c", frame="#161c1e", glass="#22383e",
            glass_hi="#3e6066", shard="#5a7a80", crack="#9ab0b4", rust="#6a3a2a", dust="#5a5248", rust_n=9, seat="#3e3832",
            broken_front=True, broken_light=True, broken_ws=True)
BURNT = dict(burnt=True, paint="#3a302a", trim="#221c18", seam="#100c0a", frame="#141010", glass="#0c0a08",
             glass_hi="#0c0a08", shard="#3a4446", crack="#3a4446", rust="#5a3a24", dust="#4a4440", rust_n=14, seat="#342a24",
             broken_front=True, broken_light=True, broken_ws=True)
top = Grid(32, 32)                               # 青綠車的車頂、引擎蓋：和側面同色＋灰塵、鏽點
noise_fill(top, shade(TEAL["paint"], 1.02), 0.08, 85)
for i in range(14):
    top.put(int(h(i, 1, 86) * 32), int(h(i, 2, 86) * 32), TEAL["dust"])
for cx, cy, r in ((8, 22, 2), (25, 6, 1)):
    blob(top, cx, cy, r, TEAL["rust"], cx + cy, density=0.7)
SHEETS = {"car_teal": (draw("car_teal", TEAL), "fit atlas"), "car_burnt": (draw("car_burnt", BURNT), "fit atlas"),
          "car_teal_top": (top, "tile 1m")}
export(SHEETS, OUTDIR)
