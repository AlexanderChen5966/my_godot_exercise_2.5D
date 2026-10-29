# B4-2 主角（3D 用）：每公尺 32 像素（密度 A，作者 2026-10-29），造型照 B4-1 的新造型（原插畫比例：頭小、腿長、駝背）。
# 造型用公尺座標的形狀描述，姿勢用參數驅動（上身前傾、手臂肩肘角度、腿的角度、呼吸起伏），一次算出全部畫格。
# 換密度（B 64、C 48，備用）只要改 PPM 重算。2D 版的主角（assets/sprites/player.png）不動。
# 輸出（排法和 A＋ 的 player.png／player_fb.png 相同，每格 32×51）：
#   player3d.png    40 格：右 待機0-3 走路4-9｜左 待機10-13 走路14-19｜右 伸手20-22 前傾23-24｜左 伸手25-27 前傾28-29｜右 手勢30-34｜左 手勢35-39
#   player3d_fb.png 20 格：正面 待機0-3 走路4-9｜背面 待機10-13 走路14-19
# 用法：python3 art/design/b4/player.py 輸出資料夾 → 兩張 spritesheet（.txt／.png）、preview.png（放大 4 倍）
import math, subprocess, sys
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/tools")
from pix import Grid
from texlib import h, shade

OUT = sys.argv[1]
PPM = 32                                   # 每公尺幾像素（A）
H_M = 1.6                                  # 畫布高 1.6 m、寬 1 m；原點（兩腳中間的地面）在畫布底部正中間
FW, FH = int(round(PPM * 1.0)), int(round(PPM * H_M))

SKIN_L, SKIN, SKIN_D, SKIN_DD = "#a8b5a3", "#8c9a8a", "#6a786c", "#4f5a50"
HAIR, HAIR_L = "#26221e", "#3e3830"
COAT_L, COAT, COAT_D, COAT_DD = "#76765a", "#5e5e42", "#45452f", "#33331f"
SHIRT, BUTTON = "#8a8466", "#a49c7c"
PANTS_L, PANTS, PANTS_D = "#363944", "#24262c", "#18191e"
SHOE, SHOE_L, SOLE = "#2a231e", "#3e352c", "#141110"
BLOOD, BLOOD_D = "#7e2620", "#561712"
PAPER, PAPER_D = "#c8c0a4", "#9a927a"
OUTLINE = "#121212"


# ---------------- 幾何 ----------------
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


