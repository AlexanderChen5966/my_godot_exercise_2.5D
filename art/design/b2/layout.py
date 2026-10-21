# B2-1 停車場的配置圖：上＝俯視圖（x 0～36 m、z −9.5～＋5）、下左＝剖面圖（從側面看鏡頭 B 與 3 公尺天花板）、下右＝配色。
# 用法：python3 art/design/b2/layout.py 輸出.png（用 ImageMagick 的 MVG 繪圖指令，中文字用 STHeiti）
import subprocess, sys

OUT = sys.argv[1]
FONT = "/System/Library/Fonts/STHeiti Medium.ttc"
W, H = 1400, 1000
cmds = [f"viewbox 0 0 {W} {H}", "fill '#1d2224'", f"rectangle 0 0 {W} {H}", f"font '{FONT}'"]


def rect(x0, y0, x1, y1, fill, stroke="none"):
    cmds.append(f"fill '{fill}' stroke '{stroke}' stroke-width 1 rectangle {x0:.1f},{y0:.1f} {x1:.1f},{y1:.1f}")


def line(x0, y0, x1, y1, color, width=1):
    cmds.append(f"stroke '{color}' stroke-width {width} fill none line {x0:.1f},{y0:.1f} {x1:.1f},{y1:.1f}")


def text(x, y, s, size=14, color="#e8e8e8"):
    s = s.replace("'", "\\'")
    cmds.append(f"stroke none fill '{color}' font-size {size} text {x:.1f},{y:.1f} '{s}'")


# ---------- 俯視圖 ----------
PX, OX, OY = 34.0, 60.0, 70.0          # 1 公尺 34 px；x=0 在 OX；z=+5 在 OY（往下是 z 變小＝往後）
def P(x, z):
    return OX + x * PX, OY + (5.0 - z) * PX

text(20, 34, "俯視圖（上＝鏡頭這一側，下＝後牆；單位公尺）", 20)
x0, y0 = P(-1, 5); x1, y1 = P(37, -9.5)
rect(x0, y0, x1, y1, "#3c4648")                       # 地面
a, b = P(-1, 1.5); c, d = P(37, -1.5)
rect(a, b, c, d, "#4d5a5c")                           # 走道（縱深帶）
text(c - 150, b + 20, "走道 z −1.5～＋1.5", 13)
for x in range(0, 37, 3):                             # 停車格線（每格 2.5 m 左右，簡化成 3 m）
    p, q = P(x, -2.6); r, s = P(x, -7.4)
    line(p, q, r, s, "#c9c39a", 1)
text(P(0.3, -2.9)[0], P(0.3, -2.9)[1] + 14, "停車格 z −2.5～−7.5", 13)
for z, xs, label in ((-2.2, (3, 10, 17, 24, 31), "第一排柱子 z −2.2"), (-8.0, (3, 10, 17, 24, 31), "第二排柱子 z −8"),
                     (3.5, (6.6, 19.5, 32.5), "前景柱子 z ＋3.5（景深糊掉）")):
    for x in xs:
        p, q = P(x - 0.3, z + 0.3); r, s = P(x + 0.3, z - 0.3)
        rect(p, q, r, s, "#8a9a9e", "#c0d0d4")
    lx = P(xs[-1] + 0.8, z)[0] if z != -2.2 else P(-0.9, z)[0]
    ly = P(0, z)[1] + (5 if z != -2.2 else 22)
    text(lx, ly, label, 12, "#b8c8cc")
a, b = P(-1, -9.0); c, d = P(37, -9.3)
rect(a, b, c, d, "#7a8a8e")
text(P(14, -9.4)[0], d + 18, "後牆 z −9（上方「B2」字樣、腰帶條紋）", 13)
# 車子
for (x, z, w, d_, lab, col) in ((13.5, -4.8, 4.2, 1.8, "翻倒的車（照原圖）", "#2e3b3e"),
                                (5.5, -5.2, 1.8, 4.2, "廢車", "#384446"), (22.0, -5.2, 1.8, 4.2, "廢車", "#384446")):
    p, q = P(x - w / 2, z + d_ / 2); r, s = P(x + w / 2, z - d_ / 2)
    rect(p, q, r, s, col, "#9fb1b6")
    text(p, s + 14, lab, 12)
# 樓梯間
p, q = P(32.0, -2.1); r, s = P(35.2, -5.1)
rect(p, q, r, s, "#55666a", "#c0d0d4")
text(p - 10, s + 14, "出口樓梯間＋門（紅色警示燈）", 12)
# 互動點
for x, lab in ((4.69, "醒來的地方"), (9.38, "燈下"), (15.63, "地面殘骸"), (23.44, "婦人"), (33.59, "出口")):
    z = -1.85 if lab != "婦人" else 0.0
    p, q = P(x, z)
    cmds.append(f"fill '#e0b040' stroke none circle {p:.1f},{q:.1f} {p + 5:.1f},{q:.1f}")
    text(p + 7, q - 6, lab, 12, "#f0d080")
