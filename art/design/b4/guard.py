# B4-4 警衛（設施走廊）：照原插畫 scene_06 的搜捕隊（頭盔、護目鏡、面罩、戰術背心、蹲低持槍瞄準）
# 與 A＋ 的像素圖（guard_anim.png：低姿搜索 4 格〔槍口慢慢掃〕、舉槍瞄準 1 格；深藍制服＋橄欖色背心，槍上有手電筒）。
# 密度 A，每格 32×51；身體用形狀算、頭手畫（figlib.py）。圖面向左（先畫面向右再鏡射）。
# 輸出 guard3d.png（5 格）：搜索 0-3、瞄準 4；並印出每格手電筒燈頭的（x, y, 槍口往下的角度）
#   → Lab3D 的 Guard/Torch（gun_torch_3d.gd）的 idle_frames、event_frame（像素、圖的左上角為 0,0、人物面向左）
# 用法：python3 art/design/b4/guard.py 輸出資料夾
import math, sys
sys.dont_write_bytecode = True                         # 不要在 art/ 留下 __pycache__
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/design/b4")
from figlib import *

OUT = sys.argv[1]

UNI = ("#465060", "#343c4a", "#262c38")              # 深藍制服
UNI_B = ("#343c4a", "#283040", "#1e2430")
VEST = ("#626448", "#4c4e38", "#3a3c2a")             # 橄欖色戰術背心
GLOVE = ("#2a2a2a", "#202020", "#181818")
BOOT = ("#2a2826", "#1c1a18", "#121110")
GUN = ("#4a4e54", "#2e3034", "#1e2024")
TORCH = ("#e8dc9a", "#e8dc9a", "#e8dc9a")
PAL = dict(H="#3e4656", L="#5e687a", K="#2a303c", G="#14181c", g="#8aa4b4", M="#2e3238", m="#4a4e54", F="#5a6068")

# 頭像（面向右）；錨點＝頭的中心（第 4.5 欄、第 5 列）。頭盔、護目鏡、面罩（看不到臉）
HEAD = ["..HHHHH...",
        ".HLLHHHH..",
        "HHHHHHHHH.",
        "HHHHHHHHHH",          # 頭盔前緣
        "KmmFFFFFFF",          # 護目鏡的框（作者 2026-10-29：護目鏡再大一點）
        "KmFGGGGGGF",          # 鏡片 3 列高、往前凸出
        "KmFGggGGGF",          # 鏡片的反光
        "KmFGGgGGGF",
        "KMMFFFFFFM",          # 面罩（比頭盔亮一點，分得開）
        ".MMMMMMMM.",
        "..MMMMM..."]   # 第 4 列起多了一列，錨點改第 5 列

_POSE = {}
TORCH_AT = []


def local(x, y):
    lx, ly = rot(_POSE["hip"], (x, y), _POSE["lean"])
    return lx, ly + _POSE["bob"]


