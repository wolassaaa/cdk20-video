"""HKBU SCIE1007 课程作业的科普视频：X1 零件，单位毫米。"""
import json
import math
import random

import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
from kit_deep import Part, MM, _adopt, _mesh as _part_mesh, _move, pose, rest, rig
from kit_parts import rrect

CELL_SOCKET_SCALE = .232
WELL_STACK_PITCH = 4.2
WELL_STACK_CLEARANCE = .01


def _mesh(P, name, pts, faces, mat, smooth=False):
    # 旧 Part.mesh 默认用等长数组；保留这里混合的三角、四边和封口面。
    return _part_mesh(P, name, pts, np.asarray(faces, dtype=object), mat, smooth=smooth)


def _named(obj, name):
    obj.name = name
    return obj


def _bevel_before_cuts(obj):
    """先倒外棱，避免小孔或浅印令整件倒角一起夹紧。"""
    bevel = next(mod for mod in obj.modifiers if mod.type == "BEVEL")
    with bpy.context.temp_override(object=obj):
        bpy.ops.object.modifier_move_to_index(modifier=bevel.name, index=0)
    return bevel


def _cell_skin(P, name, bottom, top, material):
    """真正的法线内偏置；各纬线按给定切平面的 Z 重新求解。"""
    steps = 64

    def point(a, t, inner):
        q = Vector((math.cos(t) * math.cos(a), math.cos(t) * math.sin(a), math.sin(t)))
        normal = Vector((q.x / 25, q.y / 16, q.z / 14)).normalized()
        return Vector((25 * q.x, 16 * q.y, 4 + 14 * q.z)) - (1.2 if inner else 0) * normal

    def ring(z, inner):
        pts = []
        for j in range(steps):
            a = j * math.tau / steps
            lo, hi = -math.pi / 2, math.pi / 2
            for _ in range(22):
                mid = (lo + hi) / 2
                if point(a, mid, inner).z < z:
                    lo = mid
                else:
                    hi = mid
            p = point(a, (lo + hi) / 2, inner)
            pts.append((p.x, p.y, z))
        return pts

    verts, faces = [], []

    def surface(levels, inner, cap):
        starts = []
        for z in levels:
            starts.append(len(verts))
            verts.extend(ring(z, inner))
        for l, u in zip(starts, starts[1:]):
            bridge(l, u)
        if cap is not None:
            end = len(verts)
            verts.append((0, 0, cap))
            faces.extend((starts[-1] + j, starts[-1] + (j + 1) % steps, end) for j in range(steps))
        return starts

    def bridge(l, u):
        faces.extend((l + j, l + (j + 1) % steps, u + (j + 1) % steps, u + j) for j in range(steps))

    if top is None:
        # 纬向加密到极点，避免平顶，也不产生重复极点。
        outer = surface([bottom + (18 - bottom) * math.sin(i * math.pi / 40) for i in range(20)], False, 18)
        inner = surface([bottom + (16.8 - bottom) * math.sin(i * math.pi / 40) for i in range(20)], True, 16.8)
    else:
        outer = surface([bottom, (bottom + top) / 2, top], False, None)
        inner = surface([bottom, (bottom + top) / 2, top], True, None)
        bridge(outer[-1], inner[-1])
    bridge(outer[0], inner[0])
    obj = _mesh(P, name, verts, faces, material, smooth=True)
    cap_planes = (bottom,) if top is None else (bottom, top)
    rim_verts = {v.index for v in obj.data.vertices
                 if any(abs(v.co.z - z * MM) < 1e-8 for z in cap_planes)}
    for face in obj.data.polygons:
        if all(i in rim_verts for i in face.vertices):
            # Flat sealing faces must not borrow the curved wall's optical normals.
            face.use_smooth = False
            face.material_index = 0  # same thin-shell material as both curved walls
    bevel = obj.modifiers.new("rim_bevel", "BEVEL")
    bevel.material = 0
    bevel.harden_normals = True
    bevel.width = .23 * MM
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    return _named(obj, name)


