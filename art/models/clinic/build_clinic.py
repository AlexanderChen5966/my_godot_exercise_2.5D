# B3-2b 診所的模型（在 Blender 裡執行：exec(open(這個檔案).read())，再呼叫 build_all() 或單一個 build_xxx()）。
# 座標：結構 shell 直接用區域的座標（Godot 的 x、y、z，用 G() 換成 Blender：Y＝負的 Godot z、Z 朝上）；
# 家具、小物的原點在自己的底部中心（Blender 座標），到 Godot 再擺位置。貼圖 32 像素＝1 m，UV 在建立面的時候算好。
import bpy, bmesh, math
from mathutils import Vector, Matrix

ROOT = "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/"
T = ROOT + "assets/textures/"
# 材質名稱 → (貼圖, 透明, 雙面)
TEX = {
    "M_Wall": ("clinic/wall.png", False, False), "M_FloorTile": ("clinic/floor_tile.png", False, False),
    "M_Ceiling": ("clinic/ceiling.png", False, False), "M_Curtain": ("clinic/curtain.png", False, True),
    "M_Leather": ("clinic/leather.png", False, False), "M_Window": ("clinic/window_clinic.png", False, False),
    "M_Outside": ("clinic/outside.png", False, False), "M_Door": ("clinic/door_wood.png", False, True),
    "M_Cards": ("clinic/cards.png", False, False), "M_Posters": ("clinic/posters.png", False, False),
    "M_Files": ("clinic/files.png", False, False), "M_IvyHang": ("clinic/ivy_hang.png", True, True),
    "M_IvyWall": ("clinic/ivy_wall.png", True, False), "M_Pills": ("clinic/pills.png", False, False),
    "M_Clipboard": ("clinic/clipboard.png", False, False), "M_Box": ("clinic/box.png", False, False),
    "M_Pot": ("clinic/pot.png", False, False), "M_CabPaint": ("clinic/cabinet_paint.png", False, False),
    "M_Leaves": ("common/leaves.png", True, True), "M_Metal": ("common/metal.png", False, False),
    "M_Wood": ("common/wood.png", False, False), "M_Glass": ("common/glass.png", False, False),
    "M_Tire": ("common/tire.png", False, False), "M_Cloth": ("common/cloth.png", False, False),
    "M_Blood": ("common/blood.png", False, False), "M_Paper": ("common/paper.png", False, False),
    "M_Shutter": ("street/shutter.png", False, False), "M_Sign": ("parking/sign.png", False, False),
}


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
    if name == "M_Tube":                                   # 日光燈管：沒有貼圖，發光
        b.inputs["Base Color"].default_value = (0.9, 0.95, 0.85, 1)
        b.inputs["Emission Color"].default_value = (0.9, 0.95, 0.85, 1)
        b.inputs["Emission Strength"].default_value = 2.0
        return m
    if name == "M_Dark":                                   # 天花板掉了的洞
        b.inputs["Base Color"].default_value = (0.02, 0.02, 0.018, 1)
        return m
    path, alpha, double = TEX[name]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(T + path, check_existing=True)
    t.interpolation = 'Closest'
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
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


# ======================= 結構：地板、牆、天花板、門窗、治療室 =======================
WALL_Z, DEPTH, H = -5.0, 0.2, 3.0
OPENINGS = [  # (x0, x1, 下緣, 上緣, 種類)
    (0.2, 2.4, 0.0, 2.6, "entrance"), (4.2, 6.2, 1.0, 2.4, "window"), (12.6, 14.6, 1.0, 2.4, "window"),
    (19.8, 20.8, 0.0, 2.1, "room"), (23.8, 25.8, 1.0, 2.4, "window"), (29.6, 31.6, 1.0, 2.4, "window"),
    (33.1, 34.1, 0.0, 2.1, "backdoor")]
ROOM = (18.6, 22.6, -5.2, -8.4, 2.8)


