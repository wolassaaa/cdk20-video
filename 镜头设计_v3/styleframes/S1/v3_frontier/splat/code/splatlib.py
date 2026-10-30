"""Shared Blender helpers for the SPLAT test: a 3D Gaussian splat renderer built from Cycles primitives.

Each splat = one instanced cube (half-size 1 = 3 sigma) scaled/rotated by its covariance.
The material computes, per camera ray, the ray's closest approach to the splat centre in the
splat's own (whitened) space:  r^2 = |P|^2 - (P.D)^2,  alpha = opacity * exp(-r^2 / (2 sigma^2)).
That is the exact line integral of an anisotropic 3D Gaussian, i.e. the 3DGS / EWA footprint,
but depth-ordered per pixel by the ray tracer instead of per splat by a sort.
Emission + transparent only, Russian roulette off for transparent bounces -> deterministic,
no path-tracing noise; samples only buy anti-aliasing.

View-dependent colour (the role spherical harmonics play in real 3DGS) is a fresnel-like rim
term and a fixed virtual highlight, both from the stored splat normal and the incoming ray.
"""
import bpy, math
import numpy as np

SIG2K = 5.0  # exp(-r^2 * 5) * (1 - r^2): sigma ~ 0.316 of the cube half-size; the window takes it exactly to zero at the hull


def new_mat(name):
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    try:
        m.cycles.emission_sampling = "NONE"   # 500k emissive instances must not become lights
    except Exception:
        try: m.emission_sampling = "NONE"
        except Exception: pass
    return m, nt


