# B3-3b 設施走廊的模型（在 Blender 裡執行：exec(open(這個檔案).read())，再呼叫 build_all() 或單一個 build_xxx()）。
# 共用的 MB 類別、G()、R() 和診所（art/models/clinic/build_clinic.py）相同；這裡加了沒有貼圖的發光材質（警報燈、出口外的光）與會發光的螢幕。
# 座標：結構 shell 直接用區域的座標（Godot 的 x、y、z，用 G() 換成 Blender：Y＝負的 Godot z、Z 朝上）；
# 家具、小物的原點在自己的底部中心（Blender 座標，-y 那面朝鏡頭），到 Godot 再擺位置（PLACE）。貼圖 32 像素＝1 m。
import bpy, bmesh, math
from mathutils import Vector, Matrix

ROOT = "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/"
T = ROOT + "assets/textures/"
# 材質名稱 → (貼圖, 透明, 雙面)
TEX = {
    "M_WallLab": ("lab/wall_lab.png", False, False), "M_FloorLab": ("lab/floor_lab.png", False, False),
    "M_WindowLab": ("lab/window_lab.png", True, True), "M_Monitor": ("lab/monitor.png", False, False),
    "M_Jars": ("lab/jars.png", False, False), "M_Crate": ("lab/crate.png", False, False),
    "M_FileCab": ("lab/filecab.png", False, False), "M_Folders": ("lab/folders.png", True, False),
    "M_Vent": ("lab/vent.png", False, False), "M_DoorMetal": ("lab/door_metal.png", False, True),
    "M_Soot": ("lab/soot.png", True, False), "M_Ceiling": ("clinic/ceiling.png", False, False),
    "M_Metal": ("common/metal.png", False, False), "M_Glass": ("common/glass.png", False, False),
    "M_Burnt": ("common/burnt.png", False, False), "M_Cloth": ("common/cloth.png", False, False),
    "M_Paper": ("common/paper.png", False, False), "M_Sign": ("lab/exit_sign.png", False, False),
    "M_Wood": ("common/wood.png", False, False),
}
GLOW = {"M_Alarm": (1.0, 0.12, 0.08, 1), "M_Glow": (1.0, 0.92, 0.7, 1)}
SOLID = {"M_Dark": (0.02, 0.02, 0.018, 1), "M_Cable": (0.06, 0.06, 0.06, 1)}
EMIT_TEX = {"M_Monitor": 1.5}

def G(x, y, z):
    """Godot 的座標 → Blender"""
    return (x, -z, y)


def mat(name):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = 0.85
    if name in GLOW:                                       # 沒有貼圖、會發光的（警報燈、出口外的光）
        c = GLOW[name]
        b.inputs["Base Color"].default_value = c
        b.inputs["Emission Color"].default_value = c
        b.inputs["Emission Strength"].default_value = 2.0
        return m
    if name in SOLID:                                      # 沒有貼圖的單色（洞、電線）
        b.inputs["Base Color"].default_value = SOLID[name]
        return m
    path, alpha, double = TEX[name]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(T + path, check_existing=True)
    t.interpolation = 'Closest'
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if name in EMIT_TEX:                                   # 螢幕：貼圖同時當發光
        nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = EMIT_TEX[name]
    if alpha:                                              # 透明度先四捨五入，glTF 才會匯出成 MASK（Godot 的 alpha scissor），不是 BLEND
        rnd = nt.nodes.new("ShaderNodeMath")
        rnd.operation = 'ROUND'
        nt.links.new(t.outputs["Alpha"], rnd.inputs[0])
        nt.links.new(rnd.outputs[0], b.inputs["Alpha"])
        try:
            m.blend_method = 'CLIP'
        except Exception:
            pass
        m.surface_render_method = 'DITHERED'
    m.use_backface_culling = not double
    return m


def texsize(name):
    path = TEX[name][0]
    img = bpy.data.images.load(T + path, check_existing=True)
    return img.size[0], img.size[1]


def tile_uv(p, n, size):
    su, sv = size if isinstance(size, tuple) else (size, size)
    ax = max(range(3), key=lambda i: abs(n[i]))
    if ax == 2:
        return (p[0] / su, p[1] / sv)
    if ax == 1:
        return (p[0] / su, p[2] / sv)
    return (p[1] / su, p[2] / sv)


