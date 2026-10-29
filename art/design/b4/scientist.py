# B4-4 女科學家（設施走廊）：照原插畫 scene_07（深棕色中分直髮及肩、白袍、裡面灰色上衣、擔憂的表情）
# 與 A＋ 的像素圖（scientist_anim.png：抱筆記本待機、遞出筆記本、跑走）。
# 密度 A，每格 32×51；身體用形狀算、頭手畫（figlib.py）。活人不要畫成喪屍的樣子（B4-3a）：頭擺正、手不往前抓、嘴有血色。
# 圖面向左（先畫面向右再鏡射）。輸出 scientist3d.png（8 格）：待機 0-1（抱著筆記本）、遞出 2-3、跑走 4-7（筆記本給出去了）
# 用法：python3 art/design/b4/scientist.py 輸出資料夾
import math, sys
sys.dont_write_bytecode = True                         # 不要在 art/ 留下 __pycache__
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/design/b4")
from figlib import *

OUT = sys.argv[1]

SKIN = ("#d8b498", "#c09a80", "#9a7a64")
COAT = ("#e2e4d8", "#c8cabe", "#a2a498")            # 白袍（偏灰，不要純白）
COAT_B = ("#c8cabe", "#b0b2a6", "#8e9084")
SHIRT = ("#7a7e84", "#666a70", "#50545a")           # 灰色上衣
PANTS = ("#3a3c44", "#2c2e36", "#202228")
PANTS_B = ("#2c2e36", "#22242a", "#18191e")
SHOE = ("#2e2a26", "#1e1c1a", "#141210")
BOOK = ("#8a5a36", "#6e4428", "#50301c")
PAGES = ("#d8d0b8", "#d8d0b8", "#b8b098")
PAL = dict(H="#3a2a20", L="#5a4232", K="#24180f", S="#d8b498", s="#c09a80", d="#9a7a64", B="#3a2a20",
           E="#e8e2d6", P="#2a1c18", m="#a8685c", O="#6a2a24", R="#cc9480")

# 頭像（面向右）；錨點＝頭的中心（第 4.5 欄、第 5 列）。中分直髮及肩：頂上一道亮面、後面直直垂下
HEAD_IDLE = ["..HHHHH...",
             ".HLLLHHH..",
             "HHHHHLLHH.",
             "HHHHHHHsH.",        # 額頭（中分，瀏海往兩邊）
             "HHHHHHsBBs",        # 眉（微皺，擔憂）
             "HHHHHdsEPs",        # 眼白＋瞳孔
             "HKHHHdsssS",        # 鼻子
             "HKHHKHdsRs",        # 臉頰
             "HKHHKHdmm.",        # 嘴唇
             "HKHHKH.ds.",        # 下巴
             "HHKHH..d..",        # 直髮垂到肩上
             ".HHH......"]
HEAD_RUN = HEAD_IDLE[:4] + ["HHHHHHsBBH",         # 眉毛挑高
                            "HHHHHHsEEs",         # 眼睛瞪大
                            "HKHHHdsEPs",
                            "HKHHKHdssS",
                            "HKHHKHdmm.",
                            "HKHHKH.dO.",         # 嘴微張（喘）
                            "HHKHH..d..",
                            ".HHH......"]

_POSE = {}


def local(x, y):
    lx, ly = rot(_POSE["hip"], (x, y), _POSE["lean"])
    return lx, ly + _POSE["bob"]


