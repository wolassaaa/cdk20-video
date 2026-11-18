"""HKBU SCIE1007 课程作业的科普视频：拼装板道具精模。

单位为毫米，XY 为板面。保留初版 Kit、浇口和内容件；导入时不创建场景，
不修改初版模块。旧调用方可在原处改用 import kit_parts_hd as KP。
"""
from kit_parts import *
import kit_parts as _base
from types import FunctionType as _FunctionType


def _loft(P, rings, m, *, closed=False):
    """等点数截面。闭合截面链可做有真实内壁的透明壳；其余封住两端。"""
    n = len(rings[0])
    assert all(len(ring) == n for ring in rings)
    verts = [(x + P.ox, y + P.oy, z) for ring in rings for x, y, z in ring]
    faces = []
    count = len(rings)
    for j in range(count if closed else count - 1):
        a, b = j * n, (j + 1) % count * n
        faces.extend((a+i, a+(i+1)%n, b+(i+1)%n, b+i) for i in range(n))
    if not closed:
        faces.extend((tuple(reversed(range(n))), tuple(range((count-1)*n, count*n))))
    # 统一法线；透明体要有可判定的里外。
    name = P.nm("loft")
    data = bpy.data.meshes.new(name)
    data.from_pydata([tuple(v*MM for v in point) for point in verts],[],faces)
    data.update()
    o = link(bpy.data.objects.new(name,data),P.root)
    data.materials.append(m)
    for face in data.polygons:
        face.use_smooth = True
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(o.data)
    bm.free()
    if not closed:
        o.data.polygons[-1].use_smooth = o.data.polygons[-2].use_smooth = False
    return o


def _radial(P, profile, m, x=0, z=0, closed=False):
    """沿 Y 回转；profile 可沿内壁返回出发点（真实壁厚及开口）。"""
    trig = [(math.cos(i*math.tau/64), math.sin(i*math.tau/64)) for i in range(64)]
    o = _loft(P, [[(x+r*c, y, z+r*s) for c, s in trig] for r,y in profile], m, closed=closed)
    o.data.set_sharp_from_angle(angle=math.radians(32))
    return o


def _body(P, outline, layers, m):
    """由同形的多个 XY 截面围成起伏、圆滑的注塑外壳。"""
    cx = sum(x for x,y in outline) / len(outline)
    cy = sum(y for x,y in outline) / len(outline)
    return _loft(P, [[(cx+(x-cx)*sx, cy+(y-cy)*sy, z) for x,y in outline]
                     for z,sx,sy in layers], m)


def _line(P, points, m, r=0.13, cyclic=False):
    return tube_w(P.nm("mold"), [(x+P.ox,y+P.oy,z) for x,y,z in points],
                  r, m, P.root, cyclic=cyclic)


def _rim(P, x, y, hw, hh, radius, z, m, r=0.14):
    return _line(P, [(a,b,z) for a,b in rrect(x,y,hw,hh,radius)], m, r, True)


def _ring_y(P, x, y, z, outer, inner, m, t=0.48):
    return _radial(P, [(outer-.13,y-t/2),(outer,y-t*.24),(outer,y+t*.24),
                       (outer-.13,y+t/2),(inner,y+t/2),(inner,y-t/2)],
                   m, x, z, closed=True)


def _cut(P, target, cutter):
    cutter.hide_render = cutter.hide_viewport = True
    cutter.name = target.name + "_cut"
    mod = target.modifiers.new("recess", "BOOLEAN")
    mod.object, mod.operation, mod.solver = cutter, "DIFFERENCE", "EXACT"
    # 布尔先于倒角和加权法线。
    target.modifiers.move(len(target.modifiers)-1, 0)


def _print(P, x, y, hw, hh, z, m, radius=0.10):
    return P.box(x,y,hw,hh,.065,m,z=z+.025,r=radius,bevel=.018)


