# B4-3 婦人（停車場）：照原插畫 scene_02（中年、及肩的紅褐色捲髮、橄欖褐有翻領的西裝外套、米色有扣襯衫、
# 一手提咖啡色皮包、另一手張開手掌擋在前面、瞪大眼睛尖叫）與 A＋ 的像素圖（woman_anim.png：待機、尖叫、逃跑）。
# 密度 A（每公尺 32 像素），每格 32×51；身體用形狀算、頭用手畫的像素頭像（figlib.py，B4-2 主角的做法）。
# 圖面向左（和 A＋ 一樣：尖叫時面向主角，逃跑時遊戲用 flip_h 翻成背對主角）：先畫面向右再鏡射。
# 輸出 woman3d.png（8 格）：待機 0-1、尖叫 2-3（嘴一張一合）、逃跑 4-7
# 用法：python3 art/design/b4/woman.py 輸出資料夾
import math, sys
sys.dont_write_bytecode = True                         # 不要在 art/ 留下 __pycache__
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/design/b4")
from figlib import *

OUT = sys.argv[1]

SKIN = ("#dcb494", "#c49a7c", "#9e7a62")
COAT = ("#847a50", "#6e6440", "#545030")
COAT_B = ("#6e6440", "#5a5234", "#46402a")          # 後面那隻袖子（暗一階）
BLOUSE = ("#dcd0ae", "#c8bc98", "#a89c7c")
PANTS = ("#4a3c32", "#3a2e26", "#2a221c")
PANTS_B = ("#3a2e26", "#2e241e", "#221a16")
SHOE = ("#36302a", "#221e1c", "#161412")
BAG = ("#9a6a40", "#7e5432", "#5e3e24")
STRAP = ("#4a3020", "#4a3020", "#4a3020")
PAL = dict(H="#6a3424", L="#8a4a30", K="#4a2418", S="#dcb494", s="#c49a7c", d="#9e7a62", B="#5a3020",
           E="#e8e0d0", P="#2a1c18", O="#6a2a24", m="#b0645a", R="#d4927c")

# 頭像（面向右）；錨點＝頭的中心（第 5.5 欄、第 5 列）。捲髮：外緣一顆顆凸起、裡面一圈圈的亮面，臉旁也垂著捲髮。
# 作者 2026-10-29：第一版「比較像喪屍」→ 頭擺正在肩膀上方、嘴裡用暗紅（不是黑洞）、嘴唇和臉頰有血色
HEAD_IDLE = ["...H.HH.H...",
             "..HHHHHHHH..",
             ".HHHHHHHHHH.",
             ".HHHHHHHHHHH",      # 捲捲的瀏海
             "HHHHHHHHsBBs",      # 眉
             "HHHHHHHdsEPs",      # 眼白＋瞳孔
             ".HHHHHHdsssS",      # 鼻子
             "HHHHHHHdsRs.",      # 臉頰的血色
             ".HHHHHHHdmm.",      # 嘴唇
             "..HHHHHH.ds.",      # 下巴
             "..H.HH.H.d.."]      # 捲髮垂到肩上
HEAD_SCREAM = HEAD_IDLE[:3] + [".HHHHHHHsBBH",    # 眉毛挑高（額頭露出來）
                               "HHHHHHHHsEEs",    # 眼睛瞪大
                               "HHHHHHHdsEPs",
                               ".HHHHHHdsssS",
                               "HHHHHHHdsmm.",    # 上唇
                               ".HHHHHHHdOO.",    # 張大的嘴（暗紅）
                               "..HHHHHH.Om.",
                               "..H.HH.H.d.."]
HEAD_HALF = HEAD_SCREAM[:8] + [".HHHHHHHdOm.", "..HHHHHH.ds.", "..H.HH.H.d.."]   # 嘴半合（尖叫的第二格、逃跑）


