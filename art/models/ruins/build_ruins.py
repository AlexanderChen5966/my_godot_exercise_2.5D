# B3-4b 廢墟的模型（在 Blender 裡執行：exec(open(這個檔案).read())，再呼叫 build_all() 或單一個 build_xxx()）。
# 共用的 MB 類別、G()、R() 和設施走廊（art/models/lab/build_lab.py）相同（沒有貼圖的發光、單色材質用 GLOW／SOLID）。
# 座標：結構 shell、電線 wires 直接用區域的座標（Godot 的 x、y、z，用 G() 換成 Blender：Y＝負的 Godot z、Z 朝上）；
# 其他物件的原點在自己的底部中心（Blender 座標，-y 那面朝鏡頭），到 Godot 再擺位置（PLACE）。貼圖 32 像素＝1 m。
# 借用：街道的柏油、標線、人行道貼圖，模型 street/utility_pole、street/burnt_car、street/far（遠處剪影）、common/ 的碎石與磚塊。
import bpy, bmesh, math
from mathutils import Vector, Matrix

ROOT = "/Users/alexander/Desktop/Speckit Project/失語者/失語者_2.5D/"
T = ROOT + "assets/textures/"
# 材質名稱 → (貼圖, 透明, 雙面)
TEX = {
    "M_Asphalt": ("street/asphalt.png", False, False), "M_Lane": ("street/lane.png", False, False),
    "M_Sidewalk": ("street/sidewalk.png", False, False), "M_Concrete": ("ruins/concrete_ruin.png", False, False),
    "M_Sandbag": ("ruins/sandbag.png", False, False), "M_Fence": ("ruins/fence.png", True, True),
    "M_Barbed": ("ruins/barbed.png", True, True), "M_Corrugated": ("ruins/corrugated.png", False, True),
    "M_WindowLit": ("ruins/window_lit.png", False, False), "M_SignHome": ("ruins/sign_home.png", False, False),
    "M_RedCross": ("ruins/red_cross.png", False, False), "M_NoEntry": ("ruins/no_entry.png", True, False),
    "M_Cracks": ("ruins/cracks.png", True, False), "M_Drum": ("ruins/drum.png", False, False),
    "M_Brick": ("common/brick.png", False, False), "M_Burnt": ("common/burnt.png", False, False),
    "M_Wood": ("common/wood.png", False, False), "M_Metal": ("common/metal.png", False, False),
    "M_Hazard": ("common/hazard.png", False, False), "M_Ground": ("common/floor.png", False, False),
    "M_Far": ("street/far.png", False, False),
}
GLOW = {"M_Ember": (1.0, 0.45, 0.15, 1)}
SOLID = {"M_Dark": (0.03, 0.025, 0.02, 1), "M_Rebar": (0.28, 0.17, 0.1, 1), "M_Wire": (0.05, 0.05, 0.05, 1)}
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


def floor_decal(mb, pts, mname, uvs):
    """地上的貼花（朝上）：pts 是 Godot 座標"""
    c = sum((Vector(G(*p)) for p in pts), Vector()) / len(pts)
    mb.face([G(*p) for p in pts], mname, uvs=uvs, inside=(c.x, c.y, c.z - 1))


# ======================= 結構：馬路、人行道、倒塌的樓（斷牆＋缺口）、缺口裡的瓦礫堆 =======================
FRONT_Z = -5.2                                              # 樓的正面
BLOCKS = [(0.0, 5.0, 8.0, False), (7.0, 11.5, 3.0, False), (14.0, 18.5, 7.0, True), (29.5, 36.0, 5.0, False)]   # (x0, x1, 高, 燒黑)
GAPS = [(5.0, 7.0), (11.5, 14.0), (18.5, 23.0)]           # 缺口（看得到天空、遠處剪影）；23～29.5 是避難所


