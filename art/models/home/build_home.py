# B3-5b 舊家的模型（在 Blender 裡執行：exec(open(這個檔案).read())，再呼叫 build_all() 或單一個 build_xxx()）。
# 共用的 MB 類別、G()、R() 和廢墟（art/models/ruins/build_ruins.py）相同。
# 座標：結構 shell、窗外 outside 直接用區域的座標（Godot 的 x、y、z，用 G() 換成 Blender：Y＝負的 Godot z、Z 朝上）；
# 家具的原點在自己的底部中心（Blender 座標，-y 那面朝鏡頭），到 Godot 再擺位置（PLACE）。貼圖 32 像素＝1 m。
# 配置見 art/design/b3/b3-5a_舊家配置圖.png：後牆 z −3.6、天花板 2.7 m；牆上的字 1.6～2.6 m（B3-5c 往上移）；大窗 x 26.4～29.2（窗台 0.9、上緣 2.1）。
import bpy, bmesh, math
from mathutils import Vector, Matrix

ROOT = "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/"
T = ROOT + "assets/textures/"
# 材質名稱 → (貼圖, 透明, 雙面)
TEX = {
    "M_Wallpaper": ("home/wallpaper.png", False, False), "M_WallKid": ("home/wallpaper_kid.png", False, False),
    "M_Floor": ("home/floor_wood.png", False, False), "M_Ceiling": ("home/ceiling_home.png", False, False),
    "M_Crayon": ("home/crayon_words.png", True, False), "M_Peel": ("home/peel.png", True, False), "M_Drawing": ("home/drawing.png", True, False),
    "M_Photos": ("home/photos.png", False, False), "M_Shelf": ("home/shelf_front.png", False, False),
    "M_Sofa": ("home/sofa.png", False, False), "M_Door": ("home/door_home.png", False, True),
    "M_Window": ("home/window_home.png", True, True), "M_Kitchen": ("home/kitchen.png", False, False),
    "M_Quilt": ("home/quilt.png", False, False), "M_Houses": ("home/houses_far.png", True, False),
    "M_Wood": ("common/wood.png", False, False), "M_Metal": ("common/metal.png", False, False),
    "M_Cloth": ("common/cloth.png", False, True), "M_Paper": ("common/paper.png", False, False),
    "M_Sidewalk": ("street/sidewalk.png", False, False), "M_Asphalt": ("street/asphalt.png", False, False),
}
GLOW = {"M_KidWindow": (0.55, 0.42, 0.32, 1)}
SOLID = {"M_Dark": (0.03, 0.025, 0.02, 1), "M_Brass": (0.5, 0.38, 0.18, 1), "M_Shade": (0.32, 0.26, 0.2, 1)}
EMIT_TEX = {}


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


WP = (2.0, 2.75)                                           # 壁紙一格 2 m 寬、2.75 m 高（下面 0.9 m 是護牆）
BACK = -3.6                                                # 後牆的正面
TH = 0.2                                                   # 牆厚
CEIL = 2.7
X0, X1 = 0.0, 36.0
DOORS = [(17.4, 18.5, 0.0, 2.1), (33.0, 34.2, 0.0, 2.1)]   # 女兒房間的門、大門
WINDOW = (26.4, 29.2, 0.9, 2.1)
HOLE = (8.4, 10.4, BACK, -2.0)                             # 天花板的破洞（x0, x1, z0, z1）：夕陽照在牆上的字
KID = (15.8, 20.6, -7.2)                                   # 女兒房間（x0, x1, 後牆 z）


def wall_x(mb, x0, x1, z, holes, mname, y1=CEIL):
    """朝鏡頭（+z）的牆：holes＝[(x0, x1, y0, y1)] 挖掉門、窗"""
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


