"""HKBU SCIE1007 coursework video: W3 mouth lip and injection runner."""
from kit_parts_hd import *
from kit_socket import FACE_W, SEAT_W, rounded_path

MOUTH_INNER_MM = 7.20
# 14.492657 mm maximum planar radius of the closed hero faceplate at FACE_W.
MOUTH_OUTER_MM = 9.00
LIP_SECTORS = 128
LIP_RADIAL_STATIONS = 12


def _w3_mesh(P, name, coords, faces):
    import bmesh

    name = P.nm(name)
    me = bpy.data.meshes.new(name)
    me.from_pydata([Vector(v) * MM for v in coords], [], faces)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    for face in me.polygons:
        face.use_smooth = True
    me.update()
    ob = link(bpy.data.objects.new(name, me), P.root)
    ob.data.materials.append(P.K.white)
    return ob


def _w3_loft_faces(n, ring_count, closed=False):
    faces = []
    for i in range(ring_count if closed else ring_count - 1):
        a, b = i * n, ((i + 1) % ring_count) * n
        for j in range(n):
            k = (j + 1) % n
            faces.append((a + j, a + k, b + k, b + j))
    if not closed:
        faces += [tuple(reversed(range(n))), tuple(range((ring_count - 1) * n, ring_count * n))]
    return faces


def _lip_profile():
    ri, ro = MOUTH_INNER_MM, MOUTH_OUTER_MM
    fillet = .20
    n = LIP_RADIAL_STATIONS - 2
    flat = [ri + fillet + (ro - ri - 2 * fillet) * k / (n - 1) for k in range(n)]
    profile = [(r, 0.0) for r in flat]
    # Outside lower quarter arc, then upper quarter arc, each four segments.
    for k in range(1, 5):
        a = math.pi * k / 8
        profile.append((ro - fillet + fillet * math.sin(a), fillet - fillet * math.cos(a)))
    for k in range(5):
        a = math.pi * k / 8
        profile.append((ro - fillet + fillet * math.cos(a), .50 - fillet + fillet * math.sin(a)))
    profile += [(r, .50) for r in flat[-2::-1]]
    for k in range(1, 5):
        a = math.pi * k / 8
        profile.append((ri + fillet - fillet * math.sin(a), .50 - fillet + fillet * math.cos(a)))
    for k in range(4):
        a = math.pi * k / 8
        profile.append((ri + fillet - fillet * math.cos(a), fillet - fillet * math.sin(a)))
    return profile, [ri, *flat, ro]


def _hug_profile(stations, theta):
    """Inside surface and outward thickness frame; local relief for the 048 lower lug."""
    # 0.001 mm between the nominally coincident first stations keeps faces nondegenerate.
    # The evaluated seated lug points along -Z (theta = -pi/2).
    angle = abs(math.remainder(theta + math.pi / 2, math.tau))
    q = min(1.0, max(0.0, (.25 - angle) / (.25 - .125)))
    relief = .65 * q*q*(3 - 2*q)
    side = 7.05 + relief
    dst = [Vector(p) for p in ((6.700, 13.92), (6.701, 13.92),
                                (side, 13.80), (side, 12.95), (side, 12.10))]
    dst += [Vector((r, FACE_W)) for r in stations[len(dst):]]
    dirs = [(b-a).normalized() for a,b in zip(dst,dst[1:])]
    # At the front lip, thickness points axially; on the vertical side it points radially.
    tangents = [dirs[0], dirs[0]]
    tangents += [(a+b).normalized() for a,b in zip(dirs[1:], dirs[2:])]
    tangents += [dirs[-1]]
    # Roll the outer elbow toward +W in the relieved sector, keeping the
    # full thickness while preventing the offset surfaces from folding over.
    tangents[4] = tangents[4].lerp(Vector((math.sqrt(.75), -.5)), q*q*(3 - 2*q)).normalized()
    return dst, [Vector((-v.y,v.x)) for v in tangents]


def _hug_meridian(r, h, stations, profile):
    path, normals = profile
    for i, (a, b) in enumerate(zip(stations, stations[1:])):
        if r <= b:
            f = (r - a) / (b - a)
            return path[i].lerp(path[i+1],f) + h * normals[i].lerp(normals[i+1],f).normalized()
    return path[-1] + h * normals[-1]


