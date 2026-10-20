# B1：把 2D 區域場景的互動點（Points）與近景（Near）轉成 3D 區域場景的初稿，之後再用 Toolkit 檢查與修改。
# 用法：python3 convert_area_3d.py 專案根目錄 區域名稱（例如 ParkingLot）
#   讀 scenes/areas/<名稱>.tscn，寫入 scenes/areas3d/<名稱>3D.tscn（沒有就建立，繼承 AreaBase3D）。
#   3D 場景裡 Points／Near 底下的節點每次都重新產生（手動加在那裡的會被蓋掉）；Lights、Geometry 等其他節點保留。
# 換算（和 area_3d.gd 相同）：x 64 像素＝1 公尺；縱深帶 walk_top～walk_bottom ↔ z −depth/2～＋depth/2（縱深帶外的 y 照比例延伸）；
#   像素的往上（y 變小）＝3D 的往上；放大 2 倍的像素圖 ＝ pixel_size 1/32。
# 對應：Area2D（interact_point.gd）→ Area3D（interact_point_3d.gd）；RectangleShape2D → BoxShape3D（高 2 公尺）；
#   Sprite2D → Sprite3D；AnimatedSprite2D → AnimatedSprite3D（SpriteFrames 換成 *_frames_3d.tres）；
#   AudioStreamPlayer2D → AudioStreamPlayer3D；StaticBody2D → StaticBody3D；LightOccluder2D 略過（3D 有真的陰影）。
#   用在 3D 的像素圖會把 .import 改成無損、不產生 mipmap、關閉 3D 偵測（CLAUDE.md 的 2.5D 坑①）。
import re, sys, os

PX = 64.0
DEPTH = 3.0
BASE = "res://scenes/areas3d/AreaBase3D.tscn"
POINTS_ID = 2077837389   # AreaBase3D 的 Points 節點 unique_id
ROOT_EXPORTS = ("area_width", "player_start", "edge_margin", "walk_top", "walk_bottom")

root, name = sys.argv[1], sys.argv[2]
src = open(f"{root}/scenes/areas/{name}.tscn", encoding="utf-8").read()
dst_path = f"{root}/scenes/areas3d/{name}3D.tscn"


def blocks(text):
    return re.split(r'\n(?=\[)', text.strip())


def header(b):
    return b.split("\n", 1)[0]