# ======================= 結構：地板、後牆（門、大窗）、隔間的短牆、天花板（破洞、斷掉的前緣）、女兒的房間、牆上的字與相框 =======================
def build_shell():
    mb = MB("shell")
    mb.gquad((X0 - 0.4, 0, 4.2), (X1 + 0.4, 0, 4.2), (X1 + 0.4, 0, BACK), (X0 - 0.4, 0, BACK), "M_Floor")
    wall_x(mb, X0, X1, BACK, DOORS + [WINDOW], "M_Wallpaper")
    for x0, x1, y0, y1 in DOORS + [WINDOW]:
        reveal(mb, x0, x1, y0, y1, BACK, TH, "M_Wallpaper")
        mb.gquad((x0 - 0.08, y1, BACK + 0.02), (x1 + 0.08, y1, BACK + 0.02), (x1 + 0.08, y1 + 0.1, BACK + 0.02), (x0 - 0.08, y1 + 0.1, BACK + 0.02), "M_Wood", tile=0.5)
        if y0 == 0:                                        # 門框（左右）
            for xx in (x0 - 0.08, x1):
                mb.gquad((xx, 0, BACK + 0.02), (xx + 0.08, 0, BACK + 0.02), (xx + 0.08, y1, BACK + 0.02), (xx, y1, BACK + 0.02), "M_Wood", tile=0.5)
    wx0, wx1, wy0, wy1 = WINDOW                            # 大窗：窗框（破玻璃）、窗台
    mb.gquad((wx0, wy0, BACK - 0.1), (wx1, wy0, BACK - 0.1), (wx1, wy1, BACK - 0.1), (wx0, wy1, BACK - 0.1), "M_Window", px="all")
    p0, p1 = G(wx0 - 0.12, wy0 - 0.06, BACK + 0.12), G(wx1 + 0.12, wy0, BACK)
    mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], "M_Wood", tile=0.5)
    # 兩側的牆（往前 2 m）、隔間的短牆（客廳｜走廊｜餐廳，從後牆往前 1 m）
    for x, out in ((X0, -1), (X1, 1)):
        mb.gquad((x, 0, BACK), (x, 0, 2.0), (x, CEIL, 2.0), (x, CEIL, BACK), "M_Wallpaper", tile=WP, inside=(x + out, 1, 0))
    for x in (12.5, 22.0):
        p0, p1 = G(x - 0.08, 0, BACK + 1.0), G(x + 0.08, CEIL, BACK)
        mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], "M_Wallpaper", tile=WP, skip=("+y",))
    # 天花板：到 z 1.8（再往前會佔掉畫面上方太多），破洞上面有木頭的格柵；前緣斷得高低不一
    hx0, hx1, hz0, hz1 = HOLE
    zf = 1.8
    for a, b, c, d in ((X0, hx0, BACK, zf), (hx1, X1, BACK, zf), (hx0, hx1, hz1, zf)):
        mb.gquad((a, CEIL, c), (b, CEIL, c), (b, CEIL, d), (a, CEIL, d), "M_Ceiling")
    mb.gquad((hx0, CEIL, hz0), (hx0, CEIL, hz1), (hx0, CEIL + 0.2, hz1), (hx0, CEIL + 0.2, hz0), "M_Wood", tile=0.5, inside=(hx0 - 1, CEIL, -3))
    mb.gquad((hx1, CEIL, hz1), (hx1, CEIL, hz0), (hx1, CEIL + 0.2, hz0), (hx1, CEIL + 0.2, hz1), "M_Wood", tile=0.5, inside=(hx1 + 1, CEIL, -3))
    mb.gquad((hx0, CEIL, hz1), (hx1, CEIL, hz1), (hx1, CEIL + 0.2, hz1), (hx0, CEIL + 0.2, hz1), "M_Wood", tile=0.5, inside=(9, CEIL, hz1 + 1))
    for k in range(3):                                     # 破洞裡斷掉的格柵
        x = hx0 + 0.45 + k * 0.6
        L = 0.6 + 0.8 * h01(k, 701)
        mb.beam(G(x, CEIL + 0.1, hz1), G(x + 0.05, CEIL + 0.02 - 0.25 * h01(k, 702), hz1 - L), 0.08, "M_Wood")
    x, i = X0 - 0.4, 0                                     # 斷掉的前緣（往下垂一點的灰泥板）
    while x < X1 + 0.4:
        w = 0.6 + 0.8 * h01(i, 703)
        dz = 0.4 * h01(i, 704)
        mb.gquad((x, CEIL, zf + dz), (x + w, CEIL, zf + dz), (x + w, CEIL, zf), (x, CEIL, zf), "M_Ceiling", inside=(x, CEIL + 1, zf))
        mb.gquad((x, CEIL - 0.08, zf + dz), (x + w, CEIL - 0.08, zf + dz), (x + w, CEIL, zf + dz), (x, CEIL, zf + dz), "M_Ceiling", inside=(x, CEIL, zf - 1))
        x += w
        i += 1
    # 天花板以上：樓板的厚度（前緣）＋一面暗的遮擋面（擋住天花板上方看得到的窗外房子、天空平面；窗戶的視線往下，不會被擋到）
    mb.gquad((X0 - 0.4, CEIL, zf), (X1 + 0.4, CEIL, zf), (X1 + 0.4, CEIL + 0.3, zf), (X0 - 0.4, CEIL + 0.3, zf), "M_Wood", tile=0.5)
    mb.gquad((X0 - 8, CEIL + 0.2, BACK - TH - 0.01), (X1 + 8, CEIL + 0.2, BACK - TH - 0.01), (X1 + 8, 12.0, BACK - TH - 0.01), (X0 - 8, 12.0, BACK - TH - 0.01), "M_Dark")
    # 壁紙剝落（貼花，兩種隨機；避開門窗、牆上的字）
    for k, x in enumerate((2.6, 6.4, 11.9, 14.6, 19.9, 24.3, 32.2, 35.6)):
        y = 1.3 + 0.9 * h01(k, 705)
        s_ = 0.8 + 0.5 * h01(k, 706)
        u0 = 0 if h01(k, 707) < 0.5 else 32
        mb.gquad((x - s_ / 2, y - s_ / 2, BACK + 0.005), (x + s_ / 2, y - s_ / 2, BACK + 0.005), (x + s_ / 2, y + s_ / 2, BACK + 0.005),
                 (x - s_ / 2, y + s_ / 2, BACK + 0.005), "M_Peel", px=(u0, 0, u0 + 32, 32))
    # 牆上的蠟筆字（3 × 1 m，1.6～2.6 m）：B3-5c 從 0.62 m 往上移，主角站在互動點時頭頂只擋到牆上約 1.2 m、互動提示在 1.45～1.6 m
    cx, wy = 9.375, 1.6
    mb.gquad((cx - 1.5, wy, BACK + 0.01), (cx + 1.5, wy, BACK + 0.01), (cx + 1.5, wy + 1.0, BACK + 0.01), (cx - 1.5, wy + 1.0, BACK + 0.01), "M_Crayon", px="all")
    # 相框（三個；客廳兩個、走廊一個）：貼圖 80×32 每格 27 像素
    for k, (x, y) in enumerate(((4.4, 1.45), (5.1, 1.62), (21.2, 1.5))):
        w, hh = 0.39, 0.5
        p0, p1 = G(x - w / 2, y - hh / 2, BACK + 0.03), G(x + w / 2, y + hh / 2, BACK)
        mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], "M_Wood", tile=0.5, fit={"-y": ("M_Photos", (k * 27, 0, k * 27 + 26, 32))}, skip=("+y",))
    # 女兒的房間（後牆後面）：地板、牆、天花板、小窗、牆上的全家福
    kx0, kx1, kz = KID
    mb.gquad((kx0, 0, BACK - TH), (kx1, 0, BACK - TH), (kx1, 0, kz), (kx0, 0, kz), "M_Floor")
    wall_x(mb, kx0, kx1, kz, [(19.2, 20.1, 1.0, 1.8)], "M_WallKid")
    mb.gquad((19.2, 1.0, kz - 0.05), (20.1, 1.0, kz - 0.05), (20.1, 1.8, kz - 0.05), (19.2, 1.8, kz - 0.05), "M_KidWindow")
    reveal(mb, 19.2, 20.1, 1.0, 1.8, kz, 0.05, "M_WallKid")
    mb.gquad((19.6, 1.0, kz - 0.01), (19.7, 1.0, kz - 0.01), (19.7, 1.8, kz - 0.01), (19.6, 1.8, kz - 0.01), "M_Wood", tile=0.5)
    mb.gquad((kx0, 0, kz), (kx0, 0, BACK - TH), (kx0, CEIL, BACK - TH), (kx0, CEIL, kz), "M_WallKid", tile=WP, inside=(kx0 - 1, 1, -5))
    mb.gquad((kx1, 0, BACK - TH), (kx1, 0, kz), (kx1, CEIL, kz), (kx1, CEIL, BACK - TH), "M_WallKid", tile=WP, inside=(kx1 + 1, 1, -5))
    mb.gquad((kx0, CEIL, kz), (kx1, CEIL, kz), (kx1, CEIL, BACK - TH), (kx0, CEIL, BACK - TH), "M_Ceiling")
    # 全家福（1.5～1.97 m：主角站在門口時頭頂只擋到這面牆約 0.9 m，互動提示在 1.2～1.4 m 附近）
    mb.gquad((17.65, 1.5, kz + 0.01), (18.27, 1.5, kz + 0.01), (18.27, 1.97, kz + 0.01), (17.65, 1.97, kz + 0.01), "M_Drawing", px="all")
    # 女兒房間的門板（往裡面開 75°，鉸鏈在右邊）
    m = mb.mark()
    p0, p1 = G(17.42, 0.0, BACK - TH + 0.04), G(18.48, 2.08, BACK - TH)
    mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], "M_Wood", tile=0.5, fit={"-y": ("M_Door", "all"), "+y": ("M_Door", "all")})
    mb.xform(m, R('Z', -75, G(18.48, 0, BACK - TH)))
    # 大門（往裡面開 30°，鉸鏈在右邊；門外是人行道）
    m = mb.mark()
    p0, p1 = G(33.02, 0.0, BACK - TH + 0.05), G(34.18, 2.08, BACK - TH)
    mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], "M_Wood", tile=0.5, fit={"-y": ("M_Door", "all"), "+y": ("M_Door", "all")})
    mb.xform(m, R('Z', 30, G(34.18, 0, BACK - TH)))
    return mb.finish()