def _person_hd(P, ox, m):
    P.at(ox, 0)
    P.cyl(0,6.4,0,2.45,2.5,m,axis="y",bevel=.32)
    _body(P, rrect(0,10.85,4.08,4.24,2.95),
          [(-3.46,.68,.70),(-2.85,.93,.92),(-1.4,1,1),(1.45,1,1),
           (2.62,.94,.95),(3.25,.75,.82),(3.42,.56,.65)], m)
    for s in (-1,1):
        P.ball(s*3.83,10.4,0,.88,m,sc=(.71,1.25,.95))
    # 同色浅浮雕，不换成皮肤色；帽壳分模缝绕过后脑。
    hair = smooth_loop([(-3.78,11.0),(-3.8,12.2),(-3.1,14.05),(0,15.15),
                        (3.12,14.15),(3.8,12.2),(3.6,11.65),(1.4,12.3),(-.5,11.55)],4)
    P.slab(hair,.82,m,z=2.02,bevel=.30)
    for s in (-1,1):
        P.ball(s*1.46,10.7,3.42,.49,m,sc=(1.15,.66,.60),seg=24)
    P.ball(0,9.98,3.26,.62,m,sc=(.65,1,.82),seg=24)
    P.tube([(-1.05,9.23,3.04),(0,8.99,3.35),(1.05,9.23,3.04)],.105,m,smooth=True)
    torso = smooth_loop([(-3.95,-4.6),(-5.1,-.6),(-5.65,3.85),(-4.7,5.9),
                         (-2.3,6.35),(2.3,6.35),(4.7,5.9),(5.65,3.85),
                         (5.1,-.6),(3.95,-4.6)],5)
    _body(P,torso,[(-2.95,.75,.8),(-2.35,.98,.99),(-.7,1,1),
                   (1.6,1,1),(2.7,.89,.94),(3.06,.69,.87)],m)
    P.tube([(-2.55,5.88,2.25),(-1.55,4.96,2.94),(0,4.48,3.12),
            (1.55,4.96,2.94),(2.55,5.88,2.25)],.21,m,smooth=True)
    P.box(1.8,1.3,1.1,1.05,.46,m,z=2.98,r=.3,bevel=.14)
    P.box(0,-3.75,3.8,.32,.62,m,z=2.53,r=.25,bevel=.12)
    for s in (-1,1):
        P.ball(s*5.47,3.6,0,1.72,m,sc=(1.22,1.19,1.26))
        P.slab(smooth_loop([(s*x,y) for x,y in [(5,3.0),(6.55,4.4),(7.48,2.04),
                   (8,-.88),(7.28,-2),(5.92,-1.68),(5.32,.4)]],5),
                   3.05,m,z=.06,bevel=.69)
        P.ball(s*6.9,-2.9,.15,1.42,m,sc=(.87,1.17,1.05))
        P.ball(s*6.08,-2.6,.85,.52,m,sc=(.92,1.21,.86),seg=24)
        P.box(s*2.35,-8.1,1.95,5.0,4.2,m,z=-.06,r=1.05,bevel=.70)
        P.box(s*2.35,-10.7,1.76,.58,.52,m,z=1.98,r=.34,bevel=.15)
        P.box(s*2.35,-13.6,2.03,1.45,4.84,m,z=.37,r=.91,bevel=.54)
        P.box(s*2.35,-14.86,1.92,.37,4.25,m,z=.27,r=.33,bevel=.22)
        P.tube([(s*2.35-.98,-12.78,2.77),(s*2.35+.98,-12.78,2.77)],.14,m)
    P.gate(-2.35,-15.0,"-y")


def p03_person(K):
    P = Part(K,"p03_person","white")
    _person_hd(P,-11,K.white)
    _person_hd(P,11,K.red)
    return P.done()


def p22_key(K, seed=1):
    P = Part(K,"p22_key","gold"); m = K.gold
    rng = random.Random(seed)
    teeth = [0.0]+[rng.choice((.8,1.4,2.2,3.0,3.6,4.2)) for _ in range(7)]
    # 一个连续坯体：圆柄、柄肩和有斜边的齿杆。
    bow = arc(-15.35,.6,8.95,38,322,52,ry=7.15)
    pts = [(-6.1,2.95),(19.9,2.95),(22,1.15),(22,-1.62)]
    for i,h in enumerate(reversed(teeth)):
        x = 22 - 1.4 - (i+.5)*2.88
        y = -1.7-h*.62
        pts.extend([(x+1.05,y+.28),(x+.57,y),(x-.64,y),(x-1.05,y+.26)])
    pts.extend([(-5.8,-1.7),(-7.4,-3.9),*reversed(bow),(-7.4,5.1)])
    cuts = [(rrect(6.8,1.54,12.6,.52,.46),1.6,1.65),
            (rrect(5.6,-.32,11.0,.23,.20),.95,1.53)]
    P.slab(pts,2.46,m,bevel=.22,holes=[(-17.3,.60,2.72)],cuts=cuts)
    P.ring(-17.3,.60,3.3,2.73,.40,m,z=1.22,bevel=.11)
    groove = arc(-15.35,.60,7.26,77,283,37,ry=5.68)
    P.tube([(x,y,1.22) for x,y in groove],.14,m)
    for y in (-.9,.6,2.1):
        P.box(-11.9,y,.84,.24,.23,m,z=1.217,r=.21,bevel=.075)
    P.gate(-24.3,.6,"-x"); P.gate(22,1,"+x")
    return P.done()


def p21_lock(K):
    P = Part(K,"p21_lock","blue"); m = K.blue
    path = [(-6,-1.4),(-6,8.05),*arc(0,8.27,6,180,0,42), (6,8.05),(6,-1.4)]
    P.tube(path,1.58,m)
    for x in (-6,6):
        _ring_y(P,x,3.55,0,2.04,1.32,m,t=.84)
        _ring_y(P,x,4.45,0,1.70,1.43,m,t=.36)
    hole = [(-.95,-5.8),(-1.37,-8.5),(1.37,-8.5),(.95,-5.8),
            *arc(0,-4.1,1.95,-54,234,26)]
    face = rrect(0,-5.48,9.25,7.79,1.82)
    P.slab(rrect(0,-5.5,10.5,9,2.05),6.4,m,bevel=.69,
           cuts=[(hole,1.75,3.12)])
    P.slab(face,.9,m,z=3.39,bevel=.28,cuts=[(hole,3.0,3.35)])
    P.slab(hole,.135,K.ink,z=2.25,bevel=.025)
    _rim(P,0,-5.52,10.47,8.97,2.05,-.36,m,.112)
    for x in (-6.95,6.95):
        for y in (-11.3,.64):
            P.disc(x,y,.58,.20,m,z=3.79,bevel=.08)
            P.box(x,y,.275,.066,.08,K.ink,z=3.895,r=.045,bevel=.016)
    P.gate(-10.5,-5.5,"-x"); P.gate(10.5,-5.5,"+x")
    return P.done()


