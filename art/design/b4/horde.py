# B4-5 感染者群（廢墟）：原插畫沒有，照 A＋ 的 horde_anim.png（96×44）：兩隻蹲著啃食、中間一隻站著，
# look 時站著那隻把頭轉過來。牠們是感染者，畫法照主角（灰綠皮膚、駝背、臉手畫、嘴邊的血是暗紅）。
# 密度 A；每隻用 figlib 畫成 32×51，再排成 96×51 一格（面向左）。
# 輸出 horde3d.png（8 格）：eat 0-3（頭往下 0/1/2/1 格，右邊那隻錯開半個週期）、look 4-7（同樣啃食＋站著那隻轉頭看過來）
# 用法：python3 art/design/b4/horde.py 輸出資料夾
import math, sys, subprocess
sys.dont_write_bytecode = True                         # 不要在 art/ 留下 __pycache__
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/design/b4")
from figlib import *

OUT = sys.argv[1]

SKIN = ("#a0ae9c", "#8c9a8a", "#6a786c")
PANTS = ("#363944", "#2a2c34", "#1e2026")
SHOE = ("#2a2420", "#1e1a16", "#141110")
SHIRT_A = ("#7a4e40", "#62402f", "#4a3024")         # 左邊蹲著那隻：紅褐色
SHIRT_B = ("#76765e", "#5e5e4a", "#48483a")         # 右邊蹲著那隻：灰橄欖色
SHIRT_S = ("#52627a", "#3e4c62", "#2e3a4c")         # 站著那隻：藍色
POOL = ("#4a1410", "#3a0e0c", "#2a0a08")             # 地上的血（暗紅，不要鮮紅）
PAL = dict(H="#26221e", L="#3e3830", S="#a8b5a3", s="#8c9a8a", D="#6a786c", d="#4f5a50", B="#3a2a2a", P="#1a1a16",
           E="#c4c8b4", T="#717a6a", M="#16181c", r="#4a1614", R="#6a1c16")

# 頭像（面向右）：和主角同一套畫法（眉骨重、眼白一格、凹頰、嘴是暗縫＋暗血）
HEAD_SIDE = ["...H..H.H..",
             ".HHHHLHHHH.",
             "HHLHHHHHHH.",
             "HHHHHHHHSH.",
             "HHHHsssSBBB",
             "HHHHssssDEs",
             "HHHDsDsDDDs",
             ".HHDsssssMd",
             ".HHDsssdBBR",
             "..HDDTTTMr.",
             "....dTTd.r."]
HEAD_FRONT = [".H..H.H..",       # 轉過來看（站著那隻 look）
              "HHHHHHHHH",
              "HLHHHHHLH",
              "HHsHHHsHH",
              "DSssHssSd",
              "DBBBsBBBd",
              "dsEsSsEsd",       # 空洞地瞪著
              ".DDsSsDD.",
              ".sDsDsds.",
              ".TBMMMBT.",
              "..TrRrT.."]

_POSE = {}


def crouch_parts(shirt, bite):
    """蹲著啃食（面向右）：膝蓋跪在地上、背拱起來、兩手撐地、頭低到地面；bite＝頭往下幾格"""
    b = bite / PPM
    parts = [("pool", ell(0.30, 0.02, 0.20, 0.025, 16), POOL)]
    parts.append(("leg_b", limb((-0.26, 0.42), (-0.12, 0.07), 0.14, 0.11), (PANTS[1], PANTS[2], PANTS[2])))
    parts.append(("leg_b", limb((-0.12, 0.07), (-0.42, 0.05), 0.10, 0.08), (PANTS[1], PANTS[2], PANTS[2])))
    parts.append(("shoe", [(-0.48, 0.02), (-0.36, 0.02), (-0.36, 0.09), (-0.48, 0.07)], SHOE))
    parts.append(("arm_b", limb((0.06, 0.58), (0.22, 0.05), 0.09, 0.07), (shirt[1], shirt[2], shirt[2])))
    parts.append(("torso", [(-0.32, 0.40), (-0.30, 0.56), (-0.18, 0.70), (-0.02, 0.74), (0.12, 0.70), (0.20, 0.58),
                            (0.16, 0.44), (-0.04, 0.38)], shirt))
    parts.append(("leg", limb((-0.22, 0.42), (-0.06, 0.07), 0.14, 0.11), PANTS))
    parts.append(("leg", limb((-0.06, 0.07), (-0.36, 0.05), 0.10, 0.08), PANTS))
    parts.append(("shoe", [(-0.42, 0.02), (-0.30, 0.02), (-0.30, 0.09), (-0.42, 0.07)], SHOE))
    parts.append(("neck", limb((0.14, 0.56), (0.24, 0.40 - b), 0.08, 0.07), SKIN))
    parts.append(("arm", limb((0.10, 0.60), (0.30, 0.06), 0.10, 0.08), shirt))
    parts.append(("hand", ell(0.32, 0.05, 0.045, 0.035, 10), SKIN))
    return parts, (0.30, 0.27 - b)