def build_shell():
    mb = MB("shell")
    WT = (2.0, 3.0)
    z = WALL_Z
    # 地板（前面到 z 4.2；正門外面一小段）、天花板
    mb.gquad((-0.4, 0, 4.2), (36.4, 0, 4.2), (36.4, 0, z), (-0.4, 0, z), "M_FloorTile", tile=2.0)
    mb.gquad((0.2, 0, z), (2.4, 0, z), (2.4, 0, -5.8), (0.2, 0, -5.8), "M_FloorTile", tile=2.0)
    holes = [(6.5, -1.0), (14.0, 0.5), (22.0, -1.5), (30.5, 0.0), (30.5, 0.5)]
    xs = [-0.4, 36.4]
    mb.gquad((-0.4, H, z), (36.4, H, z), (36.4, H, 4.2), (-0.4, H, 4.2), "M_Ceiling", tile=2.0)
    for hx, hz in holes:                                   # 掉了的天花板：黑洞＋垂下來的一片
        mb.gquad((hx, H - 0.01, hz), (hx + 0.5, H - 0.01, hz), (hx + 0.5, H - 0.01, hz + 0.5), (hx, H - 0.01, hz + 0.5), "M_Dark")
    for hx, hz, ang in ((6.5, -1.0, 55), (22.0, -1.5, 35)):
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
                mb.gquad((a, y0, z), (b, y0, z), (b, y1, z), (a, y1, z), "M_Wall", tile=WT)
    for x0, x1, y0, y1, kind in OPENINGS:                  # 開口的側面、上緣、窗台
        z1 = -5.8 if kind == "entrance" else z - DEPTH
        mb.gquad((x0, y0, z), (x0, y0, z1), (x0, y1, z1), (x0, y1, z), "M_Wall", tile=WT)
        mb.gquad((x1, y0, z1), (x1, y0, z), (x1, y1, z), (x1, y1, z1), "M_Wall", tile=WT)
        mb.gquad((x0, y1, z), (x1, y1, z), (x1, y1, z1), (x0, y1, z1), "M_Wall", tile=WT)
        if y0 > 0:
            mb.gquad((x0, y0, z), (x1, y0, z), (x1, y0, z1), (x0, y0, z1), "M_Wall", tile=WT)
        if kind == "window":
            mb.gquad((x0, y0, z - 0.12), (x1, y0, z - 0.12), (x1, y1, z - 0.12), (x0, y1, z - 0.12), "M_Window", px="all")
        elif kind == "backdoor":
            mb.gquad((x0, y0, z - 0.1), (x1, y0, z - 0.1), (x1, y1, z - 0.1), (x0, y1, z - 0.1), "M_Door", px="all")
        elif kind == "entrance":                          # 鐵捲門拉起一半，下面看得到外面
            mb.gquad((x0, 1.35, z - 0.08), (x1, 1.35, z - 0.08), (x1, y1, z - 0.08), (x0, y1, z - 0.08), "M_Shutter", tile=1.0)
            mb.gquad((x0, 0, -5.8), (x1, 0, -5.8), (x1, 1.65, -5.81), (x0, 1.65, -5.81), "M_Outside", px="all")
            bx0, bx1 = G(x0, 1.28, z - 0.04), G(x1, 1.38, z - 0.12)
            mb.box(bx0[0], bx1[0], bx0[1], bx1[1], bx0[2], bx1[2], "M_Metal")
    for side, xw in ((1, 0.0), (-1, 36.0)):                # 左右牆
        if side > 0:
            mb.gquad((xw, 0, 4.2), (xw, 0, z), (xw, H, z), (xw, H, 4.2), "M_Wall", tile=WT)
        else:
            mb.gquad((xw, 0, z), (xw, 0, 4.2), (xw, H, 4.2), (xw, H, z), "M_Wall", tile=WT)
    # 門框（治療室、後門、正門：木條凸出牆面 3 cm）
    for x0, x1, y0, y1, kind in OPENINGS:
        if kind in ("room", "backdoor", "entrance"):
            for bx0, bx1, by0, by1 in ((x0 - 0.08, x0, 0, y1), (x1, x1 + 0.08, 0, y1), (x0 - 0.08, x1 + 0.08, y1, y1 + 0.08)):
                p0, p1 = G(bx0, by0, z + 0.03), G(bx1, by1, z)
                mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], "M_Wood", skip=("+y", "-z"))
    # 出口牌（後門上面）
    a, b = G(33.25, 2.25, -4.92), G(33.95, 2.5, -5.0)
    mb.box(a[0], b[0], a[1], b[1], a[2], b[2], "M_Metal", fit={"-y": ("M_Sign", "all")})
    # 治療室（後牆後面的小房間，面朝裡面）
    rx0, rx1, rz0, rz1, rh = ROOM
    mb.gquad((rx0, 0, rz0), (rx1, 0, rz0), (rx1, 0, rz1), (rx0, 0, rz1), "M_FloorTile", tile=2.0)
    mb.gquad((rx0, rh, rz1), (rx1, rh, rz1), (rx1, rh, rz0), (rx0, rh, rz0), "M_Ceiling", tile=2.0)
    mb.gquad((rx0, 0, rz1), (rx1, 0, rz1), (rx1, rh, rz1), (rx0, rh, rz1), "M_Wall", tile=WT)
    mb.gquad((rx0, 0, rz0), (rx0, 0, rz1), (rx0, rh, rz1), (rx0, rh, rz0), "M_Wall", tile=WT)
    mb.gquad((rx1, 0, rz1), (rx1, 0, rz0), (rx1, rh, rz0), (rx1, rh, rz1), "M_Wall", tile=WT)
    mb.gquad((21.4, 1.2, rz1 + 0.02), (22.4, 1.2, rz1 + 0.02), (22.4, 1.9, rz1 + 0.02), (21.4, 1.9, rz1 + 0.02), "M_Window", px="all")
    for i, (cx, cy) in enumerate(((19.75, 1.25), (20.3, 1.3), (20.85, 1.22))):   # 後牆：蘋果、媽媽、房子
        u = i * 32
        mb.gquad((cx - 0.25, cy, rz1 + 0.01), (cx + 0.25, cy, rz1 + 0.01), (cx + 0.25, cy + 0.5, rz1 + 0.01), (cx - 0.25, cy + 0.5, rz1 + 0.01), "M_Cards", px=(u, 0, u + 32, 32))
    for i, zc in enumerate((-6.0, -6.6, -7.2)):            # 左邊的牆：ㄅ、ㄆ、ㄇ
        u = i * 32
        mb.gquad((rx0 + 0.01, 1.2, zc + 0.25), (rx0 + 0.01, 1.2, zc - 0.25), (rx0 + 0.01, 1.7, zc - 0.25), (rx0 + 0.01, 1.7, zc + 0.25), "M_Cards", px=(u, 32, u + 32, 64))
    # 治療室的門（開著，往裡面打開）
    a = math.radians(65)
    hx, hz = 19.8, z - DEPTH
    ex, ez = hx + math.cos(a) * 1.0, hz - math.sin(a) * 1.0
    mb.gquad((hx, 0, hz), (ex, 0, ez), (ex, 2.08, ez), (hx, 2.08, hz), "M_Door", px="all")
    # 牆上的東西：海報、佈告欄、爬藤、血跡
    mb.gquad((15.2, 1.2, z + 0.01), (15.7, 1.2, z + 0.01), (15.7, 1.9, z + 0.01), (15.2, 1.9, z + 0.01), "M_Posters", px=(0, 0, 32, 45))
    mb.gquad((21.3, 1.3, z + 0.02), (22.3, 1.3, z + 0.02), (22.3, 2.0, z + 0.02), (21.3, 2.0, z + 0.02), "M_Posters", px=(32, 0, 96, 45))
    for x0, y0 in ((2.4, 1.45), (5.6, 1.6), (13.8, 1.7), (25.0, 1.55), (31.0, 1.5)):
        mb.gquad((x0, y0, z + 0.03), (x0 + 2.0, y0, z + 0.03), (x0 + 2.0, y0 + 1.5, z + 0.03), (x0, y0 + 1.5, z + 0.03), "M_IvyWall", px="all")
    mb.gquad((1.8, 0.004, -2.5), (3.2, 0.004, -2.5), (3.2, 0.004, -3.0), (1.8, 0.004, -3.0), "M_Blood", px="all")
    return mb.finish()