# ======================= 窗外（世界座標）：人行道、馬路、對街的房子（剪影）；天空在 Godot 用廢墟的像素天空平面 =======================
def build_outside():
    mb = MB("outside")
    z0 = BACK - TH
    mb.gquad((20.6, 0.0, z0), (40.0, 0.0, z0), (40.0, 0.0, -6.0), (20.6, 0.0, -6.0), "M_Sidewalk", tile=2.0)
    mb.gquad((20.6, -0.15, -6.0), (40.0, -0.15, -6.0), (40.0, 0.0, -6.0), (20.6, 0.0, -6.0), "M_Sidewalk", tile=0.5, inside=(30, -1, -5))
    mb.gquad((14.0, -0.15, -6.0), (44.0, -0.15, -6.0), (44.0, -0.15, -13.0), (14.0, -0.15, -13.0), "M_Asphalt", tile=2.0)
    mb.gquad((14.0, -0.15, -13.0), (44.0, -0.15, -13.0), (44.0, -0.15, -30.0), (14.0, -0.15, -30.0), "M_Sidewalk", tile=2.0)
    for x0 in (16.0, 30.0):                                # 對街的房子（14 × 6 m 一張，兩張錯開）
        mb.gquad((x0, -0.15, -14.0 - (x0 - 16.0) * 0.1), (x0 + 14, -0.15, -14.0 - (x0 - 16.0) * 0.1), (x0 + 14, 5.85, -14.0 - (x0 - 16.0) * 0.1), (x0, 5.85, -14.0 - (x0 - 16.0) * 0.1), "M_Houses", px="all")
    return mb.finish()


