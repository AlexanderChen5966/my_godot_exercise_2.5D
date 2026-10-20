# B1：把 2D 區域場景的互動點（Points）與近景（Near）轉成 3D 區域場景的初稿，之後再用 Toolkit 檢查與修改。
# 用法：python3 convert_area_3d.py 專案根目錄 區域名稱（例如 ParkingLot）[--lights]
#   讀 scenes/areas/<名稱>.tscn，寫入 scenes/areas3d/<名稱>3D.tscn（沒有就建立，繼承 AreaBase3D）。
#   3D 場景裡 Points／Near 底下的節點每次都重新產生（手動加在那裡的會被蓋掉）；Lights、Geometry 等其他節點保留。
#   區域的燈只在第一次產生；加 --lights 時重新產生（會蓋掉用 Toolkit 調整過的燈）。
#   同一個點底下的圖照 2D 的節點順序（後面的畫在上面）往前錯開 0.01 公尺，避免同一個深度時前後順序不固定。
# 換算（和 area_3d.gd 相同）：x 64 像素＝1 公尺；縱深帶 walk_top～walk_bottom ↔ z −depth/2～＋depth/2（縱深帶外的 y 照比例延伸）；
#   像素的往上（y 變小）＝3D 的往上；放大 2 倍的像素圖 ＝ pixel_size 1/32。
# 對應：Area2D（interact_point.gd）→ Area3D（interact_point_3d.gd）；RectangleShape2D → BoxShape3D（高 2 公尺）；
#   Sprite2D → Sprite3D；AnimatedSprite2D → AnimatedSprite3D（SpriteFrames 換成 *_frames_3d.tres）；
#   AudioStreamPlayer2D → AudioStreamPlayer3D；StaticBody2D → StaticBody3D；LightOccluder2D 略過（3D 有真的陰影）。
#   用在 3D 的像素圖會把 .import 改成無損、不產生 mipmap、關閉 3D 偵測（CLAUDE.md 的 2.5D 坑①）。
import re, sys, os, subprocess

PX = 64.0
DEPTH = 3.0
BASE = "res://scenes/areas3d/AreaBase3D.tscn"
POINTS_ID = 2077837389   # AreaBase3D 的 Points 節點 unique_id
ROOT_EXPORTS = ("area_width", "player_start", "edge_margin", "walk_top", "walk_bottom")
LIGHTS_ID = 285009602    # AreaBase3D 的 Lights 節點 unique_id
# 子節點的腳本換成 3D 版，並照抄這些 export
SCRIPTS_3D = {
    "res://scripts/idle_variation.gd": ("res://scripts/idle_variation_3d.gd",
                                        ("base_animation", "variant_animation", "interval_min", "interval_max", "variant_loops")),
    "res://scripts/gun_torch.gd": ("res://scripts/gun_torch_3d.gd", ("follow", "idle_frames", "event_frame")),
    "res://scripts/flicker_light.gd": ("res://scripts/flicker_light_3d.gd",
                                       ("base_energy", "pulse_speed", "min_ratio", "dropout_chance", "dropout_ratio",
                                        "follow", "frame_strength", "off_sprite", "hum", "dropout_sound", "sound_cooldown")),
}

root, name = sys.argv[1], sys.argv[2]
regen_lights = "--lights" in sys.argv[3:]
src = open(f"{root}/scenes/areas/{name}.tscn", encoding="utf-8").read()
dst_path = f"{root}/scenes/areas3d/{name}3D.tscn"


def blocks(text):
    return re.split(r'\n(?=\[)', text.strip())


def header(b):
    return b.split("\n", 1)[0]


def props(b):
    out = {}
    key = None
    for line in b.split("\n")[1:]:
        m = re.match(r'([\w/]+) = (.*)', line)
        if m and (key is None):
            out[m.group(1)] = m.group(2)
            # 跨行的字串（例如 Label 的 text）：還沒結束就接著讀下一行
            v = m.group(2)
            if v.startswith('"') and (len(v) == 1 or not re.search(r'(?<!\\)"$', v)):
                key = m.group(1)
        elif key is not None:
            out[key] += "\n" + line
            if re.search(r'(?<!\\)"$', line):
                key = None
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
    extra = ""
    if top and parent in ("Points", "Lights"):
        extra = f' parent_id_path=PackedInt32Array({POINTS_ID if parent == "Points" else LIGHTS_ID})'

    out_nodes.append(f'[node name="{nname}" type="{typ}" parent="{parent}"{extra}]\n' + "\n".join(lines) + "\n")