# ======================= 家具（原點在底部中心；-y 那面朝鏡頭） =======================
def R(axis, deg, at=(0, 0, 0)):
    """繞 at 點旋轉的 4×4 矩陣"""
    at = Vector(at)
    return Matrix.Translation(at) @ Matrix.Rotation(math.radians(deg), 4, axis) @ Matrix.Translation(-at)


def build_bench():
    """候診椅：一排三張（寬 2.2 m），中間那張的椅背掉了、右邊那張歪了"""
    mb = MB("bench")
    mb.box(-1.1, 1.1, 0.02, 0.08, 0.36, 0.41, "M_Metal")
    for x in (-0.85, 0.85):
        mb.box(x - 0.03, x + 0.03, 0.02, 0.08, 0.02, 0.36, "M_Metal")
        mb.box(x - 0.03, x + 0.03, -0.24, 0.26, 0.0, 0.04, "M_Metal")
    for i, x in enumerate((-0.72, 0.0, 0.72)):
        m = mb.mark()
        mb.box(x - 0.3, x + 0.3, -0.22, 0.24, 0.41, 0.46, "M_Leather")
        if i != 1:
            mb.box(x - 0.3, x + 0.3, 0.2, 0.25, 0.5, 0.88, "M_Leather")
            mb.box(x - 0.03, x + 0.03, 0.12, 0.2, 0.4, 0.55, "M_Metal")
        if i == 2:
            mb.xform(m, R('Y', -6, (x - 0.3, 0, 0.41)))
    return mb.finish()


