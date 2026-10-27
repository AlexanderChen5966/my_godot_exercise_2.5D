# 像素貼圖的共用小工具（B3 起；B2 的 art/design/b2/textures.py 是同樣的寫法）：固定亂數、明暗顆粒、污漬、裂縫、輸出。
# 用法：from texlib import *（設計腳本先把 art/tools 加進 sys.path）
import math, subprocess
from pix import Grid


def h(x, y, s=0):
    """固定的亂數（0～1）；不用 sin（Compatibility 下會有規則紋路，A5 學到的）"""
    n = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def shade(c, k):
    """顏色乘上亮度 k"""
    r, g, b = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v * k))) for v in (r, g, b))


def noise_fill(g, base, amount=0.06, seed=0, steps=(0.9, 1.0, 1.0, 1.08), rect=None):
    """底色＋細碎的明暗顆粒；rect=(x0, y0, x1, y1) 只填一塊"""
    x0, y0, x1, y1 = rect or (0, 0, g.w - 1, g.h - 1)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
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


def crack(g, x, y, n, seed, color, wrap=True):
    """一條彎曲往下的裂縫"""
    for i in range(n):
        g.put(x % g.w if wrap else x, y % g.h if wrap else y, color)
        r = h(i, seed, 3)
        x += 1 if r < 0.55 else (0 if r < 0.8 else -1)
        y += 1 if h(i, seed, 5) < 0.7 else 0


def export(sheets, outdir, preview="preview.png"):
    """每張存 .txt＋.png，並排成放大 4 倍的預覽"""
    pngs = []
    for name, (g, kind) in sheets.items():
        txt = f"{outdir}/{name}.txt"
        g.save_txt(txt, outline=False)
        subprocess.run(["magick", txt, f"PNG32:{outdir}/{name}.png"], check=True)
        pngs.append(f"{outdir}/{name}.png")
        print(f"{name} {g.w}x{g.h} {kind}")
    subprocess.run(["magick", *pngs, "-background", "#1d2224", "-gravity", "north", "-splice", "0x0", "+append",
                    "-scale", "400%", f"{outdir}/{preview}"], check=True)