# ---------------- 側面（面向右） ----------------
def side_parts(pp):
    """pp：lean 上身前傾（度）、bob 上身下沉（m）、legs ((角度, 膝彎) 後腿, 前腿)、arm (肩角, 肘角, 手形) 前手、arm_b 後手"""
    lean, bob = pp.get("lean", 0), pp.get("bob", 0)
    hip = (-0.02, 0.80)
    parts = []
    # 腿（後腿先畫、比較暗）
    for name, (ang, bend), col in (("leg_back", pp["legs"][0], PANTS_D), ("leg_front", pp["legs"][1], PANTS)):
        knee = down(hip, 0.37, ang)
        foot = down(knee, 0.38, ang - bend)
        parts.append((name, limb(hip, knee, 0.15, 0.12), col))
        parts.append((name, limb(knee, foot, 0.12, 0.10), col))
        lift = max(0.0, foot[1] - 0.05)
        fx, fy = foot[0], foot[1]
        parts.append(("shoe", [(fx - 0.06, fy + 0.02), (fx + 0.04, fy + 0.03), (fx + 0.11, fy - 0.02 + lift * 0.3),
                               (fx + 0.11, fy - 0.05 + lift * 0.3), (fx - 0.06, fy - 0.05)], SHOE_L if col == PANTS else SHOE))

    def up(p):                                        # 上半身的點：下沉、以髖為中心往前倒
        return rot(hip, (p[0], p[1] - bob), -lean)

    # 後手（只有往後擺時露出一點袖子；手藏在身體後面）
    if "arm_b" in pp:
        sa, ea, _ = pp["arm_b"]
        sh = up((0.02, 1.16))
        el = down(sh, 0.21, sa)
        ha = down(el, 0.19, ea)
        parts.append(("arm_back", limb(sh, el, 0.11, 0.09), COAT_D))
        parts.append(("arm_back", limb(el, ha, 0.09, 0.07), COAT_D))
    torso = [(-0.15, 0.78), (0.10, 0.78), (0.13, 0.95), (0.15, 1.10), (0.11, 1.20), (0.02, 1.23), (-0.10, 1.21), (-0.17, 1.10), (-0.18, 0.95)]
    parts.append(("torso", [up(p) if p[1] > 0.85 else p for p in torso], COAT))
    parts.append(("collar", [up(p) for p in [(0.04, 1.23), (0.14, 1.17), (0.12, 1.12), (0.04, 1.18)]], SHIRT))
    hd = pp.get("head", (0, 0))                      # 頭再往前、往下多少（前傾時往前探）
    def head(p):
        return up((p[0] + hd[0], p[1] + hd[1]))
    parts.append(("neck", [up(p) for p in limb((0.07, 1.18), (0.12 + hd[0], 1.25 + hd[1]), 0.09, 0.08)], SKIN_D))
    parts.append(("head", [head(p) for p in ell(0.15, 1.34, 0.125, 0.135)], SKIN))
    parts.append(("jaw", [head(p) for p in [(0.09, 1.25), (0.26, 1.27), (0.25, 1.21), (0.15, 1.19)]], SKIN))
    parts.append(("nose", [head(p) for p in [(0.25, 1.37), (0.31, 1.31), (0.26, 1.30)]], SKIN))
    parts.append(("hair", [head(p) for p in [(0.02, 1.28), (0.01, 1.40), (0.05, 1.48), (0.10, 1.50), (0.14, 1.54), (0.18, 1.49), (0.23, 1.51),
                                            (0.27, 1.45), (0.27, 1.40), (0.19, 1.42), (0.12, 1.38), (0.09, 1.31), (0.06, 1.26)]], HAIR))
    # 前手（近的那隻）：肩角、肘角＝和垂直往下的夾角；手形 fist／open／point／chest
    sa, ea, hand = pp["arm"]
    sh = up((0.04, 1.15))
    el = down(sh, 0.21, sa)
    ha = down(el, 0.20, ea)
    parts.append(("arm", limb(sh, el, 0.12, 0.10), COAT))
    parts.append(("arm", limb(el, ha, 0.10, 0.08), COAT))
    cuff = down(el, 0.15, ea)
    parts.append(("cuff", limb(cuff, ha, 0.085, 0.08), COAT_D))
    d = (math.sin(math.radians(ea)), -math.cos(math.radians(ea)))   # 前臂的方向
    if hand == "open":                                # 手掌張開（朝前）
        parts.append(("hand", limb(ha, (ha[0] + d[0] * 0.10, ha[1] + d[1] * 0.10), 0.08, 0.09), SKIN))
    elif hand == "point":                             # 食指指出去
        parts.append(("hand", ell(ha[0] + d[0] * 0.04, ha[1] + d[1] * 0.04, 0.045, 0.045, 12), SKIN))
        parts.append(("finger", limb(ha, (ha[0] + d[0] * 0.13, ha[1] + d[1] * 0.13), 0.03, 0.025), SKIN))
    else:
        parts.append(("hand", ell(ha[0] + d[0] * 0.045, ha[1] + d[1] * 0.045, 0.05, 0.06, 12), SKIN))
    return parts