def curls(stamp):
    """頭髮（H）排成一圈一圈的捲：每一捲 3×2 格，左上亮、右下暗，每兩列錯開半捲（亮暗斜著交錯會變棋盤格）"""
    out = []
    for r, row in enumerate(stamp):
        line = ""
        for c, ch in enumerate(row):
            if ch == "H":
                off = 1 if (r // 2) % 2 else 0
                lc, lr = (c + off) % 3, r % 2
                ch = "L" if (lc == 0 and lr == 0) else ("K" if (lc == 2 and lr == 1) else "H")
            line += ch
        out.append(line)
    return out


HEAD_IDLE, HEAD_SCREAM, HEAD_HALF = (curls([r[1:] for r in st]) for st in (HEAD_IDLE, HEAD_SCREAM, HEAD_HALF))   # 後腦削掉一欄（頭髮太寬臉會擠成一條）

_POSE = {}


def local(x, y):
    lx, ly = rot(_POSE["hip"], (x, y), _POSE["lean"])
    return lx, ly + _POSE["bob"]


def parts_of(pp):
    """pp：lean 上身前傾（度，負＝往後仰）、bob、legs ((角度, 膝彎) 後腿, 前腿)、arm (肩角, 肘角, 手形) 前手、arm_b (肩角, 肘角) 後手（提皮包）"""
    lean, bob = pp.get("lean", 0), pp.get("bob", 0)
    hip = (0.0, 0.80)
    _POSE.update(hip=hip, lean=lean, bob=bob)

    def up(p):
        return rot(hip, (p[0], p[1] - bob), -lean)

    parts = []
    # 後手＋皮包（在身體後面）
    sa, ea = pp["arm_b"]
    sh = up((-0.03, 1.16))
    el = down(sh, 0.24, sa)
    ha = down(el, 0.22, ea)
    parts.append(("arm_b", limb(sh, el, 0.09, 0.08), COAT_B))
    parts.append(("arm_b", limb(el, ha, 0.08, 0.07), COAT_B))
    parts.append(("hand_b", ell(ha[0], ha[1] - 0.02, 0.035, 0.04, 10), SKIN))
    bx, by = ha[0], ha[1] - 0.06                        # 皮包掛在手下面
    parts.append(("strap", limb((bx - 0.05, by - 0.02), (bx, by + 0.03), 0.025, 0.025), STRAP))
    parts.append(("strap", limb((bx, by + 0.03), (bx + 0.05, by - 0.02), 0.025, 0.025), STRAP))
    parts.append(("bag", [(bx - 0.11, by - 0.02), (bx + 0.11, by - 0.02), (bx + 0.12, by - 0.17), (bx - 0.12, by - 0.17)], BAG))
    # 腿（後腿暗）
    for name, (ang, bend), ramp in (("leg_b", pp["legs"][0], PANTS_B), ("leg", pp["legs"][1], PANTS)):
        knee = down(hip, 0.38, ang)
        foot = down(knee, 0.37, ang - bend)
        parts.append((name, limb(hip, knee, 0.13, 0.10), ramp))
        parts.append((name, limb(knee, foot, 0.10, 0.08), ramp))
        fx, fy = foot
        parts.append(("shoe", [(fx - 0.05, fy + 0.02), (fx + 0.04, fy + 0.03), (fx + 0.09, fy - 0.01), (fx + 0.09, fy - 0.04), (fx - 0.05, fy - 0.04)], SHOE))
    # 西裝外套（長到大腿）
    torso = [(-0.16, 0.64), (0.14, 0.64), (0.15, 0.80), (0.13, 0.95), (0.15, 1.07), (0.13, 1.17), (0.07, 1.23),
             (-0.10, 1.23), (-0.16, 1.16), (-0.17, 0.98), (-0.17, 0.80)]
    parts.append(("coat", [up(p) for p in torso], COAT))
    parts.append(("blouse", [up(p) for p in [(0.02, 1.23), (0.135, 1.17), (0.135, 0.95), (0.07, 0.97)]], BLOUSE))   # 翻領中間露出的米色襯衫（原插畫很明顯）
    parts.append(("neck", [up(p) for p in limb((0.0, 1.18), (0.02 + pp.get("head", (0, 0))[0], 1.28), 0.07, 0.06)], SKIN))
    # 前手
    sa, ea, hand = pp["arm"]
    sh = up((0.02, 1.15))
    el = down(sh, 0.24, sa)
    ha = down(el, 0.22, ea)
    parts.append(("arm", limb(sh, el, 0.10, 0.085), COAT))
    parts.append(("arm", limb(el, ha, 0.085, 0.075), COAT))
    d = (math.sin(math.radians(ea)), -math.cos(math.radians(ea)))
    if hand == "open":                                  # 手掌張開擋在前面
        tip = (ha[0] + d[0] * 0.10, ha[1] + d[1] * 0.10)
        parts.append(("hand", limb(ha, tip, 0.08, 0.11), SKIN))
        for k in (-1, 0, 1):                            # 張開的手指
            parts.append(("hand", limb(tip, (tip[0] + d[0] * 0.04 + k * d[1] * 0.03, tip[1] + d[1] * 0.04 - k * d[0] * 0.03), 0.02, 0.02), SKIN))
    else:
        parts.append(("hand", ell(ha[0] + d[0] * 0.035, ha[1] + d[1] * 0.035, 0.04, 0.045, 10), SKIN))
    hd = pp.get("head", (0, 0))
    head_c = up((0.0 + hd[0], 1.41 + hd[1]))             # 頭擺正在肩膀上方（往前探會像喪屍）
    return parts, head_c


def detail(name, x, y, px, py, c, nb):
    if name == "coat":
        lx, ly = local(x, y)
        if ly < 0.67:
            c = COAT[2]                                 # 下擺
        if nb(1, 0) == "blouse" or (nb(1, 0) == "coat" and nb(2, 0) == "blouse"):
            c = COAT[0]                                 # 翻領（亮）
        if nb(1, 0) != "coat" and nb(1, 0) != "blouse" and any(abs(ly - b) < 0.016 for b in (0.93, 0.83)):
            c = "#3a3020"                               # 外套的扣子
        if 0.0 < lx < 0.09 and 0.74 < ly < 0.77:
            c = COAT[2]                                 # 口袋蓋
        if -0.13 < lx < -0.04 and abs((ly - 1.0) - (lx + 0.04) * 0.5) < 0.014:
            c = COAT[2]                                 # 背後的皺褶
    if name == "blouse" and abs(x - _POSE.get("bx", 0)) < 1 and h(px, py, 7) < 0.15:
        c = BLOUSE[2]
    if name == "bag":
        if nb(0, -1) != "bag":
            c = BAG[0]                                  # 皮包上緣
        if nb(0, 1) != "bag":
            c = BAG[2]
        if h(px, py, 9) < 0.12:
            c = BAG[2]                                  # 磨損
    if name == "shoe" and nb(0, 1) != "shoe":
        c = "#0e0c0a"
    return c


def frame(pp, stamp):
    parts, head_c = parts_of(pp)
    return render(parts, stamp, head_c, PAL, detail, anchor=(4.5, 5), front_of_head=("arm", "hand"))


IDLE = [dict(bob=b, legs=((-3, 0), (3, 0)), arm=(25, -140, "fist"), arm_b=(-4, 0)) for b in (0, 0.031)]   # 手抓著胸前的衣服
SCREAM = [dict(lean=-8, bob=0, legs=((-10, 0), (5, 0)), arm=(35, 172, "open"), arm_b=(-20, -10)),        # 往後縮、手掌護在臉旁
          dict(lean=-9, bob=0.031, legs=((-10, 0), (5, 0)), arm=(30, 168, "open"), arm_b=(-22, -12))]
RUN = []
for k in range(4):                                     # 第 0、2 格兩腳張開，1、3 格腳經過身體下方；手臂彎著前後擺（不往前伸）
    s_, c_ = math.sin(2 * math.pi * k / 4), math.cos(2 * math.pi * k / 4)
    RUN.append(dict(lean=8, bob=0 if k in (0, 2) else -0.031,
                    legs=((-22 * c_, 45 * max(0, s_)), (22 * c_, 45 * max(0, -s_))),
                    arm=(-24 * c_, -24 * c_ + 55, "fist"), arm_b=(15 * c_, 15 * c_ + 10)))

frames = [frame(p, HEAD_IDLE) for p in IDLE] + [frame(SCREAM[0], HEAD_SCREAM), frame(SCREAM[1], HEAD_HALF)] + \
         [frame(p, HEAD_HALF) for p in RUN]
frames = [mirror(f) for f in frames]                   # 面向左
sheet(frames, OUT, "woman3d")