def sprite_lines(p, scale):
    lines = [f"pixel_size = {f(scale / PX)}", "shaded = true", "alpha_cut = 1", "texture_filter = 0"]
    if "flip_h" in p:
        lines.append(f"flip_h = {p['flip_h']}")
    ox, oy = vec2(p.get("offset"))
    if ox or oy:
        lines.append(f"offset = Vector2({f(ox)}, {f(-oy)})")
    return lines


def script_lines(p, path_fix=None):
    """2D 的腳本換成 3D 版（沒有對應的略過）"""
    path = ext_path(p.get("script"))
    if path is None:
        return []
    if path not in SCRIPTS_3D:
        warnings.append(f"腳本 {path} 沒有 3D 版，略過")
        return []
    path3, keys = SCRIPTS_3D[path]
    lines = [f'script = ExtResource("{ext_id("Script", path3)}")']
    for k in keys:
        if k in p:
            v = p[k]
            if path_fix and v.startswith("NodePath("):
                v = path_fix(v)
            lines.append(f"{k} = {v}")
    return lines


def color(s, default="Color(1, 1, 1, 1)"):
    return s if s else default


draw_order = {}   # 3D 父節點路徑 -> 已經放了幾張圖


def layer_z(parent3):
    """2D 同一個父節點底下，後面的節點畫在上面：3D 往前（鏡頭方向）錯開 0.01 公尺"""
    i = draw_order.get(parent3, 0)
    draw_order[parent3] = i + 1
    return i * 0.01


def convert_child(n, typ, parent3, p, base_z):
    """點（或近景容器）底下的子節點；位置相對於父節點（像素 → 公尺，y 反向；z 跟父節點相同，圖照順序往前錯開）"""
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
        lines = [transform(x / PX, -y / PX, layer_z(parent3), -rot)] + sprite_lines(p, scale)
        lines.append(f'texture = ExtResource("{ext_id("Texture2D", path)}")')
        for k in ("hframes", "vframes", "frame"):
            if k in p:
                lines.append(f"{k} = {p[k]}")
        node(n, "Sprite3D", parent3, lines)
    elif typ == "AnimatedSprite2D":
        path = ext_path(p.get("sprite_frames"))
        path3 = path.replace(".tres", "_3d.tres")
        if not os.path.exists(root + "/" + path3.replace("res://", "")):
            # 沒有 3D 版：直接指向 PNG 的 SpriteFrames 可以沿用（例如燒毀的車）；指向 CanvasTexture 的會是白色方塊
            frames = open(root + "/" + path.replace("res://", ""), encoding="utf-8").read()
            if "CanvasTexture" in frames:
                warnings.append(f"{parent3}/{n}：{path} 用了 CanvasTexture，在 3D 會是白色方塊，要另做 {path3}")
            textures_3d.update(re.findall(r'\[ext_resource type="Texture2D"[^\]]*path="([^"]+)"', frames))
            path3 = path
        lines = [transform(x / PX, -y / PX, layer_z(parent3), -rot)] + sprite_lines(p, scale)
        lines.append(f'sprite_frames = ExtResource("{ext_id("SpriteFrames", path3)}")')
        for k in ("animation", "autoplay", "frame"):
            if k in p:
                lines.append(f"{k} = {p[k]}")
        node(n, "AnimatedSprite3D", parent3, lines + script_lines(p))
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
    elif typ == "PointLight2D":
        # 點底下的燈：目前只有警衛槍上的手電筒（gun_torch.gd）→ 聚光燈；判定範圍沿用 2D 的光照到的地面
        lines = [transform(x / PX, -y / PX, 0), f"light_color = {color(p.get('color'))}",
                 f"light_energy = {p.get('energy', '1.0')}", "spot_range = 6.0", "spot_angle = 25.0"]
        script = script_lines(p)
        if script:
            tex = ext_path(p.get("texture"))
            w = 400.0
            if tex:
                w = float(subprocess.run(["magick", "identify", "-format", "%w", root + "/" + tex.replace("res://", "")],
                                         capture_output=True, text=True).stdout)
            script.append(f"floor_reach_px = {f(w * float(p.get('texture_scale', 1)) * 0.65)}")
        node(n, "SpotLight3D", parent3, lines + script)
    elif typ == "Label":
        # 牆上的字 → Label3D（1 像素＝1/64 公尺，和 2D 畫面上的大小一樣）；位置是 Label 方框的中心
        l, tp, r, bt = (float(p.get(k, 0)) for k in ("offset_left", "offset_top", "offset_right", "offset_bottom"))
        lines = [transform((l + r) / 2 / PX, -(tp + bt) / 2 / PX, layer_z(parent3) + 0.02, -rot), f"pixel_size = {f(1 / PX)}",
                 f"modulate = {color(p.get('theme_override_colors/font_color'))}", "outline_size = 0", "shaded = true",
                 f"text = {p.get('text', '""')}", f"font_size = {p.get('theme_override_font_sizes/font_size', '16')}"]
        for k in ("horizontal_alignment", "vertical_alignment", "autowrap_mode"):
            if k in p:
                lines.append(f"{k} = {p[k]}")
        if "autowrap_mode" in p:
            lines.append(f"width = {f(r - l)}")
        node(n, "Label3D", parent3, lines)
    elif typ == "ColorRect":
        # 色塊 → 半透明的平面
        l, tp, r, bt = (float(p.get(k, 0)) for k in ("offset_left", "offset_top", "offset_right", "offset_bottom"))
        mesh = add_sub("QuadMesh", f"size = Vector2({f((r - l) / PX)}, {f((bt - tp) / PX)})")
        mat = add_sub("StandardMaterial3D", f"transparency = 1\nshading_mode = 0\nalbedo_color = {color(p.get('color'))}")
        node(n, "MeshInstance3D", parent3, [transform((l + r) / 2 / PX, -(tp + bt) / 2 / PX, layer_z(parent3) + 0.01),
                                            f'mesh = SubResource("{mesh}")', f'material_override = SubResource("{mat}")'])
    elif typ in ("CPUParticles2D", "GPUParticles2D"):
        warnings.append(f"{parent3}/{n}：粒子先略過（之後的光影階段再做 3D 版）")
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