# ---------------- 正面／背面 ----------------
def front_parts(pp, back):
    """pp：bob、step（-1～1，正＝右腳抬起）、swing（手臂前後擺，正面看是上下一點）"""
    bob, step, swing = pp.get("bob", 0), pp.get("step", 0), pp.get("swing", 0)
    parts = []
    for side in (-1, 1):                              # 腿
        lift = max(0.0, step * side) * 0.06
        x = side * 0.08
        top = (x, 0.80)
        foot = (x + side * 0.005, 0.06 + lift)
        parts.append(("leg", limb(top, foot, 0.14, 0.11), PANTS if side * (1 if not back else -1) > 0 else PANTS_D))
        parts.append(("shoe", [(x - 0.07, foot[1] - 0.06 + 0.0), (x + 0.07, foot[1] - 0.06), (x + 0.07, foot[1] + 0.02), (x - 0.07, foot[1] + 0.02)], SHOE))
    U = lambda p: (p[0], p[1] - bob)
    torso = [(-0.20, 0.78), (0.20, 0.78), (0.22, 1.00), (0.23, 1.14), (0.17, 1.22), (-0.17, 1.22), (-0.23, 1.14), (-0.22, 1.00)]
    parts.append(("torso", [U(p) if p[1] > 0.85 else p for p in torso], COAT))
    for side in (-1, 1):                              # 手臂（垂在兩側，走路時一隻往前＝看起來短一點）
        sh = U((side * 0.21, 1.14))
        k = swing * side * (1 if not back else -1)
        hand_y = 0.74 + max(0.0, k) * 0.05
        ha = (side * 0.25, hand_y - bob)
        parts.append(("arm", limb(sh, ha, 0.11, 0.08), COAT_D if side * (1 if not back else -1) < 0 else COAT))
        parts.append(("hand", ell(ha[0], ha[1] - 0.04, 0.045, 0.06, 12), SKIN_D if back else SKIN))
    if not back:
        parts.append(("collar", [U(p) for p in [(-0.08, 1.22), (0.08, 1.22), (0.0, 1.10)]], SHIRT))
    parts.append(("neck", [U(p) for p in limb((0, 1.18), (0, 1.25), 0.10, 0.09)], SKIN_D))
    parts.append(("head", [U(p) for p in ell(0, 1.35, 0.12, 0.14)], SKIN))
    if back:
        parts.append(("hair", [U(p) for p in [(-0.13, 1.27), (-0.14, 1.40), (-0.10, 1.48), (-0.04, 1.53), (0.02, 1.50), (0.07, 1.54), (0.12, 1.47),
                                             (0.14, 1.38), (0.13, 1.27), (0.06, 1.24), (-0.06, 1.24)]], HAIR))
    else:
        parts.append(("hair", [U(p) for p in [(-0.13, 1.30), (-0.14, 1.41), (-0.09, 1.49), (-0.03, 1.53), (0.03, 1.50), (0.08, 1.53), (0.13, 1.46),
                                             (0.14, 1.36), (0.10, 1.40), (0.03, 1.42), (-0.04, 1.39), (-0.10, 1.40)]], HAIR))
    return parts


# ---------------- 頭（手畫的像素頭像；這個密度用形狀算只剩一塊膚色加一塊紅，所以頭照 A＋ 與原插畫手畫） ----------------
# H 頭髮 L 頭髮亮 S 皮膚亮 s 皮膚 D 皮膚暗 d 皮膚最暗 B 眉 P 眼窩 E 眼白 W 臉上的傷 T 鬍渣 M 嘴 R 血 r 暗血
HEAD_PAL = dict(H=HAIR, L=HAIR_L, S=SKIN_L, s=SKIN, D=SKIN_D, d=SKIN_DD, B="#3a2a2a", P="#1a1a16", E="#c4c8b4",
                W="#6e3a30", T="#717a6a", M="#16181c", R=BLOOD, r="#4a1614")
HEAD_SIDE = ["...H...H....",     # 面向右；錨點＝頭的中心（第 5 欄、第 6.5 列）；照 A＋：頭髮在後半、臉往前凸、
             "..HHLHHHLH..",     # 眉和嘴唇是暗紅褐色、眼白只有一格、血很暗（不要鮮紅，會像吐舌頭）
             ".HHHHHHHHHH.",
             "HHHLHHHHSSH.",
             "HHHHsssSBBBB",     # 很重的眉骨
             "HHHHssssDEs.",     # 凹進去的眼窩＋眼白（往前瞪）
             "HHHDsDsDDDDs",     # 耳朵、鼻子（下緣暗）
             ".HHDsssssdMd",     # 嘴半開（暗縫）
             ".HHDsWsssBBB",     # 顴骨的傷、嘴唇
             "..HDDTTTTMr.",     # 鬍渣、嘴角往下滴的暗血
             "....dTTd.r.."]
HEAD_FRONT = [".H..H..H.",
              "HHLHHHLHH",
              "HHHHHHHHH",
              "HHsHHHsHH",       # 瀏海一撮一撮垂下來
              "DSssHssSd",       # 耳朵露出來
              "DBBBsBBBd",       # 很重的眉
              "dsEsSsEsd",       # 眼白（瞪著）
              ".DDsSsDD.",       # 眼下凹陷
              ".sWsDsss.",       # 臉頰的傷、鼻子的陰影
              ".TBMMMBT.",       # 嘴唇＋暗縫
              "..TTrTT.."]