def p34_flask(K):
    P = Part(K,"p34_flask","clear")
    wall = [(.10,-11.5),(8.25,-11.5),(8.83,-11.38),(9.23,-11.08),
            (9.42,-10.54),(9.38,-9.79),(9.07,-9.23),(3.45,2.68),
            (2.95,3.61),(2.72,4.6),(2.72,10.45),(2.85,10.96),
            (3.44,11.08),(3.60,11.37),(3.60,12.30),(3.44,12.58),
            (2.27,12.62),(2.12,12.44),(2.10,4.57),(2.26,3.45),
            (2.83,2.4),(8.42,-9.47),(8.58,-10.03),(8.44,-10.45),
            (8.06,-10.69),(.10,-10.70)]
    _radial(P,wall,K.clear0)
    _radial(P,[(.12,-10.62),(7.98,-10.62),(8.31,-10.43),(8.48,-10.03),
               (8.32,-9.48),(5.69,-3.84),(5.54,-3.74),(5.32,-3.94),
               (.12,-4.00)],K.liquid)
    _ring_y(P,0,-10.37,0,9.45,9.02,K.clear0,t=.42)
    for i,(y,r) in enumerate(((-6,7.61),(-3,6.20),(0,4.78))):
        hw = 1.90-.39*i
        P.tube([(x,y,math.sqrt(r*r-x*x)) for x in (-hw,-hw/2,0,hw/2,hw)],.11,K.ink)
        if i < 2:
            P.tube([(x,y+1.42,math.sqrt((r-.67)**2-x*x)) for x in (-.67,-.33,0,.33,.67)],.085,K.ink)
    P.gate(-9.2,-10.2,"-x"); P.gate(9.2,-10.2,"+x")
    return P.done()



def _surface_z(obj,x,y):
    hit,loc,_,_ = obj.ray_cast(Vector((x*MM,y*MM,.03)),Vector((0,0,-1)))
    if not hit:
        raise ValueError("Detail does not land on the molded surface")
    return loc.z/MM


def _mouse_tail(P,m):
    pts = [Vector(p) for p in smooth_path([(-10.6,-2.3,-.4),(-15.9,-5.3,-.7),(-19.1,-6.1,-.4),
                 (-22.3,-3.86,.2),(-24.25,.55,.54),(-24.55,4.92,.72)],7)]
    rings = []
    for i,p in enumerate(pts):
        t = i/(len(pts)-1)
        r = .13 + 1.07*(1-t)**1.24
        d = pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]
        a = Vector((-d.y,d.x,0)).normalized()
        b = d.normalized().cross(a)
        rings.append([tuple(p+r*(a*math.cos(j*math.tau/20)+b*math.sin(j*math.tau/20))) for j in range(20)])
    _loft(P,rings,m)


def p43_mouse(K):
    P = Part(K,"p43_mouse","white"); m = K.white
    _mouse_tail(P,m)
    shape = smooth_loop([(-14,-2),(-11.4,-6.9),(-4.5,-8.58),(1.2,-7.46),(6.6,-5.75),
            (12.4,-5.44),(16.9,-4.07),(19.1,-2.49),(17.45,-.84),(14.6,1.08),
            (10.65,3.56),(6.9,3.8),(2.52,5.1),(-3.9,5.56),(-10.8,3.1)],6)
    body = _body(P,shape,[(-4.68,.72,.49),(-3.28,.88,.83),(-1.20,.98,.98),
                   (0,1,1),(1.55,.98,.98),(2.91,.91,.9),(4.12,.79,.72),
                   (4.69,.62,.51),(4.89,.49,.35)],m)
    # 斜置的两层耳壳，内耳用同色凹盘而非换色。
    for x,y,z,rx,ry in ((8.5,4.3,2.23,3.25,3.70),(5.0,5.56,3.59,3.45,4.01)):
        ear = _body(P,circle(x,y,rx,n=64,ry=ry),
                     [(-.98,.70,.71),(-.65,.95,.96),(0,1,1),(.47,.95,.96),
                      (.64,.80,.80),(.14,.63,.62),(.04,.48,.46)],m)
        for v in ear.data.vertices:
            dy = v.co.y-y*MM
            v.co.z += z*MM+dy*.26
    P.ball(18.96,-2.50,0,.95,K.ink,sc=(.80,1,.81),seg=24)
    P.ball(12.01,.26,_surface_z(body,12.01,.26),.77,K.ink,sc=(1.1,.87,.70),seg=24)
    lid = [(11.28,.05),(11.75,.83),(12.39,.84),(12.77,.41)]
    P.tube([(x,y,_surface_z(body,x,y)) for x,y in lid],.122,m,smooth=True)
    for x,y in ((-8.3,-7.45),(-2.4,-7.54),(6.9,-5.71),(10.4,-4.4)):
        P.ball(x,y,-.74,1.55,m,sc=(1.44,.77,.81),seg=24)
        for dx in (.48,1.05):
            P.tube([(x+dx,y-.22,.43),(x+dx+.32,y-.53,.30)],.075,m)
    for i in range(3):
        P.ball(15.4+.65*i,-2.3+.26*i,1.78-.29*i,.15,m,seg=16)
    P.gate(-3,-8.5,"-y"); P.gate(-1,5.4,"+y")
    return P.done()