def build_plant():
    """枯掉的盆栽：陶盆＋乾枯的枝條與幾片葉子"""
    mb = MB("plant")
    mb.cyl((0, 0, 0.18), 'Z', 0.2, 0.36, "M_Pot", seg=10, cap="M_Dark")
    mb.cyl((0, 0, 0.37), 'Z', 0.23, 0.05, "M_Pot", seg=10)
    tips = [(-0.25, -0.05, 1.05), (0.2, 0.1, 1.2), (0.05, -0.2, 0.95), (-0.1, 0.18, 1.3), (0.3, -0.1, 0.8)]
    for t in tips:
        mid = (t[0] * 0.4, t[1] * 0.4, 0.4 + (t[2] - 0.4) * 0.55)
        mb.beam((0, 0, 0.38), mid, 0.025, "M_Wood")
        mb.beam(mid, t, 0.018, "M_Wood")
        mb.quad((t[0] - 0.09, t[1], t[2] - 0.12), (t[0] + 0.09, t[1], t[2] - 0.12), (t[0] + 0.09, t[1], t[2] + 0.04), (t[0] - 0.09, t[1], t[2] + 0.04),
                "M_Leaves", px=(int(abs(t[0]) * 40) % 20, 4, int(abs(t[0]) * 40) % 20 + 10, 14))
    return mb.finish()


def build_counter():
    """櫃台：前面的木頭檯面（1.05 m）、後面的桌子、映像管螢幕、電話、一疊病歷"""
    mb = MB("counter")
    mb.box(-1.5, 1.5, -0.25, 0.25, 0.08, 1.05, "M_Wood")
    mb.box(-1.48, 1.48, -0.22, 0.22, 0.0, 0.08, "M_Dark")
    mb.box(-1.55, 1.55, -0.3, 0.3, 1.05, 1.09, "M_CabPaint")
    mb.box(-1.45, 1.45, 0.3, 0.95, 0.72, 0.76, "M_CabPaint")
    for x in (-1.4, 1.4):
        mb.box(x - 0.03, x + 0.03, 0.35, 0.9, 0.0, 0.72, "M_Metal")
    mb.box(-0.85, -0.45, 0.45, 0.85, 0.76, 1.12, "M_CabPaint", fit={"-y": ("M_Glass", "all")})
    mb.box(-0.72, -0.58, 0.6, 0.7, 1.12, 1.16, "M_CabPaint")
    mb.box(0.45, 0.67, 0.45, 0.63, 0.76, 0.84, "M_Tire")
    mb.box(0.47, 0.65, 0.47, 0.53, 0.84, 0.88, "M_Tire")
    m = mb.mark()
    mb.box(-0.15, 0.15, -0.12, 0.12, 1.09, 1.15, "M_Paper")
    mb.xform(m, R('Z', 12))
    m = mb.mark()
    mb.box(0.8, 1.05, -0.1, 0.1, 1.09, 1.105, "M_Paper")
    mb.xform(m, R('Z', -20, (0.9, 0, 0)))
    return mb.finish()


def build_files():
    """病歷櫃（2 × 1.6 m 的木架，正面是病歷夾）"""
    mb = MB("files")
    mb.box(-1.0, 1.0, -0.175, 0.175, 0.0, 1.6, "M_Wood", fit={"-y": ("M_Files", "all")})
    return mb.finish()


def build_wheelchair():
    """輪椅：皮面座椅與椅背、金屬管、兩個大輪子、前面的小輪、腳踏"""
    mb = MB("wheelchair")
    mb.box(-0.23, 0.23, -0.2, 0.22, 0.46, 0.51, "M_Leather")
    mb.box(-0.23, 0.23, 0.2, 0.24, 0.55, 0.92, "M_Leather")
    for s in (-1, 1):
        x = s * 0.25
        mb.beam((x, 0.24, 0.3), (x, 0.26, 1.0), 0.025, "M_Metal")
        mb.beam((x, 0.26, 1.0), (x, 0.38, 1.0), 0.025, "M_Metal")
        mb.beam((x, -0.2, 0.48), (x, 0.24, 0.48), 0.025, "M_Metal")
        mb.beam((x, -0.2, 0.48), (x, -0.3, 0.12), 0.025, "M_Metal")
        mb.beam((x, -0.05, 0.7), (x, 0.24, 0.7), 0.03, "M_Metal")
        mb.beam((x, -0.05, 0.7), (x, -0.05, 0.5), 0.025, "M_Metal")
        mb.cyl((s * 0.31, 0.1, 0.3), 'X', 0.3, 0.035, "M_Tire", seg=14, cap="M_Metal")
        mb.cyl((s * 0.33, 0.1, 0.3), 'X', 0.05, 0.02, "M_Metal", seg=8)
        mb.cyl((s * 0.22, -0.3, 0.07), 'X', 0.07, 0.03, "M_Tire", seg=8)
        mb.box(x - 0.12 * (s > 0), x + 0.12 * (s < 0), -0.38, -0.26, 0.12, 0.14, "M_Metal")
    return mb.finish()