class MB:
    """組一個網格：每個面有自己的材質與 UV"""

    def __init__(self, name):
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.mats = []

    def mi(self, mname):
        if mname not in self.mats:
            self.mats.append(mname)
        return self.mats.index(mname)

    def face(self, pts, mname, uvs=None, tile=1.0, inside=None):
        """inside：一個在物體裡面的點，法線朝向它時把面反過來（圓柱、斜的柱子用）"""
        if inside is not None:
            c = sum((Vector(p) for p in pts), Vector()) / len(pts)
            n = (Vector(pts[1]) - Vector(pts[0])).cross(Vector(pts[-1]) - Vector(pts[0]))
            if n.dot(c - Vector(inside)) < 0:
                pts = list(reversed(pts))
                uvs = list(reversed(uvs)) if uvs else None
        vs = [self.bm.verts.new(p) for p in pts]
        f = self.bm.faces.new(vs)
        f.material_index = self.mi(mname)
        f.normal_update()
        if uvs is None:
            uvs = [tile_uv(p, f.normal, tile) for p in pts]
        for lp, uv in zip(f.loops, uvs):
            lp[self.uv].uv = uv
        return f

    def quad(self, bl, br, tr, tl, mname, px=None, tile=1.0):
        """px＝貼圖上的像素範圍 (x0, y0, x1, y1)（y 往下），整張貼圖用 'all'；沒給就照世界座標重複鋪"""
        if px is None:
            return self.face([bl, br, tr, tl], mname, tile=tile)
        w, h = texsize(mname)
        x0, y0, x1, y1 = (0, 0, w, h) if px == "all" else px
        uvs = [(x0 / w, 1 - y1 / h), (x1 / w, 1 - y1 / h), (x1 / w, 1 - y0 / h), (x0 / w, 1 - y0 / h)]
        return self.face([bl, br, tr, tl], mname, uvs=uvs)

    def gquad(self, bl, br, tr, tl, mname, px=None, tile=1.0):
        return self.quad(G(*bl), G(*br), G(*tr), G(*tl), mname, px, tile)

    def stain(self, cx, cy, z, rx, ry, mname="M_Blood", seg=14, seed=0):
        """地上（朝上）的一灘血：不規則的橢圓多邊形，UV 只取 blood.png 中間的橢圓（貼圖四角是深紅的底色，不能整張貼）"""
        pts, uvs = [], []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            k = 0.75 + 0.25 * abs(math.sin(a * 3 + seed) * math.cos(a * 2 + seed * 1.7))
            pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k, z))
            uvs.append((0.5 + math.cos(a) * 0.34 * k, 0.5 + math.sin(a) * 0.32 * k))
        return self.face(pts, mname, uvs=uvs)

    def box(self, x0, x1, y0, y1, z0, z1, mname, tile=1.0, fit=None, skip=()):
        """Blender 座標的方塊；fit＝{面: (材質, 像素範圍)} 給要貼整張圖的面（'-y' 是朝鏡頭的那面）"""
        F = {"-y": ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)),
             "+y": ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)),
             "+x": ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)),
             "-x": ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)),
             "+z": ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)),
             "-z": ((x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0))}
        for k, pts in F.items():
            if k in skip:
                continue
            if fit and k in fit:
                self.quad(*pts, fit[k][0], fit[k][1])
            else:
                self.quad(*pts, mname, tile=tile)

    def cbox(self, cx, cy, w, d, z0, z1, mname, **kw):
        self.box(cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0, z1, mname, **kw)

    def cyl(self, c, axis, r, length, mname, seg=10, tile=0.5, cap=None):
        """圓柱：c 中心、axis 'X'/'Y'/'Z'；cap＝兩端的材質（預設和側面相同）"""
        cap = cap or mname
        rot = {"Z": Matrix.Identity(3), "X": Matrix.Rotation(math.pi / 2, 3, 'Y'), "Y": Matrix.Rotation(math.pi / 2, 3, 'X')}[axis]
        ring = []
        for s in (-0.5, 0.5):
            ring.append([Vector(c) + rot @ Vector((r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg), s * length))
                         for i in range(seg)])
        for i in range(seg):
            j = (i + 1) % seg
            self.face([ring[0][i], ring[0][j], ring[1][j], ring[1][i]], mname, tile=tile, inside=c)
        self.face(ring[0], cap, tile=tile, inside=c)
        self.face(ring[1], cap, tile=tile, inside=c)

    def beam(self, p0, p1, w, mname, tile=0.5):
        """兩點之間的方柱（寬 w）：斜的管子、腳、桿子"""
        p0, p1 = Vector(p0), Vector(p1)
        d = (p1 - p0).normalized()
        up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
        u = d.cross(up).normalized() * w / 2
        v = d.cross(u).normalized() * w / 2
        c0 = [p0 + u + v, p0 - u + v, p0 - u - v, p0 + u - v]
        c1 = [p1 + u + v, p1 - u + v, p1 - u - v, p1 + u - v]
        mid = (p0 + p1) / 2
        for i in range(4):
            j = (i + 1) % 4
            self.face([c0[i], c0[j], c1[j], c1[i]], mname, tile=tile, inside=mid)
        self.face(c0, mname, tile=tile, inside=mid)
        self.face(c1, mname, tile=tile, inside=mid)

    def mark(self):
        return len(self.bm.verts)

    def xform(self, start, M):
        """把 start 之後新增的頂點套用 4×4 矩陣（旋轉、移動一組零件）"""
        self.bm.verts.ensure_lookup_table()
        for v in self.bm.verts[start:]:
            v.co = M @ v.co

    def finish(self, recalc=False):
        if recalc:
            bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.get(self.name) or bpy.data.meshes.new(self.name)
        me.materials.clear()                              # 先清材質槽再寫入網格（清材質會把面的材質編號歸零）
        for mname in self.mats:
            me.materials.append(mat(mname))
        self.bm.to_mesh(me)
        self.bm.free()
        ob = bpy.data.objects.get(self.name)
        if not ob:
            ob = bpy.data.objects.new(self.name, me)
            bpy.context.scene.collection.objects.link(ob)
        ob.data = me
        print(self.name, "面數", len(me.polygons), tuple(round(v, 2) for v in ob.dimensions))
        return ob