def jag(x0, x1, seed, amp):
    """斷掉的牆頂：x0～x1 之間高低不一的點（回傳 (x, 往上多少)）"""
    pts, x, i = [], x0, 0
    while x < x1 - 0.05:
        pts.append((x, amp * h01(i, seed)))
        x += 0.35 + 0.4 * h01(i + 50, seed)
        i += 1
    pts.append((x1, amp * h01(i, seed)))
    return pts


def h01(i, s):
    n = (i * 374761393 + s * 668265263) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def build_shell():
    mb = MB("shell")
    # 馬路（裂縫、褪色的中線）與前後人行道、後面的路緣
    mb.gquad((-1, 0, 2.6), (37, 0, 2.6), (37, 0, -3.3), (-1, 0, -3.3), "M_Asphalt", tile=2.0)
    for x in range(0, 36, 3):
        if h01(x, 401) < 0.25:
            continue                                       # 有幾段褪掉了
        mb.gquad((x, 0.004, 0.06), (x + 1.5, 0.004, 0.06), (x + 1.5, 0.004, -0.06), (x, 0.004, -0.06), "M_Lane", tile=0.5)
    mb.gquad((-1, 0.15, 4.2), (37, 0.15, 4.2), (37, 0.15, 2.6), (-1, 0.15, 2.6), "M_Sidewalk", tile=2.0)
    mb.gquad((-1, 0.15, -3.3), (37, 0.15, -3.3), (37, 0.15, FRONT_Z), (-1, 0.15, FRONT_Z), "M_Sidewalk", tile=2.0)
    mb.gquad((-1, 0, -3.3), (37, 0, -3.3), (37, 0.15, -3.3), (-1, 0.15, -3.3), "M_Sidewalk", tile=0.5)
    mb.gquad((-1, 0.0, FRONT_Z), (37, 0.0, FRONT_Z), (37, 0.0, -14), (-1, 0.0, -14), "M_Ground", tile=2.0)
    for i, (cx, cz, ang) in enumerate(((3.0, -0.5, 10), (10.0, 1.2, -15), (20.5, -2.0, 5), (27.0, 0.8, -25), (34.0, -1.0, 20))):
        a = math.radians(ang)
        pts = [(cx + dx * math.cos(a) - dz * math.sin(a), 0.006, cz + dx * math.sin(a) + dz * math.cos(a))
               for dx, dz in ((-1, 0.5), (1, 0.5), (1, -0.5), (-1, -0.5))]
        floor_decal(mb, pts, "M_Cracks", [(0, 0), (1, 0), (1, 1), (0, 1)])
    # 倒塌的樓：正面有窗洞（後面是暗的）、斷掉的牆頂、外露的樓板與鋼筋、兩側的牆
    z = FRONT_Z
    for bi, (x0, x1, top, burnt) in enumerate(BLOCKS):
        M = "M_Burnt" if burnt else "M_Concrete"
        full = math.floor(top / 3.0) * 3.0 if top >= 3 else 0.0
        wins = []                                          # (wx0, wx1, wy0, wy1)
        for f in range(int(full // 3)):
            for k in range(int((x1 - x0) // 2)):
                wx = x0 + 0.6 + k * 2.0
                if wx + 1.2 <= x1 - 0.3 and h01(f * 10 + k, 402 + bi) > 0.12:
                    wins.append((wx, wx + 1.2, f * 3.0 + 0.9, f * 3.0 + 2.3))
        cuts = sorted({x0, x1} | {w[0] for w in wins} | {w[1] for w in wins})
        for a, b in zip(cuts, cuts[1:]):
            ys = sorted({0.0, full} | {w[2] for w in wins if w[0] <= a and b <= w[1]} | {w[3] for w in wins if w[0] <= a and b <= w[1]})
            for y0, y1 in zip(ys, ys[1:]):
                if any(w[0] <= a and b <= w[1] and w[2] <= y0 and y1 <= w[3] for w in wins):
                    continue                               # 窗洞
                mb.gquad((a, y0, z), (b, y0, z), (b, y1, z), (a, y1, z), M, tile=2.0)
        for wx0, wx1, wy0, wy1 in wins:                    # 窗洞：裡面暗、上下左右的厚度
            mb.gquad((wx0, wy0, z - 0.3), (wx1, wy0, z - 0.3), (wx1, wy1, z - 0.3), (wx0, wy1, z - 0.3), "M_Dark")
            mb.gquad((wx0, wy0, z), (wx0, wy0, z - 0.3), (wx0, wy1, z - 0.3), (wx0, wy1, z), M, tile=2.0)
            mb.gquad((wx1, wy0, z - 0.3), (wx1, wy0, z), (wx1, wy1, z), (wx1, wy1, z - 0.3), M, tile=2.0)
            mb.gquad((wx0, wy0, z), (wx1, wy0, z), (wx1, wy0, z - 0.3), (wx0, wy0, z - 0.3), M, tile=2.0)
        # 斷掉的牆頂（full 以上到 top，再往上高低不一）
        base = max(full, top - 0.7)                        # 斷口從這個高度往上長（只剩一層的樓 top＝full，不能低於樓層線）
        jp = jag(x0, x1, 410 + bi, 1.4)
        pts = [G(x0, full, z), G(x1, full, z)] + [G(x, base + dy, z) for x, dy in reversed(jp)]
        mb.face(pts, M, inside=G((x0 + x1) / 2, full + 0.5, z - 1))
        # 外露的樓板（每層一片，往前凸、斷得長短不一）與鋼筋
        for f in range(1, int(full // 3) + 1):
            y = f * 3.0
            ex0 = x0 - 0.3 * h01(f, 420 + bi)
            ex1 = x1 + 0.3 * h01(f + 5, 420 + bi)
            p0, p1 = G(ex0, y - 0.12, z + 0.25 + 0.2 * h01(f, 421)), G(ex1, y + 0.08, z)
            mb.box(p0[0], p1[0], p0[1], p1[1], p0[2], p1[2], M, tile=2.0, skip=("+y",))
            for k in range(3):
                rx = ex0 + (ex1 - ex0) * (0.2 + 0.3 * k)
                a = Vector(G(rx, y - 0.02, z + 0.25))
                mb.beam(a, a + Vector((0.1 * (k - 1), -0.25 - 0.2 * h01(k, 422 + f), -0.15 * h01(k, 423))), 0.02, "M_Rebar")
        # 兩側的牆（往後 6 m）
        mb.gquad((x0, 0, z - 6.0), (x0, 0, z), (x0, base, z), (x0, base, z - 6.0), M, tile=2.0)
        mb.gquad((x1, 0, z), (x1, 0, z - 6.0), (x1, base, z - 6.0), (x1, base, z), M, tile=2.0)
    # 缺口裡的瓦礫堆（斜坡＋散落的碎塊、磚）
    for gi, (x0, x1) in enumerate(GAPS):
        hh = 1.2 + 0.6 * h01(gi, 430)
        a, b, c, d = G(x0, 0, z), G(x1, 0, z), G(x1 - 0.5, hh, z - 1.6), G(x0 + 0.5, hh, z - 1.6)
        mb.face([a, b, c, d], "M_Concrete", inside=G((x0 + x1) / 2, 0, z - 3))
        e, f_ = G(x1 - 0.2, 0, z - 3.5), G(x0 + 0.2, 0, z - 3.5)
        mb.face([d, c, e, f_], "M_Concrete", inside=G((x0 + x1) / 2, 0, z - 1.6))
        mb.face([a, d, f_], "M_Concrete", inside=G(x1, 0, z - 1.6))
        mb.face([b, e, c], "M_Concrete", inside=G(x0, 0, z - 1.6))
        for k in range(5):
            cx = x0 + 0.3 + (x1 - x0 - 0.6) * h01(k, 431 + gi)
            cz = z + 0.4 - 1.2 * h01(k + 9, 431 + gi)
            s = 0.18 + 0.2 * h01(k + 3, 432)
            m = mb.mark()
            p = G(cx, 0, cz)
            mb.box(p[0] - s, p[0] + s, p[1] - s * 0.7, p[1] + s * 0.7, 0, s * 0.9, "M_Brick" if k % 2 else "M_Concrete", tile=1.0)
            mb.xform(m, R('Z', 40 * h01(k, 433), p) @ R('X', 12 * (h01(k, 434) - 0.5), p))
    return mb.finish()


# ======================= 遠處的剪影（世界座標）：比街道的 street/far 低、斷斷續續，缺口上面看得到天空 =======================
def build_far():
    """遠處倒塌的高樓：高 5～13 m、牆頂斷得高低不一，中間有空隙（街道的遠景 19 m 高，會把天空整片擋住）"""
    mb = MB("far_ruins")
    x, i = -8.0, 0
    while x < 44:
        w = 3.0 + 3.5 * h01(i, 460)
        if h01(i, 461) > 0.25:                             # 有些位置空著
            zf = -15.0 - 10.0 * h01(i, 462)
            top = 5.0 + 8.0 * h01(i, 463)
            jp = jag(x, x + w, 470 + i, 2.0)
            pts = [G(x, 0, zf), G(x + w, 0, zf)] + [G(xx, top + dy, zf) for xx, dy in reversed(jp)]
            mb.face(pts, "M_Far", tile=4.0, inside=G(x + w / 2, 1, zf - 1))
            mb.gquad((x, 0, zf - 3), (x, 0, zf), (x, top, zf), (x, top, zf - 3), "M_Far", tile=4.0)
            mb.gquad((x + w, 0, zf), (x + w, 0, zf - 3), (x + w, top, zf - 3), (x + w, top, zf), "M_Far", tile=4.0)
        x += w + 1.5 + 3.0 * h01(i, 464)
        i += 1
    return mb.finish()


# ======================= 電線（世界座標）：三根電線桿之間下垂的電線、斷掉垂到地上的一條 =======================
POLES = [(2.0, -3.7, 8.0), (16.6, -3.7, -10.0), (31.0, -3.7, 0.0)]   # (x, z, 往左右歪幾度；Godot 繞 z 軸)


def pole_point(i, dx, hy):
    """第 i 根電線桿上、橫擔 dx、高 hy 的點（Godot 座標，含歪斜）"""
    x, zz, t = POLES[i]
    t = math.radians(t)
    return (x + dx * math.cos(t) - hy * math.sin(t), 0.15 + dx * math.sin(t) + hy * math.cos(t), zz)


def build_wires():
    mb = MB("wires")
    for i in range(len(POLES) - 1):
        for dx, hy, sag in ((0.7, 8.3, 1.6), (-0.7, 8.3, 1.3), (0.3, 7.6, 2.2)):
            a, b = Vector(pole_point(i, dx, hy)), Vector(pole_point(i + 1, -dx, hy))
            n = 10
            pts = [a.lerp(b, k / n) - Vector((0, sag * 4 * (k / n) * (1 - k / n), 0)) for k in range(n + 1)]
            for p, q in zip(pts, pts[1:]):
                mb.beam(G(*p), G(*q), 0.025, "M_Wire")
    top = Vector(pole_point(2, 0.7, 8.3))                  # 斷掉的一條：從最右邊的電線桿垂到地上
    pts = [top, top + Vector((0.4, -2.5, 0.3)), top + Vector((0.9, -5.5, 0.9)), Vector((32.6, 0.03, -2.2)), Vector((33.4, 0.03, -2.0))]
    for p, q in zip(pts, pts[1:]):
        mb.beam(G(*p), G(*q), 0.025, "M_Wire")
    return mb.finish()


# ======================= 避難所（原點在圍欄中間的地面；-y 朝鏡頭） =======================
def build_shelter():
    """鐵絲網圍欄（上面有刺網、紅十字牌，門開著）、後面的鐵皮屋（窗戶亮著）、營火、沙包"""
    mb = MB("shelter")
    X0, X1, GATE = -2.9, 2.9, (-0.5, 0.7)
    D = 3.4                                                # 圍欄往後的深度
    mb.quad((X0 - 0.2, 0.0, 0.16), (X1 + 0.2, 0.0, 0.16), (X1 + 0.2, 8.4, 0.16), (X0 - 0.2, 8.4, 0.16), "M_Ground", tile=2.0)
    def fence(p0, p1):
        p0, p1 = Vector(p0), Vector(p1)
        mb.face([p0, p1, p1 + Vector((0, 0, 2.0)), p0 + Vector((0, 0, 2.0))], "M_Fence", tile=1.0)
        mb.face([p0 + Vector((0, 0, 2.0)), p1 + Vector((0, 0, 2.0)), p1 + Vector((0, 0, 2.28)), p0 + Vector((0, 0, 2.28))], "M_Barbed",
                uvs=[(0, 0), ((p1 - p0).length, 0), ((p1 - p0).length, 1), (0, 1)])
        n = max(1, round((p1 - p0).length / 1.45))
        for k in range(n + 1):
            q = p0.lerp(p1, k / n)
            mb.beam(q, q + Vector((0, 0, 2.3)), 0.05, "M_Metal")
    fence((X0, 0, 0.16), (GATE[0], 0, 0.16)); fence((GATE[1], 0, 0.16), (X1, 0, 0.16))
    fence((X0, D, 0.16), (X0, 0, 0.16)); fence((X1, 0, 0.16), (X1, D, 0.16))
    m = mb.mark()                                          # 開著的門（往外開 50°）
    fence((GATE[0], 0, 0.16), (GATE[1], 0, 0.16))
    mb.xform(m, R('Z', -50, (GATE[0], 0, 0)))
    mb.quad((0.95, -0.02, 1.15), (1.25, -0.02, 1.15), (1.25, -0.02, 1.45), (0.95, -0.02, 1.45), "M_RedCross", px="all")
    # 鐵皮屋
    sx0, sx1, sy0, sy1, hf, hb = -2.0, 2.0, 3.8, 6.8, 2.4, 2.0
    door, win = (-1.4, -0.6), (0.3, 1.05, 1.0, 1.6)
    for a, b, y0, y1 in ((sx0, door[0], 0.16, hf), (door[0], door[1], 2.1, hf), (door[1], win[0], 0.16, hf),
                         (win[0], win[1], 0.16, win[2]), (win[0], win[1], win[3], hf), (win[1], sx1, 0.16, hf)):
        mb.quad((a, sy0, y0), (b, sy0, y0), (b, sy0, y1), (a, sy0, y1), "M_Corrugated", tile=1.0)
    mb.quad((door[0], sy0 + 0.05, 0.16), (door[1], sy0 + 0.05, 0.16), (door[1], sy0 + 0.05, 2.1), (door[0], sy0 + 0.05, 2.1), "M_Dark")
    m = mb.mark()                                          # 半開的門板
    mb.quad((door[0], sy0, 0.16), (door[1], sy0, 0.16), (door[1], sy0, 2.1), (door[0], sy0, 2.1), "M_Corrugated", tile=1.0)
    mb.xform(m, R('Z', 35, (door[0], sy0, 0)))
    mb.quad((win[0], sy0 - 0.01, win[2]), (win[1], sy0 - 0.01, win[2]), (win[1], sy0 - 0.01, win[3]), (win[0], sy0 - 0.01, win[3]), "M_WindowLit", px="all")
    mb.quad((sx0, sy1, 0.16), (sx0, sy0, 0.16), (sx0, sy0, hf), (sx0, sy1, hb), "M_Corrugated", tile=1.0)
    mb.quad((sx1, sy0, 0.16), (sx1, sy1, 0.16), (sx1, sy1, hb), (sx1, sy0, hf), "M_Corrugated", tile=1.0)
    mb.face([(sx0 - 0.2, sy0 - 0.4, hf + 0.05), (sx1 + 0.2, sy0 - 0.4, hf + 0.05), (sx1 + 0.2, sy1 + 0.2, hb), (sx0 - 0.2, sy1 + 0.2, hb)],
            "M_Corrugated", tile=1.0, inside=(0, 5, 0))
    # 營火（石頭圍一圈、燒黑的木頭、炭火）
    fx, fy = 1.9, 2.2
    for k in range(8):
        a = 2 * math.pi * k / 8
        mb.cbox(fx + 0.38 * math.cos(a), fy + 0.38 * math.sin(a), 0.16, 0.14, 0.16, 0.28, "M_Concrete", tile=0.5)
    for a in (20, 80, 140):
        r = math.radians(a)
        mb.beam((fx - 0.3 * math.cos(r), fy - 0.3 * math.sin(r), 0.2), (fx + 0.3 * math.cos(r), fy + 0.3 * math.sin(r), 0.28), 0.07, "M_Burnt")
    mb.quad((fx - 0.22, fy - 0.22, 0.2), (fx + 0.22, fy - 0.22, 0.2), (fx + 0.22, fy + 0.22, 0.2), (fx - 0.22, fy + 0.22, 0.2), "M_Ember", tile=0.5)
    # 圍欄內側的沙包
    mb.box(-2.7, -1.2, 0.15, 0.55, 0.16, 0.66, "M_Sandbag", tile=(1.0, 0.5))
    return mb.finish()


# ======================= 路上的東西（原點在底部中心） =======================
def build_barricade():
    """路障：三層沙包＋靠在上面的鐵板"""
    mb = MB("barricade")
    for k, (w, d) in enumerate(((1.2, 0.3), (1.05, 0.26), (0.8, 0.22))):
        mb.box(-w, w, -d, d, k * 0.25, k * 0.25 + 0.25, "M_Sandbag", tile=(1.0, 0.5))
    m = mb.mark()
    mb.box(0.1, 1.1, -0.02, 0.02, 0.0, 1.3, "M_Metal", tile=1.0)
    mb.xform(m, Matrix.Translation((0, 0.5, 0)) @ R('X', 18) @ R('Z', 8))
    return mb.finish()


def build_barrier():
    """拒馬（擋路）：橫的木樑、三組 X 形的腳、鐵絲網、黃色的警示牌"""
    mb = MB("barrier")
    mb.beam((-1.0, 0, 0.45), (1.0, 0, 0.45), 0.1, "M_Wood")
    for x in (-0.85, 0.0, 0.85):
        mb.beam((x, -0.45, 0.0), (x, 0.45, 0.9), 0.07, "M_Wood")
        mb.beam((x, 0.45, 0.0), (x, -0.45, 0.9), 0.07, "M_Wood")
    for zz in (0.22, 0.58):
        mb.quad((-1.0, -0.12, zz), (1.0, -0.12, zz), (1.0, -0.12, zz + 0.25), (-1.0, -0.12, zz + 0.25), "M_Barbed", tile=(1.0, 0.25))
    mb.box(-0.25, 0.25, -0.1, -0.06, 0.32, 0.56, "M_Metal", fit={"-y": ("M_Hazard", "all")})
    return mb.finish()


def build_drum():
    """火桶：鏽鐵桶（貼圖包一圈）、裡面燒黑、上面的炭火（火焰在 Godot 放像素動畫）"""
    mb = MB("drum")
    r, hh, n = 0.29, 0.9, 12
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        p = [(r * math.cos(a0), r * math.sin(a0), 0), (r * math.cos(a1), r * math.sin(a1), 0),
             (r * math.cos(a1), r * math.sin(a1), hh), (r * math.cos(a0), r * math.sin(a0), hh)]
        mb.face(p, "M_Drum", uvs=[(i / n, 0), ((i + 1) / n, 0), ((i + 1) / n, 1), (i / n, 1)], inside=(0, 0, hh / 2))
        q = [(r * 0.95 * math.cos(a1), r * 0.95 * math.sin(a1), 0.5), (r * 0.95 * math.cos(a0), r * 0.95 * math.sin(a0), 0.5),
             (r * 0.95 * math.cos(a0), r * 0.95 * math.sin(a0), hh), (r * 0.95 * math.cos(a1), r * 0.95 * math.sin(a1), hh)]
        mb.face(q, "M_Burnt", tile=0.5, inside=(2 * math.cos((a0 + a1) / 2), 2 * math.sin((a0 + a1) / 2), hh / 2))
    mb.face([(r * 0.9 * math.cos(2 * math.pi * i / n), r * 0.9 * math.sin(2 * math.pi * i / n), 0.78) for i in range(n)], "M_Ember",
            tile=0.5, inside=(0, 0, 0))
    return mb.finish()


def build_sign_home():
    """回家的綠色路牌：柱子＋牌面（房子＋箭頭的圖形）"""
    mb = MB("sign_home")
    mb.beam((0, 0.03, 0), (0, 0.03, 2.6), 0.06, "M_Metal")
    mb.box(-0.375, 0.375, -0.04, 0.0, 2.2, 2.575, "M_Metal", fit={"-y": ("M_SignHome", "all")})
    return mb.finish()


def build_fallen_sign():
    """倒在地上的禁止進入牌：圓牌斜躺、彎掉的柱子"""
    mb = MB("fallen_sign")
    n = 12
    m = mb.mark()
    pts = [(0.2 * math.cos(2 * math.pi * i / n), 0.2 * math.sin(2 * math.pi * i / n), 0.0) for i in range(n)]
    uvs = [(0.5 + 0.5 * math.cos(2 * math.pi * i / n), 0.5 + 0.5 * math.sin(2 * math.pi * i / n)) for i in range(n)]
    mb.face(pts, "M_NoEntry", uvs=uvs, inside=(0, 0, -1))
    mb.xform(m, Matrix.Translation((0, 0, 0.06)) @ R('X', 12))
    mb.beam((0.18, 0.05, 0.03), (0.9, 0.2, 0.03), 0.05, "M_Metal")
    mb.beam((0.9, 0.2, 0.03), (1.3, 0.05, 0.15), 0.05, "M_Metal")
    return mb.finish()


def build_charred():
    """燒焦的木板（地上的前景）"""
    mb = MB("charred")
    for k, (x, y, ang, L) in enumerate(((-0.2, 0.0, 15, 1.0), (0.25, -0.1, -40, 0.8), (0.0, 0.15, 70, 0.6))):
        m = mb.mark()
        mb.box(-L / 2, L / 2, -0.07, 0.07, k * 0.04, k * 0.04 + 0.05, "M_Burnt", tile=0.5)
        mb.xform(m, Matrix.Translation((x, y, 0)) @ R('Z', ang))
    return mb.finish()


def build_front_wall():
    """前景的斷牆：低矮、上緣斷得高低不一，露出鋼筋"""
    mb = MB("front_wall")
    W, T_ = 0.7, 0.25
    jp = jag(-W, W, 440, 0.6)
    top = [(x, -T_ / 2, 0.7 + dy) for x, dy in jp]
    mb.face([(-W, -T_ / 2, 0), (W, -T_ / 2, 0)] + list(reversed(top)), "M_Concrete", tile=2.0, inside=(0, 1, 0.3))
    back = [(x, T_ / 2, zz) for x, _, zz in top]
    mb.face([(W, T_ / 2, 0), (-W, T_ / 2, 0)] + back, "M_Concrete", tile=2.0, inside=(0, -1, 0.3))
    for a, b, c, d in zip(top, top[1:], back[1:], back):
        mb.face([a, b, c, d], "M_Concrete", tile=2.0, inside=(0, 0, 0))
    mb.quad((-W, T_ / 2, 0), (-W, -T_ / 2, 0), top[0], back[0], "M_Concrete", tile=2.0)
    mb.quad((W, -T_ / 2, 0), (W, T_ / 2, 0), back[-1], top[-1], "M_Concrete", tile=2.0)
    for k, x in enumerate((-0.4, 0.05, 0.45)):
        zz = 0.7 + 0.6 * max(dy for xx, dy in jp if abs(xx - x) < 0.5)
        mb.beam((x, 0, zz - 0.2), (x + 0.05 * (k - 1), -0.05, zz + 0.35), 0.02, "M_Rebar")
        mb.beam((x + 0.05 * (k - 1), -0.05, zz + 0.35), (x + 0.2 * (k - 1), -0.15, zz + 0.5), 0.02, "M_Rebar")
    return mb.finish()


def build_rebar():
    """前景的鋼筋：一塊水泥塊伸出彎掉的鋼筋"""
    mb = MB("rebar")
    m = mb.mark()
    mb.box(-0.35, 0.35, -0.25, 0.25, 0.0, 0.3, "M_Concrete", tile=1.0)
    mb.xform(m, R('Z', 12) @ R('Y', 6))
    for k in range(5):
        x = -0.25 + 0.12 * k
        a = (x, 0.0, 0.25)
        b = (x + 0.05 * (k - 2), -0.05 * k, 0.9 + 0.3 * h01(k, 450))
        c = (b[0] + 0.25 * (h01(k, 451) - 0.5), b[1] - 0.15, b[2] + 0.25)
        mb.beam(a, b, 0.025, "M_Rebar")
        mb.beam(b, c, 0.025, "M_Rebar")
    return mb.finish()


def build_all():
    for fn in BUILDERS:
        fn()


BUILDERS = [build_shell, build_far, build_wires, build_shelter, build_barricade, build_barrier, build_drum, build_sign_home, build_fallen_sign,
            build_charred, build_front_wall, build_rebar]


# ======================= B3-4b 預覽時的擺放位置（Godot 座標 x, y, z, 繞 y 軸轉幾度；B3-4c 照這份放進 Ruins3D） =======================
# shell、far_ruins、wires 放在原點（不用街道的 street/far：19 m 高會擋住天空）；拒馬放在 Near/Barrier（18.75, 0, 0.26）底下；避難所放在互動點 Shelter 附近（圍欄中間 26.5）。
# 借用：street/utility_pole 照 POLES（繞 z 軸歪斜，y 0.15）、street/burnt_car、common/rubble、common/bricks。
PLACE = {
    "barricade": [(5.9, 0, -3.0, 0), (21.1, 0, -3.0, 8)], "drum": [(4.7, 0, -2.4, 0), (19.5, 0, -2.4, 0)],
    "barrier": [(18.75, 0, 0.26, 0)], "shelter": [(26.5, 0, -2.6, 0)], "sign_home": [(33.6, 0.15, -3.6, 0)],
    "fallen_sign": [(9.7, 0, 2.3, 20), (31.9, 0, 2.3, -30)], "charred": [(5.5, 0, 2.3, 0), (28.4, 0, 2.3, 60)],
    "front_wall": [(6.6, 0, 3.4, 0), (22.0, 0, 3.4, 180)], "rebar": [(16.5, 0, 3.2, 0), (30.8, 0, 3.2, 40)],
}
BORROWED = {
    "street/burnt_car": [(10.1, 0, -2.6, 8)], "common/rubble": [(15.0, 0, 2.3, 0)], "common/bricks": [(21.0, 0, 2.3, 30)],
}
