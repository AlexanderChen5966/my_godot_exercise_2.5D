# B4-5 妻子（廢墟的避難所）：短髮照 A＋（作者：經過末日髮型會變；原插畫 scene_19 的長捲髮頭像 HEAD_LONG 保留），衣服照 A＋ 的 wife_anim.png（咖啡色長外套，
# 倖存者的樣子；回憶裡的橘色洋裝不適合現在）。動作照 A＋：分麵包（把麵包遞出去 → 收回胸前撕開 → 再遞出去）。
# 活人不要畫成喪屍的樣子（B4-3a）：頭擺正、手肘彎著在腰的高度遞出、臉有血色。
# 密度 A，每格 32×51，身體用形狀算、頭手畫（figlib.py）；圖面向左（先畫面向右再鏡射）。
# 輸出 wife3d.png（4 格）：idle 0-3
# 用法：python3 art/design/b4/wife.py 輸出資料夾
import math, sys
sys.dont_write_bytecode = True                         # 不要在 art/ 留下 __pycache__
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/design/b4")
from figlib import *

OUT = sys.argv[1]

SKIN = ("#dcb494", "#c49a7c", "#9e7a62")
COAT = ("#a46a3c", "#8a5630", "#6c4224")
COAT_B = ("#8a5630", "#744828", "#5a381e")
SCARF = ("#7a6a58", "#665848", "#4e4438")           # 圍巾（灰褐色）
PANTS = ("#3e3430", "#302824", "#221c1a")
PANTS_B = ("#302824", "#262020", "#1a1614")
SHOE = ("#36302a", "#221e1c", "#161412")
BREAD = ("#dcae68", "#ba8c4c", "#8a6432")
PAL = dict(H="#7a3a24", L="#9a5232", K="#56281a", S="#dcb494", s="#c49a7c", d="#9e7a62", B="#5a3020",
           E="#e8e0d0", P="#2a1c18", m="#b0645a", R="#d4927c")

# 頭像（面向右）；錨點＝頭的中心（第 4.5 欄、第 5 列）。過肩的長捲髮垂在背後
HEAD = ["...HHHHH...",
        "..HHHHHHHH.",
        ".HHHHHHHHHH",
        ".HHHHHHHHsH",          # 瀏海往旁邊撥
        "HHHHHHHHsBB",          # 眉（溫和）
        "HHHHHHHdsEP",          # 眼白＋瞳孔
        "HHHHHHHdssS",          # 鼻子
        "HHHHHHHdsRs",          # 臉頰的血色
        "HHHHHHHHdmm",          # 嘴唇（淡淡地笑）
        "HHHHHH..ds.",          # 下巴
        "HHHHHH...d.",
        "HHHHH......",          # 長髮垂到背後
        ".HHHH......",
        "..HH......."]