def p44_plug_bin(K):
    P = Part(K,"p44_plug_bin","green"); g = K.green; m = K.black
    P.at(-18,0)
    for s in (-1,1):
        P.slab(rrect(s*2.7,7.05,.92,3.85,.5),1.7,g,bevel=.22,
               holes=[(s*2.7,9.55,.38)])
    casing = rrect(0,-1,5.8,5.46,1.53)
    P.slab(casing,4.98,g,bevel=.69)
    _rim(P,0,-1,5.76,5.40,1.53,-.17,g,.13)
    P.box(0,-1,4.11,3.57,.52,g,z=2.52,r=1.06,bevel=.22)
    for y in (-2.32,-1.12,.08,1.28):
        P.box(0,y,2.95,.20,.28,g,z=2.83,r=.17,bevel=.08)
    P.box(0,-6.88,2.56,1.67,3.6,g,r=.91,bevel=.53)
    for y,r in ((-7.87,1.78),(-8.63,1.56),(-9.32,1.34),(-9.95,1.18)):
        _ring_y(P,.12,y,0,r,.87,g,t=.39)
    P.tube([(0,-8.61,0),(.19,-10.58,0),(.88,-12.4,.05),(2.69,-14.13,.24),
            (5.45,-14.91,.42)],.96,g,smooth=True)
    P.gate(-5.8,-1,"-x")
    P.at(-2.5,0)
    bolt = [(2.22,15),(-5.44,.26),(-.85,.26),(-3.15,-14.68),
            (5.81,2.42),(1.05,2.42),(4.83,15)]
    P.slab(bolt,2.86,g,bevel=.46)
    P.slab([(2.72,13.53),(-3.79,.97),(.10,.97),(-1.97,-11.38),
            (4.43,1.73),(.14,1.73),(3.93,13.53)],.32,g,z=1.37,bevel=.13)
    P.gate(-3,-14.2,"-y")
    P.at(15.5,0)
    _radial(P,[(.10,-14.5),(4.94,-14.5),(5.49,-14.17),(5.71,-13.65),
               (6.87,5.16),(7.06,5.74),(7.06,6.32),(6.23,6.32),
               (5.20,-12.67),(4.95,-13.07),(.10,-13.08)],m)
    for a in range(0,360,30):
        sn,cs = math.sin(math.radians(a)),math.cos(math.radians(a))
        P.tube([(5.65*sn,-13.25,5.65*cs),(6.23*sn,-5.0,6.23*cs),
                (6.82*sn,4.84,6.82*cs)],.30,m,smooth=True)
    _ring_y(P,0,5.49,0,7.23,6.54,m,t=.87)
    _radial(P,[(.12,6.31),(7.85,6.31),(8.28,6.51),(8.42,6.87),(8.42,7.50),
               (8.18,7.80),(7.68,8.07),(6.51,8.53),(3.17,9.03),(.12,9.14)],m)
    P.tube([(-2.48,8.81,.05),(-2.48,10.31,.05),(-1.78,11.16,.05),
            (0,11.41,.05),(1.78,11.16,.05),(2.48,10.31,.05),(2.48,8.81,.05)],.66,m,smooth=True)
    P.gate(6.6,-1,"+x")
    return P.done()


def _pane(P,x,y,hw,hh,z,m):
    _print(P,x,y,hw,hh,z,m,.14)
    P.box(x,y-hh+.03,hw+.28,.17,.34,P.K.white,z=z+.045,r=.14,bevel=.09)


def p14_buildings(K):
    P = Part(K,"p14_buildings","white"); m = K.white
    P.at(-17.5,0)
    P.box(0,-5.35,6.65,6.98,6.4,m,z=-1.4,r=.45,bevel=.35)
    for i,(y,hw,depth) in enumerate(((-13.03,8.06,6.6),(-12.4,7.97,7.65),(-11.72,7.68,8.54))):
        P.box(-.40,y,hw,1.16,depth,m,z=.24*i,r=.39,bevel=.23)
    for x in (-5.6,-1.9,1.8,5.5):
        P.box(x,-5.02,.92,6.0,4.12,m,z=2.49,r=.69,bevel=.56)
        for dx in (-.42,.42):
            P.tube([(x+dx,-10.37,4.19),(x+dx,0.27,4.19)],.10,m)
        for y in (-10.8,.86):
            P.box(x,y,1.19,.63,.75,m,z=4.17,r=.32,bevel=.19)
    P.box(0,2.55,7.64,1.21,8.6,m,r=.49,bevel=.32)
    P.box(0,3.74,8.35,.58,9.1,m,r=.36,bevel=.25)
    P.slab([(-8.28,4.02),(8.28,4.02),(0,10.35)],7.93,m,z=.31,bevel=.31)
    P.tube([(-8.13,4.02,4.05),(0,10.21,4.05),(8.13,4.02,4.05)],.34,m)
    P.disc(0,6.55,1.04,.39,m,z=4.30,bevel=.13)
    P.gate(-.5,-14.2,"-y")

    P.at(0,0)
    hcuts = [(rrect(x,y,1.38,1.14,.22),1.24,4.40)
             for x in (-3.7,3.7) for y in (-1.8,-5.45,-9.1)]
    hcuts += [(rrect(0,-11.64,1.75,2.47,.45),1.25,4.4)]
    P.slab(rrect(0,-2.7,7.25,11.54,.81),8.9,m,bevel=.41,cuts=hcuts)
    for x in (-3.7,3.7):
        for y in (-1.8,-5.45,-9.1):
            _pane(P,x,y,1.22,.98,3.84,K.ink)
            P.box(x,y,.075,.95,.44,m,z=4.05,r=.057,bevel=.025)
    _pane(P,0,-11.64,1.54,2.20,3.85,K.ink)
    P.box(0,-11.64,.09,2.15,.64,m,z=4.08,r=.06,bevel=.025)
    P.box(0,-8.75,2.25,.28,1.18,m,z=4.65,r=.19,bevel=.17)
    P.box(0,7.66,6.33,.60,.46,m,z=4.70,r=.35,bevel=.18)
    _print(P,0,4.45,2.45,.81,4.45,K.ink)
    _print(P,0,4.45,.81,2.45,4.47,K.ink)
    P.gate(0,-14.2,"-y")

    P.at(17.6,0)
    tower = rrect(-3.40,-1.1,3.44,13.1,.74)
    cuts = [(rrect(-3.4,y,2.28,.85,.25),.95,4.28) for y in (8.25,4.6,.95,-2.7,-6.35,-10)]
    P.slab(tower,8.60,m,bevel=.40,cuts=cuts)
    for y in (8.25,4.6,.95,-2.7,-6.35,-10):
        _pane(P,-3.4,y,2.05,.70,3.90,K.ink)
        for x in (-4.43,-2.37):
            P.box(x,y,.10,.68,.47,m,z=4.05,r=.08,bevel=.036)
    P.box(-3.4,11.8,2.39,.53,.72,m,z=4.27,r=.31,bevel=.22)
    P.tube([(-3.4,11.43,0),(-3.4,15.54,0)],.39,m)
    P.box(1.9,-12.77,5.25,1.41,6.63,m,r=.57,bevel=.36)
    P.box(3.95,-9.72,3.73,3.96,7.86,m,r=.64,bevel=.42)
    P.ball(3.95,-5.71,1.1,3.72,m,sc=(1,.97,.92),seg=48)
    P.ring(3.95,-5.71,3.75,3.28,.42,m,z=2.17,bevel=.15)
    _pane(P,4,-11.45,2.65,.91,3.93,K.ink)
    P.gate(.4,-14.2,"-y")
    return P.done()