def parts_of(pp):
    """pp：lean、bob、crouch（髖往下幾公尺）、legs、aim（槍口往下的角度）、gun_y（槍托在胸前的高度）"""
    lean, bob, crouch = pp.get("lean", 0), pp.get("bob", 0), pp.get("crouch", 0)
    hip = (0.0, 0.80 - crouch)
    _POSE.update(hip=hip, lean=lean, bob=bob)

    def up(p):
        return rot(hip, (p[0], p[1] - crouch - bob), -lean)

    parts = []
    # 腿：蹲低時膝蓋往前彎
    for name, (ang, bend), ramp in (("leg_b", pp["legs"][0], UNI_B), ("leg", pp["legs"][1], UNI)):
        knee = down(hip, 0.38, ang)
        foot = down(knee, 0.37, ang - bend)
        parts.append((name, limb(hip, knee, 0.15, 0.12), ramp))
        parts.append((name, limb(knee, foot, 0.12, 0.10), ramp))
        fx, fy = foot
        parts.append(("boot", [(fx - 0.06, fy + 0.05), (fx + 0.05, fy + 0.05), (fx + 0.11, fy - 0.01), (fx + 0.11, fy - 0.04), (fx - 0.06, fy - 0.04)], BOOT))
    sh_b = up((-0.04, 1.16))                           # 後手（握槍把）先畫，在身體後面
    torso = [(-0.17, 0.74), (0.13, 0.74), (0.15, 0.95), (0.16, 1.10), (0.12, 1.21), (-0.10, 1.23), (-0.18, 1.15), (-0.19, 0.95)]
    parts.append(("torso", [up(p) for p in torso], UNI))
    parts.append(("vest", [up(p) for p in [(-0.15, 0.82), (0.14, 0.82), (0.16, 0.98), (0.16, 1.12), (0.10, 1.18), (-0.12, 1.18), (-0.16, 1.10)]], VEST))
    parts.append(("belt", [up(p) for p in [(-0.17, 0.76), (0.14, 0.76), (0.14, 0.81), (-0.17, 0.81)]], GLOVE))
    # 槍：槍托抵在肩上，槍口往前（往下 aim 度）；手電筒在槍口下
    aim = pp["aim"]
    stock = up((-0.02, pp.get("gun_y", 1.06)))
    a = math.radians(aim - lean)                       # 槍跟著上身轉
    dirv = (math.cos(a), -math.sin(a))
    muzzle = (stock[0] + dirv[0] * 0.44, stock[1] + dirv[1] * 0.44)   # 短的卡賓槍（長了槍口會超出畫格）
    # 兩隻手：後手握槍把（扳機），前手托護木
    grip = (stock[0] + dirv[0] * 0.14 + dirv[1] * 0.03, stock[1] + dirv[1] * 0.14 - dirv[0] * 0.03)
    fore = (stock[0] + dirv[0] * 0.30 + dirv[1] * 0.03, stock[1] + dirv[1] * 0.30 - dirv[0] * 0.03)
    el_b = (sh_b[0] + 0.02, sh_b[1] - 0.18)
    parts.insert(0, ("arm_b", limb(sh_b, el_b, 0.10, 0.09), UNI_B))
    parts.insert(1, ("arm_b", limb(el_b, grip, 0.09, 0.08), UNI_B))
    sh = up((0.04, 1.14))
    el = ((sh[0] + fore[0]) / 2 - 0.02, min(sh[1], fore[1]) - 0.12)
    parts.append(("arm", limb(sh, el, 0.11, 0.10), UNI))
    parts.append(("arm", limb(el, fore, 0.10, 0.09), UNI))
    parts.append(("gun", limb((stock[0] - dirv[0] * 0.08, stock[1] - dirv[1] * 0.08), muzzle, 0.07, 0.04), GUN))
    mag = (stock[0] + dirv[0] * 0.18, stock[1] + dirv[1] * 0.18)
    parts.append(("gun", limb(mag, (mag[0] + dirv[1] * 0.10 + dirv[0] * 0.03, mag[1] - dirv[0] * 0.10 + dirv[1] * 0.03), 0.04, 0.035), GUN))   # 彈匣
    tl = (stock[0] + dirv[0] * 0.38 + dirv[1] * 0.035, stock[1] + dirv[1] * 0.38 - dirv[0] * 0.035)
    parts.append(("torch", limb(tl, (tl[0] + dirv[0] * 0.06, tl[1] + dirv[1] * 0.06), 0.035, 0.035), GUN))
    TORCH_AT.append(((tl[0] + dirv[0] * 0.07), (tl[1] + dirv[1] * 0.07), aim - lean))
    parts.append(("glove", ell(fore[0], fore[1], 0.04, 0.035, 10), GLOVE))
    parts.append(("glove", ell(grip[0], grip[1], 0.035, 0.035, 10), GLOVE))
    head_c = up((0.02, 1.38))
    return parts, head_c


def detail(name, x, y, px, py, c, nb):
    if name == "vest":
        lx, ly = local(x, y)
        if any(abs(lx - p) < 0.016 for p in (0.02, 0.08)) and 0.86 < ly < 1.0:
            c = VEST[2]                                 # 彈匣袋的縫線
        if abs(ly - 1.0) < 0.016:
            c = VEST[2]                                 # 彈匣袋上緣
    if name == "torch" and nb(1, 0) != "torch":
        c = TORCH[0]                                    # 手電筒的燈頭（亮）
    if name == "gun" and nb(0, -1) != "gun":
        c = GUN[0]
    if name == "boot" and nb(0, 1) != "boot":
        c = "#0c0b0a"
    return c


def frame(pp):
    parts, head_c = parts_of(pp)
    return render(parts, HEAD, head_c, PAL, detail, anchor=(4.5, 5), front_of_head=("gun", "arm", "glove", "torch"))


# 低姿搜索：蹲低、上身前傾，槍口往下慢慢掃（角度變化）；瞄準：站高一點、槍口水平
SEARCH = [dict(crouch=0.15, lean=12, legs=((-25, 5), (40, 50)), aim=a, bob=b) for a, b in ((28, 0), (24, 0), (20, 0.031), (24, 0.031))]
AIM = [dict(crouch=0.08, lean=4, legs=((-20, 0), (30, 40)), aim=4, gun_y=1.12)]   # aim＝lean：槍口剛好水平（測試檢查手電筒水平照過來）

frames = [frame(p) for p in SEARCH + AIM]
frames = [mirror(f) for f in frames]                   # 面向左
sheet(frames, OUT, "guard3d")
ox = FW / 2
print("手電筒（像素 x, y, 角度；面向左）：")
for i, (tx, ty, ang) in enumerate(TORCH_AT):
    px = FW - (tx * PPM + ox)                          # 鏡射後的 x
    py = FH - ty * PPM
    print(f"  第 {i} 格  {px:.1f}, {py:.1f}, {ang:.0f}")