def waves(stamp):
    """頭髮（H）畫成長波浪：斜的亮、暗髮絲，每三列往前錯一格（點狀的亮暗會變成小捲或圓點，和婦人的 curls() 不同）"""
    out = []
    for r, row in enumerate(stamp):
        line = ""
        for c, ch in enumerate(row):
            if ch == "H":
                k = (c + r // 3) % 4
                ch = "L" if k == 0 else ("K" if k == 2 and r >= 4 else "H")
            line += ch
        out.append(line)
    return out


HEAD_LONG = waves([r[1:] for r in HEAD])              # 長髮（原插畫回憶裡的樣子）：保留當備用；後腦削掉一欄（頭髮太寬臉會擠成一條）
# 作者 2026-10-29：維持 A＋ 的短髮（經過末日，髮型和服裝都會變），長髮的頭像保留
HEAD_SHORT = waves(["..HHHHH...",
                    ".HHHHHHHH.",
                    "HHHHHHHHHH",
                    "HHHHHHHHsH",          # 瀏海往旁邊撥
                    "HHHHHHHsBB",          # 眉（溫和）
                    "HHHHHHdsEP",          # 眼白＋瞳孔
                    "HHHHHHdssS",          # 鼻子
                    "HHHHHHdsRs",          # 臉頰的血色
                    ".HHHHHHdmm",          # 嘴唇（淡淡地笑）
                    "..HHH..ds.",          # 短髮剪到下巴
                    ".......d.."])
HEAD = HEAD_SHORT


def parts_of(pp):
    """pp：bob、arm (肩角, 肘角) 前手、arm_b (肩角, 肘角) 後手、bread：offer（在前手上）／chest（兩手在胸前撕開）"""
    bob = pp.get("bob", 0)
    hip = (0.0, 0.80)
    up = lambda p: (p[0], p[1] - bob)
    parts = []
    sa, ea = pp["arm_b"]
    sh = up((-0.03, 1.16))
    el = down(sh, 0.24, sa)
    ha = down(el, 0.22, ea)
    parts.append(("arm_b", limb(sh, el, 0.09, 0.08), COAT_B))
    parts.append(("arm_b", limb(el, ha, 0.08, 0.07), COAT_B))
    parts.append(("hand_b", ell(ha[0], ha[1], 0.035, 0.04, 10), SKIN))
    for name, ang, ramp in (("leg_b", -3, PANTS_B), ("leg", 3, PANTS)):
        knee = down(hip, 0.38, ang)
        foot = down(knee, 0.37, ang)
        parts.append((name, limb(hip, knee, 0.12, 0.10), ramp))
        parts.append((name, limb(knee, foot, 0.10, 0.08), ramp))
        fx, fy = foot
        parts.append(("shoe", [(fx - 0.05, fy + 0.03), (fx + 0.04, fy + 0.03), (fx + 0.09, fy - 0.01), (fx + 0.09, fy - 0.04), (fx - 0.05, fy - 0.04)], SHOE))
    coat = [(-0.17, 0.42), (0.14, 0.42), (0.14, 0.80), (0.12, 0.95), (0.14, 1.07), (0.13, 1.17), (0.07, 1.23),
            (-0.10, 1.23), (-0.16, 1.16), (-0.17, 0.98), (-0.17, 0.80)]
    parts.append(("coat", [up(p) if p[1] > 0.6 else p for p in coat], COAT))
    parts.append(("scarf", [up(p) for p in [(-0.08, 1.24), (0.10, 1.24), (0.13, 1.16), (0.10, 1.10), (-0.06, 1.12)]], SCARF))
    parts.append(("neck", [up(p) for p in limb((0.0, 1.20), (0.02, 1.28), 0.07, 0.06)], SKIN))
    sa, ea = pp["arm"]
    sh = up((0.02, 1.15))
    el = down(sh, 0.24, sa)
    ha = down(el, 0.22, ea)
    d = (math.sin(math.radians(ea)), -math.cos(math.radians(ea)))
    parts.append(("arm", limb(sh, el, 0.10, 0.085), COAT))
    parts.append(("arm", limb(el, ha, 0.085, 0.075), COAT))
    hc = (ha[0] + d[0] * 0.035, ha[1] + d[1] * 0.035)
    if pp["bread"] == "chest":                          # 撕開的麵包，兩塊在胸前
        parts.append(("bread", ell(hc[0] + 0.02, hc[1] + 0.03, 0.06, 0.04, 12), BREAD))
    parts.append(("hand", ell(hc[0], hc[1], 0.04, 0.045, 10), SKIN))
    if pp["bread"] == "offer":                          # 一塊麵包放在手上遞出去
        parts.append(("bread", ell(hc[0] + 0.03, hc[1] + 0.05, 0.07, 0.04, 12), BREAD))
    return parts, up((0.0, 1.39))


def detail(name, x, y, px, py, c, nb):
    if name == "coat":
        if y < 0.45:
            c = COAT[2]                                 # 下擺
        if abs(y - 0.84) < 0.016 and nb(0, 0) == "coat":
            c = "#4a2e1a"                               # 腰帶
        if nb(1, 0) not in ("coat", "scarf", "arm", "hand", "bread") and any(abs(y - b) < 0.016 for b in (1.0, 0.92, 0.72, 0.62)):
            c = "#3a2414"                               # 扣子
        if 0.0 < x < 0.10 and abs(y - 0.68) < 0.016:
            c = COAT[2]                                 # 口袋
        if h(px, py, 31) < 0.015:
            c = COAT[2]                                 # 舊外套的磨損
    if name == "bread" and h(px, py, 32) < 0.25:
        c = BREAD[2]                                    # 麵包皮的紋路
    if name == "shoe" and nb(0, 1) != "shoe":
        c = "#0e0c0a"
    return c


def frame(pp):
    parts, head_c = parts_of(pp)
    return render(parts, HEAD, head_c, PAL, detail, anchor=(3.5, 5), front_of_head=("arm", "hand", "bread"))


IDLE = [dict(bob=0, arm=(8, 78), arm_b=(-3, 0), bread="offer"),           # 遞出去（手肘貼著身體、前臂往前；整條手臂伸直像要抓人）
        dict(bob=0.031, arm=(4, 68), arm_b=(-3, 0), bread="offer"),       # 稍微收回
        dict(bob=0.031, arm=(25, -150), arm_b=(-3, 0), bread="chest"),     # 收回胸前撕開麵包（後手往前會從背後露出一點）
        dict(bob=0, arm=(12, 82), arm_b=(-3, 0), bread="offer")]          # 再遞出去

frames = [mirror(frame(p)) for p in IDLE]              # 面向左
sheet(frames, OUT, "wife3d")