def build_iv_stand():
    """點滴架：五腳底座、桿子、掛勾、點滴袋與管子"""
    mb = MB("iv_stand")
    for i in range(5):
        a = 2 * math.pi * i / 5
        mb.beam((0, 0, 0.06), (0.28 * math.cos(a), 0.28 * math.sin(a), 0.04), 0.03, "M_Metal")
        mb.cyl((0.28 * math.cos(a), 0.28 * math.sin(a), 0.025), 'X', 0.025, 0.02, "M_Tire", seg=6)
    mb.beam((0, 0, 0.03), (0, 0, 1.9), 0.025, "M_Metal")
    mb.beam((-0.16, 0, 1.86), (0.16, 0, 1.86), 0.018, "M_Metal")
    mb.box(0.08, 0.2, -0.025, 0.025, 1.5, 1.78, "M_Cloth")
    mb.beam((0.14, 0, 1.5), (0.1, -0.02, 0.9), 0.008, "M_Paper")
    return mb.finish()


def build_cart_boxes():
    """推車（米白烤漆、三層）＋旁邊疊著的紙箱"""
    mb = MB("cart_boxes")
    for x in (-0.95, -0.15):
        for y in (-0.22, 0.22):
            mb.box(x - 0.015, x + 0.015, y - 0.015, y + 0.015, 0.06, 0.92, "M_Metal")
            mb.cyl((x, y, 0.035), 'X', 0.035, 0.02, "M_Tire", seg=6)
    for z in (0.15, 0.52, 0.88):
        mb.box(-0.97, -0.13, -0.24, 0.24, z, z + 0.03, "M_CabPaint")
    mb.box(-0.8, -0.55, -0.1, 0.1, 0.91, 0.97, "M_Pills")
    mb.box(-0.45, -0.25, -0.12, 0.08, 0.55, 0.62, "M_Box")
    for (cx, cy, w, d, z0, h, ang) in ((0.35, 0.0, 0.55, 0.45, 0.0, 0.4, 0), (0.85, 0.05, 0.5, 0.42, 0.0, 0.35, 8),
                                       (0.45, 0.05, 0.45, 0.38, 0.4, 0.32, -10), (0.9, -0.05, 0.4, 0.35, 0.35, 0.3, 25)):
        m = mb.mark()
        mb.cbox(cx, cy, w, d, z0, z0 + h, "M_Box")
        mb.xform(m, R('Z', ang, (cx, cy, 0)))
    return mb.finish()


def build_curtain():
    """布簾：天花板上的軌道（3 m 高）、皺褶的布（下緣參差、破了一角），寬 1.8 m"""
    mb = MB("curtain")
    mb.box(-0.95, 0.95, -0.02, 0.02, 2.94, 2.98, "M_Metal")
    n = 12
    pts = []
    for i in range(n + 1):
        x = -0.9 + 1.8 * i / n
        y = 0.07 * (1 if i % 2 else -1)
        bottom = 0.35 + 0.25 * ((i * 7919) % 5) / 4
        pts.append((x, y, bottom))
    for i in range(n):
        (x0, y0, b0), (x1, y1, b1) = pts[i], pts[i + 1]
        if i == 8:
            b0 = b1 = 1.4                                   # 破掉的一角
        mb.quad((x0, y0, b0), (x1, y1, b1), (x1, y1, 2.92), (x0, y0, 2.92), "M_Curtain", tile=1.0)
    return mb.finish()


