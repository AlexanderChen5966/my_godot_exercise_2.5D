# B4-1 主角的密度比較：同一份造型（公尺座標的形狀）用三種密度算成像素，比較哪一種放進 3D 最好看。
#   A：每公尺 32 像素（32×48，和場景貼圖同密度）  C：48 像素（48×72）  B：64 像素（64×96）
# 造型照原插畫（scene_18、scene_20）與 A＋ 的主角：駝背、往前探的頭、凌亂的深色頭髮、灰綠帶傷的皮膚、
# 橄欖綠的襯衫外套、深色長褲、手上有血。面向右（側面）；待機一格、走路一格（左腳往前）。
# 用法：python3 art/design/b4/player_density.py 輸出資料夾 → 每格的 .txt／.png 與 preview.png
import math, subprocess, sys
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/tools")
from pix import Grid
from texlib import h, shade

OUT = sys.argv[1]
H_M = 1.6                                  # 畫布高（公尺）；身高約 1.52 m（駝背，頭照像素人物的習慣畫大一點）

SKIN, SKIN_D, SKIN_L = "#8c9a8a", "#6a786c", "#a6b2a2"
HAIR, HAIR_L = "#26221e", "#3e3830"
COAT, COAT_D, COAT_L = "#5e5e42", "#45452f", "#74744f"
SHIRT = "#8a8466"
PANTS, PANTS_D, PANTS_L = "#24262c", "#18191e", "#34363e"
SHOE, SHOE_L = "#2a231e", "#3e352c"
BLOOD, BLOOD_D = "#7e2620", "#561712"
EYE = "#e8e2c0"
OUTLINE = "#121212"


