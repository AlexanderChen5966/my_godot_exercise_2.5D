# B3-1b：從 A3 的燒毀車動畫（assets/sprites/props/burnt_car_anim.png，4 格 120×44）把火焰挑出來，
# 做成單獨的火焰動畫（引擎蓋的大火、車窗的小火各一套，4 格）：只留橘黃色（R 高、R>G>B）的像素，其他透明。
# 用法：python3 art/design/b3/fire_extract.py 輸出資料夾 → fire_big.png（4 格 24×22）、fire_small.png（4 格 16×18）
import subprocess, sys
OUT = sys.argv[1]
SRC = "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/assets/sprites/props/burnt_car_anim.png"
txt = subprocess.run(["magick", SRC, "txt:-"], capture_output=True, text=True).stdout.splitlines()[1:]
px = {}
for line in txt:
    xy, rest = line.split(":", 1)
    x, y = map(int, xy.split(","))
    vals = rest.strip().split(")")[0].strip("( ").split(",")
    r, g, b, a = (int(float(v)) for v in vals[:4])
    px[(x, y)] = (r, g, b, a)
def is_fire(c):
    r, g, b, a = c
    return a > 0 and r >= 150 and r > g > b and (r - b) > 60
for name, (x0, y0, w, h) in {"fire_big": (2, 0, 24, 22), "fire_small": (32, 2, 16, 18)}.items():
    lines = [f"# ImageMagick pixel enumeration: {w * 4},{h},255,srgba"]
    for f in range(4):
        for y in range(h):
            for x in range(w):
                c = px.get((f * 120 + x0 + x, y0 + y), (0, 0, 0, 0))
                X = f * w + x
                if is_fire(c):
                    lines.append(f"{X},{y}: ({c[0]},{c[1]},{c[2]},255)  #{c[0]:02X}{c[1]:02X}{c[2]:02X}FF  srgba")
                else:
                    lines.append(f"{X},{y}: (0,0,0,0)  #00000000  none")
    open(f"{OUT}/{name}.txt", "w").write("\n".join(lines) + "\n")
    subprocess.run(["magick", f"{OUT}/{name}.txt", f"PNG32:{OUT}/{name}.png"], check=True)
    print(name, w * 4, h)