def build_cabinet():
    """藥櫃：米白烤漆、下面有門、上面三層（左邊的玻璃門開著、右邊的玻璃破了），中間那層留給錄音筆"""
    mb = MB("cabinet")
    W, D, Hc = 0.45, 0.21, 1.8
    mb.box(-W, W, D - 0.02, D, 0.0, Hc, "M_CabPaint", fit={"-y": ("M_Wood", (0, 0, 32, 16))})   # 櫃子裡面是深色的木板
    mb.box(-W, -W + 0.02, -D, D, 0.0, Hc, "M_CabPaint")
    mb.box(W - 0.02, W, -D, D, 0.0, Hc, "M_CabPaint")
    mb.box(-W, W, -D, D, Hc - 0.03, Hc, "M_CabPaint")
    mb.box(-W, W, -D, D, 0.0, 0.72, "M_CabPaint")
    mb.box(-0.005, 0.005, -D - 0.005, -D, 0.05, 0.68, "M_Dark")
    for x in (-0.06, 0.04):
        mb.box(x, x + 0.02, -D - 0.025, -D, 0.5, 0.58, "M_Metal")
    for z in (1.07, 1.42):
        mb.box(-W + 0.02, W - 0.02, -D, D - 0.02, z, z + 0.02, "M_CabPaint")
    for i, (x, z) in enumerate(((-0.3, 0.72), (-0.18, 0.72), (-0.05, 0.72), (0.2, 0.72), (0.32, 0.72), (-0.32, 1.44), (-0.2, 1.44), (0.1, 1.44), (0.25, 1.44), (0.33, 1.09))):
        hgt = 0.13 + 0.05 * (i % 3)
        mb.cyl((x, 0.03 * (i % 2), z + hgt / 2), 'Z', 0.045, hgt, "M_Pills" if i % 4 else "M_Glass", seg=8, cap="M_Paper")
    mb.cyl((0.18, -0.06, 1.135), 'X', 0.045, 0.14, "M_Pills", seg=8, cap="M_Paper")   # 倒下的藥罐
    def door(x0, x1, glass):
        for a, b in (((x0, -D, 0.73), (x1, -D, 0.73)), ((x0, -D, 1.76), (x1, -D, 1.76)), ((x0, -D, 0.73), (x0, -D, 1.76)), ((x1, -D, 0.73), (x1, -D, 1.76))):
            mb.beam(a, b, 0.03, "M_CabPaint")
        if glass:
            mb.quad((x0, -D, 0.74), (x1, -D, 0.74), (x1, -D, 1.75), (x0, -D, 1.75), "M_Glass", tile=0.5)
    m = mb.mark()
    door(-W + 0.015, -0.015, True)
    mb.xform(m, R('Z', -115, (-W + 0.015, -D, 0)))
    door(0.015, W - 0.015, False)
    for (x, z) in ((0.05, 0.76), (0.4, 0.76), (0.4, 1.7)):
        mb.quad((x - 0.03, -D - 0.002, z - 0.03), (x + 0.03, -D - 0.002, z - 0.03), (x + 0.01, -D - 0.002, z + 0.05), (x - 0.02, -D - 0.002, z + 0.04), "M_Glass", tile=0.5)
    return mb.finish()


def build_clinic_chair():
    """診療椅：底座、柱子、皮面的座墊、往後傾的椅背與頭枕、扶手、腳踏"""
    mb = MB("clinic_chair")
    mb.box(-0.3, 0.3, -0.25, 0.25, 0.0, 0.05, "M_Metal")
    mb.cyl((0, 0.05, 0.25), 'Z', 0.07, 0.4, "M_Metal", seg=8)
    mb.box(-0.28, 0.28, -0.3, 0.3, 0.45, 0.58, "M_Leather")
    m = mb.mark()
    mb.box(-0.27, 0.27, 0.25, 0.37, 0.55, 1.3, "M_Leather")
    mb.box(-0.14, 0.14, 0.24, 0.36, 1.3, 1.5, "M_Leather")
    mb.xform(m, R('X', -18, (0, 0.3, 0.55)))
    m = mb.mark()
    mb.box(-0.26, 0.26, -0.75, -0.3, 0.38, 0.5, "M_Leather")
    mb.xform(m, R('X', 22, (0, -0.3, 0.5)))
    for s in (-1, 1):
        mb.beam((s * 0.33, 0.15, 0.55), (s * 0.33, 0.15, 0.72), 0.025, "M_Metal")
        mb.box(s * 0.33 - 0.04, s * 0.33 + 0.04, -0.2, 0.25, 0.72, 0.77, "M_Leather")
    return mb.finish()


def build_stool():
    """治療師的圓凳：五腳、桿子、圓座墊"""
    mb = MB("stool")
    for i in range(5):
        a = 2 * math.pi * i / 5 + 0.3
        mb.beam((0, 0, 0.06), (0.22 * math.cos(a), 0.22 * math.sin(a), 0.03), 0.03, "M_Metal")
    mb.cyl((0, 0, 0.27), 'Z', 0.025, 0.44, "M_Metal", seg=6)
    mb.cyl((0, 0, 0.52), 'Z', 0.19, 0.08, "M_Leather", seg=12)
    return mb.finish()