def convert_lights():
    """區域的燈（根節點底下的 PointLight2D）→ OmniLight3D，放在縱深帶中間、離地 (地面線 − y) 公尺
    （放在後緣時離後面的物件太近，會照出亮斑）；跟著某個互動點的燈（例如車上的火）放在那個點前面 0.6 公尺"""
    points_y = {n: vec2(p.get("position"))[1] for n, typ, parent, p in nodes2 if parent == "Points"}
    for n, typ, parent, p in nodes2:
        if parent != "." or typ != "PointLight2D":
            continue
        x, y = vec2(p.get("position"))
        z = 0.0
        m = re.match(r'NodePath\("\.\./Points/([^/"]+)', p.get("follow", ""))
        if m and m.group(1) in points_y:
            z = y_to_z(points_y[m.group(1)]) + 0.6
        rng = float(p.get("texture_scale", 1)) * 4.0   # 2D 的光貼圖半徑 256 像素 × texture_scale ＝ 4 公尺 × texture_scale
        lines = [transform(x / PX, max((walk_top - y) / PX, 0.5), z), f"light_color = {color(p.get('color'))}",
                 f"light_energy = {p.get('base_energy', p.get('energy', '1.0'))}", f"omni_range = {f(rng)}"]
        # 2D 的燈在區域根節點底下，3D 的在 Lights 底下：路徑多一層
        node(n, "OmniLight3D", "Lights", lines + script_lines(p, lambda v: v.replace('NodePath("../', 'NodePath("../../')), top=True)


convert_tree("Points")
has_near = any(parent == "Near" for _, _, parent, _ in nodes2)
if has_near:
    convert_tree("Near")
# 燈只在第一次（3D 場景還沒有燈）時產生，之後用 Toolkit 調整的燈不會被蓋掉
if regen_lights or not (os.path.exists(dst_path) and 'parent="Lights"' in open(dst_path, encoding="utf-8").read()):
    convert_lights()

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
            if regen_lights and par == "Lights":
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