def splat_material(name="splat", light_dir=(-0.45, -0.55, 0.70)):
    """Instancer attributes used: col (vec), alpha, nrm (vec), rim, spec, glow, dif (float)."""
    m, nt = new_mat(name)
    N = nt.nodes; L = nt.links

    def attr(nm, out="Vector"):
        a = N.new("ShaderNodeAttribute"); a.attribute_type = "INSTANCER"; a.attribute_name = nm
        return a.outputs[out]

    def vm(op, a, b=None, sc=None):
        n = N.new("ShaderNodeVectorMath"); n.operation = op
        L.new(a, n.inputs[0])
        if b is not None:
            if isinstance(b, (tuple, list)): n.inputs[1].default_value = b
            else: L.new(b, n.inputs[1])
        if sc is not None: n.inputs["Scale"].default_value = sc
        return n

    def mth(op, a, b=None, c=None, clamp=False):
        n = N.new("ShaderNodeMath"); n.operation = op; n.use_clamp = clamp
        for i, x in enumerate((a, b, c)):
            if x is None: continue
            if isinstance(x, (int, float)): n.inputs[i].default_value = float(x)
            else: L.new(x, n.inputs[i])
        return n.outputs[0]

    geo = N.new("ShaderNodeNewGeometry")
    lp = N.new("ShaderNodeAttribute"); lp.attribute_type = "GEOMETRY"; lp.attribute_name = "lp"
    P = lp.outputs["Vector"]
    # ray direction in world = -Incoming; to object space (inverse transform incl. inverse scale)
    neg = vm("SCALE", geo.outputs["Incoming"], sc=-1.0)
    vt = N.new("ShaderNodeVectorTransform"); vt.vector_type = "VECTOR"
    vt.convert_from = "WORLD"; vt.convert_to = "OBJECT"
    L.new(neg.outputs["Vector"], vt.inputs[0])
    D = vm("NORMALIZE", vt.outputs[0]).outputs["Vector"]
    pd = vm("DOT_PRODUCT", P, D).outputs["Value"]
    pp = vm("DOT_PRODUCT", P, P).outputs["Value"]
    r2 = mth("SUBTRACT", pp, mth("MULTIPLY", pd, pd))
    g = mth("EXPONENT", mth("MULTIPLY", r2, -SIG2K))
    # cut the tail beyond 3 sigma so the cube hull never shows
    win = mth("SUBTRACT", 1.0, r2, clamp=True)   # (1 - r^2) window: exactly zero at the hull
    a = mth("MULTIPLY", mth("MULTIPLY", g, win), attr("alpha", "Fac"))
    a = mth("MULTIPLY", a, mth("SUBTRACT", 1.0, geo.outputs["Backfacing"]))
    a = mth("MINIMUM", a, 0.995)

    # view-dependent colour (the job spherical harmonics do in real 3DGS):
    #   rim = (1-|n.i|)^3  ;  two softboxes seen in the reflection vector  ;  a little lambert for form
    I = geo.outputs["Incoming"]
    nrm = attr("nrm")
    ndotv = vm("DOT_PRODUCT", nrm, I).outputs["Value"]
    ndi = mth("ABSOLUTE", ndotv)
    rim = mth("POWER", mth("SUBTRACT", 1.0, ndi, clamp=True), 2.4)
    rim = mth("MULTIPLY", rim, attr("rim", "Fac"))
    ld = np.array(light_dir, float); ld /= np.linalg.norm(ld)
    refl = vm("REFLECT", vm("SCALE", I, sc=-1.0).outputs["Vector"], nrm).outputs["Vector"]

    def box(d, up, hw, hh, soft):
        d = np.array(d, float); d /= np.linalg.norm(d)
        up = np.array(up, float); up -= up.dot(d) * d; up /= np.linalg.norm(up)
        rt = np.cross(d, up)
        fac = lambda ax, h: mth("MULTIPLY", mth("SUBTRACT", h + soft, mth("ABSOLUTE", vm("DOT_PRODUCT", refl, tuple(ax)).outputs["Value"])), 1.0 / (2 * soft))
        cl = lambda x: mth("MINIMUM", mth("MAXIMUM", x, 0.0), 1.0)
        m = mth("MULTIPLY", cl(fac(rt, hw)), cl(fac(up, hh)))
        front = mth("GREATER_THAN", vm("DOT_PRODUCT", refl, tuple(d)).outputs["Value"], 0.0)
        return mth("MULTIPLY", m, front)

    strip = box((-0.80, -0.42, 0.42), (0, 0, 1), 0.040, 0.60, 0.075)      # tall strip, upper left: the long glass streak
    over = box((0.25, -0.30, 0.92), (0, 1, 0), 0.40, 0.05, 0.09)         # broad overhead box
    spec = mth("ADD", strip, mth("MULTIPLY", over, 0.55))
    spec = mth("MULTIPLY", spec, attr("spec", "Fac"))
    nl = mth("MAXIMUM", vm("DOT_PRODUCT", nrm, tuple(ld)).outputs["Value"], 0.0)
    dw = attr("dif", "Fac")
    lamb = mth("ADD", mth("SUBTRACT", 1.0, dw), mth("MULTIPLY", dw, nl))
    # the far wall of the glass is dimmer than the near wall (rim and highlights only; solid vessels keep their body)
    side = mth("ADD", 0.38, mth("MULTIPLY", mth("GREATER_THAN", ndotv, 0.0), 0.62))
    gain = mth("ADD", lamb, mth("MULTIPLY", mth("ADD", rim, spec), side))
    gain = mth("MULTIPLY", gain, attr("glow", "Fac"))
    colv = vm("SCALE", attr("col"), sc=1.0)
    L.new(gain, colv.inputs["Scale"])
    # add a white component for the highlight so spec on red vessels reads as a glint, kept small
    em = N.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0
    L.new(colv.outputs["Vector"], em.inputs["Color"])
    tr = N.new("ShaderNodeBsdfTransparent")
    mx = N.new("ShaderNodeMixShader")
    L.new(a, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    out = N.new("ShaderNodeOutputMaterial")
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m


def splat_object(name, n, mat):
    """Point mesh with n vertices + GN that instances a cube per point with rot (euler) / scl from attributes."""
    me = bpy.data.meshes.new(name)
    me.vertices.add(n)
    for nm, tp in (("rot", "FLOAT_VECTOR"), ("scl", "FLOAT_VECTOR"), ("col", "FLOAT_VECTOR"), ("nrm", "FLOAT_VECTOR"),
                   ("alpha", "FLOAT"), ("rim", "FLOAT"), ("spec", "FLOAT"), ("glow", "FLOAT"), ("dif", "FLOAT")):
        me.attributes.new(nm, tp, "POINT")
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ng = bpy.data.node_groups.new(name + "_gn", "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes; L = ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    cube = N.new("GeometryNodeMeshCube"); cube.inputs["Size"].default_value = (2.0, 2.0, 2.0)
    for k in ("Vertices X", "Vertices Y", "Vertices Z"): cube.inputs[k].default_value = 2
    st = N.new("GeometryNodeStoreNamedAttribute"); st.data_type = "FLOAT_VECTOR"; st.domain = "POINT"
    st.inputs["Name"].default_value = "lp"
    gp = N.new("GeometryNodeInputPosition")
    L.new(cube.outputs["Mesh"], st.inputs["Geometry"]); L.new(gp.outputs[0], st.inputs["Value"])
    sm = N.new("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = mat
    L.new(st.outputs["Geometry"], sm.inputs["Geometry"])
    iop = N.new("GeometryNodeInstanceOnPoints")
    L.new(gi.outputs[0], iop.inputs["Points"]); L.new(sm.outputs[0], iop.inputs["Instance"])
    ra = N.new("GeometryNodeInputNamedAttribute"); ra.data_type = "FLOAT_VECTOR"; ra.inputs["Name"].default_value = "rot"
    e2r = N.new("FunctionNodeEulerToRotation")
    L.new(ra.outputs["Attribute"], e2r.inputs[0]); L.new(e2r.outputs[0], iop.inputs["Rotation"])
    sa = N.new("GeometryNodeInputNamedAttribute"); sa.data_type = "FLOAT_VECTOR"; sa.inputs["Name"].default_value = "scl"
    L.new(sa.outputs["Attribute"], iop.inputs["Scale"])
    L.new(iop.outputs["Instances"], go.inputs[0])
    md = ob.modifiers.new("gn", "NODES"); md.node_group = ng
    return ob


def set_attrs(ob, pos, rot, scl, col, nrm, alpha, rim, spec, glow, dif):
    me = ob.data
    me.attributes["position"].data.foreach_set("vector", np.ascontiguousarray(pos, np.float32).ravel())
    for nm, arr in (("rot", rot), ("scl", scl), ("col", col), ("nrm", nrm)):
        me.attributes[nm].data.foreach_set("vector", np.ascontiguousarray(arr, np.float32).ravel())
    for nm, arr in (("alpha", alpha), ("rim", rim), ("spec", spec), ("glow", glow), ("dif", dif)):
        me.attributes[nm].data.foreach_set("value", np.ascontiguousarray(arr, np.float32).ravel())
    me.update()


def cycles_setup(samples=96, pct=100, tbounces=192):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    pref = bpy.context.preferences.addons["cycles"].preferences
    pref.compute_device_type = "OPTIX"; pref.get_devices()
    for d in pref.devices: d.use = (d.type == "OPTIX")
    c = scn.cycles
    c.device = "GPU"
    c.samples = samples
    c.use_adaptive_sampling = False
    c.use_denoising = False
    c.max_bounces = tbounces
    c.diffuse_bounces = 0; c.glossy_bounces = 0; c.transmission_bounces = 0; c.volume_bounces = 0
    c.transparent_max_bounces = tbounces
    c.min_transparent_bounces = tbounces   # no Russian roulette on transparency -> deterministic
    c.min_light_bounces = 0
    c.caustics_reflective = False; c.caustics_refractive = False
    c.seed = 11; c.use_animated_seed = False
    c.pixel_filter_type = "BLACKMAN_HARRIS"; c.filter_width = 1.6
    scn.render.use_persistent_data = True
    scn.render.resolution_x = 1920; scn.render.resolution_y = 1080; scn.render.resolution_percentage = pct
    vs = scn.view_settings; vs.view_transform = "Standard"; vs.look = "None"; vs.exposure = 0.0; vs.gamma = 1.0
    scn.display_settings.display_device = "sRGB"
    scn.render.image_settings.file_format = "PNG"; scn.render.image_settings.color_mode = "RGB"
    scn.render.image_settings.color_depth = "8"
    w = bpy.data.worlds.new("w"); scn.world = w
    try: w.use_nodes = True
    except Exception: pass
    bg = w.node_tree.nodes.get("Background")
    if bg: bg.inputs["Color"].default_value = (0, 0, 0, 1); bg.inputs["Strength"].default_value = 0.0


def euler_from_mats(R):
    """R: (n,3,3) rotation matrices (columns = local axes in world) -> XYZ euler (n,3) as Blender uses."""
    # Blender XYZ euler: R = Rz * Ry * Rx
    sy = -R[:, 2, 0]
    sy = np.clip(sy, -1.0, 1.0)
    y = np.arcsin(sy)
    x = np.arctan2(R[:, 2, 1], R[:, 2, 2])
    z = np.arctan2(R[:, 1, 0], R[:, 0, 0])
    return np.stack([x, y, z], 1)
