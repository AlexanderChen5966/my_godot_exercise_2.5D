# B3-6b 牆前的模型（在 Blender 裡執行：exec(open(這個檔案).read())，再呼叫 build_all() 或單一個 build_xxx()）。
# 共用的 MB 類別、G()、R()、wall_x()／reveal() 的寫法和舊家（art/models/home/build_home.py）相同。
# 座標：結構 shell 直接用區域的座標（Godot 的 x、y、z，用 G() 換成 Blender：Y＝負的 Godot z、Z 朝上）；
# 椅子的原點在底部中心（Blender 座標，-y 那面朝鏡頭），到 Godot 再擺位置（PLACE）。貼圖 32 像素＝1 m。
# 配置見 art/design/b3/b3-6a_牆前配置圖.png：後牆 z −3.6、天花板 2.8 m（x 19～27 塌了）；補過的灰泥 x 21.9～25、炭筆字 1.7～2.5 m。
import bpy, bmesh, math
from mathutils import Vector, Matrix

ROOT = "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/"
T = ROOT + "assets/textures/"
# 材質名稱 → (貼圖, 透明, 雙面)
TEX = {
    "M_Wall": ("wall/wall_old.png", False, False), "M_BrickPatch": ("wall/brick_patch.png", True, False),
    "M_Plaster": ("wall/plaster_patch.png", True, False), "M_Charcoal": ("wall/charcoal_words.png", True, False),
    "M_Floor": ("common/floor.png", False, False), "M_Ceiling": ("home/ceiling_home.png", False, False),
    "M_Wood": ("common/wood.png", False, False), "M_WindowLit": ("ruins/window_lit.png", False, False),
}
GLOW = {}
SOLID = {"M_Dark": (0.02, 0.02, 0.025, 1)}
EMIT_TEX = {"M_WindowLit": 1.2}

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
    if name in GLOW:                                       # 沒有貼圖、會發光的（女兒房間的小窗）
        c = GLOW[name]
        b.inputs["Base Color"].default_value = c
        b.inputs["Emission Color"].default_value = c
        b.inputs["Emission Strength"].default_value = 1.0
        return m
    if name in SOLID:
        b.inputs["Base Color"].default_value = SOLID[name]
        return m
    path, alpha, double = TEX[name]
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(T + path, check_existing=True)
    t.interpolation = 'Closest'
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    if name in EMIT_TEX:
        nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = EMIT_TEX[name]
    if alpha:                                              # 透明度先四捨五入，glTF 才會匯出成 MASK（Godot 的 alpha scissor）
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
        """inside：一個在物體裡面的點，法線朝向它時把面反過來"""
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

    def gquad(self, bl, br, tr, tl, mname, px=None, tile=1.0, inside=None):
        """Godot 座標的四邊形；inside＝牆裡面的一點（Godot 座標），法線一律朝外（側牆、門窗洞的厚度用）"""
        if inside is not None:
            return self.face([G(*bl), G(*br), G(*tr), G(*tl)], mname, tile=tile, inside=G(*inside))
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
        """兩點之間的方柱（寬 w）：斜的木條、腳、桿子"""
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


def h01(i, s):
    n = (i * 374761393 + s * 668265263) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0



WP = (2.0, 2.8)                                            # 舊牆一格 2 m 寬、2.8 m 高
BACK = -3.6                                                # 後牆的正面
TH = 0.2                                                   # 牆厚
CEIL = 2.8
X0, X1 = 0.0, 36.0
DOORS = [(5.7, 6.8, 0.0, 2.1), (27.5, 28.7, 0.0, 2.1)]    # 門洞 1（暗的走廊）、門洞 2（暖光的房間）
GAP = (19.0, 27.0)                                         # 天花板塌掉的一段
CX = 23.4375                                               # 牆（互動點）


def wall_x(mb, x0, x1, z, holes, mname, y1=CEIL):
    """朝鏡頭（+z）的牆：holes＝[(x0, x1, y0, y1)] 挖掉門洞、窗"""
    cuts = sorted({x0, x1} | {a for a, b, c, d in holes} | {b for a, b, c, d in holes})
    for a, b in zip(cuts, cuts[1:]):
        hs = [hh for hh in holes if hh[0] <= a and b <= hh[1]]
        ys = sorted({0.0, y1} | {hh[2] for hh in hs} | {hh[3] for hh in hs})
        for c, d in zip(ys, ys[1:]):
            if any(hh[2] <= c and d <= hh[3] for hh in hs):
                continue
            mb.gquad((a, c, z), (b, c, z), (b, d, z), (a, d, z), mname, tile=WP)