def _u05_clear_skin(K):
    """只给 u05 薄壳用直透材质；共享 kit_clear 保留原吸收。"""
    if hasattr(K, "clear0_u05"):
        return K.clear0_u05

    material = K.clear0.copy()
    material.name = f"{K.clear0.name}_u05_thin"
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    out = next(node for node in nodes if node.type == "OUTPUT_MATERIAL")
    surface = out.inputs["Surface"]
    glass = surface.links[0].from_socket
    thin_glass = nodes.new("ShaderNodeBsdfTransparent")
    thin_glass.inputs["Color"].default_value = (0.96, 0.98, 0.99, 1.0)
    mix = nodes.new("ShaderNodeMixShader")
    mix.name = "u05 thin rim mix"
    mix.inputs[0].default_value = 0.88
    links.new(glass, mix.inputs[1])
    links.new(thin_glass.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], surface)

    # 薄壳原本不参与体积吸收；直接留空 Volume，避开 Cycles 5.3 的混合分支。
    nodes.remove(out.inputs["Volume"].links[0].from_node)
    K.clear0_u05 = material
    return material


def _u05_nucleus_color(material):
    """Tint only the tagged small core; other Kit users keep the stock color."""
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    key = "u05 nucleus tint"
    if nodes.get(key) is not None:
        return
    shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    socket = shader.inputs["Base Color"]
    attribute = nodes.new("ShaderNodeAttribute")
    attribute.attribute_type = "OBJECT"
    attribute.attribute_name = "u05_optical_grade"
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = key
    mix.inputs[1].default_value = socket.default_value
    mix.inputs[2].default_value = (0.94, 0.38, 0.52, 1.0)
    links.new(attribute.outputs["Fac"], mix.inputs[0])
    links.new(mix.outputs[0], socket)


def u05_cell_shell(K, *, seat_spacing=10.5):
    P = Part(K, "u05_cell_shell", "white")
    skin_material = _u05_clear_skin(K)
    _u05_nucleus_color(K.cellpink)
    cuts = [(D, .3, .05) for D in (
        [(x + .4 * math.cos(i * math.tau / 24), y + .4 * math.sin(i * math.tau / 24))
         for i in range(24)] for x in (-18, 18) for y in (-7.5, 7.5))]
    base = _named(P.slab(rrect(0, 0, 25, 16, 6), 2, K.white, z=-1, bevel=.25, cuts=cuts), "u05_base")
    _bevel_before_cuts(base)
    for i, x in enumerate((-seat_spacing, 0, seat_spacing)):
        _named(P.box(x, 0, 5.5, 5.5, .6, K.white, z=.3, r=.6, bevel=.2), f"u05_seat_{i}")
    _cell_skin(P, "collar", 0, 1.925, skin_material)
    lid = _cell_skin(P, "lid", 2.075, None, skin_material)
    _adopt(_move(P, "shell", "rot", (0, 110), pivot=(0, 16, 2), axis=(-1, 0, 0)), lid)
    # Center on the shell's XY axes; lift the sphere above the middle socket.
    nucleus_center = (0, 0, 12.55)
    core = _named(P.ball(*nucleus_center, 3, K.cellpink), "u05_nucleus")
    core["u05_optical_grade"] = 1.0
    film = _named(P.ball(*nucleus_center, 3.5, K.clear), "u05_nucleus_film")
    film.modifiers.new("nucleus_film_thickness", "SOLIDIFY").thickness = .45 * MM
    for x in (-12, 12):
        P.gate(x, -16, "-y", -1)
    P.root["seat_spacing_mm"] = seat_spacing
    P.root["socket_scale"] = CELL_SOCKET_SCALE
    return P.done()


def cell_socket_positions(root):
    """装配用的三个座台中心，按片中从左到右排列。"""
    d = root["seat_spacing_mm"]
    return ((-d, "slots"), (0, "round"), (d, "tri"))