def R(axis, deg, at=(0, 0, 0)):
    """繞 at 點旋轉的 4×4 矩陣"""
    at = Vector(at)
    return Matrix.Translation(at) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-at)


# ======================= 結構：地板、後牆（觀察窗、起火的門口、出口）、天花板與管線、後面的實驗室 =======================
WALL_Z, DEPTH, H = -3.6, 0.2, 3.0
ROOM_Z = -7.0
OPENINGS = [  # (x0, x1, 下緣, 上緣, 種類)
    (1.0, 3.0, 1.0, 2.2, "window"), (6.6, 7.8, 0.0, 2.1, "firedoor"), (8.4, 10.4, 1.0, 2.2, "window"),
    (14.0, 16.0, 1.0, 2.2, "window"), (19.6, 21.6, 1.0, 2.2, "window"), (27.4, 29.4, 1.0, 2.2, "window"),
    (33.0, 34.4, 0.0, 2.1, "exit")]
ROOMS = [0.0, 6.2, 13.0, 19.0, 26.6, 32.0, 36.0]          # 後面的實驗室用隔牆分成幾間
FIRE_ROOM = (6.2, 13.0)                                     # 起火的那一間
EXIT_ROOM = (32.0, 36.0)                                    # 出口外的通道（盡頭是外面的光）


def floor_decal(mb, pts, mname, uvs):
    """地上的貼花（朝上）：pts 是 Godot 座標"""
    c = sum((Vector(G(*p)) for p in pts), Vector()) / len(pts)
    mb.face([G(*p) for p in pts], mname, uvs=uvs, inside=(c.x, c.y, c.z - 1))