def reveal(mb, x0, x1, y0, y1, z, depth, mname):
    """門窗洞的厚度（左右、上、下）"""
    zm, ym = z - depth / 2, (y0 + y1) / 2
    mb.gquad((x0, y0, z - depth), (x0, y0, z), (x0, y1, z), (x0, y1, z - depth), mname, tile=WP, inside=(x0 - 1, ym, zm))
    mb.gquad((x1, y0, z), (x1, y0, z - depth), (x1, y1, z - depth), (x1, y1, z), mname, tile=WP, inside=(x1 + 1, ym, zm))
    mb.gquad((x0, y1, z), (x1, y1, z), (x1, y1, z - depth), (x0, y1, z - depth), mname, tile=WP, inside=((x0 + x1) / 2, y1 + 1, zm))
    if y0 > 0:
        mb.gquad((x0, y0, z - depth), (x1, y0, z - depth), (x1, y0, z), (x0, y0, z), "M_Wood", tile=0.5, inside=((x0 + x1) / 2, y0 - 1, zm))


def room(mb, x0, x1, zb, holes=()):
    """後牆後面的小房間：地板、左右牆、後牆（holes 挖窗）、天花板"""
    z0 = BACK - TH
    mb.gquad((x0, 0, z0), (x1, 0, z0), (x1, 0, zb), (x0, 0, zb), "M_Floor", tile=2.0)
    wall_x(mb, x0, x1, zb, list(holes), "M_Wall")
    mb.gquad((x0, 0, zb), (x0, 0, z0), (x0, CEIL, z0), (x0, CEIL, zb), "M_Wall", tile=WP, inside=(x0 - 1, 1, (z0 + zb) / 2))
    mb.gquad((x1, 0, z0), (x1, 0, zb), (x1, CEIL, zb), (x1, CEIL, z0), "M_Wall", tile=WP, inside=(x1 + 1, 1, (z0 + zb) / 2))
    mb.gquad((x0, CEIL, zb), (x1, CEIL, zb), (x1, CEIL, z0), (x0, CEIL, z0), "M_Ceiling")


# ======================= 結構：地板、後牆（兩個門洞）、塌了一段的天花板、補過的灰泥＋炭筆字、剝落露出磚、後面的走廊與房間 =======================
def build_shell():
    mb = MB("shell")
    mb.gquad((X0 - 0.4, 0, 4.2), (X1 + 0.4, 0, 4.2), (X1 + 0.4, 0, BACK), (X0 - 0.4, 0, BACK), "M_Floor", tile=2.0)
    wall_x(mb, X0, X1, BACK, DOORS, "M_Wall")
    for k, (x0, x1, y0, y1) in enumerate(DOORS):
        reveal(mb, x0, x1, y0, y1, BACK, TH, "M_Wall")
        # 木頭門框（左右、上），門洞 1 的右邊那根斷了一截
        mb.gquad((x0 - 0.1, y1, BACK + 0.02), (x1 + 0.1, y1, BACK + 0.02), (x1 + 0.1, y1 + 0.1, BACK + 0.02), (x0 - 0.1, y1 + 0.1, BACK + 0.02), "M_Wood", tile=0.5)
        mb.gquad((x0 - 0.1, 0, BACK + 0.02), (x0, 0, BACK + 0.02), (x0, y1, BACK + 0.02), (x0 - 0.1, y1, BACK + 0.02), "M_Wood", tile=0.5)
        top = 1.3 if k == 0 else y1
        mb.gquad((x1, 0, BACK + 0.02), (x1 + 0.1, 0, BACK + 0.02), (x1 + 0.1, top, BACK + 0.02), (x1, top, BACK + 0.02), "M_Wood", tile=0.5)
    for x, out in ((X0, -1), (X1, 1)):
        mb.gquad((x, 0, BACK), (x, 0, 2.0), (x, CEIL, 2.0), (x, CEIL, BACK), "M_Wall", tile=WP, inside=(x + out, 1, 0))
    # 天花板：到 z 1.6，x 19～27 塌了（斷口高低不一、垂下斷掉的木樑）；天花板以上一面暗的遮擋面（夜晚）
    zf = 1.6
    g0, g1 = GAP
    for a, b in ((X0 - 0.4, g0), (g1, X1 + 0.4)):
        mb.gquad((a, CEIL, BACK), (b, CEIL, BACK), (b, CEIL, zf), (a, CEIL, zf), "M_Ceiling")
        mb.gquad((a, CEIL, zf), (b, CEIL, zf), (b, CEIL + 0.3, zf), (a, CEIL + 0.3, zf), "M_Wood", tile=0.5)
    for x, sgn in ((g0, 1), (g1, -1)):                    # 斷口：一塊塊往塌掉的那邊伸出、長短不一
        z, i = BACK, 0
        while z < zf - 0.05:
            d = 0.4 + 0.5 * h01(i, 901 + int(x))
            L = 0.2 + 0.9 * h01(i + 7, 902 + int(x))
            z1 = min(zf, z + d)
            mb.gquad((x, CEIL, z), (x + sgn * L, CEIL, z), (x + sgn * L, CEIL, z1), (x, CEIL, z1), "M_Ceiling",
                     inside=(x, CEIL + 1, (z + z1) / 2))
            z, i = z1, i + 1
    for k, (x, z, dx, dy) in enumerate(((19.4, -2.6, 1.6, -0.9), (20.6, -1.0, 1.2, -0.6), (26.4, -2.2, -1.5, -1.1), (25.0, -0.2, -0.8, -0.5))):
        mb.beam(G(x, CEIL + 0.05, z), G(x + dx, CEIL + 0.05 + dy, z + 0.2 * (k - 1.5)), 0.12, "M_Wood")   # 垂下的斷樑
    mb.gquad((X0 - 8, CEIL + 0.25, BACK - TH - 0.01), (X1 + 8, CEIL + 0.25, BACK - TH - 0.01), (X1 + 8, 12.0, BACK - TH - 0.01),
             (X0 - 8, 12.0, BACK - TH - 0.01), "M_Dark")
    # 補過的灰泥（3.1 × 2.3 m）＋炭筆字（2.6 × 0.8 m，1.7～2.5 m）
    mb.gquad((CX - 1.55, 0.3, BACK + 0.008), (CX + 1.55, 0.3, BACK + 0.008), (CX + 1.55, 2.6, BACK + 0.008), (CX - 1.55, 2.6, BACK + 0.008),
             "M_Plaster", px="all")
    mb.gquad((CX - 1.3, 1.7, BACK + 0.014), (CX + 1.3, 1.7, BACK + 0.014), (CX + 1.3, 2.5, BACK + 0.014), (CX - 1.3, 2.5, BACK + 0.014),
             "M_Charcoal", px="all")
    # 灰泥剝落露出磚（貼花，兩種隨機；避開門洞、補過的灰泥）
    for k, x in enumerate((2.5, 9.0, 12.6, 15.5, 19.6, 30.5, 34.0)):
        y = 0.6 + 1.5 * h01(k, 903)
        s_ = 0.7 + 0.6 * h01(k, 904)
        u0 = 0 if h01(k, 905) < 0.5 else 32
        mb.gquad((x - s_ / 2, y - s_ / 2, BACK + 0.005), (x + s_ / 2, y - s_ / 2, BACK + 0.005), (x + s_ / 2, y + s_ / 2, BACK + 0.005),
                 (x - s_ / 2, y + s_ / 2, BACK + 0.005), "M_BrickPatch", px=(u0, 0, u0 + 32, 32))
    # 門洞 1 後面：暗的走廊（不放燈）；門洞 2 後面：房間，後牆有亮著的窗（暖光）
    room(mb, 4.6, 8.0, -6.0)
    room(mb, 26.0, 31.5, -7.4, holes=[(29.6, 30.8, 1.0, 1.8)])
    mb.gquad((29.6, 1.0, -7.45), (30.8, 1.0, -7.45), (30.8, 1.8, -7.45), (29.6, 1.8, -7.45), "M_WindowLit", px="all")
    reveal(mb, 29.6, 30.8, 1.0, 1.8, -7.4, 0.05, "M_Wall")
    return mb.finish()