def place_cell_sockets(K, root):
    """在壳的局部坐标装三台 mini；量真实网格而非规格表的近似外径。"""
    from kit_socket import h01b_cdk20_socket

    sockets = []
    for x, pattern in cell_socket_positions(root):
        socket = h01b_cdk20_socket(K, lod="mini", pattern=pattern)
        socket.scale = (root["socket_scale"],) * 3
        socket.rotation_euler.z = -math.pi / 2  # 孔轴朝 -Y。
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        points = []
        for obj in socket.children_recursive:
            if obj.hide_render or obj.type not in ("MESH", "CURVE", "FONT"):
                continue
            evaluated = obj.evaluated_get(depsgraph)
            mesh = evaluated.to_mesh()
            points.extend(evaluated.matrix_world @ vertex.co / MM for vertex in mesh.vertices)
            evaluated.to_mesh_clear()
        x_mid = (min(v.x for v in points) + max(v.x for v in points)) / 2
        y_mid = (min(v.y for v in points) + max(v.y for v in points)) / 2
        socket.parent = root
        socket.location = Vector((x - x_mid, -y_mid, .6 - min(v.z for v in points))) * MM
        sockets.append(socket)
    bpy.context.view_layer.update()
    return sockets


def _nipper_spring(P, mat):
    """薄 V 形簧片的两侧等厚；窄边用直接建模的 0.205 mm 倒面。"""
    path = [Vector(p) for p in ((-3.35,-13.17),(-.67,-10),(0,-5.4),
                               (.65,-10),(3.26,-13.17))]
    centers = [path[0]]
    for prev, corner, after in zip(path, path[1:], path[2:]):
        incoming = (prev-corner).normalized()
        outgoing = (after-corner).normalized()
        half_turn = incoming.angle(outgoing) / 2
        radius = .22
        trim = radius / math.tan(half_turn)
        start = corner + trim*incoming
        end = corner + trim*outgoing
        center = corner + (incoming+outgoing).normalized() * radius/math.sin(half_turn)
        first = math.atan2(start.y-center.y,start.x-center.x)
        last = math.atan2(end.y-center.y,end.x-center.x)
        span = (last-first+math.pi) % math.tau - math.pi
        for i in range(9):
            angle = first + span*i/8
            centers.append(center + Vector((radius*math.cos(angle),radius*math.sin(angle))))
    centers.append(path[-1])
    tangents = [(centers[min(i+1,len(centers)-1)]-centers[max(0,i-1)]).normalized()
                for i in range(len(centers))]
    normals = [Vector((-t.y,t.x)) for t in tangents]

    def profile(width):
        left = [c+width*n for c,n in zip(centers,normals)]
        right = [c-width*n for c,n in zip(centers,normals)]
        tail = [centers[-1]+width*(normals[-1]*math.cos(a)+tangents[-1]*math.sin(a))
                for a in (i*math.pi/8 for i in range(1,8))]
        head = [centers[0]-width*(normals[0]*math.cos(a)+tangents[0]*math.sin(a))
                for a in (i*math.pi/8 for i in range(1,8))]
        return left+tail+right[::-1]+head

    outlines = [profile(w) for w in (.035,.18,.18,.035)]
    levels = (1.525, 1.670, 1.930, 2.075)
    n = len(outlines[0])
    vertices = [(p.x,p.y,z) for outline,z in zip(outlines,levels) for p in outline]
    faces = [tuple(range(n)), tuple(range(3*n,4*n))]
    for base in range(0,3*n,n):
        for i in range(n):
            j = (i+1)%n
            faces.append((base+i,base+j,base+n+j,base+n+i))
    spring = _named(_mesh(P,"leaf_spring",vertices,faces,mat),"h14_leaf_spring")
    spring["chamfer_ring_size"] = n
    return spring