def build_shell():
    mb = MB("shell")
    WT = (2.0, 3.0)
    z, zb = WALL_Z, WALL_Z - DEPTH
    # 走廊的地板、天花板（掉了幾片：黑洞＋垂下來的一片）
    mb.gquad((-0.4, 0, 4.2), (36.4, 0, 4.2), (36.4, 0, z), (-0.4, 0, z), "M_FloorLab", tile=1.0)
    mb.gquad((-0.4, H, z), (36.4, H, z), (36.4, H, 4.2), (-0.4, H, 4.2), "M_Ceiling", tile=2.0)
    for hx, hz in ((4.5, -0.5), (9.0, 1.0), (17.5, -1.5), (20.5, 0.0), (29.0, -1.0)):
        mb.gquad((hx, H - 0.01, hz), (hx + 0.5, H - 0.01, hz), (hx + 0.5, H - 0.01, hz + 0.5), (hx, H - 0.01, hz + 0.5), "M_Dark")
    for hx, hz, ang in ((9.0, 1.0, 50), (20.5, 0.0, 30)):
        a = math.radians(ang)
        lo, lz = H - 0.02 - 0.5 * math.sin(a), hz + 0.5 - 0.5 * math.cos(a)
        mb.gquad((hx, lo, lz), (hx + 0.5, lo, lz), (hx + 0.5, H - 0.02, hz + 0.5), (hx, H - 0.02, hz + 0.5), "M_Ceiling", px=(16, 16, 32, 32))
    # 後牆（避開開口）
    cuts = sorted({0.0, 36.0} | {o[0] for o in OPENINGS} | {o[1] for o in OPENINGS})
    for a, b in zip(cuts, cuts[1:]):
        op = next((o for o in OPENINGS if o[0] <= a and b <= o[1]), None)
        spans = [(0.0, H)] if op is None else [(0.0, op[2]), (op[3], H)]
        for y0, y1 in spans:
            if y1 - y0 > 0.001:
                mb.gquad((a, y0, z), (b, y0, z), (b, y1, z), (a, y1, z), "M_WallLab", tile=WT)
    for x0, x1, y0, y1, kind in OPENINGS:                  # 開口的側面、上緣、窗台
        mb.gquad((x0, y0, z), (x0, y0, zb), (x0, y1, zb), (x0, y1, z), "M_WallLab", tile=WT)
        mb.gquad((x1, y0, zb), (x1, y0, z), (x1, y1, z), (x1, y1, zb), "M_WallLab", tile=WT)
        mb.gquad((x0, y1, z), (x1, y1, z), (x1, y1, zb), (x0, y1, zb), "M_WallLab", tile=WT)
        if y0 > 0:
            mb.gquad((x0, y0, z), (x1, y0, z), (x1, y0, zb), (x0, y0, zb), "M_Metal", tile=0.5)
            p0, p1 = G(x0 - 0.05, y0 - 0.04, z + 0.06), G(x1 + 0.05, y0, z)
            mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], "M_Metal", skip=("+y",))
        if kind == "window":
            mb.gquad((x0, y0, z - 0.1), (x1, y0, z - 0.1), (x1, y1, z - 0.1), (x0, y1, z - 0.1), "M_WindowLab", px="all")
        else:                                              # 門框（金屬，凸出牆面 3 cm）
            for bx0, bx1, by0, by1 in ((x0 - 0.08, x0, 0, y1), (x1, x1 + 0.08, 0, y1), (x0 - 0.08, x1 + 0.08, y1, y1 + 0.08)):
                p0, p1 = G(bx0, by0, z + 0.03), G(bx1, by1, z)
                mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], "M_Metal", skip=("+y", "-z"))
    # 出口的鐵門：被撞開，往外面開了 70°（門軸在右邊）
    a = math.radians(70)
    hx, hz = 34.4, zb
    ex, ez = hx - math.cos(a) * 1.4, hz - math.sin(a) * 1.4
    mb.gquad((ex, 0, ez), (hx, 0, hz), (hx, 2.08, hz), (ex, 2.08, ez), "M_DoorMetal", px="all")
    a, b = G(33.35, 2.25, z + 0.08), G(34.05, 2.5, z)      # 出口牌
    mb.box(a[0], b[0], a[1], b[1], a[2], b[2], "M_Metal", fit={"-y": ("M_Sign", "all")})
    # 左右牆
    mb.gquad((0.0, 0, 4.2), (0.0, 0, z), (0.0, H, z), (0.0, H, 4.2), "M_WallLab", tile=WT)
    mb.gquad((36.0, 0, z), (36.0, 0, 4.2), (36.0, H, 4.2), (36.0, H, z), "M_WallLab", tile=WT)
    # 燒焦的痕跡（起火的門口上面、旁邊的窗戶上面）
    mb.gquad((6.2, 0.9, z + 0.01), (8.2, 0.9, z + 0.01), (8.2, 2.9, z + 0.01), (6.2, 2.9, z + 0.01), "M_Soot", px="all")
    mb.gquad((8.4, 2.2, z + 0.01), (10.4, 2.2, z + 0.01), (10.4, 3.0, z + 0.01), (8.4, 3.0, z + 0.01), "M_Soot", px=(0, 6, 64, 32))   # 只貼在窗戶上面的牆（開口前面懸空會擋住窗戶）
    # 通風管口（24.1 進去、30.5 出來；出來的那個格柵掉在地上）
    mb.gquad((23.77, 0.05, z + 0.02), (24.52, 0.05, z + 0.02), (24.52, 0.8, z + 0.02), (23.77, 0.8, z + 0.02), "M_Vent", px="all")
    mb.gquad((30.1, 0.05, z + 0.005), (30.85, 0.05, z + 0.005), (30.85, 0.8, z + 0.005), (30.1, 0.8, z + 0.005), "M_Dark")
    for bx0, bx1, by0, by1 in ((30.04, 30.1, 0.0, 0.86), (30.85, 30.91, 0.0, 0.86), (30.04, 30.91, 0.8, 0.86)):
        p0, p1 = G(bx0, by0, z + 0.03), G(bx1, by1, z)
        mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], "M_Metal", skip=("+y", "-z"))
    floor_decal(mb, [(29.95, 0.02, -2.75), (30.7, 0.02, -2.6), (30.75, 0.02, -3.35), (30.0, 0.02, -3.5)], "M_Vent",
                [(0, 0), (1, 0), (1, 1), (0, 1)])
    # 管線（沿著後牆上面）與支架
    mb.cyl(G(18.0, 2.75, -3.35), 'X', 0.08, 36.0, "M_Metal", seg=8, tile=1.0)
    mb.cyl(G(18.0, 2.52, -3.45), 'X', 0.05, 36.0, "M_Metal", seg=6, tile=1.0)
    mb.cyl(G(18.0, 2.85, -2.95), 'X', 0.06, 36.0, "M_Metal", seg=6, tile=1.0)
    for x in range(2, 36, 3):
        p0, p1 = G(x - 0.03, 2.4, -3.0), G(x + 0.03, 2.9, z)
        mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], "M_Metal")
    # 後面的實驗室：地板、天花板、後牆、隔牆（起火的那間是焦黑的；出口外是通道，盡頭是外面的光）
    for a, b in zip(ROOMS, ROOMS[1:]):
        fire = (a, b) == FIRE_ROOM
        fl = "M_Burnt" if fire else "M_FloorLab"
        wl = "M_Burnt" if fire else "M_WallLab"
        mb.gquad((a, 0, zb), (b, 0, zb), (b, 0, ROOM_Z), (a, 0, ROOM_Z), fl, tile=1.0)
        mb.gquad((a, H, ROOM_Z), (b, H, ROOM_Z), (b, H, zb), (a, H, zb), "M_Burnt" if fire else "M_Ceiling", tile=2.0)
        if (a, b) == EXIT_ROOM:
            mb.gquad((a, 0, ROOM_Z), (32.6, 0, ROOM_Z), (32.6, H, ROOM_Z), (a, H, ROOM_Z), wl, tile=WT)
            mb.gquad((35.4, 0, ROOM_Z), (b, 0, ROOM_Z), (b, H, ROOM_Z), (35.4, H, ROOM_Z), wl, tile=WT)
            mb.gquad((32.6, 2.6, ROOM_Z), (35.4, 2.6, ROOM_Z), (35.4, H, ROOM_Z), (32.6, H, ROOM_Z), wl, tile=WT)
            mb.gquad((32.6, 0, ROOM_Z - 0.3), (35.4, 0, ROOM_Z - 0.3), (35.4, 2.6, ROOM_Z - 0.3), (32.6, 2.6, ROOM_Z - 0.3), "M_Glow")
        else:
            mb.gquad((a, 0, ROOM_Z), (b, 0, ROOM_Z), (b, H, ROOM_Z), (a, H, ROOM_Z), wl, tile=WT)
        mb.gquad((a, 0, ROOM_Z), (a, 0, zb), (a, H, zb), (a, H, ROOM_Z), wl, tile=WT)             # 左邊的隔牆（面朝右）
        mb.gquad((b, 0, zb), (b, 0, ROOM_Z), (b, H, ROOM_Z), (b, H, zb), wl, tile=WT)             # 右邊的隔牆（面朝左）
    mb.gquad((8.0, 0.8, ROOM_Z + 0.01), (11.0, 0.8, ROOM_Z + 0.01), (11.0, 3.0, ROOM_Z + 0.01), (8.0, 3.0, ROOM_Z + 0.01), "M_Soot", px="all")
    return mb.finish()