# ======================= 椅子（原點在底部中心；面向牆＝椅背在 -y 朝鏡頭） =======================
def build_chair():
    """木頭椅子：四隻腳、座板、椅背（直條）；一隻腳短了一截，椅子微微歪著"""
    mb = MB("chair")
    for x in (-0.2, 0.2):
        for y in (-0.2, 0.2):
            mb.cbox(x, y, 0.045, 0.045, 0.0 if (x, y) != (0.2, 0.2) else 0.03, 0.45, "M_Wood", tile=0.25)
    mb.box(-0.24, 0.24, -0.24, 0.24, 0.45, 0.5, "M_Wood", tile=0.25)
    for x in (-0.2, 0.2):
        mb.cbox(x, -0.2, 0.045, 0.045, 0.5, 1.0, "M_Wood", tile=0.25)
    mb.box(-0.24, 0.24, -0.23, -0.18, 0.88, 0.98, "M_Wood", tile=0.25)
    for x in (-0.08, 0.08):
        mb.cbox(x, -0.2, 0.03, 0.03, 0.5, 0.88, "M_Wood", tile=0.25)
    return mb.finish()


def build_all():
    for fn in BUILDERS:
        fn()


BUILDERS = [build_shell, build_chair]


# ======================= B3-6b 預覽時的擺放位置（Godot 座標 x, y, z, 繞 y 軸轉幾度；B3-6c 照這份放進 Wall3D） =======================
# shell 放在原點。借用：common/plank（倒下的木板）、common/rubble（碎灰泥）、ruins/front_wall（前景的斷牆，縮放 0.45）、
# home/doorframe（斷掉的門框，前景）；熊布偶（home_near_bear）、炭筆（wall_near_charcoal）的小像素圖在 Godot 放。
PLACE = {"chair": [(11.0, 0, -2.6, -15)]}
BORROWED = {
    "common/plank": [(16.5, 0, -2.7, 20), (33.0, 0, -2.6, -25)], "common/rubble": [(6.25, 0, 2.4, 0), (29.7, 0, 2.4, 0)],
    "ruins/front_wall": [(7.2, 0, 3.5, 0), (34.5, 0, 3.5, 180)], "home/doorframe": [(15.0, 0, 3.3, 0)],
}