# ======================= 家具（原點在底部中心；-y 朝鏡頭） =======================
def build_bookshelf():
    """書架：往右歪（靠在牆上），正面是書（貼圖），側面木頭"""
    mb = MB("bookshelf")
    m = mb.mark()
    mb.box(-0.45, 0.45, -0.17, 0.17, 0.0, 2.0, "M_Wood", tile=0.5, fit={"-y": ("M_Shelf", "all")})
    mb.xform(m, R('Y', 7, (0.45, 0, 0)))
    for k in range(4):                                     # 掉在地上的書
        mm = mb.mark()
        mb.box(-0.12, 0.12, -0.08, 0.08, 0.0, 0.04, "M_Cloth" if k % 2 else "M_Paper", tile=0.25)
        mb.xform(mm, Matrix.Translation((-0.7 + k * 0.22, -0.35 - 0.1 * (k % 2), k % 2 * 0.04)) @ R('Z', 30 * k - 20))
    return mb.finish()


def build_sofa():
    """破掉的沙發：座墊、靠背、扶手、短腳；一個座墊滑出來斜躺"""
    mb = MB("sofa")
    W, D = 1.1, 0.42
    for x in (-0.95, -0.7, 0.7, 0.95):
        for y in (-0.3, 0.3):
            mb.cbox(x if abs(x) > 0.8 else x * 1.3, y, 0.06, 0.06, 0.0, 0.1, "M_Wood", tile=0.25)
    mb.box(-W, W, -D, D, 0.1, 0.3, "M_Sofa", tile=1.0)
    mb.box(-W, W, D - 0.22, D, 0.3, 0.88, "M_Sofa", tile=1.0)
    for x in (-W, W - 0.18):
        mb.box(x, x + 0.18, -D, D, 0.3, 0.62, "M_Sofa", tile=1.0)
    mb.box(-W + 0.18, -0.02, -D + 0.02, D - 0.22, 0.3, 0.44, "M_Sofa", tile=1.0)
    m = mb.mark()
    mb.box(-0.45, 0.45, -0.2, 0.2, 0.0, 0.14, "M_Sofa", tile=1.0)
    mb.xform(m, Matrix.Translation((0.55, -0.42, 0.12)) @ R('X', -25) @ R('Z', 12))
    return mb.finish()