# ======================= 家具、道具（原點在底部中心；-y 那面朝鏡頭） =======================
def build_rack():
    """實驗架：金屬的四根柱子、五層板子，三層放滿瓶罐（正面是 jars 貼圖）"""
    mb = MB("rack")
    W, D, Hr = 0.6, 0.22, 1.9
    for x in (-W, W):
        for y in (-D, D):
            mb.beam((x, y, 0), (x, y, Hr), 0.04, "M_Metal")
    for k, zz in enumerate((0.08, 0.53, 0.98, 1.43, 1.88)):
        mb.box(-W, W, -D, D, zz, zz + 0.02, "M_Metal")
        if k < 3:                                          # 瓶罐：每層的正面（左右翻過來，看起來不重複）
            u0, u1 = (0, 32) if k % 2 == 0 else (32, 0)
            mb.quad((-W + 0.03, -0.05, zz + 0.02), (W - 0.03, -0.05, zz + 0.02), (W - 0.03, -0.05, zz + 0.45), (-W + 0.03, -0.05, zz + 0.45),
                    "M_Jars", px=(u0, 0, u1, 16))
    mb.quad((W, D, 0), (-W, D, 0), (-W, D, Hr), (W, D, Hr), "M_Metal", tile=0.5)
    for (x, y, ang) in ((0.25, -0.12, 70), (-0.3, -0.1, -80)):            # 倒在最上層的瓶子
        m = mb.mark()
        mb.cyl((x, y, 1.45), 'X', 0.04, 0.16, "M_Glass", seg=6)
        mb.xform(m, R('Z', ang, (x, y, 1.45)))
    return mb.finish()