def p09_iv_bag(K):
    P = Part(K,"p09_iv_bag","clear"); m = K.clear0
    outline = rrect(0,2.50,9.52,10.65,3.06,n=12)
    shell = _body(P,outline,[(-3.15,.78,.87),(-2.76,.86,.92),(-1.95,.92,.95),
                             (-.50,1,1),(.50,1,1),(1.82,.95,.98),(2.64,.90,.95),
                             (3.28,.82,.88),(3.47,.67,.77)],m)
    cavity = _body(P,outline,[(-2.77,.72,.79),(-2.27,.83,.87),(-.60,.93,.94),
                               (.54,.93,.94),(1.80,.88,.92),(2.67,.79,.85),
                               (3.03,.64,.73)],m)
    _cut(P,shell,cavity)
    fluid = smooth_loop([(-5.65,-6.48),(-7.8,-5.18),(-8.1,1.38),(-7.48,5.52),
                        (-3.33,5.17),(1.50,5.30),(7.36,5.60),(8.02,3.02),
                        (7.90,-3.99),(6.48,-6.57),(0,-7.01)],5)
    _body(P,fluid,[(-2.53,.79,.79),(-1.73,.90,.93),(-.46,1,1),(.62,1,1),
                   (1.81,.84,.91),(2.47,.75,.79),(2.73,.61,.68)],K.liq_blue)
    _rim(P,0,2.5,9.27,10.38,2.86,.56,m,.14)
    P.slab(rrect(0,13.9,3.25,2.02,1.26),1.36,m,bevel=.32,holes=[(0,14.50,1.02)])
    for x,y in ((-.98,-9.98),(2.71,-8.82)):
        _radial(P,[(.11,y-1.52),(1.25,y-1.52),(1.52,y-1.23),(1.52,y+1.68),
                   (1.26,y+2.04),(.11,y+2.04)],m,x)
    _radial(P,[(.11,-14.15),(1.52,-14.15),(1.94,-13.85),(1.94,-11.02),
                (1.52,-10.78),(.11,-10.78)],m,-.98)
    for y in (-11.30,-12.04,-12.78,-13.49):
        _ring_y(P,-.98,y,0,2.02,1.74,m,t=.31)
    P.tube([(-.98,-13.93,.02),(-.94,-14.64,.11),(-.43,-15.63,.16)],.34,m,smooth=True)
    for i in range(4):
        y = 8.05-i*3.12
        P.tube([(4.8,y,3.41),(5.76,y,3.33),(6.65,y,3.19)],.098,K.ink)
    P.gate(-9.3,2.5,"-x"); P.gate(9.3,2.5,"+x")
    return P.done()



def p10_calendar(K):
    P = Part(K,"p10_calendar","green"); m = K.green
    P.box(0,5.03,10.5,10.27,2.45,m,z=-.18,r=1.53,bevel=.46)
    # 页沿从侧面可见；蓝图中的 4×3 方格及尺刻度不变。
    for j in range(4):
        P.box(.12*j,4.45+.12*j,9.74-.12*j,9.1,.30,m,z=1.28+.26*j,r=.85,bevel=.09)
    P.box(0,12.86,10.37,1.97,3.58,m,z=.16,r=.93,bevel=.48)
    for x in (-5.2,5.2):
        P.tube([(x,13.40,-.66),(x,15.25,-.50),(x,15.30,1.08),
                (x,14.72,2.47),(x,13.08,2.20),(x,12.21,1.81)],.37,m,smooth=True)
        P.disc(x,12.15,.65,.19,m,z=1.95,bevel=.078)
    _rim(P,0,2.94,9.20,6.72,.63,2.20,m,.14)
    for row in range(3):
        for col in range(4):
            x,y = (col-1.5)*4.35,7.48-row*4.35
            P.box(x,y,1.69,1.60,.25,m,z=2.2,r=.26,bevel=.08)
            _print(P,x,y,1.35,1.26,2.326,K.inkw,.12)
    P.box(0,-12.20,25,2.8,2.42,m,r=.92,bevel=.38)
    _rim(P,0,-12.20,24.3,2.25,.65,1.20,m,.112)
    for i in range(11):
        major = i%5==0
        _print(P,-22.5+4.5*i,-13.82+(1.71 if major else 1.04),.22,1.71 if major else 1.04,1.21,K.inkw,.13)
    P.gate(-10.3,5.2,"-x"); P.gate(10.3,5.2,"+x"); P.gate(-25,-12.2,"-x")
    return P.done()