def build_floor_lamp():
    """落地燈：圓座、細桿、歪掉的燈罩（沒有電，不亮）"""
    mb = MB("floor_lamp")
    mb.cyl((0, 0, 0.02), 'Z', 0.16, 0.04, "M_Metal", seg=10)
    mb.beam((0, 0, 0.04), (0.02, 0, 1.5), 0.03, "M_Metal")
    m = mb.mark()
    r0, r1, hh, n = 0.13, 0.22, 0.28, 10
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        mb.face([(r1 * math.cos(a0), r1 * math.sin(a0), 0), (r1 * math.cos(a1), r1 * math.sin(a1), 0),
                 (r0 * math.cos(a1), r0 * math.sin(a1), hh), (r0 * math.cos(a0), r0 * math.sin(a0), hh)], "M_Shade", tile=0.25)
    mb.xform(m, Matrix.Translation((0.02, 0, 1.38)) @ R('Y', 18))
    return mb.finish()


def build_coffee_table():
    """翻倒的矮桌：桌面立起來、四隻腳朝外"""
    mb = MB("coffee_table")
    m = mb.mark()
    mb.box(-0.5, 0.5, -0.28, 0.28, 0.38, 0.43, "M_Wood", tile=0.5)
    for x in (-0.44, 0.44):
        for y in (-0.22, 0.22):
            mb.cbox(x, y, 0.05, 0.05, 0.0, 0.38, "M_Wood", tile=0.25)
    mb.xform(m, Matrix.Translation((0, 0.0, 0.28)) @ R('X', 90) @ Matrix.Translation((0, 0, -0.43)))
    return mb.finish()


def build_wardrobe():
    """倒下的衣櫃（擋路）：躺著、櫃門朝上（一扇半開），長 1.9 m"""
    mb = MB("wardrobe")
    L, Wd, Hh = 0.95, 0.3, 0.6
    mb.box(-L, L, -Wd, Wd, 0.0, Hh, "M_Wood", tile=0.5, skip=("+z",))
    mb.box(-L, L, -Wd, Wd, Hh - 0.03, Hh, "M_Wood", tile=0.5, skip=("-z",))
    for x0 in (-L + 0.04, 0.02):
        mb.box(x0, x0 + L - 0.06, -Wd + 0.04, Wd - 0.04, Hh, Hh + 0.02, "M_Door", tile=0.5,
               fit={"+z": ("M_Door", (2, 2, 30, 66))})
    m = mb.mark()
    mb.box(0.02, L - 0.04, -Wd + 0.04, Wd - 0.04, 0, 0.02, "M_Door", tile=0.5, fit={"+z": ("M_Door", (2, 2, 30, 66))})
    mb.xform(m, Matrix.Translation((0, 0, Hh + 0.02)) @ R('X', -40, (0, -Wd + 0.04, 0)))
    mb.cbox(-0.06, -0.1, 0.03, 0.12, Hh + 0.02, Hh + 0.05, "M_Brass")
    for k in range(3):                                     # 掉出來的衣服
        mm = mb.mark()
        mb.box(-0.25, 0.25, -0.12, 0.12, 0.0, 0.05, "M_Cloth", tile=0.5)
        mb.xform(mm, Matrix.Translation((0.3 + k * 0.3, -0.45 - 0.08 * k, 0)) @ R('Z', 25 * k - 10))
    return mb.finish()