def build_alarm():
    """警報燈：原點在牆面上的固定點；金屬底座＋紅色燈罩（第 2 個材質，熄滅時換暗）"""
    mb = MB("alarm")
    mb.box(-0.15, 0.15, -0.1, 0.0, -0.08, 0.08, "M_Metal")
    mb.cyl((0, -0.15, 0), 'Y', 0.09, 0.1, "M_Alarm", seg=10)
    mb.box(-0.1, 0.1, -0.21, -0.19, -0.1, -0.08, "M_Metal")
    return mb.finish()


def build_cart():
    """推車（掩護）：不鏽鋼推車兩層、輪子，上面一台儀器（螢幕）和一塊垂下來的布"""
    mb = MB("cart")
    W, D = 0.65, 0.3
    for x in (-W + 0.03, W - 0.03):
        for y in (-D + 0.03, D - 0.03):
            mb.beam((x, y, 0.08), (x, y, 0.95), 0.035, "M_Metal")
            mb.cyl((x, y, 0.04), 'X', 0.04, 0.03, "M_Cable", seg=6)
    for zz in (0.3, 0.92):
        mb.box(-W, W, -D, D, zz, zz + 0.03, "M_Metal")
    mb.box(-0.5, 0.05, -0.2, 0.2, 0.95, 1.3, "M_Metal", fit={"-y": ("M_Monitor", "all")})
    mb.box(0.15, 0.55, -0.25, 0.15, 0.95, 1.05, "M_Metal")
    mb.box(-0.4, 0.2, -0.22, 0.2, 0.33, 0.55, "M_Metal")                  # 下層的箱子
    mb.quad((0.1, -D - 0.01, 0.55), (0.62, -D - 0.01, 0.6), (0.62, -D - 0.01, 0.97), (0.1, -D - 0.01, 0.97), "M_Cloth", tile=0.5)
    mb.quad((0.1, -D - 0.01, 0.97), (0.62, -D - 0.01, 0.97), (0.62, 0.0, 0.97), (0.1, 0.0, 0.97), "M_Cloth", tile=0.5)
    return mb.finish()