def p11_bill(K):
    P = Part(K,"p11_bill","green"); m = K.green
    P.box(0,0,22,10.5,1.84,m,r=1.36,bevel=.37)
    P.box(0,0,20.91,9.36,.48,m,z=.96,r=1.16,bevel=.20)
    _rim(P,0,0,20.35,8.80,1.12,1.21,m,.15)
    _rim(P,0,0,18.58,7.07,.87,1.20,m,.14)
    P.disc(0,0,5.36,.84,m,z=1.32,ry=5.84,bevel=.25)
    for j in range(2):
        P.ring(0,0,5.58-j*.62,5.27-j*.62,.21,m,z=1.46+j*.25,bevel=.07)
    P.text("$",7.5,0,-.15,1.74,K.inkw)
    for s in (-1,1):
        P.disc(s*13.35,0,2.35,.49,m,z=1.26,bevel=.20)
        for j in range(2):
            P.ring(s*13.35,0,2.59-j*.64,2.38-j*.64,.19,m,z=1.45,bevel=.055)
        for t in (-1,1):
            pts = [(s*(6.2+.115*i),t*(5.34+.53*math.sin(i*math.tau/19)),1.225)
                   for i in range(93)]
            _line(P,pts,m,.105)
            for i in range(5):
                _print(P,s*(17.4+i*.63),t*7.66,.115,.42-(i%2)*.14,1.204,m,.085)
    P.gate(-22,0,"-x"); P.gate(22,0,"+x")
    return P.done()


def p12_medal(K):
    P = Part(K,"p12_medal","gold"); m = K.gold; y0 = -4.5
    for s in (-1,1):
        strap = [(s*1.65,5.95),(s*4.63,15.93),(s*9.52,15.93),(s*3.54,6.03)]
        P.slab(strap,1.57,m,z=-.48,bevel=.28)
        for u in (.24,.49,.74):
            a = Vector(strap[0]).lerp(Vector(strap[3]),u)
            b = Vector(strap[1]).lerp(Vector(strap[2]),u)
            P.tube([(*a,.33),(*((a+b)*.5),.41),(*b,.30)],.127,m,smooth=True)
    P.ring(0,6.20,1.52,.73,1.39,m,z=-.05,bevel=.19)
    P.disc(0,y0,11,3.16,m,bevel=.53)
    P.ring(0,y0,10.18,9.68,.49,m,z=1.56,bevel=.15)
    P.ring(0,y0,9.28,9.02,.19,m,z=1.63,bevel=.062)
    for x,y in circle(0,y0,9.53,n=52):
        P.ball(x,y,1.58,.176,m,seg=12)
    profile = [(-3.7,-6.5),(-3.25,-3.84),(-4.4,-1.61),(-4.90,2.11),
               (-3.75,5.2),(-.74,6.23),(2.41,5.13),(3.29,2.56),(3.53,1.06),
               (4.68,.05),(3.64,-.56),(3.45,-1.30),(3.85,-1.82),
               (2.46,-3.34),(2.02,-4.81),(3.79,-6.34)]
    _body(P,smooth_loop([(x,y+y0) for x,y in profile],4),
          [(1.50,1,1),(1.78,1,1),(2.18,.91,.95),(2.45,.63,.79)],m)
    P.gate(-11,y0,"-x"); P.gate(11,y0,"+x")
    return P.done()


def p13_chip(K, label="AI"):
    P = Part(K,"p13_chip","black"); m = K.black
    P.box(0,0,11.2,11.2,3.30,m,z=-.12,r=1.36,bevel=.55)
    P.box(0,0,10.74,10.74,.91,m,z=1.58,r=1.0,bevel=.27)
    _rim(P,0,0,11.16,11.16,1.36,-.38,m,.117)
    P.box(0,0,8.82,8.82,.84,m,z=2.30,r=.84,bevel=.26)
    _rim(P,0,0,8.12,8.12,.67,2.738,m,.11)
    for i in range(6):
        t = -8.75+3.5*i
        lead = [(10.63,.30),(11.84,.30),(12.84,-.63),(14.30,-.63),
                (14.30,-1.25),(12.61,-1.25),(11.66,-.30),(10.63,-.30)]
        for s in (-1,1):
            for swap in (False,True):
                coords = [[(s*u,t+dw,z) if not swap else (t+dw,s*u,z) for u,z in lead]
                           for dw in (-.72,.72)]
                o = _loft(P,coords,m)
                b = o.modifiers.new("lead radius","BEVEL")
                b.width,b.segments,b.limit_method = .115*MM,3,"ANGLE"
                o.modifiers.new("lead normals","WEIGHTED_NORMAL")
    # 两侧浇口原高为 0；边缘料脚在原位置留一体的挂耳。
    for x,y in ((-14.2,1.75),(14.2,-1.75)):
        P.box(x*.972,y,.49,.59,.80,m,z=-.37,r=.21,bevel=.19)
    P.ring(-9.61,9.57,.83,.62,.20,m,z=2.055,bevel=.065)
    _print(P,-9.61,9.57,.31,.31,2.052,K.inkw,.21)
    P.text(label,3.0 if len(label)>9 else 3.6 if len(label)>3 else 6.0,0,-.1,2.72,K.inkw)
    P.gate(-14.2,1.75,"-x"); P.gate(14.2,-1.75,"+x")
    return P.done()