def poly_in(px, py, pts):
    """點在多邊形裡面嗎（射線法）"""
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]; xj, yj = pts[j]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def limb(p0, p1, w0, w1):
    """兩點之間的粗線段（四邊形，起點寬 w0、終點寬 w1）"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L, dx / L
    return [(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2), (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
            (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2), (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)]


def rot(c, p, deg):
    a = math.radians(deg)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * math.cos(a) - y * math.sin(a), c[1] + x * math.sin(a) + y * math.cos(a))


def pose(walk):
    """回傳要畫的零件（由後往前）：(名稱, 多邊形或橢圓, 顏色組)。座標：x 往右（面向）、y 往上，原點在兩腳中間的地面"""
    parts = []
    hip = (-0.02, 0.80)
    # 腿：後腿（遠的那隻）先畫、比較暗
    if walk:
        legs = [("leg_back", -15, PANTS_D), ("leg_front", 17, PANTS)]
    else:
        legs = [("leg_back", -3, PANTS_D), ("leg_front", 3, PANTS)]
    for name, ang, col in legs:
        knee = rot(hip, (hip[0], 0.43), ang)
        bend = 10 if (walk and ang < 0) else 0
        foot = rot(knee, (knee[0], 0.05), ang - bend if ang < 0 else ang * 0.25)
        parts.append((name, ("poly", limb(hip, knee, 0.15, 0.12)), col))
        parts.append((name, ("poly", limb(knee, foot, 0.12, 0.10)), col))
        toe = (foot[0] + 0.09, foot[1] - 0.04)
        parts.append(("shoe", ("poly", [(foot[0] - 0.06, foot[1] + 0.02), (foot[0] + 0.04, foot[1] + 0.03), (toe[0] + 0.02, toe[1] + 0.02),
                                        (toe[0] + 0.02, toe[1] - 0.01), (foot[0] - 0.06, foot[1] - 0.05)]), SHOE_L if col == PANTS else SHOE))
    # 後手（遠的那隻）
    sh = (0.02, 1.16)
    swing = -18 if walk else 4
    elbow = rot(sh, (sh[0] + 0.03, 0.97), swing)
    hand = rot(elbow, (elbow[0] + 0.05, 0.76), swing * 0.6)
    parts.append(("arm_back", ("poly", limb(sh, elbow, 0.11, 0.09)), COAT_D))
    parts.append(("arm_back", ("poly", limb(elbow, hand, 0.09, 0.07)), COAT_D))
    # 後面的手（側面時被身體與腿擋住，露出來只會像一團東西）不畫
    # 上身（駝背：肩往前、背拱起）
    torso = [(-0.15, 0.78), (0.10, 0.78), (0.13, 0.95), (0.15, 1.10), (0.11, 1.20), (0.02, 1.23), (-0.10, 1.21), (-0.17, 1.10), (-0.18, 0.95)]
    parts.append(("torso", ("poly", torso), COAT))
    parts.append(("collar", ("poly", [(0.04, 1.23), (0.14, 1.17), (0.12, 1.12), (0.04, 1.18)]), SHIRT))
    # 脖子、頭（往前探）
    parts.append(("neck", ("poly", limb((0.07, 1.18), (0.12, 1.25), 0.09, 0.08)), SKIN_D))
    parts.append(("head", ("ell", 0.15, 1.34, 0.125, 0.135), SKIN))
    parts.append(("jaw", ("poly", [(0.09, 1.25), (0.26, 1.27), (0.25, 1.21), (0.15, 1.19)]), SKIN))
    parts.append(("nose", ("poly", [(0.25, 1.37), (0.31, 1.31), (0.26, 1.30)]), SKIN))
    parts.append(("hair", ("poly", [(0.02, 1.28), (0.01, 1.40), (0.05, 1.48), (0.10, 1.50), (0.14, 1.54), (0.18, 1.49), (0.23, 1.51),
                                     (0.27, 1.45), (0.27, 1.40), (0.19, 1.42), (0.12, 1.38), (0.09, 1.31), (0.06, 1.26)]), HAIR))
    # 前手（近的那隻，垂在身側、手上有血）
    swing = 16 if walk else -2
    sh = (0.04, 1.15)
    elbow = rot(sh, (sh[0] + 0.02, 0.96), swing)
    hand = rot(elbow, (elbow[0] + 0.04, 0.75), swing * 0.6)
    parts.append(("arm", ("poly", limb(sh, elbow, 0.12, 0.10)), COAT))
    parts.append(("arm", ("poly", limb(elbow, hand, 0.10, 0.08)), COAT))
    parts.append(("cuff", ("poly", limb(rot(elbow, (elbow[0] + 0.037, 0.80), swing * 0.6), hand, 0.085, 0.08)), COAT_D))
    parts.append(("hand", ("ell", hand[0] + 0.01, hand[1] - 0.045, 0.05, 0.065), SKIN))
    return parts


def inside(shape, x, y):
    if shape[0] == "poly":
        return poly_in(x, y, shape[1])
    _, cx, cy, rx, ry = shape
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1


def render(ppm, walk):
    W = int(round(ppm * 1.0))                 # 畫布寬 1 m
    Hh = int(round(ppm * H_M))
    g = Grid(W, Hh)
    ox = W * 0.42                             # 原點（兩腳中間）在畫布的 x
    owner = [[None] * W for _ in range(Hh)]
    parts = pose(walk)
    for py in range(Hh):
        for px in range(W):
            x = (px + 0.5 - ox) / ppm
            y = (Hh - py - 0.5) / ppm
            for idx, (name, shape, col) in enumerate(parts):
                if inside(shape, x, y):
                    owner[py][px] = (idx, name, col, x, y)
    s = ppm / 32.0                            # 細節的粗細照密度調整（至少 1 像素）
    for py in range(Hh):
        for px in range(W):
            o = owner[py][px]
            if not o:
                continue
            idx, name, col, x, y = o
            c = col
            # 明暗：光從前上方來，背面與下緣暗、前緣亮（零件的邊界判斷用相鄰像素）
            left = owner[py][px - 1] if px > 0 else None
            up = owner[py - 1][px] if py > 0 else None
            right = owner[py][px + 1] if px < W - 1 else None
            down = owner[py + 1][px] if py < Hh - 1 else None
            if name in ("torso", "arm", "head", "jaw", "leg_front", "hand"):
                if not right or right[1] != name and right[0] < idx:
                    c = shade(col, 1.18)              # 前緣受光
                if not left or (left[1] != name and left[0] < idx):
                    c = shade(col, 0.8)               # 背面暗
            # 細節（公尺座標定位；密度不夠時自然消失或只剩 1 像素）
            if name == "torso":
                if abs(x - (0.07 - (y - 1.2) * 0.2)) < 0.012 * max(1, 1 / s) and y < 1.18:
                    c = COAT_D                         # 前襟
                if ppm >= 48 and abs(x - (0.095 - (y - 1.2) * 0.2)) < 0.01 and 0.85 < y < 1.15 and int(y * 100) % 9 < 2:
                    c = "#2e2e20"                      # 扣子
                if 0.80 < y < 0.84:
                    c = COAT_D                         # 下擺
                if ppm >= 48 and abs((x + 0.06) - (y - 0.9) * 0.6) < 0.008 and 0.86 < y < 1.05:
                    c = COAT_D                         # 皺褶
                if -0.05 < x < 0.04 and 0.97 < y < 1.03 and h(px, py, 41) < 0.6:
                    c = BLOOD_D                        # 衣服上乾掉的血
            if name == "head":
                if 0.195 < x < 0.235 and 1.33 < y < 1.37:
                    c = "#1a1a16"                      # 眼窩
                    if ppm >= 48 and 0.21 < x < 0.228 and 1.342 < y < 1.36:
                        c = EYE                        # 混濁的眼白
                if 0.12 < x < 0.17 and 1.27 < y < 1.33 and h(px, py, 42) < 0.35:
                    c = SKIN_D                         # 臉頰凹陷
                if ppm >= 48 and 0.13 < x < 0.17 and 1.35 < y < 1.39 and h(px, py, 43) < 0.5:
                    c = "#7a4a3a"                      # 擦傷
            if name == "jaw":
                if 0.20 < x < 0.26 and 1.225 < y < 1.245:
                    c = BLOOD                          # 嘴角的血
                if 0.215 < x < 0.23 and y < 1.23:
                    c = BLOOD_D
            if name == "hair" and h(px // max(1, int(s)), py // max(1, int(s)), 44) < 0.25:
                c = HAIR_L
            if name in ("leg_front", "leg_back"):
                if ppm >= 48 and 0.40 < y < 0.46:
                    c = shade(c, 0.85)                 # 膝蓋的皺
            if name in ("hand",) and h(px, py, 45) < 0.45:
                c = BLOOD                              # 手上的血
            g.put(px, py, c)
    # 外框：透明鄰格的邊緣畫深色（和 A＋ 的像素人物一樣）
    edge = []
    for py in range(Hh):
        for px in range(W):
            if g.get(px, py):
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                qx, qy = px + dx, py + dy
                if 0 <= qx < W and 0 <= qy < Hh and g.get(qx, qy):
                    edge.append((px, py)); break
    for px, py in edge:
        g.put(px, py, OUTLINE)
    return g


DENS = [("A", 32), ("C", 48), ("B", 64)]
pngs = []
for tag, ppm in DENS:
    for walk in (False, True):
        g = render(ppm, walk)
        name = f"{OUT}/player_{tag}_{'walk' if walk else 'idle'}"
        g.save_txt(name + ".txt", outline=False)
        subprocess.run(["magick", name + ".txt", "PNG32:" + name + ".png"], check=True)
        pngs.append(name + ".png")
        print(tag, ppm, "walk" if walk else "idle", g.w, "x", g.h)
# 預覽：每張都放大到同樣的高度（288 px），並排
subprocess.run(["magick", *sum([["(", p, "-filter", "point", "-resize", "x288", "-bordercolor", "#3a3f44", "-border", "10", ")"] for p in pngs], []),
                "-background", "#3a3f44", "-gravity", "south", "+append", f"{OUT}/preview.png"], check=True)