def stand_parts(bob):
    """站著（面向右）：駝背、頭往前探、手垂著"""
    hip = (-0.02, 0.80)
    up = lambda p: rot(hip, (p[0], p[1] - bob), -14)
    parts = []
    for name, ang, ramp in (("leg_b", -3, (PANTS[1], PANTS[2], PANTS[2])), ("leg", 3, PANTS)):
        knee = down(hip, 0.37, ang)
        foot = down(knee, 0.38, ang)
        parts.append((name, limb(hip, knee, 0.15, 0.12), ramp))
        parts.append((name, limb(knee, foot, 0.12, 0.10), ramp))
        parts.append(("shoe", [(foot[0] - 0.06, foot[1] + 0.02), (foot[0] + 0.11, foot[1] - 0.02), (foot[0] + 0.11, foot[1] - 0.05), (foot[0] - 0.06, foot[1] - 0.05)], SHOE))
    torso = [(-0.15, 0.76), (0.10, 0.76), (0.13, 0.95), (0.15, 1.10), (0.11, 1.20), (0.02, 1.23), (-0.10, 1.21), (-0.17, 1.10), (-0.18, 0.95)]
    parts.append(("torso", [up(p) if p[1] > 0.85 else p for p in torso], SHIRT_S))
    parts.append(("neck", [up(p) for p in limb((0.07, 1.18), (0.14, 1.25), 0.09, 0.08)], SKIN))
    sh = up((0.04, 1.15))
    el = down(sh, 0.21, 6)
    ha = down(el, 0.20, 10)
    parts.append(("arm", limb(sh, el, 0.11, 0.09), SHIRT_S))
    parts.append(("arm", limb(el, ha, 0.09, 0.08), SHIRT_S))
    parts.append(("hand", ell(ha[0], ha[1] - 0.04, 0.045, 0.055, 10), SKIN))
    return parts, up((0.17, 1.34))


def detail(name, x, y, px, py, c, nb):
    if name == "pool":
        c = POOL[1] if h(px, py, 21) < 0.7 else POOL[2]
    if name == "torso" and h(px, py, 22) < 0.02:
        c = "#4a1a14"                                   # 衣服上乾掉的血（零星幾點，多了像圓點花紋）
    if name == "hand" and h(px, py, 23) < 0.4:
        c = "#5a1a14"
    if name == "shoe" and nb(0, 1) != "shoe":
        c = "#0e0c0a"
    return c


BITE = [0, 1, 2, 1]
FW3 = FW * 3


def frame(k, look):
    a_parts, a_head = crouch_parts(SHIRT_A, BITE[k])
    b_parts, b_head = crouch_parts(SHIRT_B, BITE[(k + 2) % 4])
    s_parts, s_head = stand_parts(0.031 if k in (1, 2) else 0)
    A = mirror(render(a_parts, HEAD_SIDE, a_head, PAL, detail, anchor=(5, 4.5)))
    B = mirror(render(b_parts, HEAD_SIDE, b_head, PAL, detail, anchor=(5, 4.5)))
    if look:                                           # 轉過來看：正面的頭（不鏡射）
        Sg = mirror(render(s_parts, None, s_head, PAL, detail))
        Sh = render([], HEAD_FRONT, (-s_head[0], s_head[1]), PAL, None, anchor=(4, 5))
    else:
        Sg = mirror(render(s_parts, HEAD_SIDE, s_head, PAL, detail, anchor=(5, 5)))
        Sh = None
    G = Grid(FW3, FH)
    for img, ox in ((Sg, 32), (Sh, 32), (A, 0), (B, 62)):
        if img is None:
            continue
        for y in range(FH):
            for x in range(FW):
                c = img.get(x, y)
                if c and 0 <= ox + x < FW3:
                    G.put(ox + x, y, c)
    return G


frames = [frame(k, False) for k in range(4)] + [frame(k, True) for k in range(4)]
S = Grid(FW3 * len(frames), FH)
for i, f in enumerate(frames):
    for y in range(FH):
        for x in range(FW3):
            c = f.get(x, y)
            if c:
                S.put(i * FW3 + x, y, c)
S.save_txt(f"{OUT}/horde3d.txt", outline=False)
subprocess.run(["magick", f"{OUT}/horde3d.txt", f"PNG32:{OUT}/horde3d.png"], check=True)
print("horde3d", S.w, "x", S.h, len(frames), "格")