HEAD_BACK = [".H..HH.H.",
             "HHHHHHHHH",
             "HLLHHHLLH",
             "HHHHHHHHH",
             "HHHLLHHHH",
             "DHHHHHHHd",
             "DHHHHLLHd",
             ".HHHHHHH.",
             ".HLLHHHH.",
             "..HHHHH..",
             "..dsssd..",
             "...DsD..."]
HEAD_PARTS = ("head", "jaw", "nose", "hair")
FRONT_OF_HEAD = ("arm", "cuff", "hand", "finger")   # 側面時畫在頭前面的（手舉到臉前）
_POSE = {}
CLIPPED = []


def local(x, y):
    """側面上半身的點 → 站直時的座標（拿來放口袋、皺褶這些細節）"""
    lx, ly = rot(_POSE["hip"], (x, y), _POSE["lean"])
    return lx, ly + _POSE["bob"]


# ---------------- 畫 ----------------
def render(parts, view):
    g = Grid(FW, FH)
    ox = FW / 2
    head_c = None
    if view == "side":
        hp = next(p for n, p, c in parts if n == "head")
        head_c = (sum(p[0] for p in hp) / len(hp), sum(p[1] for p in hp) / len(hp))
    else:
        hp = next(p for n, p, c in parts if n == "head")
        head_c = (sum(p[0] for p in hp) / len(hp), sum(p[1] for p in hp) / len(hp))
    body = [pt for pt in parts if pt[0] not in HEAD_PARTS]
    owner = [[None] * FW for _ in range(FH)]
    for py in range(FH):
        for px in range(FW):
            x = (px + 0.5 - ox) / PPM
            y = (FH - py - 0.5) / PPM
            for idx, (name, pts, col) in enumerate(body):
                if poly_in(x, y, pts):
                    owner[py][px] = (idx, name, col, x, y)

    def nb(px, py):
        return owner[py][px] if 0 <= px < FW and 0 <= py < FH else None

    for py in range(FH):
        for px in range(FW):
            o = owner[py][px]
            if not o:
                continue
            idx, name, col, x, y = o
            c = col
            left, right, up_, dn = nb(px - 1, py), nb(px + 1, py), nb(px, py - 1), nb(px, py + 1)
            left2 = nb(px - 2, py)
            same = lambda q: q and q[1] == name
            if view == "side":
                # 光從右前上方：前緣亮、後緣兩格漸暗
                if name in ("torso", "arm"):
                    if not same(right):
                        c = COAT_L
                    elif not same(left):
                        c = COAT_DD if name == "torso" else COAT_D
                    elif not same(left2) and name == "torso":
                        c = COAT_D
                if name == "leg_front":
                    if not same(right):
                        c = PANTS_L
                    elif not same(left):
                        c = PANTS_D
                if name == "hand":
                    c = SKIN_L if not same(right) else (SKIN_D if not same(left) or not same(dn) else SKIN)
                if name == "neck":
                    c = SKIN_DD if not same(left) else SKIN_D
                if name == "torso":
                    lx, ly = local(x, y) if y > 0.85 else (x, y)
                    if 0.79 < ly < 0.83:
                        c = COAT_D                     # 下擺
                    if not same(right) and any(abs(ly - b) < 0.016 for b in (1.12, 1.02, 0.92)):
                        c = BUTTON                     # 門襟的鈕扣
                    if 0.0 < lx < 0.10 and 1.06 < ly < 1.09 and same(right):
                        c = COAT_D                     # 胸前口袋蓋
                    if -0.13 < lx < -0.02 and abs((ly - 0.90) - (lx + 0.02) * 0.35) < 0.014:
                        c = COAT_D                     # 腰部的皺褶
                    if -0.05 < lx < 0.04 and 0.95 < ly < 1.0 and h(px, py, 41) < 0.3:
                        c = BLOOD_D                    # 衣服上乾掉的血（零星幾點）
                if name == "collar":
                    c = SHIRT if same(up_) else shade(SHIRT, 1.12)
                if name == "arm" and _POSE.get("elbow") and math.hypot(x - _POSE["elbow"][0], y - _POSE["elbow"][1]) < 0.035 and same(right):
                    c = COAT_D                         # 手肘的摺痕
                if name == "hand" and h(px, py, 45) < 0.3:
                    c = BLOOD                          # 手上的血
                if name == "shoe":
                    c = SOLE if not (up_ and up_[1] == "shoe") and False else c
                    if not (dn and dn[1] == "shoe"):
                        c = SOLE                       # 鞋底
                    elif not (up_ and up_[1] == "shoe"):
                        c = SHOE_L
            else:
                front = view == "front"
                if name in ("torso", "leg", "arm"):
                    base = {"torso": (COAT_L, COAT, COAT_D), "arm": (COAT_L, col, COAT_DD), "leg": (PANTS_L, col, PANTS_D)}[name]
                    if not same(right):
                        c = base[0]                    # 光從右前方
                    elif not same(left):
                        c = base[2]
                if name == "torso":
                    if 0.79 < y < 0.83:
                        c = COAT_D                     # 下擺
                    if (left and left[1] == "arm") or (right and right[1] == "arm"):
                        c = COAT_DD                    # 手臂下的陰影
                    if front:
                        if abs(x) < 0.016 and y < 1.12:
                            c = BUTTON if any(abs(y - b) < 0.016 for b in (1.06, 0.96, 0.86)) else COAT_D   # 門襟＋鈕扣
                        if 0.05 < abs(x) < 0.15 and 1.04 < y < 1.07:
                            c = COAT_D                 # 兩個胸前口袋蓋
                        if 0.04 < x < 0.12 and 0.93 < y < 0.98 and h(px, py, 47) < 0.3:
                            c = BLOOD_D
                    else:
                        if abs(y - 1.15) < 0.016 and abs(x) < 0.19:
                            c = COAT_D                 # 背後的肩線
                        if abs(x) < 0.012 and y < 0.97:
                            c = COAT_D                 # 背後的縫線
                        if -0.06 < x < 0.06 and 0.98 < y < 1.12:
                            c = PAPER if y > 0.99 else PAPER_D   # 背上夾著的病歷卡（原插畫）
                            if abs(y - 1.08) < 0.02 and abs(x) < 0.04:
                                c = PAPER_D
                if name == "arm" and abs(y - 0.97) < 0.016 and same(left) and same(right):
                    c = COAT_D                         # 手肘的摺痕
                if name == "leg" and abs(y - 0.45) < 0.016 and same(left) and same(right):
                    c = PANTS_L                        # 膝蓋
                if name == "collar":
                    c = SHIRT
                if name == "neck":
                    c = SKIN_D
                if name == "hand":
                    c = (SKIN if front else SKIN_D) if same(left) else SKIN_DD
                    if front and x > 0 and h(px, py, 46) < 0.4:
                        c = BLOOD                      # 右手的血
                if name == "shoe":
                    c = SOLE if not (dn and dn[1] == "shoe") else (SHOE_L if not (up_ and up_[1] == "shoe") else SHOE)
            g.put(px, py, c)
    # 頭像：錨點對到頭的中心；擋在臉前的手不蓋掉
    stamp = HEAD_SIDE if view == "side" else (HEAD_FRONT if view == "front" else HEAD_BACK)
    ac, ar = (5, 6.5) if view == "side" else (4, 6.5)
    cpx, cpy = head_c[0] * PPM + ox, FH - head_c[1] * PPM
    tlx, tly = int(round(cpx - ac - 0.5)), int(round(cpy - ar - 0.5))
    for r, row in enumerate(stamp):
        for cc, ch in enumerate(row):
            if ch == ".":
                continue
            px, py = tlx + cc, tly + r
            if not (0 <= px < FW and 0 <= py < FH):
                CLIPPED.append(view)                   # 頭像超出畫格（會被切掉）
                continue
            o = owner[py][px]
            if view == "side" and o and o[1] in FRONT_OF_HEAD:
                continue
            g.put(px, py, HEAD_PAL[ch])
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