def build_crates():
    """木箱（掩護）：兩個並排、一個疊在上面（歪的）"""
    mb = MB("crates")
    m = mb.mark()
    mb.box(-0.75, 0.05, -0.4, 0.4, 0.0, 0.8, "M_Crate", fit={"-y": ("M_Crate", (0, 0, 26, 26))})
    m = mb.mark()
    mb.box(0.1, 0.8, -0.35, 0.35, 0.0, 0.7, "M_Crate", fit={"-y": ("M_Crate", (0, 0, 23, 23))})
    mb.xform(m, R('Z', 6, (0.45, 0, 0)))
    m = mb.mark()
    mb.box(-0.6, 0.0, -0.3, 0.3, 0.8, 1.4, "M_Crate", fit={"-y": ("M_Crate", (0, 0, 19, 19))})
    mb.xform(m, R('Z', -10, (-0.3, 0, 0)))
    return mb.finish()


def build_records():
    """實驗紀錄：靠牆的檔案櫃（最上面的抽屜拉出來）、旁邊倒下的一個、地上散落的紀錄"""
    mb = MB("records")
    mb.box(-0.85, -0.35, -0.3, 0.3, 0.0, 1.3, "M_Metal", fit={"-y": ("M_FileCab", "all")})
    mb.box(-0.83, -0.37, -0.62, -0.3, 1.0, 1.24, "M_Metal")
    mb.quad((-0.8, -0.6, 1.2), (-0.4, -0.6, 1.2), (-0.4, -0.32, 1.2), (-0.8, -0.32, 1.2), "M_Folders", px=(0, 0, 16, 10))
    # 倒下的檔案櫃：側躺，抽屜那面朝鏡頭（貼圖轉 90°）
    m = mb.mark()
    x0, x1, y0, y1, z0, z1 = -0.2, 1.1, -0.3, 0.3, 0.0, 0.5
    mb.box(x0, x1, y0, y1, z0, z1, "M_Metal", skip=("-y",))
    mb.face([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], "M_FileCab", uvs=[(1, 0), (1, 1), (0, 1), (0, 0)])
    mb.box(0.85, 1.1, -0.65, -0.3, 0.05, 0.45, "M_Metal")                  # 掉出來一半的抽屜
    mb.xform(m, R('Z', 12, (0.45, 0, 0)))
    for pts, uv in (([(-0.7, -1.05, 0.01), (0.3, -1.05, 0.01), (0.3, -0.55, 0.01), (-0.7, -0.55, 0.01)], (0, 0, 32, 16)),
                    ([(0.2, -1.15, 0.012), (1.1, -1.0, 0.012), (1.05, -0.6, 0.012), (0.15, -0.75, 0.012)], (32, 0, 0, 16))):
        x0p, y0p, x1p, y1p = uv
        uvs = [(x0p / 32, 1 - y1p / 16), (x1p / 32, 1 - y1p / 16), (x1p / 32, 1 - y0p / 16), (x0p / 32, 1 - y0p / 16)]
        mb.face(pts, "M_Folders", uvs=uvs, inside=(0, -0.8, -1))
    return mb.finish()


def build_lab_bench(burnt=False):
    """實驗桌（後面的實驗室）：桌面、兩邊的櫃子、螢幕、燒杯、紙；burnt＝起火那間（焦黑、螢幕壞了）"""
    mb = MB("bench_burnt" if burnt else "lab_bench")
    M = "M_Burnt" if burnt else "M_Metal"
    mb.box(-0.9, 0.9, -0.35, 0.35, 0.86, 0.9, M)
    for x0, x1 in ((-0.88, -0.3), (0.3, 0.88)):
        mb.box(x0, x1, -0.33, 0.33, 0.0, 0.86, M)
    mb.beam((-0.4, 0.15, 0.9), (-0.4, 0.15, 1.0), 0.04, M)
    mb.box(-0.65, -0.15, 0.05, 0.11, 0.98, 1.35, M, fit={"-y": ("M_Dark", None) if burnt else ("M_Monitor", "all")})
    if not burnt:
        for i, (x, y, hh) in enumerate(((0.2, -0.1, 0.16), (0.32, 0.05, 0.12), (0.45, -0.15, 0.2))):
            mb.cyl((x, y, 0.9 + hh / 2), 'Z', 0.04, hh, "M_Glass", seg=6)
        mb.quad((0.05, -0.3, 0.905), (0.4, -0.3, 0.905), (0.4, -0.05, 0.905), (0.05, -0.05, 0.905), "M_Paper", tile=0.5)
    else:
        m = mb.mark()
        mb.box(-0.3, 0.3, -0.2, 0.2, 0.0, 0.04, "M_Burnt")                # 掉在地上燒焦的板子
        mb.xform(m, R('Z', 25) @ Matrix.Translation((0.6, -0.7, 0)))
    return mb.finish()


