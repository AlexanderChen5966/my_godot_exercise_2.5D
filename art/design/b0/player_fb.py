# B0-3 主角的正面（往畫面外走）、背面（往畫面裡走）走路圖（照原圖：正面 scene_18 的倒影、背面 scene_20 的背影；
# 顏色、身高、比例照現有側面的 player.png）。32x48，各 6 格，第 0、3 格是腳著地（和側面一樣，腳步聲用同一組畫格）。
# 用法：python3 player_fb.py 輸出資料夾 → front_f0..5.txt、back_f0..5.txt、預覽圖
import sys, subprocess
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/tools")
from pix import Grid, OUT

OUTDIR = sys.argv[1]
# 側面 player.png 用到的顏色
JK_D, JK, JK_L = "#33342A", "#4A4A3A", "#5D5C48"   # 外套暗、中、亮
SHIRT = "#8A8676"
PANTS_D, PANTS_L = "#23252A", "#2F3238"
SHOE = "#1F1C1A"
HAIR = "#2B2622"
SKIN, SKIN_D, SKIN_L = "#7D8F86", "#5C6B65", "#9AABA2"
DARK = "#3A2A2A"           # 眉毛、嘴
BLOOD_D, BLOOD = "#4A1614", "#6E1F1C"
EYE = "#D8DCCC"

# 每一格：(上半身往下沉, 左腳位移, 右腳位移)；腳位移正數＝往前（畫面上低 1 格），負數＝抬起
# 0 左腳著地 → 1 右腳抬起往前 → 2 右腳經過 → 3 右腳著地 → 4 左腳抬起 → 5 左腳經過
STEPS = [(1, 1, -2), (0, 0, -3), (0, 0, -1), (1, -2, 1), (0, -3, 0), (0, -1, 0)]
# 待機 4 格（4 fps）：和側面待機一樣，腳不動、上半身往下沉 0 → 1 → 2 → 1 格（喘氣）
IDLE = [(0, 0, 0), (1, 0, 0), (2, 0, 0), (1, 0, 0)]


def legs(g, dl, dr, back):
    # 左腳 x11～14、右腳 x17～20（畫面上的左右）；腳越往前越長
    for (x0, dy, inner) in ((11, dl, 14), (17, dr, 17)):
        bottom = 43 + dy
        g.rect(x0, 31, x0 + 3, bottom, PANTS_D)
        g.vline(inner if x0 == 11 else x0 + 1, 31, bottom, PANTS_L)   # 褲管內側的亮面
        g.rect(x0 - 1 if x0 == 11 else x0, bottom + 1, x0 + 3 if x0 == 11 else x0 + 4, bottom + 3, SHOE)
        if back:
            g.hline(x0 if x0 == 11 else x0 + 1, x0 + 2 if x0 == 11 else x0 + 3, bottom + 1, "#2A2622")  # 鞋跟
    g.vline(15, 31, 47, None)
    g.vline(16, 31, 47, None)


def body(g, bob, back):
    y = bob
    # 駝背：肩膀窄、往外下垂，脖子被低下的頭擋住；外套 x9～22
    g.rect(11, 15 + y, 20, 16 + y, JK)
    g.rect(10, 16 + y, 21, 17 + y, JK)
    g.rect(9, 18 + y, 22, 29 + y, JK)
    g.rect(9, 18 + y, 10, 28 + y, JK_D)      # 外側暗面
    g.rect(21, 18 + y, 22, 28 + y, JK_D)
    g.rect(10, 28 + y, 21, 30 + y, JK_D)     # 下襬
    if back:
        g.rect(11, 16 + y, 14, 21 + y, JK_L)     # 左肩受光
        g.vline(15, 18 + y, 29 + y, JK_D)        # 背後的縫線
        g.hline(12, 19, 15 + y, JK_L)            # 衣領
    else:
        g.rect(14, 16 + y, 17, 27 + y, SHIRT)    # 敞開的外套裡的襯衫
        g.vline(13, 16 + y, 27 + y, JK_L)        # 領口受光
        g.vline(18, 17 + y, 27 + y, JK_D)
        g.rect(11, 19 + y, 12, 26 + y, JK_L)     # 左胸受光
        g.put(16, 18 + y, BLOOD_D); g.put(16, 19 + y, BLOOD)     # 從嘴角滴下來的血
        g.put(15, 24 + y, BLOOD_D)
    # 手臂垂在兩側，稍微往前（手在下襬旁邊）
    for x0 in (7, 23):
        g.rect(x0, 18 + y, x0 + 1, 27 + y, JK)
        g.vline(x0 if x0 == 7 else x0 + 1, 18 + y, 27 + y, JK_D)
        g.put(x0 + (1 if x0 == 7 else 0), 17 + y, JK)            # 下垂的肩膀接到手臂
        g.rect(x0, 28 + y, x0 + 1, 30 + y, SKIN_D if back else SKIN)
        g.put(x0 + (1 if x0 == 7 else 0), 30 + y, SKIN_D)
    blood_x = 7 if back else 23          # 血在右手（正面時在畫面右邊，背面時在畫面左邊）
    g.put(blood_x, 29 + y, BLOOD); g.put(blood_x + 1, 30 + y, BLOOD_D)