def build_dining():
    """餐桌與三張椅子（一張倒在地上），桌上的盤子"""
    mb = MB("dining")
    mb.box(-0.7, 0.7, -0.4, 0.4, 0.71, 0.75, "M_Wood", tile=0.5)
    for x in (-0.64, 0.64):
        for y in (-0.34, 0.34):
            mb.cbox(x, y, 0.05, 0.05, 0.0, 0.71, "M_Wood", tile=0.25)
    def chair(m0, M):
        for x in (-0.18, 0.18):
            for y in (-0.18, 0.18):
                mb.cbox(x, y, 0.04, 0.04, 0.0, 0.45, "M_Wood", tile=0.25)
        mb.box(-0.21, 0.21, -0.21, 0.21, 0.45, 0.49, "M_Wood", tile=0.25)
        mb.box(-0.21, 0.21, 0.17, 0.21, 0.49, 0.95, "M_Wood", tile=0.25)
        mb.xform(m0, M)
    chair(mb.mark(), Matrix.Translation((-0.35, 0.55, 0)) @ R('Z', 180))
    chair(mb.mark(), Matrix.Translation((0.95, 0.05, 0)) @ R('Z', 100))
    chair(mb.mark(), Matrix.Translation((-1.25, -0.25, 0.21)) @ R('Z', -60) @ R('X', 90, (0, 0.21, 0)) @ Matrix.Translation((0, 0, -0.21)))
    for k, (x, y) in enumerate(((-0.35, 0.05), (0.3, -0.1))):
        mb.cyl((x, y, 0.765), 'Z', 0.11, 0.02, "M_Metal", seg=10)
    return mb.finish()


def build_counter():
    """流理台：正面是櫃門（貼圖集左半），檯面、水槽、牆上的吊櫃（一扇掉了）"""
    mb = MB("counter")
    mb.box(-1.4, 1.4, -0.3, 0.3, 0.0, 0.88, "M_Metal", tile=0.5, fit={"-y": ("M_Kitchen", (0, 0, 90, 29))})
    mb.box(-1.43, 1.43, -0.33, 0.3, 0.88, 0.92, "M_Metal", tile=0.5)
    mb.box(0.2, 0.75, -0.2, 0.15, 0.86, 0.925, "M_Dark")
    mb.beam((0.65, 0.22, 0.92), (0.65, 0.22, 1.15), 0.03, "M_Metal")
    mb.beam((0.65, 0.22, 1.15), (0.65, 0.05, 1.15), 0.03, "M_Metal")
    mb.box(-1.4, 0.4, -0.18, 0.18, 1.45, 2.1, "M_Wood", tile=0.5)
    m = mb.mark()
    mb.box(0.4, 0.9, -0.2, -0.18, 0.0, 0.62, "M_Wood", tile=0.5)
    mb.xform(m, Matrix.Translation((0.3, -0.5, 0.0)) @ R('Y', -70, (0.4, 0, 0)))
    for k in range(3):
        mb.cyl((-1.0 + k * 0.25, 0.0, 0.97), 'Z', 0.05, 0.1, "M_Cloth" if k == 1 else "M_Metal", seg=8)
    return mb.finish()


def build_fridge():
    """冰箱：正面是貼圖集右半（把手、褪色的紙），往前歪一點"""
    mb = MB("fridge")
    m = mb.mark()
    mb.box(-0.4, 0.4, -0.35, 0.35, 0.0, 1.8, "M_Metal", tile=0.5, fit={"-y": ("M_Kitchen", (92, 0, 118, 58))})
    mb.xform(m, R('X', -3, (0, -0.35, 0)))
    return mb.finish()