def props(b):
    out = {}
    for line in b.split("\n")[1:]:
        m = re.match(r'([\w/]+) = (.*)', line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def attr(h, key):
    m = re.search(r"(?<![\w])" + key + r'="([^"]*)"', h)
    return m.group(1) if m else None


def vec2(s, default=(0.0, 0.0)):
    if s is None:
        return default
    a, b = re.match(r'Vector2\(([^,]+), ([^)]+)\)', s).groups()
    return float(a), float(b)


def f(v):
    return f"{v:.6f}".rstrip("0").rstrip(".") if v != int(v) else str(int(v))


# ---- 讀 2D 場景 ----
ext2 = {}
sub2 = {}
nodes2 = []
for b in blocks(src):
    h = header(b)
    if h.startswith("[ext_resource"):
        ext2[attr(h, "id")] = (attr(h, "type"), attr(h, "path"))
    elif h.startswith("[sub_resource"):
        sub2[attr(h, "id")] = (attr(h, "type"), props(b))
    elif h.startswith("[node"):
        nodes2.append((attr(h, "name"), attr(h, "type"), attr(h, "parent"), props(b)))

root_props = nodes2[0][3]
walk_top = float(root_props.get("walk_top", 650))
walk_bottom = float(root_props.get("walk_bottom", 735))


def y_to_z(y):
    return -DEPTH / 2 + (y - walk_top) / (walk_bottom - walk_top) * DEPTH


def z_len(h):
    return h / (walk_bottom - walk_top) * DEPTH


def ext_path(ref):
    m = re.match(r'ExtResource\("([^"]+)"\)', ref or "")
    return ext2[m.group(1)][1] if m else None


# ---- 產生 3D 節點 ----
ext3 = {}     # path -> (type, id)
sub3 = []     # 文字
out_nodes = []
textures_3d = set()
warnings = []


def ext_id(typ, path):
    if path not in ext3:
        ext3[path] = (typ, f"cv{len(ext3) + 1}")
    return ext3[path][1]


def add_sub(typ, body):
    sid = f"{typ}_cv{len(sub3) + 1}"
    sub3.append(f'[sub_resource type="{typ}" id="{sid}"]\n{body}\n')
    return sid


def transform(x, y, z, rot_z=0.0):
    import math
    c, s = math.cos(rot_z), math.sin(rot_z)
    return f"transform = Transform3D({f(c)}, {f(s)}, 0, {f(-s)}, {f(c)}, 0, 0, 0, 1, {f(x)}, {f(y)}, {f(z)})"


def node(nname, typ, parent, lines, top=False):
    extra = f' parent_id_path=PackedInt32Array({POINTS_ID})' if top and parent == "Points" else ""
    out_nodes.append(f'[node name="{nname}" type="{typ}" parent="{parent}"{extra}]\n' + "\n".join(lines) + "\n")


def sprite_lines(p, scale):
    lines = [f"pixel_size = {f(scale / PX)}", "shaded = true", "alpha_cut = 1", "texture_filter = 0"]
    if "flip_h" in p:
        lines.append(f"flip_h = {p['flip_h']}")
    ox, oy = vec2(p.get("offset"))
    if ox or oy:
        lines.append(f"offset = Vector2({f(ox)}, {f(-oy)})")
    return lines


def convert_child(n, typ, parent3, p, base_z):
    """點（或近景容器）底下的子節點；位置相對於父節點（像素 → 公尺，y 反向；z 跟父節點相同）"""
    x, y = vec2(p.get("position"))
    rot = float(p.get("rotation", 0))
    scale = vec2(p.get("scale"), (1.0, 1.0))[0]
    if typ == "CollisionShape2D":
        sid = re.match(r'SubResource\("([^"]+)"\)', p["shape"]).group(1)
        w, h = vec2(sub2[sid][1]["size"])
        # 2D 的 y 範圍換成 z 範圍（相對於點的原點）
        z0 = y_to_z(base_z + y - h / 2) - y_to_z(base_z)
        z1 = y_to_z(base_z + y + h / 2) - y_to_z(base_z)
        box = add_sub("BoxShape3D", f"size = Vector3({f(w / PX)}, 2, {f(z1 - z0)})")
        node(n, "CollisionShape3D", parent3, [transform(x / PX, 1, (z0 + z1) / 2), f'shape = SubResource("{box}")'])
    elif typ == "Sprite2D":
        path = ext_path(p.get("texture"))
        textures_3d.add(path)
        lines = [transform(x / PX, -y / PX, 0, -rot)] + sprite_lines(p, scale)
        lines.append(f'texture = ExtResource("{ext_id("Texture2D", path)}")')
        for k in ("hframes", "vframes", "frame"):
            if k in p:
                lines.append(f"{k} = {p[k]}")
        node(n, "Sprite3D", parent3, lines)
    elif typ == "AnimatedSprite2D":
        path = ext_path(p.get("sprite_frames"))
        path3 = path.replace(".tres", "_3d.tres")
        if not os.path.exists(root + "/" + path3.replace("res://", "")):
            warnings.append(f"{parent3}/{n}：沒有 {path3}，先用 2D 的 {path}（若指向 CanvasTexture 會是白色方塊）")
            path3 = path
        lines = [transform(x / PX, -y / PX, 0, -rot)] + sprite_lines(p, scale)
        lines.append(f'sprite_frames = ExtResource("{ext_id("SpriteFrames", path3)}")')
        for k in ("animation", "autoplay", "frame"):
            if k in p:
                lines.append(f"{k} = {p[k]}")
        node(n, "AnimatedSprite3D", parent3, lines)
    elif typ == "AudioStreamPlayer2D":
        path = ext_path(p.get("stream"))
        md = float(p.get("max_distance", 2000)) / PX
        lines = [transform(x / PX, -y / PX, 0), f'stream = ExtResource("{ext_id("AudioStream", path)}")',
                 "attenuation_model = 1", f"unit_size = {f(md / 4)}", f"max_distance = {f(md)}"]
        for k in ("volume_db", "autoplay", "bus"):
            if k in p:
                lines.append(f"{k} = {p[k]}")
        node(n, "AudioStreamPlayer3D", parent3, lines)
    elif typ == "StaticBody2D":
        node(n, "StaticBody3D", parent3, [transform(x / PX, 0, y_to_z(base_z + y) - y_to_z(base_z))])
        return True   # 子節點（Shape、Sprite）接著轉
    elif typ == "LightOccluder2D":
        pass
    else:
        warnings.append(f"{parent3}/{n}：{typ} 沒有對應，略過")
    return False


def convert_tree(top_parent):
    """轉換 top_parent（Points 或 Near）底下的節點"""
    tops = {}   # 2D 路徑 -> (3D 路徑, 原點的像素 y)
    for n, typ, parent, p in nodes2:
        if parent == top_parent:
            x, y = vec2(p.get("position"))
            if typ == "Area2D":
                lines = [transform(x / PX, 0, y_to_z(y)), f'script = ExtResource("{ext_id("Script", "res://scripts/interact_point_3d.gd")}")',
                         f"point_id = {p['point_id']}"]
                node(n, "Area3D", top_parent, lines, top=True)
                tops[f"{top_parent}/{n}"] = (f"{top_parent}/{n}", y)
            elif typ == "StaticBody2D":
                node(n, "StaticBody3D", top_parent, [transform(x / PX, 0, y_to_z(y))], top=True)
                tops[f"{top_parent}/{n}"] = (f"{top_parent}/{n}", y)
            elif typ == "Sprite2D":   # 近景物件：原點在底部
                path = ext_path(p.get("texture"))
                textures_3d.add(path)
                scale = vec2(p.get("scale"), (1.0, 1.0))[0]
                lines = [transform(x / PX, 0, y_to_z(y))] + sprite_lines(p, scale)
                lines.append(f'texture = ExtResource("{ext_id("Texture2D", path)}")')
                node(n, "Sprite3D", top_parent, lines, top=True)
            else:
                warnings.append(f"{top_parent}/{n}：{typ} 沒有對應，略過")
    # 子節點（可能再一層，例如 Block/Shape）
    for n, typ, parent, p in nodes2:
        if parent in tops:
            path3, base_y = tops[parent]
            if convert_child(n, typ, path3, p, base_y):
                x, y = vec2(p.get("position"))
                tops[f"{parent}/{n}"] = (f"{path3}/{n}", base_y + y)


convert_tree("Points")
has_near = any(parent == "Near" for _, _, parent, _ in nodes2)
if has_near:
    convert_tree("Near")

# ---- 合併到 3D 場景 ----
keep_ext, keep_sub, keep_nodes = [], [], []
scene_header = None
root_node = None
if os.path.exists(dst_path):
    for b in blocks(open(dst_path, encoding="utf-8").read()):
        h = header(b)
        par = attr(h, "parent") or ""
        if h.startswith("[gd_scene"):
            scene_header = h
        elif h.startswith("[ext_resource"):
            keep_ext.append(b)
        elif h.startswith("[sub_resource"):
            keep_sub.append(b)
        elif h.startswith("[node"):
            if par == "." and attr(h, "name") == "Near":
                continue
            if par.startswith("Points/") or par == "Points" or par.startswith("Near"):
                continue
            if par == "" :
                root_node = b
            else:
                keep_nodes.append(b)
else:
    scene_header = "[gd_scene format=3]"
    keep_ext.append(f'[ext_resource type="PackedScene" path="{BASE}" id="1"]')
    root_node = f'[node name="{name}3D" instance=ExtResource("1")]'

# 根節點：沿用 2D 的區域設定
rlines = [l for l in root_node.split("\n") if not re.match(r'(' + "|".join(ROOT_EXPORTS) + r') = ', l)]
for k in ROOT_EXPORTS:
    if k in root_props:
        rlines.append(f"{k} = {root_props[k]}")
root_node = "\n".join(rlines)

# 只留下仍被用到的 ext／sub resource
body_text = "\n".join([root_node] + keep_nodes)
keep_ext = [b for b in keep_ext if f'ExtResource("{attr(header(b), "id")}")' in body_text + "\n".join(keep_sub)]
keep_sub = [b for b in keep_sub if f'SubResource("{attr(header(b), "id")}")' in body_text + "\n".join(keep_sub)]
existing_paths = {attr(header(b), "path"): attr(header(b), "id") for b in keep_ext}
new_ext = []
gen_text = "\n".join(out_nodes)
for path, (typ, eid) in ext3.items():
    if path in existing_paths:
        gen_text = gen_text.replace(f'ExtResource("{eid}")', f'ExtResource("{existing_paths[path]}")')
    else:
        new_ext.append(f'[ext_resource type="{typ}" path="{path}" id="{eid}"]')

parts = [re.sub(r' load_steps=\d+', "", scene_header), "\n".join(keep_ext + new_ext)]
parts += [b.strip() for b in keep_sub] + [s.strip() for s in sub3]
parts.append(root_node.strip())
parts += [b.strip() for b in keep_nodes]
if has_near:
    parts.append('[node name="Near" type="Node3D" parent="."]')
parts.append(gen_text.replace("\n[node", "\n\n[node").strip())
open(dst_path, "w", encoding="utf-8").write("\n\n".join(p for p in parts if p) + "\n")

# ---- 像素圖的 .import：無損、無 mipmap、關閉 3D 偵測 ----
fixed = []
for path in sorted(t for t in textures_3d if t):
    imp = root + "/" + path.replace("res://", "") + ".import"
    t = open(imp, encoding="utf-8").read()
    t2 = re.sub(r'compress/mode=\d', "compress/mode=0", t)
    t2 = re.sub(r'mipmaps/generate=\w+', "mipmaps/generate=false", t2)
    t2 = re.sub(r'detect_3d/compress_to=\d', "detect_3d/compress_to=0", t2)
    if t2 != t:
        open(imp, "w", encoding="utf-8").write(t2)
        fixed.append(os.path.basename(path))

print(f"寫入 {dst_path}：{len(out_nodes)} 個節點、{len(ext3)} 個外部資源、{len(sub3)} 個形狀")
if fixed:
    print("改了匯入設定：" + "、".join(fixed))
for w in warnings:
    print("⚠ " + w)
