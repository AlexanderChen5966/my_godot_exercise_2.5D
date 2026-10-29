# B2-3 停車場的像素貼圖（32 像素＝1 公尺，和人物的像素密度相同）。
# 用法：python3 art/design/b2/textures.py 輸出資料夾 → 每張貼圖的 .txt（ImageMagick 格式）與 .png、預覽 preview.png
# 會重複鋪的（tile）上下左右可以無縫接起來；只用一次的（fit）照物件的大小畫。顏色照 B2-1 的配色。
import sys, subprocess, math
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/tools")
from pix import Grid

OUTDIR = sys.argv[1]


def h(x, y, s=0):
    """固定的亂數（0～1），不用 sin（A5 學到的：規則紋路）"""
    n = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def shade(c, k):
    """顏色乘上亮度 k"""
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * k))) for v in (r, g, b))


def noise_fill(g, base, amount=0.06, seed=0, steps=(0.9, 1.0, 1.0, 1.08)):
    """底色＋細碎的明暗顆粒（每一格隨機挑一個亮度）"""
    for y in range(g.h):
        for x in range(g.w):
            k = steps[int(h(x, y, seed) * len(steps))]
            g.put(x, y, shade(base, k + (h(x, y, seed + 9) - 0.5) * amount))


def blob(g, cx, cy, r, color, seed, wrap=True, density=0.75):
    """不規則的一團（污漬、鏽斑），tile 時會從另一邊接回來"""
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = math.hypot(dx, dy) / (r + 0.5)
            if d <= 1 and h(cx + dx, cy + dy, seed) < density * (1.15 - d):
                x, y = cx + dx, cy + dy
                if wrap:
                    x, y = x % g.w, y % g.h
                g.put(x, y, color)


def crack(g, x, y, n, seed, color):
    """一條彎曲的裂縫"""
    for i in range(n):
        g.put(x % g.w, y % g.h, color)
        r = h(i, seed, 3)
        x += 1 if r < 0.55 else (0 if r < 0.8 else -1)
        y += 1 if h(i, seed, 5) < 0.7 else 0


SHEETS = {}


def sheet(name, w, h_, kind):
    g = Grid(w, h_)
    SHEETS[name] = (g, kind)
    return g


# ---- 地面：水泥（2 m 一格），油漬、裂縫、細碎顆粒 ----
g = sheet("floor", 64, 64, "tile 2m")
noise_fill(g, "#4a5658", 0.07, 1)
for cx, cy, r in ((14, 20, 6), (46, 50, 8), (52, 10, 4)):
    blob(g, cx, cy, r, "#3c4648", cx * 7 + cy)
blob(g, 30, 40, 3, "#343c3e", 99)
crack(g, 6, 34, 26, 4, "#2c3436")
crack(g, 40, 2, 18, 8, "#2c3436")
for i in range(18):                               # 小石子、灰塵的亮點
    g.put(int(h(i, 1, 21) * 64), int(h(i, 2, 21) * 64), "#5e6a6c")

# ---- 牆（天花板也用，顏色在材質裡調暗）：模板水泥，每 1 m 一條接縫、螺栓孔、往下流的水漬 ----
g = sheet("wall", 64, 64, "tile 2m")
noise_fill(g, "#5c6c70", 0.05, 2)
for y in (0, 32):
    g.hline(0, 63, y, "#4c5a5e")
for x in (0, 32):
    g.vline(x, 0, 63, "#53626a")
for x, y in ((8, 8), (24, 8), (40, 8), (56, 8), (8, 40), (24, 40), (40, 40), (56, 40)):
    g.put(x, y, "#3a4548"); g.put(x + 1, y, "#45525a")
for x0, seed in ((12, 1), (45, 2), (58, 3)):      # 水漬：從接縫往下流，越下面越淡
    for y in range(1, 30):
        if h(x0, y, seed) < 0.8 - y / 40:
            g.put(x0 + (1 if h(y, seed, 4) < 0.2 else 0), y, "#506064")
            g.put(x0, y + 32, "#53636a" if h(x0, y, seed + 1) < 0.5 else g.get(x0, y + 32))

# ---- 柱身：一面 0.6 m × 2.25 m（20×72），上方有「B2」模板字，下方磨損 ----
g = sheet("pillar", 20, 72, "fit")
noise_fill(g, "#6e7f83", 0.05, 3)
g.vline(0, 0, 71, "#62727a"); g.vline(19, 0, 71, "#5a6a70")      # 稜角的明暗
B2 = ["##..###", "#.#...#", "##..###", "#.#.#..", "##..###"]
for dy, row in enumerate(B2):                     # 「B2」每格 2×2 像素，字高 10（約 31 cm）
    for dx, v in enumerate(row):
        if v == "#":
            g.rect(3 + dx * 2, 12 + dy * 2, 4 + dx * 2, 13 + dy * 2, "#d8d4c0")
g.hline(2, 17, 9, "#c9c39a"); g.hline(2, 17, 24, "#c9c39a")      # 字上下的白線
for i in range(40):                               # 下半部的刮痕與髒污
    x, y = int(h(i, 7, 1) * 20), 50 + int(h(i, 8, 1) * 22)
    g.put(x, y, "#5c6c70" if h(i, 9, 1) < 0.6 else "#7a8a8e")