def p27_data_disks(K):
    P = Part(K,"p27_data_disks","black"); m = K.black
    P.box(0,0,25,11,2.0,m,r=1.57,bevel=.47)
    _rim(P,0,0,24.24,10.37,1.18,.98,m,.13)
    for x in (-20,-10,0,10,20):
        for y in (-5.38,5.38):
            P.disc(x,y,4.17,.65,m,z=1.22,bevel=.27)
            P.disc(x,y,3.54,5.67,m,z=4.24,bevel=.34)
            for k in range(3):
                P.disc(x,y,4.21,1.44,m,z=2.30+1.92*k,bevel=.36)
            P.ring(x,y,3.61,2.99,.33,m,z=6.92,bevel=.11)
            P.ring(x,y,1.59,.88,.33,m,z=7.15,bevel=.11)
            P.disc(x,y,.34,.14,m,z=6.94,bevel=.055)
    for x in (-24.24,24.24):
        for y in (-2,2):
            P.disc(x,y,.31,.2,m,z=1.01,bevel=.075)
    P.gate(-25,0,"-x"); P.gate(25,0,"+x")
    return P.done()


def p46_newspaper(K):
    P = Part(K,"p46_newspaper","white"); m = K.white
    for i in range(5):
        P.box(.19*i,-.14*i,19.91,14.57,.31,m,z=-.79+.234*i,r=.49,bevel=.082)
    # 硬边保留在整页轮廓，翻角用独立上翘的薄页。
    pts = [(-20,-14.05),(-19.56,-14.55),(17.80,-14.55),(20,-12.34),
           (20,14.04),(19.47,14.58),(-19.43,14.58),(-20,14.05)]
    P.slab(pts,1.16,m,z=.36,bevel=.27)
    curl = P.slab([(16.78,-14.44),(17.72,-14.55),(20,-12.31),(19.68,-11.48),
                   (18.09,-12.06),(16.92,-13.38)],.42,m,z=.89,bevel=.13)
    for v in curl.data.vertices:
        v.co.z += max(0, v.co.x/MM-17.7)*.31*MM
    P.text("Daily News",4.8,0,11,0.94,K.ink)
    _print(P,0,8.0,18,.19,.94,K.ink)
    P.text("AI discovers a cancer drug",3.1,0,5.20,.94,K.ink,italic=True)
    _print(P,0,2.60,18,.095,.94,K.ink)
    _print(P,-9.6,-5.40,8,6.6,.94,K.inkg,.21)
    _rim(P,-9.6,-5.4,8.13,6.72,.32,.98,m,.08)
    for i in range(8):
        _print(P,9.0,.6-1.8*i,8.6 if i!=7 else 5.0,.23,.94,K.inkg)
    P.gate(-20,0,"-x"); P.gate(20,0,"+x")
    return P.done()


def p15_sample_tube(K):
    P = Part(K,"p15_sample_tube","clear"); m = K.clear0
    wall = [(.10,-14),(1.22,-13.80),(2.30,-13.30),(3.06,-12.38),(3.49,-11.10),
            (3.61,-10.33),(3.61,7.19),(3.74,7.52),(3.74,8.37),(3.56,8.54),
            (3.01,8.54),(2.92,8.36),(2.92,-10.18),(2.81,-10.89),(2.45,-11.94),
            (1.80,-12.75),(.90,-13.18),(.10,-13.36)]
    for x in (-13,0,13):
        P.at(x,0)
        _radial(P,wall,m)
        fill = [(.10,-13.24),(.84,-13.12),(1.68,-12.69),(2.35,-11.86),
                (2.73,-10.81),(2.81,-10.17),(2.81,-3.22),(2.70,-3.12),
                (2.48,-3.26),(.10,-3.35)]
        _radial(P,fill,K.liquid)
        cap = [(7.93,3.97),(8.23,4.28),(11.90,4.28),(12.50,3.92),(12.73,3.61)]
        rings = [[(r*(1 if i%4 in (0,1) else .944)*math.cos(i*math.tau/64),y,
                   r*(1 if i%4 in (0,1) else .944)*math.sin(i*math.tau/64))
                  for i in range(64)] for y,r in cap]
        o = _loft(P,rings,m)
        o.data.set_sharp_from_angle(angle=math.radians(32))
        _ring_y(P,0,7.68,0,4.02,3.44,m,t=.40)
        P.gate(0,-13.8,"-y")
    return P.done()


