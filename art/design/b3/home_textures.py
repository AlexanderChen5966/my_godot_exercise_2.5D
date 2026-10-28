# B3-5b 舊家的像素貼圖（32 像素＝1 m；字、畫、相框用 2 倍密度 64 像素＝1 m；窗外遠處的房子 16 像素＝1 m）。
# 借用：天空 ruins/sky、人行道 street/sidewalk、柏油 street/asphalt；共用的木板 common/wood、金屬 common/metal、碎布 common/cloth、舊報紙 common/paper。
# 這裡畫舊家專屬的（輸出到 assets/textures/home/）。主角不是華人：畫面上不放中文；牆上的蠟筆字是英文（作者 2026-10-28 選「兩行」）。
# 道具照 2D 原本陰沉的風格（作者 B3-2b）：小孩的畫也是褪色、發黃的。
# 用法：python3 art/design/b3/home_textures.py 輸出資料夾 → 每張的 .txt、.png 與 preview.png
import math, sys
sys.path.insert(0, "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/art/tools")
from pix import Grid
from texlib import h, shade, noise_fill, blob, crack, export

OUTDIR = sys.argv[1]
SHEETS = {}


def sheet(name, w, h_, kind):
    g = Grid(w, h_)
    SHEETS[name] = (g, kind)
    return g


# 5×7 的字（蠟筆字用）
GLYPH = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"], "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."], "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"], "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"], "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"], "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"], "N": ["#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."], "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."], "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."], "V": ["#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"], "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    ",": ["..", "..", "..", "..", "..", ".#", "#."], ".": [".", ".", ".", ".", ".", ".", "#"], "'": ["#", "#", ".", ".", ".", ".", "."],
}