# ---- 警示條紋：45° 黃黑相間（1 m 一格，可以無縫接），有磨損 ----
g = sheet("hazard", 32, 32, "tile 1m")
for y in range(32):
    for x in range(32):
        band = ((x + y) // 8) % 2
        c = "#b8a23c" if band == 0 else "#1c2224"
        if h(x, y, 11) < 0.12:
            c = "#8a7c3a" if band == 0 else "#30383a"
        g.put(x, y, c)

# ---- 地面標線：舊的黃白漆，斑駁（0.5 m 一格） ----
g = sheet("line", 16, 16, "tile 0.5m")
for y in range(16):
    for x in range(16):
        r = h(x, y, 12)
        g.put(x, y, "#c9c39a" if r < 0.7 else ("#a8a482" if r < 0.9 else "#4a5658"))

# ---- 金屬（管線、燈座、門框、保險桿）：深灰、細碎鏽點（1 m 一格） ----
g = sheet("metal", 32, 32, "tile 1m")
noise_fill(g, "#55606a", 0.06, 13)
for i in range(10):
    blob(g, int(h(i, 1, 13) * 32), int(h(i, 2, 13) * 32), 1, "#6a3a2a", i, density=0.9)

# ---- 車漆：深青、灰塵與鏽斑（1 m 一格） ----
g = sheet("carpaint", 32, 32, "tile 1m")
noise_fill(g, "#2e3b3e", 0.05, 14)
for cx, cy, r in ((6, 8, 3), (22, 20, 4), (28, 4, 2)):
    blob(g, cx, cy, r, "#4a3428", cx + cy, density=0.6)
for i in range(12):
    g.put(int(h(i, 3, 14) * 32), int(h(i, 4, 14) * 32), "#3e4c50")

# ---- 門：0.95 × 2.05 m（30×66），鐵門、上下兩塊壓花板、鏽、門縫 ----
g = sheet("door", 30, 66, "fit")
noise_fill(g, "#4e5c58", 0.05, 15)
for x0, y0, x1, y1 in ((4, 26, 25, 40), (4, 44, 25, 60)):        # 壓花板（上方小窗是另外的模型）
    g.rect(x0, y0, x1, y0, "#5e6c68"); g.rect(x0, y0, x0, y1, "#5e6c68")
    g.rect(x0, y1, x1, y1, "#3e4a48"); g.rect(x1, y0, x1, y1, "#3e4a48")
g.vline(0, 0, 65, "#3a4644"); g.vline(29, 0, 65, "#3a4644")
for cx, cy, r in ((24, 62, 4), (3, 64, 3), (20, 30, 2)):
    blob(g, cx, cy, r, "#6a3a2a", cx * 3 + cy, wrap=False, density=0.6)
for x in range(30):                               # 門下緣的髒污
    if h(x, 0, 16) < 0.6:
        g.put(x, 65, "#2c3436")

# ---- 出口牌：0.7 × 0.25 m，2 倍密度（44×16）；綠底、白色的門＋逃生人形＋箭頭（2026-10-29 作者：中文「出口」換成和設施走廊 lab/exit_sign 相同的圖形，主角不是華人） ----
g = sheet("sign", 44, 16, "fit")
g.rect(0, 0, 43, 15, "#1f6a4a")
g.rect(0, 0, 43, 0, "#2c8a62"); g.rect(0, 15, 43, 15, "#14432f")
W_ = "#e8f0e8"
g.rect(4, 3, 11, 13, W_); g.rect(5, 4, 10, 13, "#1f6a4a")                # 門
RUN = ["......##.", "......##.", "....####.", "...#.###.", "..#..####", ".....##..", "....###..", "...##.##.", "..##...#.", ".##....##"]
for dy, row in enumerate(RUN):                                            # 跑向門口的人
    for dx, v in enumerate(row):
        if v == "#":
            g.put(13 + dx, 3 + dy, W_)
for t in range(4):                                                        # 箭頭（往右）
    g.vline(35 + t, 8 - (3 - t), 8 + (3 - t), W_)
g.rect(25, 7, 34, 9, W_)

# ---- 血跡：攤平在地上（貼在頂面，64×32 對應 1.4 × 0.5 m 的範圍），深淺不一、邊緣暗 ----
g = sheet("blood", 64, 32, "fit")
for y in range(32):
    for x in range(64):
        d = math.hypot((x - 26) / 28, (y - 16) / 14)
        r = h(x, y, 17)
        c = "#3a0808" if d > 0.85 else ("#550e0e" if r < 0.7 else "#6a1414")
        g.put(x, y, c)

# ---- 碎布、玻璃、輪胎：小張的細碎紋理 ----
g = sheet("cloth", 16, 16, "tile 0.5m")
noise_fill(g, "#5a5248", 0.08, 18)
for y in range(0, 16, 4):
    g.hline(0, 15, y, "#4e4740")
g = sheet("glass", 16, 16, "tile 0.5m")
noise_fill(g, "#25474d", 0.08, 19)
g.line(2, 13, 12, 3, "#3e6a72"); g.line(5, 14, 14, 5, "#335a62")
g = sheet("tire", 16, 16, "tile 0.5m")
noise_fill(g, "#1a1d1e", 0.08, 20)
for y in range(0, 16, 3):
    g.hline(0, 15, y, "#25292a")

# ---- 輸出：每張 .txt＋.png，預覽（放大 4 倍排在一起） ----
pngs = []
for name, (g, kind) in SHEETS.items():
    txt = f"{OUTDIR}/{name}.txt"
    g.save_txt(txt, outline=False)
    subprocess.run(["magick", txt, f"PNG32:{OUTDIR}/{name}.png"], check=True)
    pngs.append(f"{OUTDIR}/{name}.png")
    print(f"{name} {g.w}x{g.h} {kind}")
subprocess.run(["magick", *pngs, "-background", "#1d2224", "-gravity", "north", "-splice", "0x0", "+append",
                "-scale", "400%", f"{OUTDIR}/preview.png"], check=True)
