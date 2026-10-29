# B4 人物共用：形狀（公尺座標）→ 像素，加三層明暗、手畫頭像、描邊。做法和 B4-2 主角（player.py）相同：
#   身體用形狀算＋三層明暗與細節，頭用手畫的像素頭像（這個密度用形狀算臉只剩一塊膚色，作者 2026-10-29）。
# 用法：from figlib import *；parts＝[(名稱, 多邊形, (亮, 中, 暗))]，render(parts, 頭像, 頭的中心, 調色盤, detail)。
import math, subprocess, sys
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/tools")
from pix import Grid
from texlib import h, shade

PPM = 32                                   # 每公尺幾像素（密度 A）
H_M = 1.6                                  # 畫布高 1.6 m、寬 1 m；原點（兩腳中間的地面）在畫布底部正中間
FW, FH = int(round(PPM * 1.0)), int(round(PPM * H_M))
OUTLINE = "#121212"
CLIPPED = []


def poly_in(px, py, pts):
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def limb(p0, p1, w0, w1):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    return [(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2), (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
            (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2), (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)]


def ell(cx, cy, rx, ry, n=20):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def rot(c, p, deg):
    """繞 c 轉 deg 度（正＝逆時針；面向右時往前倒＝負）"""
    a = math.radians(deg)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def down(p, length, ang):
    """從 p 往下 length，ang＝和垂直往下的夾角（正＝往前）"""
    a = math.radians(ang)
    return (p[0] + length * math.sin(a), p[1] - length * math.cos(a))


def render(parts, stamp, head_c, pal, detail=None, anchor=None, front_of_head=()):
    """parts：[(名稱, 多邊形, (亮, 中, 暗))]，後面的蓋前面的；光從右前上方（前緣亮、後緣暗）。
    stamp：頭像（字串列，"." 透明），錨點（欄, 列）對到 head_c（公尺）；front_of_head 裡的部位畫在頭像前面。
    detail(name, x, y, px, py, c, nb) → 顏色：放鈕扣、口袋、血這些細節（nb(dx, dy) 取鄰格的部位名稱）。"""
    g = Grid(FW, FH)
    ox = FW / 2
    owner = [[None] * FW for _ in range(FH)]
    for py in range(FH):
        for px in range(FW):
            x = (px + 0.5 - ox) / PPM
            y = (FH - py - 0.5) / PPM
            for idx, (name, pts, ramp) in enumerate(parts):
                if poly_in(x, y, pts):
                    owner[py][px] = (idx, name, ramp, x, y)

    def name_at(px, py):
        return owner[py][px][1] if 0 <= px < FW and 0 <= py < FH and owner[py][px] else None

    for py in range(FH):
        for px in range(FW):
            o = owner[py][px]
            if not o:
                continue
            idx, name, ramp, x, y = o
            c = ramp[1]
            if name_at(px + 1, py) != name:
                c = ramp[0]
            elif name_at(px - 1, py) != name:
                c = ramp[2]
            if detail:
                c = detail(name, x, y, px, py, c, lambda dx, dy: name_at(px + dx, py + dy))
            g.put(px, py, c)
    if stamp:
        ac, ar = anchor or ((len(stamp[0]) - 1) / 2, (len(stamp) - 1) / 2)
        cpx, cpy = head_c[0] * PPM + ox, FH - head_c[1] * PPM
        tlx, tly = int(round(cpx - ac - 0.5)), int(round(cpy - ar - 0.5))
        for r, row in enumerate(stamp):
            for cc, ch in enumerate(row):
                if ch == ".":
                    continue
                px, py = tlx + cc, tly + r
                if not (0 <= px < FW and 0 <= py < FH):
                    CLIPPED.append((px, py))       # 頭像超出畫格（會被切掉）
                    continue
                if name_at(px, py) in front_of_head:
                    continue
                g.put(px, py, pal[ch])
    edge = []
    for py in range(FH):
        for px in range(FW):
            if g.get(px, py):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                qx, qy = px + dx, py + dy
                if 0 <= qx < FW and 0 <= qy < FH and g.get(qx, qy):
                    edge.append((px, py)); break
    for px, py in edge:
        g.put(px, py, OUTLINE)
    return g


def mirror(g):
    m = Grid(g.w, g.h)
    for y in range(g.h):
        for x in range(g.w):
            c = g.get(x, y)
            if c:
                m.put(g.w - 1 - x, y, c)
    return m


def sheet(frs, out, name):
    S = Grid(FW * len(frs), FH)
    for i, f in enumerate(frs):
        for y in range(FH):
            for x in range(FW):
                c = f.get(x, y)
                if c:
                    S.put(i * FW + x, y, c)
    S.save_txt(f"{out}/{name}.txt", outline=False)
    subprocess.run(["magick", f"{out}/{name}.txt", f"PNG32:{out}/{name}.png"], check=True)
    if CLIPPED:
        print("⚠ 頭像超出畫格", len(CLIPPED), "格像素")
    print(name, S.w, "x", S.h, len(frs), "格")