def p17_paper_book(K):
    P = Part(K,"p17_paper_book","white"); m = K.white
    P.at(-15,0)
    for i in range(4):
        P.box(.24*i,-.24*i,8.73,12.38,.34,m,z=-.72+i*.26,r=.41,bevel=.09)
    P.slab([(-8.8,-11.96),(-8.39,-12.40),(6.84,-12.40),(8.8,-10.43),
            (8.8,11.96),(8.33,12.40),(-8.40,12.40),(-8.8,11.98)],1.14,m,z=.40,bevel=.23)
    flap = P.slab([(6.54,-12.25),(6.84,-12.39),(8.8,-10.43),(7.01,-10.39)],.36,m,z=.95,bevel=.09)
    for v in flap.data.vertices:
        v.co.z += max(0,v.co.x/MM-P.ox-6.55)*.21*MM
    _print(P,-1.6,9,5.4,1,.97,K.ink)
    for i in range(4):
        _print(P,0,5.6-1.9*i,6.8,.26,.97,K.inkg)
    _print(P,-3.2,-6.2,3.4,3.4,.97,K.inkg)
    for i in range(4):
        _print(P,4,-3.6-1.8*i,2.8,.26,.97,K.inkg)
    P.gate(-8.8,0,"-x")
    P.at(12,0)
    P.box(0,-.4,13.2,10.2,1.48,m,z=-.66,r=1.04,bevel=.39)
    P.capsule(0,-10.58,9.78,.78,m,z=-.49)
    for s in (-1,1):
        for i in range(4):
            P.box(s*6.11,.01*i,6.20-.12*i,9.64-.11*i,.49,m,z=.13+.37*i,r=.65,bevel=.16)
        coords = [(.06,1.52),(1.0,2.28),(2.90,2.62),(5.66,2.79),
                  (8.25,2.63),(10.88,2.25),(12.14,1.65),(12.21,1.20),(.06,1.20)]
        section = [[(s*x,y,z) for x,z in coords] for y in (-9.28,9.28)]
        _loft(P,section,m)
        # 横线顺着书页从书脊向外弯曲。
        for i in range(6):
            y = 5.65-2.25*i
            _line(P,[(s*x,y,z) for x,z in [(2,2.46),(3,2.65),(5.66,2.80),(8.25,2.65),
                   (10.62 if i!=5 else 8.75,2.31 if i!=5 else 2.59)]],K.inkg,.116)
    P.gate(13.2,-.4,"+x")
    return P.done()


def p18_loupe_checklist(K):
    P = Part(K,"p18_loupe_checklist","black"); m = K.black
    P.at(-13.5,0)
    P.ring(0,5.0,9.6,7.32,3.36,m,bevel=.47,n=80)
    P.ring(0,5.0,9.44,8.62,.49,m,z=1.73,bevel=.16,n=80)
    P.ring(0,5.0,7.66,7.08,.44,m,z=-.61,bevel=.14,n=80)
    _body(P,circle(0,5,7.33,n=80),[(-.60,.63,.63),(-.43,.87,.87),
          (-.16,1,1),(.68,1,1),(1.03,.88,.88),(1.27,.48,.48),(1.30,.14,.14)],K.clear0)
    P.box(0,-5.17,2.29,1.55,3.73,m,r=.52,bevel=.32)
    P.box(0,-10.53,1.89,5.02,3.39,m,r=1.32,bevel=.56)
    for y in (-8.15,-9.26,-10.37,-11.48,-12.59):
        P.box(0,y,1.29,.16,.30,m,z=1.69,r=.14,bevel=.08)
    P.gate(-9.5,5,"-x")
    P.at(13.5,0)
    P.box(0,-1.2,9.60,13.20,2.56,m,r=1.48,bevel=.39)
    _rim(P,0,-1.2,8.95,12.55,1.27,1.27,m,.14)
    P.box(0,-2.2,7.98,11,.57,K.inkw,z=1.51,r=.59,bevel=.16)
    P.slab(rrect(0,11.52,4.50,1.97,.93),2.52,m,z=.99,bevel=.47,
           holes=[(0,12.22,.65)])
    P.box(0,10.38,3.53,.49,.56,m,z=2.08,r=.31,bevel=.16)
    for x in (-2.83,2.83):
        P.disc(x,11.55,.62,.28,m,z=2.24,bevel=.10)
    for i in range(4):
        y = 5.0-4.6*i
        _rim(P,-5.46,y,1.32,1.21,.28,1.80,K.ink,.105)
        P.slab([(-6.80,y+.10),(-5.90,y-1.20),(-3.60,y+1.50),(-4.10,y+1.90),
                (-5.90,y-.20),(-6.30,y+.50)],.16,K.ink,z=1.93,bevel=.048)
        _print(P,1.81,y,4.38,.26,1.80,K.ink)
    P.gate(9.6,-1.2,"+x")
    return P.done()


# 初版函数引用其定义模块而非调用模块；在 HD 命名空间重新绑定调度入口，
# 不改写 kit_parts 的全局。ZONES 里的带参数 lambda 也走 HD 工厂。
def _local_dispatch(fn):
    adapted = _FunctionType(fn.__code__,globals(),fn.__name__,fn.__defaults__,fn.__closure__)
    adapted.__doc__ = fn.__doc__
    return adapted


CATALOG = [(num,title,(lambda K: p13_chip(K,"AlphaFold")) if num=="13"
            else globals().get(factory.__name__,factory)) for num,title,factory in _base.CATALOG]
ZONES = _local_dispatch(_base.ZONES)
make_board = _local_dispatch(_base.make_board)
# 初版底座用内部器官缓存，保持同一个字典引用。
_ORG = _base._ORG
build_catalog = _local_dispatch(_base.build_catalog)
build_board = _local_dispatch(_base.build_board)