def head(g, bob, back):
    y = bob
    # 低著頭（比側面的臉低 2 格，壓在肩膀上）：臉 9～15，亂髮蓋住額頭
    g.rect(12, 8 + y, 19, 14 + y, SKIN)
    g.rect(13, 15 + y, 18, 15 + y, SKIN_D)
    g.rect(12, 5 + y, 19, 9 + y, HAIR)
    g.rect(13, 4 + y, 18, 4 + y, HAIR)
    for x, dy in ((11, 5), (11, 6), (20, 5), (20, 7), (11, 8), (14, 3), (17, 2), (18, 3), (12, 4), (20, 4), (10, 6)):
        g.put(x, dy + y, HAIR)               # 亂翹的頭髮
    if back:
        g.rect(12, 5 + y, 19, 13 + y, HAIR)     # 背面整個是頭髮
        g.rect(11, 7 + y, 20, 11 + y, HAIR)
        g.hline(13, 18, 14 + y, HAIR)
        g.put(12, 13 + y, SKIN_D); g.put(19, 13 + y, SKIN_D)   # 耳朵
        g.hline(14, 17, 15 + y, SKIN_D)                        # 低頭露出的後頸
        g.put(14, 6 + y, "#3A3430"); g.put(17, 5 + y, "#3A3430"); g.put(13, 9 + y, "#3A3430")  # 頭髮的光澤
    else:
        g.put(13, 10 + y, HAIR); g.put(18, 10 + y, HAIR)        # 瀏海垂下
        g.put(15, 9 + y, SKIN_L); g.put(16, 9 + y, SKIN_L)       # 額頭受光（側面的 n）
        g.hline(13, 14, 10 + y, DARK); g.hline(17, 18, 10 + y, DARK)   # 眉頭壓低
        g.put(14, 11 + y, EYE); g.put(17, 11 + y, EYE)           # 混濁的眼睛
        g.put(13, 11 + y, DARK); g.put(18, 11 + y, DARK)
        g.rect(18, 11 + y, 19, 14 + y, SKIN_D)                   # 右半邊臉的陰影
        g.put(17, 11 + y, EYE)
        g.vline(15, 12 + y, 13 + y, SKIN_D)                      # 鼻子
        g.hline(14, 17, 14 + y, DARK)                            # 嘴
        g.put(16, 15 + y, BLOOD)                                 # 嘴角的血（側面也有）
        g.put(13, 12 + y, BLOOD_D)                               # 臉上的傷（scene_18）


def frame(step, back):
    g = Grid(32, 48)
    bob, dl, dr = step
    legs(g, dl, dr, back)
    body(g, bob, back)
    head(g, bob, back)
    # 手臂和身體之間留一條外框，看得出是兩個東西
    for x in (9, 22):
        g.vline(x, 18 + bob, 29 + bob, OUT)
    return g


names = {}
for kind in ("front", "back"):
    for anim, steps in (("walk", STEPS), ("idle", IDLE)):
        key = f"{anim}_{kind}"
        names[key] = []
        for i, step in enumerate(steps):
            p = f"{OUTDIR}/{key}_f{i}.txt"
            frame(step, kind == "back").save_txt(p)
            subprocess.run(["magick", p, f"PNG32:{OUTDIR}/{key}_f{i}.png"], check=True)
            names[key].append(f"{OUTDIR}/{key}_f{i}.png")
# 預覽：每排最左是側面（參考），接著待機 4 格、空一格、走路 6 格（放大 8 倍）；GIF 各一個
side = f"{OUTDIR}/side.png"
blank = f"{OUTDIR}/blank.png"
subprocess.run(["magick", "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/assets/sprites/player.png",
                "-crop", "32x48+0+0", "+repage", side], check=True)
subprocess.run(["magick", "-size", "16x48", "xc:none", blank], check=True)
rows = []
for kind in ("front", "back"):
    row = f"{OUTDIR}/row_{kind}.png"
    subprocess.run(["magick", side, blank, *names[f"idle_{kind}"], blank, *names[f"walk_{kind}"], "+append", "+repage", row], check=True)
    rows.append(row)
subprocess.run(["magick", *rows, "-append", "+repage", "-background", "#556", "-flatten", "-scale", "800%", f"{OUTDIR}/preview.png"], check=True)
subprocess.run(["magick", *rows, "-append", "+repage", "-background", "#5a5f6a", "-flatten", "-scale", "200%", f"{OUTDIR}/game_scale.png"], check=True)
for key, files in names.items():
    delay = "25" if key.startswith("idle") else "12"
    subprocess.run(["magick", "-delay", delay, "-dispose", "background", *files, "-background", "#556",
                    "-scale", "600%", "-loop", "0", f"{OUTDIR}/{key}_preview.gif"], check=True)