# 燈具
for x, on in ((2.5, False), (9.38, True), (17.0, False), (24.0, False), (30.0, False)):
    p, q = P(x - 0.8, -1.0); r, s = P(x + 0.8, -1.2)
    rect(p, q, r, s, "#d8f0ff" if on else "#55606a")
text(P(10.4, -1.0)[0], P(0, -1.0)[1] + 4, "← 燈管（只有這盞亮、會閃）", 12, "#d8f0ff")
# 鏡頭 B 的視野（主角在 x 9.4 時）
half = 3.93
p, q = P(9.38 - half, 0); r, s = P(9.38 + half, 0)
line(p, q + 2, r, s + 2, "#ff8060", 2)
text(p, q - 8, "鏡頭 B：主角的深度看得到約 7.9 m 寬", 12, "#ff9a80")
for x in range(0, 37, 6):
    p, q = P(x, -9.5)
    text(p - 6, q + 34, f"{x}", 12, "#888")

# ---------- 剖面圖 ----------
SX, SOX, SOY = 26.0, 60.0, 900.0      # 1 公尺 26 px；z=+8 在左、z=−10 在右；y=0 在 SOY
def S(z, y):
    return SOX + (8.0 - z) * SX, SOY - y * SX

text(20, 620, "剖面圖（側面看：左＝鏡頭，右＝後牆）", 20)
p, q = S(8, 0); r, s = S(-10, -0.2)
rect(p, q, r, s, "#3c4648")                           # 地面
p, q = S(-9.0, 3.3); r, s = S(-9.3, 0)
rect(p, q, r, s, "#7a8a8e")                           # 後牆
p, q = S(8, 3.3); r, s = S(-9.3, 3.0)
rect(p, q, r, s, "#55606a")                           # 天花板 3 m
for z in (3.5, -2.2, -8.0):
    p, q = S(z + 0.25, 3.0); r, s = S(z - 0.25, 2.5)
    rect(p, q, r, s, "#6a7a7e")                       # 大樑
for z in (3.5, -2.2, -8.0):
    p, q = S(z + 0.3, 2.5); r, s = S(z - 0.3, 0)
    rect(p, q, r, s, "#8a9a9e")                       # 柱子
p, q = S(-0.9, 2.65); r, s = S(-1.1, 2.55)
rect(p, q, r, s, "#d8f0ff")                           # 燈管
a, b = S(1.5, 0); c, d = S(-1.5, 0)
line(a, b - 3, c, d - 3, "#e0b040", 4)
text(a, b + 18, "走道 3 m", 12, "#f0d080")
p, q = S(0.1, 1.5); r, s = S(-0.1, 0)
rect(p, q, r, s, "#c8b890")                           # 主角 1.5 m
text(r + 4, q + 10, "主角 1.5 m", 12)
cz, cy = 7.17, 2.23                                   # 鏡頭 B 的位置
p, q = S(cz, cy)
cmds.append(f"fill '#ff8060' stroke none circle {p:.1f},{q:.1f} {p + 6:.1f},{q:.1f}")
text(p - 40, q - 12, "鏡頭 B（高 2.2 m、距離 7.2 m、俯 5°）", 12, "#ff9a80")
import math
for ang in (-5 + 20, -5 - 20):                        # 上下視角 ±20°
    dz = -10.0 - cz
    dy = math.tan(math.radians(ang)) * abs(dz)
    r, s = S(-10.0, cy + dy)
    line(p, q, r, s, "#ff806080", 1)
text(S(5, 3.0)[0], S(5, 3.0)[1] - 8, "天花板 3 m（大樑下 2.5 m）", 12)
text(S(-6, 0)[0], S(-6, 0)[1] + 18, "停車格", 12)

# ---------- 配色 ----------
text(820, 620, "配色（貼圖的固有色；暗的感覺交給燈光）", 18)
pal = [("#4a5658", "水泥地"), ("#3c4648", "地面暗部、污漬"), ("#5c6c70", "牆、天花板"), ("#6e7f83", "柱子"),
       ("#c9c39a", "地面標線（舊黃白）"), ("#b8a23c", "警示條紋黃"), ("#1c2224", "警示條紋黑"), ("#2e3b3e", "車漆（深青）"),
       ("#9fb1b6", "燈管冷光"), ("#ba4f42", "紅色警示燈"), ("#550e0e", "血跡、鏽紅"), ("#25474d", "原圖的青綠（陰影色）")]
for i, (c, n) in enumerate(pal):
    x = 820 + (i % 2) * 280
    y = 650 + (i // 2) * 52
    rect(x, y, x + 60, y + 40, c, "#888")
    text(x + 70, y + 26, f"{n}  {c}", 13)

mvg = OUT + ".mvg"
open(mvg, "w", encoding="utf-8").write("\n".join(cmds) + "\n")
subprocess.run(["magick", "-size", f"{W}x{H}", "xc:#1d2224", "-draw", f"@{mvg}", OUT], check=True)