def h14_nippers(K):
    P = Part(K, "h14_nippers", "white")
    for sign, role in ((1, "jaw_a"), (-1, "jaw_b")):
        pivot = (sign * 2.9, 8, 2)
        axis = (0, 0, -sign)
        joint = _move(P, role, "rot", (0, 18), pivot=pivot, axis=axis)
        z = 1.0 if sign == 1 else 2.70
        outline = [(1.1, 9.8), (1.3, 7.8), (2.3, 6.2), (1, 3), (-6.9,-3.5),
                   (-6.9,-21), (-4.4,-21), (-3.5,-5), (3,-.3), (4.4,6.1), (4.65,8.4), (4.2,10.4)]
        arm = P.slab([(sign*x,y) for x,y in outline], 1.1, K.black, z=z, bevel=.2,
                     holes=[(pivot[0],pivot[1],1.52)])
        arm.name = "h14_body_" + role
        arm_bevel = _bevel_before_cuts(arm)
        arm_bevel.width = .22 * MM

        # A narrow cutting land preserves the measured gap after the exposed edges are rounded.
        polygon = [(.018,22), (.018,10), (2.65,10), (3.9,14.5), (2.2,21.1)]
        beveled = [(x+(1.2*math.tan(math.radians(30)) if x < .02 else 0),y) for x,y in polygon]
        verts = [(sign*x,y,zz) for zz,xy in ((.8,beveled),(2.,polygon),(3.2,beveled)) for x,y in xy]
        n = len(polygon)
        faces = [tuple(range(n)), tuple(range(2*n,3*n))]
        faces.extend((k+j*n,(k+1)%n+j*n,(k+1)%n+(j+1)*n,k+(j+1)*n)
                     for j in range(2) for k in range(n))
        blade = _named(_mesh(P,"blade_"+role,verts,faces,K.black),"h14_blade_"+role)
        # 保留 30° 刃口工作斜面与 0.036 mm 合拢净隙；只钝化背部棱线。
        weight = blade.data.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
        pts = list(blade.data.vertices)
        for edge in blade.data.edges:
            if all(abs(pts[i].co.x / MM) > 1.0 for i in edge.vertices):
                weight.data[edge.index].value = 1
        bevel = blade.modifiers.new("blade_back_bevel", "BEVEL")
        bevel.width = .26 * MM
        bevel.segments = 3
        bevel.use_clamp_overlap = False
        bevel.limit_method = "WEIGHT"
        grip = _named(P.box(-5.75*sign,-11,2.25,11,2.75,K.white,z=1.875,r=1.4,bevel=.38),
                      "h14_grip_"+role)
        ribs = []
        for i in range(5):
            rib = P.box(-5.75*sign,-5-2.5*i,1.82,.37,.55,K.white,z=3.375,r=.31,bevel=.205)
            ribs.append(_named(rib,f"h14_rib_{role}_{i}"))
        _adopt(joint, arm, blade, grip, *ribs)
        # Body bore is 3.04, pin shaft 3.00. The fixed heads sit outside both body layers.
        _named(P.cyl(*pivot,1.5,4,K.gold_satin,bevel=.23), "h14_rivet_"+role)
    spring = _nipper_spring(P, K.gold_satin)
    _adopt(rig(P.root)["jaw_a"], spring)
    # 44 mm long axis follows the 52 mm board-cell axis.
    P.root.rotation_euler.z = -math.pi/2
    P.gate(-22,5.75,"-x",1.88)
    return P.done()


def _well_outline(hx, hy, radius, chamfer):
    """同一拓扑的四角；先倒圆三个角，再截右上角。"""
    pts = rrect(0,0,hx,hy,radius,n=5)
    # Replace the entire upper right arc with two points on the 45 degree cut.
    keep = [(x,y) for x,y in pts if x + y < hx + hy - chamfer - .0001]
    cut = [(hx, hy-chamfer),(hx-chamfer,hy)]
    return sorted(keep+cut,key=lambda p: math.atan2(p[1], p[0]))


def _round_ring(x, y, r, n=16):
    return [(x + r*math.cos(i*math.tau/n), y+r*math.sin(i*math.tau/n)) for i in range(n)]