def parts_of(pp):
    """pp：lean、bob、legs ((角度, 膝彎) 後腿, 前腿)、arm (肩角, 肘角) 前手、arm_b (肩角, 肘角) 後手、book：none／hug／offer"""
    lean, bob = pp.get("lean", 0), pp.get("bob", 0)
    hip = (0.0, 0.80)
    _POSE.update(hip=hip, lean=lean, bob=bob)

    def up(p):
        return rot(hip, (p[0], p[1] - bob), -lean)

    parts = []
    sa, ea = pp["arm_b"]                               # 後手
    sh = up((-0.03, 1.16))
    el = down(sh, 0.24, sa)
    ha = down(el, 0.22, ea)
    parts.append(("arm_b", limb(sh, el, 0.09, 0.08), COAT_B))
    parts.append(("arm_b", limb(el, ha, 0.08, 0.07), COAT_B))
    parts.append(("hand_b", ell(ha[0], ha[1] - 0.02, 0.035, 0.04, 10), SKIN))
    for name, (ang, bend), ramp in (("leg_b", pp["legs"][0], PANTS_B), ("leg", pp["legs"][1], PANTS)):
        knee = down(hip, 0.38, ang)
        foot = down(knee, 0.37, ang - bend)
        parts.append((name, limb(hip, knee, 0.12, 0.10), ramp))
        parts.append((name, limb(knee, foot, 0.10, 0.08), ramp))
        fx, fy = foot
        parts.append(("shoe", [(fx - 0.05, fy + 0.02), (fx + 0.04, fy + 0.03), (fx + 0.09, fy - 0.01), (fx + 0.09, fy - 0.04), (fx - 0.05, fy - 0.04)], SHOE))
    # 白袍（長到膝蓋，跑的時候下擺往後飄）
    flap = pp.get("flap", 0.0)
    coat = [(-0.15 - flap, 0.46), (0.12, 0.48), (0.13, 0.80), (0.12, 0.95), (0.14, 1.07), (0.13, 1.17), (0.07, 1.23),
            (-0.10, 1.23), (-0.16, 1.16), (-0.16, 0.98), (-0.16, 0.80)]
    parts.append(("coat", [up(p) if p[1] > 0.6 else p for p in coat], COAT))
    parts.append(("shirt", [up(p) for p in [(0.03, 1.23), (0.12, 1.17), (0.125, 0.86), (0.08, 0.86)]], SHIRT))
    parts.append(("neck", [up(p) for p in limb((0.0, 1.18), (0.02, 1.28), 0.07, 0.06)], SKIN))
    sa, ea = pp["arm"]                                 # 前手
    sh = up((0.02, 1.15))
    el = down(sh, 0.24, sa)
    ha = down(el, 0.22, ea)
    d = (math.sin(math.radians(ea)), -math.cos(math.radians(ea)))
    book = pp.get("book", "none")
    if book == "hug":                                  # 筆記本抱在胸前（直立、封面朝外）
        bx, by = up((0.15, 0.98))
        parts.append(("book", [(bx - 0.05, by - 0.15), (bx + 0.05, by - 0.15), (bx + 0.05, by + 0.13), (bx - 0.05, by + 0.13)], BOOK))
    parts.append(("arm", limb(sh, el, 0.10, 0.085), COAT))
    parts.append(("arm", limb(el, ha, 0.085, 0.075), COAT))
    parts.append(("cuff", limb(down(el, 0.17, ea), ha, 0.08, 0.075), COAT))
    parts.append(("hand", ell(ha[0] + d[0] * 0.035, ha[1] + d[1] * 0.035, 0.04, 0.045, 10), SKIN))
    if book == "offer":                                # 遞出去：平放在手掌上
        bx, by = ha[0] + d[0] * 0.04, ha[1] + d[1] * 0.04 + 0.04
        parts.append(("book", [(bx - 0.10, by - 0.02), (bx + 0.10, by - 0.02), (bx + 0.10, by + 0.04), (bx - 0.10, by + 0.04)], BOOK))
        parts.append(("pages", [(bx - 0.09, by - 0.02), (bx + 0.09, by - 0.02), (bx + 0.09, by + 0.0), (bx - 0.09, by + 0.0)], PAGES))
    head_c = up((0.0, 1.39))
    return parts, head_c


def detail(name, x, y, px, py, c, nb):
    if name == "coat":
        lx, ly = local(x, y)
        if ly < 0.5:
            c = COAT[2]                                 # 下擺
        if nb(1, 0) == "shirt":
            c = COAT[0]                                 # 翻領
        if -0.02 < lx < 0.09 and abs(ly - 0.74) < 0.016:
            c = COAT[2]                                 # 口袋
        if 0.06 < lx < 0.10 and 1.04 < ly < 1.10 and nb(-1, 0) == "coat":
            c = "#4a6a8a" if ly > 1.07 else COAT[2]     # 胸前口袋插著筆
        if -0.14 < lx < -0.05 and abs((ly - 0.92) - (lx + 0.05) * 0.5) < 0.014:
            c = COAT[2]                                 # 背後的皺褶
    if name == "book":
        if nb(1, 0) != "book" and nb(1, 0) != "pages":
            c = BOOK[0]
        if h(px, py, 13) < 0.1:
            c = BOOK[2]
    if name == "shoe" and nb(0, 1) != "shoe":
        c = "#0e0c0a"
    return c


def frame(pp, stamp):
    parts, head_c = parts_of(pp)
    return render(parts, stamp, head_c, PAL, detail, anchor=(4.5, 5), front_of_head=("arm", "hand", "cuff"))


IDLE = [dict(bob=b, legs=((-3, 0), (3, 0)), arm=(28, -150), arm_b=(10, -60), book="hug") for b in (0, 0.031)]
EVENT = [dict(lean=2, legs=((-4, 0), (6, 0)), arm=(15, 70), arm_b=(-4, 0), book="offer"),          # 手肘貼著身體、在腰的高度慢慢遞出
         dict(lean=3, legs=((-4, 0), (6, 0)), arm=(22, 80), arm_b=(-4, 0), book="offer")]   # （整條手臂伸直像要抓人）
RUN = []
for k in range(4):
    s_, c_ = math.sin(2 * math.pi * k / 4), math.cos(2 * math.pi * k / 4)
    RUN.append(dict(lean=8, bob=0 if k in (0, 2) else -0.031, flap=0.06 + 0.03 * abs(s_),
                    legs=((-22 * c_, 45 * max(0, s_)), (22 * c_, 45 * max(0, -s_))),
                    arm=(-24 * c_, -24 * c_ + 55), arm_b=(24 * c_, 24 * c_ + 55)))

frames = [frame(p, HEAD_IDLE) for p in IDLE + EVENT] + [frame(p, HEAD_RUN) for p in RUN]
frames = [mirror(f) for f in frames]                   # 面向左
sheet(frames, OUT, "scientist3d")