def build_gurney():
    """擔架床：金屬框、四隻腳與輪子、下層、床墊（血跡）、立起來的一邊護欄"""
    mb = MB("gurney")
    L, Wd = 1.0, 0.33
    for (a, b) in (((-L, -Wd, 0.72), (L, -Wd, 0.72)), ((-L, Wd, 0.72), (L, Wd, 0.72)), ((-L, -Wd, 0.72), (-L, Wd, 0.72)), ((L, -Wd, 0.72), (L, Wd, 0.72))):
        mb.beam(a, b, 0.04, "M_Metal")
    for x in (-0.9, 0.9):
        for y in (-0.28, 0.28):
            mb.beam((x, y, 0.12), (x, y, 0.72), 0.035, "M_Metal")
            mb.cyl((x, y, 0.07), 'Y', 0.07, 0.04, "M_Tire", seg=8)
    mb.box(-0.9, 0.9, -0.28, 0.28, 0.3, 0.32, "M_Metal")
    m = mb.mark()
    mb.box(-0.95, 0.95, -0.3, 0.3, 0.74, 0.84, "M_Cloth", fit={"+z": ("M_Blood", "all")})
    mb.box(0.62, 0.92, -0.22, 0.22, 0.84, 0.9, "M_Cloth")
    mb.xform(m, R('Z', 3))
    for x in (-0.6, 0.0, 0.6):
        mb.beam((x, Wd + 0.02, 0.74), (x, Wd + 0.02, 1.02), 0.02, "M_Metal")
    mb.beam((-0.7, Wd + 0.02, 1.0), (0.7, Wd + 0.02, 1.0), 0.025, "M_Metal")
    return mb.finish()


def build_room_props():
    """治療室裡：書桌、椅子、倒下的名牌、小鏡子、桌上散落的圖卡"""
    mb = MB("room_props")
    mb.box(-0.6, 0.6, -0.3, 0.3, 0.71, 0.75, "M_Wood")
    for x in (-0.56, 0.56):
        mb.box(x - 0.03, x + 0.03, -0.26, 0.26, 0.0, 0.71, "M_Wood")
    mb.box(-0.56, 0.56, 0.24, 0.27, 0.35, 0.71, "M_Wood")
    m = mb.mark()
    mb.box(-0.12, 0.12, -0.03, 0.03, 0.75, 0.81, "M_Wood", fit={"+z": ("M_Metal", (0, 0, 8, 2))})
    mb.xform(m, R('X', 90, (0, -0.03, 0.75)) @ Matrix.Translation((0.15, -0.1, 0)))
    mb.box(-0.4, -0.25, 0.05, 0.08, 0.75, 1.0, "M_Glass")
    mb.box(-0.37, -0.28, 0.0, 0.12, 0.75, 0.77, "M_Wood")
    for (x, y, ang, u) in ((0.3, 0.05, 15, 0), (0.42, -0.12, -25, 64)):
        m = mb.mark()
        mb.quad((x - 0.12, y - 0.12, 0.752), (x + 0.12, y - 0.12, 0.752), (x + 0.12, y + 0.12, 0.752), (x - 0.12, y + 0.12, 0.752), "M_Cards", px=(u, 0, u + 32, 32))
        mb.xform(m, R('Z', ang, (x, y, 0)))
    m = mb.mark()                                          # 椅子（往後退、有點歪）
    mb.box(-0.2, 0.2, -0.2, 0.2, 0.42, 0.46, "M_Wood")
    mb.box(-0.2, 0.2, -0.24, -0.2, 0.46, 0.85, "M_Wood")
    for x in (-0.18, 0.18):
        for y in (-0.18, 0.18):
            mb.box(x - 0.02, x + 0.02, y - 0.02, y + 0.02, 0.0, 0.42, "M_Wood")
    mb.xform(m, Matrix.Translation((0.1, -0.65, 0)) @ R('Z', 20))
    return mb.finish()


def build_lamp(hang=False):
    """日光燈（原點在天花板的固定點）：燈座、兩根燈管（材質第 2 個＝M_Tube，閃爍時換暗的）；hang＝一頭掉下來、掛在鏈子上"""
    mb = MB("lamp_hang" if hang else "lamp")
    mb.box(-0.6, 0.6, -0.13, 0.13, -0.08, 0.0, "M_CabPaint")
    for y in (-0.06, 0.06):
        mb.cyl((0, y, -0.1), 'X', 0.02, 1.1, "M_Tube", seg=6)
    if hang:
        mb.xform(0, R('Y', 28, (-0.6, 0, 0)) @ Matrix.Translation((0, 0, -0.25)))
        mb.beam((-0.6, 0, 0.0), (-0.6, 0, -0.25), 0.01, "M_Metal")
    return mb.finish()