def h21_mouth_lip(K):
    """X = socket +W; leave the returned root at identity under the socket."""
    P = Part(K, "h21_mouth_lip", "white")
    profile, stations = _lip_profile()
    width = MOUTH_OUTER_MM - MOUTH_INNER_MM
    shapes = {name: [] for name in ("Basis", "bulge", "ripple3", "ripple5", "hug")}
    angles = [j * math.tau / LIP_SECTORS for j in range(LIP_SECTORS)]
    hug_profiles = [_hug_profile(stations, a) for a in angles]
    for r, h in profile:
        s = (r - MOUTH_INNER_MM) / width
        bulge_r = 9.00 - (1 - s) * 5.00
        bulge_w = FACE_W + .25 + 3.00 * (1 - s)**1.5
        # Offset the cross-section about the deformed middle sheet along its normal.
        slope = -.90 * math.sqrt(1 - s)
        normal_w = 1 / math.hypot(1, slope)
        normal_r = -slope * normal_w
        for a, hug_profile in zip(angles, hug_profiles):
            hug_r, hug_w = _hug_meridian(r, h, stations, hug_profile)
            c, k = math.cos(a), math.sin(a)
            samples = (
                (r, FACE_W + h),
                (bulge_r + normal_r * (h - .25), bulge_w + normal_w * (h - .25)),
                (r, FACE_W + h + .5 * .35 * (1 + math.sin(3 * a)) * math.sin(math.pi * s)),
                (r, FACE_W + h + .5 * .25 * (1 + math.sin(5 * a + .7)) * math.sin(math.pi * s)),
                (hug_r, hug_w),
            )
            for coords, (radius, axial) in zip(shapes.values(), samples):
                coords.append((axial, radius * c, radius * k))
    lip = _w3_mesh(P, "lip", shapes["Basis"], _w3_loft_faces(LIP_SECTORS, len(profile), True))
    for name, coords in shapes.items():
        key = lip.shape_key_add(name=name, from_mix=False)
        if name != "Basis":
            key.data.foreach_set("co", [v for coord in coords for v in Vector(coord) * MM])
            key.value = 0.0
    return P.done()


def _runner_path(rise, reach):
    p3 = Vector((-reach, 0, rise))
    path = rounded_path([(0, 0, 0), (0, 0, rise - 16), (-.43 * reach, 0, rise - 4), p3], 6)
    # Replace the final straight section from the last rounded corner with a
    # cubic Hermite span. Its entrance follows the old path; its exit is -X.
    a = path[-2]
    delta = p3 - a
    b = a + delta / 3
    c = p3 + Vector((-delta.x / 3, 0, 0))
    for k in range(1, 13):
        t = k / 12
        path.insert(-1, (1-t)**3 * a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*p3)
    path.pop()  # the cubic already ends at P3
    return path


def _fillet_profile(points, rounds):
    """Circular fillets specified by radius; preserve the nominal profile vertices."""
    points = [Vector(p) for p in points]
    out = []
    for i, b in enumerate(points):
        if i not in rounds:
            out.append(tuple(b))
            continue
        radius = rounds[i]
        u = (points[i-1] - b).normalized()
        v = (points[i+1] - b).normalized()
        half = u.angle(v) / 2
        center = b + (u + v).normalized() * (radius / math.sin(half))
        tangent = radius / math.tan(half)
        s = (b + tangent*u - center).normalized()
        t = (b + tangent*v - center).normalized()
        for k in range(5):
            # 2D profile; normalized linear interpolation stays on the arc.
            # Blender's Vector.slerp is 3D-only.
            a = s.lerp(t, k / 4).normalized()
            out.append(tuple(center + radius*a))
    return out


def h22_nozzle_runner(K, rise=34.0, reach=17.0):
    """A closed swept feed rod; run_u is normalized arclength along its axis."""
    P = Part(K, "h22_nozzle_runner", "white")
    path = _runner_path(rise, reach)
    # The root collar occupies the first 1.2 mm of the vertical section.
    # The lower cap also gets a .20 mm fillet leading into the collar.
    base = _fillet_profile([(0, 1.2), (0, 1.7), (1.2, 1.7), (1.2, 1.2)], {1: .20, 2: .20})[1:]
    base[0] = (0.0, base[0][1])
    base.append((1.4, 1.2))
    along = [0.0]
    for a, b in zip(path, path[1:]):
        along.append(along[-1] + (b - a).length)
    normal_y = Vector((0, 1, 0))
    sections = [(Vector((0, 0, z)), Vector((0, 0, 1)), r, z) for z, r in base]
    for i in range(1, len(path) - 1):
        if along[i] <= base[-1][0]:
            continue
        tangent = ((path[i] - path[i-1]).normalized() + (path[i+1] - path[i]).normalized()).normalized()
        sections.append((path[i], tangent, 1.2, along[i]))
    direction = Vector((-1, 0, 0))
    p3 = path[-1]
    nozzle = [(0, 1.2), (0, 2.3), (5.0, 1.5), (5.0, .6), (6.6, .3)]
    for a, r in _fillet_profile(nozzle, {1: .30, 2: .30}):
        sections.append((p3 + a*direction, direction, r, along[-1] + a))
    coords, values = [], []
    n = 64
    for point, tangent, r, distance in sections:
        across = tangent.cross(normal_y)
        for j in range(n):
            a = j * math.tau / n
            coords.append(point + r * (math.cos(a) * normal_y + math.sin(a) * across))
            values.append(distance / sections[-1][-1])
    ob = _w3_mesh(P, "sweep", coords, _w3_loft_faces(n, len(sections)))
    ob.data.attributes.new("run_u", "FLOAT", "POINT").data.foreach_set("value", values)
    ob.data.set_sharp_from_angle(angle=math.radians(35))
    tip_center = p3 + 6.6*direction
    tip = link(bpy.data.objects.new(P.name + "__tip", None), P.root)
    tip.location = tip_center * MM
    # Local +X is the locator's forward vector, so it points along world -X.
    tip.rotation_euler.z = math.pi
    tip["locator"] = "tip"
    P.gate(tip_center.x, tip_center.y, "-x", tip_center.z)
    P.root["path_length_mm"] = sections[-1][-1]
    return P.done()