def u06_wellplate(K):
    P = Part(K,"u06_wellplate","white")
    verts, faces = [], []

    def ring(points,z):
        start = len(verts)
        verts.extend((x,y,z) for x,y in points)
        return list(range(start,len(verts)))

    def walls(a,b):
        assert len(a)==len(b)
        for i,j in zip(range(len(a)), list(range(1,len(a)))+[0]):
            faces.append((a[i],a[j],b[j],b[i]))

    outline = _well_outline(21.3,14.25,1.5,3)
    inner = _well_outline(20.7,13.65,.9,3-.6*(2-math.sqrt(2)))
    shoulder = _well_outline(20.68,13.63,.88,3-.62*(2-math.sqrt(2)))
    lip_top = _well_outline(20.48,13.43,.68,3-.82*(2-math.sqrt(2)))
    bottom_edge = _well_outline(21.1, 14.05, 1.3, 3 - .2 * (2 - math.sqrt(2)))
    # 保留 4.2 叠距，名义凹深 0.6；给凹底增加 0.01 面间公差，消除共面。
    recess = .6 + WELL_STACK_CLEARANCE
    edges = [ring(inner,recess),ring(inner,0),ring(bottom_edge,0),
             ring(outline,.2),ring(outline,3.99),ring(shoulder,4.19),
             ring(shoulder,4.6),ring(lip_top,4.8)]
    faces.append(tuple(edges[0]))
    for a,b in zip(edges,edges[1:]):
        walls(a,b)
    wall_top=edges[-1]
    holes, sites = [], []
    for y in range(8):
        for x in range(12):
            a,b = 3*x-16.5,3*y-10.5
            sites.append((a,b))
            rows = [ring(_round_ring(a,b,1.3),4.8),
                    ring(_round_ring(a,b,1.1),4.6),
                    ring(_round_ring(a,b,1.1),1.8),
                    ring(_round_ring(a,b,.9),1.6)]
            holes.append(rows[0])
            for u,v in zip(rows,rows[1:]):
                walls(u,v)
            faces.append(tuple(rows[-1]))
    # Triangulate the top with the 96 bore-edge constraints; exclude each hole face.
    loops = [wall_top, *holes]
    top_ids = [v for loop in loops for v in loop]
    by_orig = {v:i for i,v in enumerate(top_ids)}
    polylines = [[by_orig[v] for v in loop] for loop in loops]
    _, _, triangles, orig_verts, _, orig_faces = delaunay_2d_cdt(
        [Vector(verts[i][:2]) for i in top_ids], [], polylines, 0, 1e-6)
    faces.extend(tuple(top_ids[orig_verts[i][0]] for i in tri)
                 for tri, parents in zip(triangles,orig_faces) if parents == [0])
    _mesh(P,"tray",verts,faces,K.white).name = "u06_tray"
    order = random.Random(96).sample(range(96),62)
    for i, mat, prefix in ((order[:38],K.liq_blue,"blue"),(order[38:],K.dishpink,"pink")):
        for index in i:
            x,y = sites[index]
            rings = [(1.6,.89),(1.8,1.0),(2.2,1.0)]
            dv = [(px,py,z) for z,r in rings for px,py in _round_ring(x,y,r)]
            df = [tuple(range(16)),tuple(range(32,48))]
            df.extend((j+i*16,(j+1)%16+i*16,(j+1)%16+(i+1)*16,j+(i+1)*16)
                      for i in range(2) for j in range(16))
            disc = _mesh(P,"fill",dv,df,mat)
            disc.name=f"u06_{prefix}_{index:02}"
    P.root["fill"] = json.dumps(dict(blue=order[:38],pink=order[38:]))
    P.root["stack_pitch_mm"] = WELL_STACK_PITCH
    P.root["underside_recess_mm"] = recess
    return P.done()


def h19_tag(K,text="048",color="gold"):
    face, ink = {"gold":(K.gold,K.ink),"blue":(K.blue,K.inkw),"grey":(K.nuc_grey,None)}[color]
    P=Part(K,"h19_tag", "white" if color=="grey" else color)
    plate = _named(P.slab(rrect(0,0,4.5,8,2),1.6,face,z=.8,bevel=.4,holes=[(0,6.0,1.1)]),"h19_plate")
    # 5.0 OD and 3.4 ID imply .8 radial stock. Preserve the specified .7 mm along X.
    y,z=8.04,1.57
    ring=P.torus(0,y,z,2.10,.4,K.gold,rot=(0,math.pi/2,0))
    ring.scale.z=.875
    ring.name="h19_hanging_ring"
    parts=[plate,ring]
    if text and ink:
        marking=P.text(text,4.2,0,-.9,1.6,ink)
        marking.data.extrude=.006*MM
        marking.location.z=1.608*MM
        bpy.context.view_layer.update()
        if marking.dimensions.y and marking.dimensions.x:
            marking.scale.y=4.2*MM/marking.dimensions.y
            marking.scale.x=min(marking.scale.y,7.8*MM/marking.dimensions.x)
        parts.append(marking)
    _adopt(_move(P,"swing","rot",(-25,25),pivot=(0,y,z),axis=(1,0,0)),*parts)
    return P.done()