def side_frame(pp):
    lean, bob = pp.get("lean", 0), pp.get("bob", 0)
    _POSE.update(hip=(-0.02, 0.80), lean=lean, bob=bob)
    sa, ea, _ = pp["arm"]
    sh = rot((-0.02, 0.80), (0.04, 1.15 - bob), -lean)
    _POSE["elbow"] = down(sh, 0.21, sa)
    return render(side_parts(pp), "side")


# ---------------- 姿勢表 ----------------
IDLE = [dict(bob=b, legs=((-3, 0), (3, 0)), arm=(-2, 2, "fist")) for b in (0, 0, 0.031, 0.031)]
WALK = []
for k in range(6):                                 # 第 0、3 格兩腳張開著地（player_3d.gd 在這兩格播腳步聲），中間兩格擺動的腳彎膝
    s_ = math.sin(2 * math.pi * k / 6)
    c_ = math.cos(2 * math.pi * k / 6)
    WALK.append(dict(bob=0.031 if k in (0, 3) else 0,
                     legs=((-16 * c_, 18 * max(0, s_)), (16 * c_, 18 * max(0, -s_))),
                     arm=(-14 * c_, -6 * c_, "fist"), arm_b=(14 * c_, 18 * c_, "fist")))
REACH = [dict(lean=5, legs=((-4, 0), (6, 0)), arm=(35, 45, "open"), head=(0.01, 0)),
         dict(lean=8, legs=((-6, 0), (8, 0)), arm=(60, 70, "open"), head=(0.02, -0.01)),
         dict(lean=10, legs=((-7, 0), (9, 0)), arm=(78, 85, "open"), head=(0.03, -0.01))]