def build_bench_burnt():
    return build_lab_bench(burnt=True)


def build_hanging_cable():
    """從天花板垂下來的電線（前景）：原點在天花板的固定點；兩條，末端斷開"""
    mb = MB("hanging_cable")
    for pts, w in (([(0, 0, 0), (0.04, 0, -0.35), (0.12, 0.02, -0.75), (0.1, 0.03, -1.05), (0.18, 0.02, -1.35)], 0.03),
                   ([(0.15, 0.05, 0), (0.18, 0.05, -0.3), (0.28, 0.06, -0.55), (0.32, 0.06, -0.7)], 0.022)):
        for a, b in zip(pts, pts[1:]):
            mb.beam(a, b, w, "M_Cable")
        e = Vector(pts[-1])
        for d in ((0.03, 0, -0.05), (-0.02, 0.01, -0.06), (0.0, -0.02, -0.05)):   # 斷開的銅線
            mb.beam(e, e + Vector(d), 0.008, "M_Metal")
    return mb.finish()


def build_floor_cable():
    """地上的電線（前景）：彎彎曲曲的一條"""
    mb = MB("floor_cable")
    pts = [(-0.8 + 0.2 * i, 0.12 * math.sin(i * 1.3), 0.015) for i in range(9)]
    for a, b in zip(pts, pts[1:]):
        mb.beam(a, b, 0.03, "M_Cable")
    return mb.finish()


def build_vials():
    """地上的藥瓶（前景）：三支倒下的小瓶子"""
    mb = MB("vials")
    for (x, y, ang) in ((-0.15, 0.0, 20), (0.05, -0.08, -35), (0.2, 0.06, 80)):
        m = mb.mark()
        mb.cyl((x, y, 0.025), 'X', 0.025, 0.12, "M_Glass", seg=6)
        mb.cyl((x + 0.07, y, 0.025), 'X', 0.02, 0.02, "M_Metal", seg=6)
        mb.xform(m, R('Z', ang, (x, y, 0)))
    return mb.finish()


def build_all():
    for fn in BUILDERS:
        fn()


BUILDERS = [build_shell, build_rack, build_alarm, build_cart, build_crates, build_records, build_lab_bench, build_bench_burnt,
            build_hanging_cable, build_floor_cable, build_vials]


# ======================= B3-3b 預覽時的擺放位置（Godot 座標 x, y, z, 繞 y 軸轉幾度；B3-3c 照這份放進 Lab3D） =======================
# 推車、木箱、檔案櫃放在互動點 CartHide、Crates、Records 的位置；地上的碎玻璃、病歷夾、舊報紙用共用模型（common/glass_shards、clinic/clipboard、common/papers）。
PLACE = {
    "rack": [(5.2, 0, -3.35, 0), (11.8, 0, -3.35, 0), (25.6, 0, -3.35, 0)],
    "alarm": [(3.75, 2.5, -3.6, 0), (16.9, 2.5, -3.6, 0), (26.6, 2.5, -3.6, 0)],
    "cart": [(14.84, 0, 0.26, 0)], "crates": [(22.66, 0, 0.26, 0)], "records": [(17.97, 0, -3.25, 0)],
    "lab_bench": [(2.0, 0, -5.3, 0), (15.0, 0, -5.4, 0), (20.6, 0, -5.0, 0), (28.4, 0, -5.3, 0)],
    "bench_burnt": [(9.4, 0, -5.2, 0)],
    "hanging_cable": [(13.0, 3.0, 3.1, 0), (31.5, 3.0, 3.1, 0)],
    "floor_cable": [(9.4, 0, 2.3, 0)], "vials": [(5.2, 0, 2.3, 0), (32.0, 0, 2.3, 30)],
}
