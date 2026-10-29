# B4-5 女兒（舊家的窗外）：照原插畫 scene_19（橘紅色及肩頭髮、齊瀏海、橘色 T 恤）；劇本說「她長高了」，畫成十歲左右。
# 作者 2026-10-29：畫成全身、靠窗台擋住下半部（A＋ 的 daughter_anim.png 只有 24×22 的上半身）。
# 她站在街上看著窗內（鏡頭這一側），所以畫正面；離開時轉成背面。活人不要畫成喪屍的樣子（B4-3a）。
# 密度 A，每格 32×51，身體用形狀算、頭手畫（figlib.py）。
# 輸出 daughter3d.png（5 格）：idle 0、blink 1（眨眼）、wave 2-3（比出同樣的手勢：手按胸口 → 舉起手掌；指向地面那下被窗台擋住）、leave 4（背面）
# 用法：python3 art/design/b4/daughter.py 輸出資料夾
import sys
sys.dont_write_bytecode = True                         # 不要在 art/ 留下 __pycache__
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/design/b4")
from figlib import *

OUT = sys.argv[1]

SKIN = ("#f0c8a8", "#dcae90", "#b88c74")
SHIRT = ("#e08a48", "#c87438", "#a05a2a")           # 橘色 T 恤（舊了、有點髒）
JEANS = ("#4e5c7a", "#3e4a64", "#2e384e")
SHOE = ("#c4c0b4", "#a4a094", "#7a766c")
PAL = dict(H="#c0602c", L="#e0843c", K="#8a4020", S="#f0c8a8", s="#dcae90", d="#b88c74", E="#ece6dc", P="#2a1c18",
           R="#e8a088", m="#c07868")

# 頭像（正面）；錨點＝頭的中心（第 4.5 欄、第 5 列）。齊瀏海、及肩直髮，兩邊垂到肩膀
HEAD_FRONT = ["..HHHHHH..",
              ".HHLLHHHH.",
              "HHHHHHLHHH",
              "HHHHHHHHHH",       # 齊瀏海
              "HHsSSSSsHH",
              "HsEPSSEPsH",       # 眼白＋瞳孔（看著窗內）
              "HsRsSSsRsH",       # 臉頰的血色
              "HHssmmssHH",       # 嘴
              "HH.dssd.HH",       # 下巴，兩邊的頭髮
              "HK......KH",
              ".H......H."]
HEAD_BLINK = HEAD_FRONT[:5] + ["HsddSSddsH"] + HEAD_FRONT[6:]
HEAD_BACK = ["..HHHHHH..",
             ".HHLLHHHH.",
             "HHHHHHLHHH",
             "HHHLHHHHHH",
             "HHHHHHHLHH",
             "HHLHHHHHHH",
             "HHHHHLHHHH",
             "HKHHHHHHKH",
             "HHHHHHHHHH",
             "HK.dssd.KH",
             ".H......H."]


def parts_of(pose, back=False):
    """pose：idle／chest（手按胸口）／palm（舉起手掌）；back＝背面（離開）"""
    parts = []
    for side in (-1, 1):                               # 腿＋鞋
        x = side * 0.055
        parts.append(("leg", limb((x, 0.62), (x, 0.07), 0.10, 0.08), JEANS))
        parts.append(("shoe", [(x - 0.06, 0.0), (x + 0.06, 0.0), (x + 0.06, 0.07), (x - 0.06, 0.07)], SHOE))
    parts.append(("shirt", [(-0.12, 0.56), (0.12, 0.56), (0.12, 0.80), (0.135, 0.94), (0.09, 1.00), (-0.09, 1.00), (-0.135, 0.94), (-0.12, 0.80)], SHIRT))   # 小孩：窄一點（太寬像大人）
    parts.append(("neck", limb((0, 0.97), (0, 1.03), 0.08, 0.07), SKIN))
    for side in (-1, 1):                               # 手臂：短袖＋手
        sh = (side * 0.13, 0.94)
        right_hand = side == (1 if back else -1)       # 她的右手（正面在畫面左邊）
        if right_hand and pose == "chest":
            el, ha = (side * 0.16, 0.76), (side * -0.01, 0.86)
        elif right_hand and pose == "palm":
            el, ha = (side * 0.21, 0.82), (side * 0.20, 1.05)
        else:
            el, ha = (side * 0.155, 0.76), (side * 0.16, 0.58)
        parts.append(("sleeve", limb(sh, (sh[0] + (el[0] - sh[0]) * 0.45, sh[1] + (el[1] - sh[1]) * 0.45), 0.10, 0.09), SHIRT))
        parts.append(("arm", limb((sh[0] + (el[0] - sh[0]) * 0.4, sh[1] + (el[1] - sh[1]) * 0.4), el, 0.065, 0.06), SKIN))
        parts.append(("arm", limb(el, ha, 0.06, 0.055), SKIN))
        if right_hand and pose == "palm":              # 張開的手掌朝前
            parts.append(("hand", ell(ha[0], ha[1] + 0.03, 0.045, 0.06, 12), SKIN))
        else:
            parts.append(("hand", ell(ha[0], ha[1] - 0.02, 0.035, 0.04, 10), SKIN))
    return parts, (0.0, 1.14)


def detail(name, x, y, px, py, c, nb):
    if name == "shirt":
        if abs(y - 0.58) < 0.016:
            c = SHIRT[2]                                # 下擺
        if h(px, py, 41) < 0.015:
            c = SHIRT[2]                                # 舊了、有點髒
    if name == "leg" and abs(y - 0.33) < 0.016:
        c = JEANS[0]                                    # 膝蓋
    if name == "shoe" and nb(0, 1) != "shoe":
        c = "#4a4640"                                   # 鞋底
    return c


def frame(pose, stamp, back=False):
    parts, head_c = parts_of(pose, back)
    front = () if back else ("arm", "hand")
    return render(parts, stamp, head_c, PAL, detail, anchor=(4.5, 5), front_of_head=front)


frames = [frame("idle", HEAD_FRONT), frame("idle", HEAD_BLINK), frame("chest", HEAD_FRONT), frame("palm", HEAD_FRONT),
          frame("idle", HEAD_BACK, back=True)]
sheet(frames, OUT, "daughter3d")