def build_lamp_hang():
    return build_lamp(True)


# ======================= 前景與地上小物 =======================
def build_pills():
    """地上散落的藥罐（4 個）"""
    mb = MB("pills")
    for (x, y, axis, h_) in ((-0.15, 0.02, 'X', 0.1), (0.05, -0.08, 'Y', 0.09), (0.2, 0.06, 'X', 0.08)):
        mb.cyl((x, y, 0.035), axis, 0.035, h_, "M_Pills", seg=8, cap="M_Paper")
    mb.cyl((0.0, 0.12, 0.05), 'Z', 0.035, 0.1, "M_Pills", seg=8, cap="M_Paper")
    return mb.finish()


def build_clipboard():
    """地上的病歷夾"""
    mb = MB("clipboard")
    m = mb.mark()
    mb.box(-0.125, 0.125, -0.175, 0.175, 0.0, 0.015, "M_Wood", fit={"+z": ("M_Clipboard", "all")})
    mb.xform(m, R('Z', 25))
    return mb.finish()


def build_leaves():
    """共用：地上的落葉（兩片貼花，1 m 與 0.6 m）"""
    mb = MB("leaves")
    mb.quad((-0.5, -0.5, 0.004), (0.5, -0.5, 0.004), (0.5, 0.5, 0.004), (-0.5, 0.5, 0.004), "M_Leaves", px="all")
    m = mb.mark()
    mb.quad((0.3, -0.2, 0.006), (0.9, -0.2, 0.006), (0.9, 0.4, 0.006), (0.3, 0.4, 0.006), "M_Leaves", px="all")
    mb.xform(m, R('Z', 40, (0.6, 0.1, 0)))
    return mb.finish()


def build_ivy_hang():
    """從天花板垂下來的爬藤（兩片交叉的貼花，1 × 2 m；放在 y 1 時上緣剛好碰到天花板）"""
    mb = MB("ivy_hang")
    for ang in (0, 65):
        m = mb.mark()
        mb.quad((-0.5, 0, 0), (0.5, 0, 0), (0.5, 0, 2.0), (-0.5, 0, 2.0), "M_IvyHang", px="all")
        mb.xform(m, R('Z', ang))
    return mb.finish()


def build_all():
    for fn in BUILDERS:
        fn()


BUILDERS = [build_shell, build_bench, build_plant, build_counter, build_files, build_wheelchair, build_iv_stand, build_cart_boxes,
            build_curtain, build_cabinet, build_clinic_chair, build_stool, build_gurney, build_room_props, build_lamp, build_lamp_hang,
            build_pills, build_clipboard, build_leaves, build_ivy_hang]


# ======================= B3-2b 預覽時的擺放位置（Godot 座標 x, y, z, 繞 y 軸轉幾度；B3-2c 照這份放進 Clinic3D） =======================
PLACE = {
    "bench": [(4.0, 0, -4.4, 0), (23.7, 0, -4.4, 0)], "plant": [(6.4, 0, -4.5, 0)], "counter": [(11.9, 0, -3.4, 0)],
    "files": [(11.9, 0, -4.8, 0)], "wheelchair": [(15.4, 0, -3.0, 25), (29.4, 0, -3.6, -30)], "iv_stand": [(16.7, 0, -3.2, 0), (25.6, 0, -3.7, 0)],
    "cart_boxes": [(31.3, 0, -4.55, 0)], "curtain": [(7.3, 0, -2.6, 0), (18.0, 0, -2.6, 0), (6.4, 0, 3.5, 0), (23.6, 0, 3.5, 0)],
    "cabinet": [(9.4, 0, -2.5, 0)], "clinic_chair": [(27.25, 0, -2.55, 0)], "stool": [(28.2, 0, -2.5, 0)], "gurney": [(14.8, 0, 0.3, -8)],
    "room_props": [(20.3, 0, -7.9, 0)], "lamp": [(5.0, 3.0, -1.0, 0), (12.0, 3.0, 0.5, 0), (18.0, 3.0, -1.0, 0), (30.0, 3.0, -1.0, 0)],
    "lamp_hang": [(22.5, 3.0, -1.0, 0)], "pills": [(4.7, 0, 2.2, 0), (31.7, 0, 2.2, 40)], "leaves": [(10.0, 0, 2.2, 0), (29.7, 0, 2.2, 70)],
    "clipboard": [(17.2, 0, 2.2, 0)], "ivy_hang": [(13.0, 1.0, 3.5, 0), (16.8, 1.0, 3.5, 30)],
}