def build_kid_bed():
    """女兒的小床：木框、床墊、疊得整整齊齊的被子、枕頭；床邊的小凳子"""
    mb = MB("kid_bed")
    mb.box(-0.85, 0.85, -0.42, 0.42, 0.1, 0.32, "M_Wood", tile=0.5)
    for x in (-0.82, 0.82):
        for y in (-0.39, 0.39):
            mb.cbox(x, y, 0.06, 0.06, 0.0, 0.1, "M_Wood", tile=0.25)
    mb.box(-0.9, -0.82, -0.42, 0.42, 0.0, 0.75, "M_Wood", tile=0.5)
    mb.box(-0.82, 0.82, -0.4, 0.4, 0.32, 0.45, "M_Cloth", tile=0.5)
    mb.box(0.15, 0.75, -0.3, 0.3, 0.45, 0.6, "M_Quilt", tile=0.5)
    mb.box(-0.78, -0.35, -0.25, 0.25, 0.45, 0.56, "M_Quilt", tile=0.5)
    mb.box(0.95, 1.25, -0.15, 0.15, 0.0, 0.3, "M_Wood", tile=0.5)
    return mb.finish()


# ======================= 前景（z 約 ＋3.3，要低、不擋主角） =======================
def build_hanging_board():
    """從天花板前緣斷掉垂下來的木條（頂端在 2.7 m，斜斜往下到 1.95 m；放在走道上方，不擋主角）"""
    mb = MB("hanging_board")
    mb.beam((-0.6, 0, 2.7), (0.5, -0.05, 1.95), 0.12, "M_Wood")
    mb.beam((0.1, 0.05, 2.7), (0.35, 0.0, 2.25), 0.08, "M_Wood")
    return mb.finish()


def build_doorframe():
    """斷掉的門框（前景、低）：一根直的斷在 0.9 m，一根橫的掉在地上"""
    mb = MB("doorframe")
    mb.box(-0.06, 0.06, -0.06, 0.06, 0.0, 0.85, "M_Wood", tile=0.5)
    mb.beam((-0.06, 0, 0.85), (0.05, 0, 0.95), 0.12, "M_Wood")
    mb.beam((0.25, -0.1, 0.05), (1.3, 0.1, 0.05), 0.1, "M_Wood")
    return mb.finish()


def build_all():
    for fn in BUILDERS:
        fn()


BUILDERS = [build_shell, build_outside, build_bookshelf, build_sofa, build_floor_lamp, build_coffee_table, build_wardrobe, build_dining,
            build_counter, build_fridge, build_kid_bed, build_hanging_board, build_doorframe]


# ======================= B3-5b 預覽時的擺放位置（Godot 座標 x, y, z, 繞 y 軸轉幾度；B3-5c 照這份放進 Home3D） =======================
# shell、outside 放在原點；衣櫃放在 Near/Wardrobe（13.75, 0, 0.26）底下取代 2D 的像素圖；天空用 ruins/sky（平面放在 z −45）。
# 借用：common/papers、common/plank（地上的前景）；熊布偶、蠟筆、相框的小像素圖（Near）照舊。
PLACE = {
    "bookshelf": [(1.9, 0, -3.25, 0)], "sofa": [(5.3, 0, -3.0, 0)], "floor_lamp": [(7.3, 0, -3.25, 0)],
    "coffee_table": [(11.6, 0, -2.4, 15)], "wardrobe": [(13.75, 0, 0.26, 10)], "dining": [(23.9, 0, -2.5, 0)],
    "counter": [(31.0, 0, -3.28, 0)], "fridge": [(35.2, 0, -3.2, -6)], "kid_bed": [(16.8, 0, -6.7, 0)],
    "hanging_board": [(3.0, 0, 1.7, 0), (30.0, 0, 1.7, 180)], "doorframe": [(13.0, 0, 3.3, 0)],
}
BORROWED = {"common/papers": [(28.9, 0, 2.3, 0)], "common/plank": [(20.0, 0, 2.4, 30)]}