LEAN = [dict(lean=12, legs=((-5, 0), (5, 0)), arm=(8, 14, "fist"), head=(0.0, -0.02)),      # 頭像比較寬，往前探太多會超出畫格
        dict(lean=20, legs=((-6, 0), (6, 0)), arm=(14, 22, "fist"), head=(-0.05, -0.04))]
GESTURE = [dict(legs=((-3, 0), (3, 0)), arm=(-2, 2, "fist")),            # 站好（手勢開始與結束）
           dict(legs=((-3, 0), (3, 0)), arm=(50, -95, "open")),           # 手按胸口（我）：前臂橫過胸前
           dict(legs=((-3, 0), (3, 0)), arm=(40, 170, "open")),           # 手掌舉到臉前、朝前（在）
           dict(lean=3, legs=((-3, 0), (3, 0)), arm=(40, 30, "point")),   # 指向地面（這裡）
           dict(lean=4, legs=((-3, 0), (3, 0)), arm=(32, 18, "point"))]   # 往下點（第 3、4 格交替＝點兩下）

side_r = [side_frame(p) for p in IDLE + WALK]
act_r = [side_frame(p) for p in REACH + LEAN]
ges_r = [side_frame(p) for p in GESTURE]


def mirror(g):
    m = Grid(g.w, g.h)
    for y in range(g.h):
        for x in range(g.w):
            c = g.get(x, y)
            if c:
                m.put(g.w - 1 - x, y, c)
    return m


frames = side_r + [mirror(f) for f in side_r] + act_r + [mirror(f) for f in act_r] + ges_r + [mirror(f) for f in ges_r]
FB_IDLE = [dict(bob=b) for b in (0, 0, 0.031, 0.031)]
FB_WALK = [dict(bob=0.031 if k in (1, 4) else 0, step=math.sin(2 * math.pi * k / 6), swing=math.sin(2 * math.pi * k / 6)) for k in range(6)]
fb = [render(front_parts(p, False), "front") for p in FB_IDLE + FB_WALK] + [render(front_parts(p, True), "back") for p in FB_IDLE + FB_WALK]


def sheet(frs, name):
    S = Grid(FW * len(frs), FH)
    for i, f in enumerate(frs):
        for y in range(FH):
            for x in range(FW):
                c = f.get(x, y)
                if c:
                    S.put(i * FW + x, y, c)
    S.save_txt(f"{OUT}/{name}.txt", outline=False)
    subprocess.run(["magick", f"{OUT}/{name}.txt", f"PNG32:{OUT}/{name}.png"], check=True)
    print(name, S.w, "x", S.h, len(frs), "格")


if CLIPPED:
    print("⚠ 頭像超出畫格", len(CLIPPED), "格像素", set(CLIPPED))
sheet(frames, "player3d")
sheet(fb, "player3d_fb")
subprocess.run(["magick", f"{OUT}/player3d.png", f"{OUT}/player3d_fb.png", "-background", "#3a3f44", "-gravity", "west", "-append",
                "-filter", "point", "-resize", "400%", f"{OUT}/preview.png"], check=True)