def crayon_line(g, y, s, scale, seed):
    """一行蠟筆字（置中）：每個字上下晃一點、整行微微往右上斜；筆畫有斷續、深淺不一"""
    adv = [(len(GLYPH[c][0]) * scale + max(1, scale // 2)) if c != " " else 3 * scale for c in s]
    x = (g.w - sum(adv)) // 2
    for i, c in enumerate(s):
        if c != " ":
            if scale > 1:
                dy = int(round((h(i, 1, seed) - 0.5) * 2.2)) - (i * scale) // 30
            else:
                dy = (1 if h(i, 1, seed) < 0.2 else 0) - i // 14              # 小字只偶爾掉一格，不然讀不出來
            for gy, row in enumerate(GLYPH[c]):
                for gx, v in enumerate(row):
                    if v != "#":
                        continue
                    for sy in range(scale):
                        for sx in range(scale):
                            px, py = x + gx * scale + sx, y + dy + gy * scale + sy
                            r = h(px, py, seed + 7)
                            if r < (0.1 if scale > 1 else 0.03):
                                continue                                  # 蠟筆沒塗到的地方
                            g.put(px, py, "#c4483a" if r > 0.8 else ("#7e2620" if r < 0.2 else "#a8342c"))
        x += adv[i]


# ---- 壁紙（寬 2 m 一格、高 2.75 m 整面，64×88）：下面 0.9 m 深色木板護牆，上面褪色的直條紋壁紙；剝落露出灰泥、從天花板流下來的水漬 ----
g = sheet("wallpaper", 64, 88, "tile 2m × 2.75m")
for y in range(88):
    for x in range(64):
        z = 2.75 - (y + 0.5) / 32
        if z < 0.9:
            c = shade("#4e3a2a", 0.9 + (h(x, y, 501) - 0.5) * 0.12 - (0.2 if x % 10 == 0 else 0) - (0.1 if z < 0.08 else 0))
        else:
            stripe = 0.94 if x % 8 in (0, 1) else 1.0
            dot = 0.9 if (x % 8 == 4 and y % 6 == 3) else 1.0             # 小小的花紋
            stain = 0.12 * h(x // 3, 1, 502) * max(0.0, (z - 1.7) / 1.05)   # 越上面越髒
            c = shade("#8a7a5c", stripe * dot * (0.95 + (h(x, y, 503) - 0.5) * 0.07) - stain)
        g.put(x, y, c)
g.hline(0, 63, 59, "#2e2218"); g.hline(0, 63, 58, "#6a5038"); g.hline(0, 63, 57, "#3a2a1e")   # 護牆上緣的木條（0.9 m）
for i in range(5):                                                        # 水漬：從天花板流下來
    x = int(h(i, 1, 504) * 64)
    n = 14 + int(h(i, 2, 504) * 30)
    for k in range(n):
        xx = (x + (1 if h(i, k, 505) < 0.25 else 0)) % 64
        g.put(xx, k, shade("#6a5a40", 0.95 + h(i, k, 506) * 0.1))
        if k < n // 2:
            g.put((xx + 1) % 64, k, shade("#74644a", 1.0))
crack(g, 40, 2, 16, 509, "#5a4e3a")

# ---- 壁紙剝落的貼花（兩塊，各 1 m 見方，fit 64×32，透明）：露出灰泥、邊上捲起來（壁紙不畫，免得每 2 m 重複一次） ----
g = sheet("peel", 64, 32, "fit alpha")
for i, (cx, cy, rx, ry) in enumerate(((16, 15, 11, 8), (48, 16, 8, 12))):
    for dy in range(-ry - 2, ry + 3):
        for dx in range(-rx - 2, rx + 3):
            d = math.hypot(dx / rx, dy / ry) + (h(cx + dx // 2, cy + dy // 2, 507 + i) - 0.5) * 0.22
            x, y = cx + dx, cy + dy
            if not (0 <= x < 64 and 0 <= y < 32):
                continue
            if d <= 0.82:
                g.put(x, y, shade("#a09880", 0.88 + h(x, y, 508) * 0.12))
            elif d <= 1.0:
                g.put(x, y, "#a8986e" if dy < 0 else "#3e3424")             # 捲起的邊（上亮下暗）

# ---- 女兒房間的壁紙（同樣大小，64×88）：淡藍灰、小圓點，沒有護牆；褪色、角落發黴 ----
g = sheet("wallpaper_kid", 64, 88, "tile 2m × 2.75m")
for y in range(88):
    for x in range(64):
        c = shade("#6e7a80", 0.95 + (h(x, y, 511) - 0.5) * 0.07)
        if (x % 8 == 2 and y % 8 == 2) or (x % 8 == 6 and y % 8 == 6):
            c = shade("#9a8a70", 0.95)                                    # 褪色的小圓點
        g.put(x, y, c)
g.hline(0, 63, 85, "#4a3e30"); g.hline(0, 63, 86, "#3a3026"); g.hline(0, 63, 87, "#2e261e")     # 踢腳板
for i in range(6):
    blob(g, int(h(i, 1, 512) * 64), int(h(i, 2, 512) * 18), 3, "#4e5a50", i + 80, density=0.5)   # 天花板下的黴
for i in range(3):
    x = int(h(i, 3, 513) * 64)
    for k in range(10 + int(h(i, 4, 513) * 20)):
        g.put(x, k, "#5a6266")

# ---- 木地板（1 m 一格，32×32）：沿 x 方向的長條木板（寬 8 像素＝25 cm），接縫錯開、刮痕、灰塵 ----
g = sheet("floor_wood", 32, 32, "tile 1m")
for y in range(32):
    row = y // 8
    for x in range(32):
        seg = ((x + row * 11) // 32)
        base = ["#584230", "#54402e", "#5c4532", "#523e2c"][(row * 3 + seg) % 4]
        grain = 0.94 if (x * 3 + y * 7 + row) % 11 == 0 else 1.0
        c = shade(base, grain * (0.95 + (h(x, y, 521) - 0.5) * 0.08))
        if y % 8 == 0:
            c = shade(c, 0.72)                                            # 木板之間的縫
        elif (x + row * 11) % 32 == 0:
            c = shade(c, 0.8)                                             # 木板的頭
        g.put(x, y, c)
for i in range(3):
    x0, y0 = int(h(i, 1, 522) * 32), 1 + 8 * int(h(i, 2, 522) * 4)
    for k in range(4 + int(h(i, 3, 522) * 6)):
        g.put((x0 + k) % 32, y0 + 3, "#6e5840")                           # 刮痕
blob(g, 20, 20, 3, "#4a3a2c", 523, density=0.5)

# ---- 天花板（1 m 一格，32×32）：灰泥、細裂縫、水漬的圈 ----
g = sheet("ceiling_home", 32, 32, "tile 1m")
noise_fill(g, "#6a5e4e", 0.06, 531)
blob(g, 18, 18, 6, "#5e5244", 533, density=0.7)                         # 水漬
blob(g, 18, 18, 3, "#54483a", 534, density=0.8)
crack(g, 3, 0, 32, 532, "#4e4436")

# ---- 牆上的蠟筆字（3 × 1 m，2 倍密度 fit 192×64，透明）：大字兩行、小字三行（作者 2026-10-28 定：照劇本的兩句） ----
g = sheet("crayon_words", 192, 64, "fit 2x alpha")
crayon_line(g, 2, "DADDY,", 2, 541)
crayon_line(g, 19, "I KNOW IT'S YOU.", 2, 542)
crayon_line(g, 38, "IF YOU CAME BACK, I WOULD", 1, 543)
crayon_line(g, 47, "KNOW IT WAS YOU, BECAUSE", 1, 544)
crayon_line(g, 56, "YOU WOULD NEVER HURT ME.", 1, 545)

# ---- 全家福的蠟筆畫（約 0.62 × 0.47 m，2 倍密度 fit 40×30，透明）：發黃的紙、爸爸、媽媽、女孩牽手，房子、太陽；右下角撕掉一塊、膠帶 ----
g = sheet("drawing", 40, 30, "fit 2x alpha")
for y in range(30):
    for x in range(40):
        if x + y > 62:
            continue                                                      # 撕掉的角
        g.put(x, y, shade("#b4a47c", 0.94 + (h(x, y, 551) - 0.5) * 0.08 - (0.08 if x < 2 or y < 2 else 0)))
g.vline(19, 1, 28, shade("#b4a47c", 0.85))                                # 對折過的痕
def stick(cx, top, tall, col):
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if abs(dx) + abs(dy) < 2:
                g.put(cx + dx, top + 1 + dy, col)                         # 頭
    g.vline(cx, top + 3, top + tall - 3, col)
    g.line(cx, top + tall - 3, cx - 2, top + tall, col); g.line(cx, top + tall - 3, cx + 2, top + tall, col)
    g.hline(cx - 3, cx + 3, top + 5, col)                                 # 張開的手（牽在一起）
# 照劇本（女兒的房間）：高高的爸爸、長頭髮的媽媽、中間牽著兩人的小女孩；爸爸的嘴巴旁邊畫了好多個小小的愛心
stick(7, 5, 19, "#3e4e6a"); stick(14, 13, 11, "#a8742e"); stick(21, 8, 16, "#8a3a30")
g.vline(19, 9, 15, "#5a3a2a"); g.vline(23, 9, 15, "#5a3a2a")
g.line(10, 10, 11, 18, "#3e4e6a"); g.line(18, 13, 17, 18, "#8a3a30")                # 牽著女孩的手（斜斜往下）              # 媽媽的長頭髮
for hx, hy in ((10, 2), (14, 4), (10, 7)):                               # 小愛心（褪色的紅）
    g.put(hx, hy, "#9a4a40"); g.put(hx + 2, hy, "#9a4a40"); g.hline(hx, hx + 2, hy + 1, "#9a4a40"); g.put(hx + 1, hy + 2, "#9a4a40")
g.hline(5, 34, 25, "#4e6a3a"); g.hline(4, 30, 26, "#4e6a3a")              # 草地
for x0, y0 in ((29, 14),):                                                # 房子
    g.rect(x0, y0 + 4, x0 + 8, y0 + 10, "#6a4a34"); g.rect(x0 + 1, y0 + 5, x0 + 7, y0 + 9, "#b4a47c")
    for t in range(5):
        g.hline(x0 + 4 - t, x0 + 4 + t, y0 + t, "#7e3a2a")
    g.rect(x0 + 3, y0 + 7, x0 + 5, y0 + 10, "#6a4a34")
for a in range(0, 360, 45):                                               # 太陽（右上）
    g.put(34 + int(round(2.6 * math.cos(math.radians(a)))), 5 + int(round(2.6 * math.sin(math.radians(a)))), "#b48a30")
g.put(34, 5, "#b48a30")
g.rect(17, 0, 22, 1, "#c8c0a0")                                           # 膠帶

# ---- 相框（三個，2 倍密度 fit 80×32）：木框、褪色泛黃的照片（看不清臉的人影）；中間那張玻璃裂了 ----
g = sheet("photos", 80, 32, "fit 2x")
for k in range(3):
    x0 = k * 27
    g.rect(x0, 0, x0 + 25, 31, "#3a2a1e"); g.rect(x0 + 1, 1, x0 + 24, 30, "#5a4030")
    for y in range(4, 28):
        for x in range(x0 + 4, x0 + 22):
            g.put(x, y, shade("#8a7458", 0.9 + (y - 4) * 0.008 + (h(x, y, 561 + k) - 0.5) * 0.06))
    people = [((x0 + 9, 8, 14), (x0 + 17, 10, 12)), ((x0 + 13, 9, 13),), ((x0 + 8, 9, 13), (x0 + 15, 10, 12), (x0 + 19, 17, 6))][k]
    for cx, top, tall in people:                                          # 人影（深褐色的剪影）
        g.rect(cx - 1, top, cx + 1, top + 2, "#4a3a2a")                   # 頭、脖子、肩膀往下
        g.put(cx, top + 3, "#4a3a2a")
        g.rect(cx - 3, top + 4, cx + 3, min(27, top + tall), "#4a3a2a")
    if k == 1:
        g.line(x0 + 6, 5, x0 + 15, 16, "#c8c0a8"); g.line(x0 + 15, 16, x0 + 21, 13, "#c8c0a8"); g.line(x0 + 15, 16, x0 + 12, 27, "#c8c0a8")

# ---- 書架的正面（0.9 × 2 m，fit 29×64）：深色木框、五層，書顏色暗沉、有缺的、倒下來斜放的 ----
g = sheet("shelf_front", 29, 64, "fit")
g.rect(0, 0, 28, 63, "#3a2a1e")
BOOK = ["#4a3a3a", "#3a4a4a", "#4e4a36", "#5a3a2e", "#3e3e4e", "#5a5040"]
for s in range(5):
    y1 = 61 - s * 12
    g.rect(2, y1 - 10, 26, y1, "#1e1610")                                 # 層板裡面（暗）
    g.hline(1, 27, y1 + 1, "#5a4030")                                     # 層板
    x = 2
    i = 0
    while x < 26:
        w = 2 + int(h(s, i, 571) * 2)
        tall = 6 + int(h(s, i, 572) * 4)
        if h(s, i, 573) < 0.18:                                           # 空著
            x += w + 1
        else:
            col = BOOK[int(h(s, i, 574) * len(BOOK))]
            for xx in range(x, min(26, x + w) + 1):
                g.vline(xx, y1 - tall, y1, shade(col, 0.9 + (xx - x) * 0.06))
            g.put(x, y1 - tall + 2, shade(col, 1.3))                      # 書背上的線
            x += w + 1
        i += 1
    if s == 2:                                                            # 倒下斜放的書
        for k in range(5):
            g.hline(18 + k, 22 + k, y1 - k, "#5a3a2e")

# ---- 沙發布（1 m 一格，32×32）：褪色的橄欖褐、粗織的格紋、一道破口露出發黃的棉花 ----
g = sheet("sofa", 32, 32, "tile 1m")
for y in range(32):
    for x in range(32):
        k = 0.95 + (0.04 if (x // 2 + y // 2) % 2 == 0 else 0) + (h(x, y, 581) - 0.5) * 0.06
        g.put(x, y, shade("#5a5440", k - (0.08 if x % 16 == 0 else 0)))
for k in range(10):                                                       # 破口（中間寬、兩頭尖，露出棉花）
    x, y = 8 + k, 12 + (k * 3) // 4
    w = 1 + min(k, 9 - k) // 2
    g.put(x, y - 1, "#2e2a20")
    for t in range(w):
        g.put(x, y + t, "#c8bc98" if h(x, t, 583) > 0.3 else "#b0a480")
    g.put(x, y + w, "#2e2a20")
blob(g, 24, 24, 3, "#4a4434", 582, density=0.6)

# ---- 門（1 × 2.1 m，fit 32×68）：深色木頭的鑲板門、黃銅門把（大門、女兒房間的門板共用） ----
g = sheet("door_home", 32, 68, "fit")
for y in range(68):
    for x in range(32):
        g.put(x, y, shade("#4a3424", 0.92 + (h(x // 2, y, 591) - 0.5) * 0.1))
for x0, y0, x1, y1 in ((4, 4, 14, 24), (17, 4, 27, 24), (4, 28, 14, 44), (17, 28, 27, 44), (4, 48, 14, 63), (17, 48, 27, 63)):
    g.rect(x0, y0, x1, y0, "#2e2018"); g.rect(x0, y0, x0, y1, "#2e2018")     # 鑲板：左上暗、右下亮
    g.rect(x0, y1, x1, y1, "#5e4632"); g.rect(x1, y0, x1, y1, "#5e4632")
g.rect(26, 34, 28, 36, "#a08040"); g.put(27, 35, "#d0b060")                # 門把
for i in range(3):
    blob(g, int(h(i, 1, 592) * 30), int(h(i, 2, 592) * 66), 1, "#3a2a1e", i + 90, wrap=False, density=0.8)

# ---- 大窗（2.8 × 1.2 m，fit 90×38，透明）：木窗框分三格，玻璃大多破了只剩邊上的碎片；窗台 ----
g = sheet("window_home", 90, 38, "fit alpha")
F = "#4a3424"
for y in range(38):
    for x in range(90):
        frame = x < 3 or x > 86 or y < 3 or y > 34 or x in (29, 30, 59, 60) or (y in (12, 13) and (x < 29 or x > 60))
        if frame:
            g.put(x, y, shade(F, 0.92 + (h(x, y, 601) - 0.5) * 0.12 - (0.15 if y > 34 or x > 86 else 0)))
for x0, x1 in ((3, 28), (31, 58), (61, 86)):                              # 每一格邊上剩下的碎玻璃（三角形）
    for k in range(3):
        side = int(h(x0, k, 602) * 4)
        n = 3 + int(h(x0, k, 603) * 5)
        for t in range(n):
            for u in range(n - t):
                if side == 0:
                    x, y = x0 + 3 + k * 7 + u, 3 + t
                elif side == 1:
                    x, y = x1 - 3 - k * 7 - u, 34 - t
                elif side == 2:
                    x, y = x0 + t, 14 + k * 6 + u
                else:
                    x, y = x1 - t, 14 + k * 6 + u
                if 0 <= y < 38 and x0 <= x <= x1 and g.get(x, y) is None:
                    g.put(x, y, "#9aa6aa" if (x + y) % 5 else "#c8d0d0")

# ---- 廚房（fit 120×58）：左＝流理台正面（2.8 × 0.9 m，90×29：櫃門、把手、一扇開著），右＝冰箱正面（0.8 × 1.8 m，26×58：把手、褪色的紙） ----
g = sheet("kitchen", 120, 58, "fit atlas")
for y in range(29):
    for x in range(90):
        g.put(x, y, shade("#6e6656", 0.94 + (h(x, y, 611) - 0.5) * 0.08 - (0.25 if y < 2 else 0)))
for k in range(5):
    x0 = 2 + k * 18
    if k == 3:
        g.rect(x0, 4, x0 + 15, 27, "#1e1a16")                             # 開著的櫃門（裡面暗）
        continue
    g.rect(x0, 4, x0 + 15, 4, "#4e483c"); g.rect(x0, 4, x0, 27, "#4e483c"); g.rect(x0 + 15, 4, x0 + 15, 27, "#857c6a"); g.rect(x0, 27, x0 + 15, 27, "#857c6a")
    g.rect(x0 + 6, 7, x0 + 9, 7, "#9a9488")                               # 把手
blob(g, 70, 20, 3, "#5a5242", 612, wrap=False, density=0.6)
for y in range(58):
    for x in range(92, 118):
        g.put(x, y, shade("#8a8476", 0.92 + (h(x, y, 613) - 0.5) * 0.06 - (0.2 if x in (92, 117) else 0) - (0.2 if y in (0, 57) else 0)))
g.hline(93, 116, 18, "#4e4a40")                                           # 冷凍庫的縫
g.vline(114, 6, 14, "#5a564c"); g.vline(114, 22, 34, "#5a564c")            # 把手
g.rect(98, 25, 106, 33, "#b4a47c"); g.line(99, 31, 101, 27, "#7e3a2a"); g.line(101, 27, 104, 30, "#7e3a2a")   # 褪色的紙（小孩的塗鴉）
g.put(102, 25, "#8a3a30")                                                 # 磁鐵
for i in range(4):
    blob(g, 93 + int(h(i, 1, 614) * 24), int(h(i, 2, 614) * 56), 2, "#6e5a44", i + 95, wrap=False, density=0.5)   # 鏽、污漬

# ---- 被子（0.5 m 一格，16×16）：褪色的灰粉紅、細格紋（疊得整整齊齊的被子、枕頭） ----
g = sheet("quilt", 16, 16, "tile 0.5m")
for y in range(16):
    for x in range(16):
        c = "#7a6062" if (x // 4 + y // 4) % 2 == 0 else "#6e5658"
        if x % 8 == 0 or y % 8 == 0:
            c = "#8a7472"
        g.put(x, y, shade(c, 0.95 + (h(x, y, 621) - 0.5) * 0.06))

# ---- 對街的房子（14 × 6 m，16 像素＝1 m，fit 224×96，透明）：三間斜屋頂的房子、暗的窗（有一扇破了）、枯樹、矮圍牆；屋頂邊緣被夕陽照亮 ----
g = sheet("houses_far", 224, 96, "fit alpha 16px/m")
HOUSES = [(4, 66, 46, 30), (74, 136, 38, 34), (146, 214, 50, 28)]        # (x0, x1, 牆高, 屋頂高)
for hi, (x0, x1, wh, rh) in enumerate(HOUSES):
    base = 95
    top = base - wh
    for y in range(top, base + 1):
        for x in range(x0, x1 + 1):
            g.put(x, y, shade("#3a2e2a", 0.92 + (h(x // 2, y // 2, 631 + hi) - 0.5) * 0.08))
    mid = (x0 + x1) / 2
    for t in range(rh):
        half = (x1 - x0) / 2 + 3 - t * ((x1 - x0) / 2 + 3) / rh
        for x in range(int(mid - half), int(mid + half) + 1):
            g.put(x, top - t, "#2e2422")
        g.put(int(mid - half), top - t, "#a8643a"); g.put(int(mid + half), top - t, "#7a4a30")   # 夕陽照到的屋頂邊
    for k in range(2):                                                    # 窗（暗；中間那間有一扇破的）
        wx = int(x0 + 10 + k * (x1 - x0 - 30))
        g.rect(wx, top + 10, wx + 9, top + 22, "#4e3e34")
        g.rect(wx + 1, top + 11, wx + 8, top + 21, "#161210" if not (hi == 1 and k == 0) else "#0a0806")
        g.vline(wx + 4, top + 11, top + 21, "#4e3e34"); g.hline(wx + 1, wx + 8, top + 16, "#4e3e34")
    g.rect(int(mid - 4), base - 18, int(mid + 4), base, "#241c18")        # 門
g.rect(66, 84, 74, 95, "#2a2220"); g.rect(136, 86, 146, 95, "#2a2220")     # 房子之間的矮圍牆
for x0, h0 in ((140, 74),):                                               # 枯樹：主幹＋分岔的樹枝
    g.vline(x0, h0, 95, "#1e1816"); g.vline(x0 + 1, h0 + 4, 95, "#1e1816")
    for k, (dx, dy) in enumerate(((-8, -10), (7, -12), (-5, -18), (4, -20), (10, -6))):
        y0 = h0 + 4 + k * 3
        g.line(x0, y0, x0 + dx, y0 + dy, "#1e1816")

export(SHEETS, OUTDIR)
