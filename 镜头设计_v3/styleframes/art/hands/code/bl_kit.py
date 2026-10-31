"""HKBU SCIE1007 coursework science video. Hands direction, Blender kit: top-down camera, one low sun, a stand-in hand built from metaballs.
The hand is a placeholder for phone footage of the team's own hands. Scale: 100 px = 1 unit at 1920 x 1080. Image right = +X, image up = +Y."""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

SH = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/_shared"
sys.path.insert(0, SH)
from scene_cdk20 import build  # noqa: E402

RAW = r"D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/hands/code/_raw"
SUN = Vector((-0.62, 0.50, 0.60)).normalized()


def scene(w=1920, h=1080, samples=128, with_protein=False):
    sc, ob, cam = build(w, h, samples=samples)
    sc.render.film_transparent = True
    sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
    sc.cycles.use_denoising, sc.cycles.denoiser = True, "OPTIX"
    sc.cycles.max_bounces = 6
    if not with_protein:
        bpy.data.objects.remove(ob)
        ob = None
    else:
        c = sum((Vector(v) for v in ob.bound_box), Vector()) / 8
        ob.data.transform(Matrix.Translation(-c))
        ob.data.update()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = w / 100.0
    cam.data.clip_end = 200
    cam.location = (0, 0, 40)
    cam.rotation_mode = "XYZ"
    cam.rotation_euler = (0, 0, 0)
    s = bpy.data.lights.new("sun", "SUN")
    s.energy, s.angle, s.color = 3.6, math.radians(2.0), (1.0, 1.0, 1.0)
    so = bpy.data.objects.new("sun", s)
    so.rotation_mode = "QUATERNION"
    so.rotation_quaternion = SUN.to_track_quat("Z", "Y")
    sc.collection.objects.link(so)
    wd = bpy.data.worlds.new("w")
    wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
    wd.node_tree.nodes["Background"].inputs[1].default_value = 0.16
    sc.world = wd
    return sc, ob, cam


def catcher(z=0.0):
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, z))
    p = bpy.context.object
    p.is_shadow_catcher = True
    return p


def skin(tone=(0.50, 0.215, 0.125), name="skin", dust=0.55):
    """Deep warm base, blood blotches, fine lines, and ash caught on the skin so it belongs to the world."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]
    b.inputs["Subsurface Weight"].default_value = 0.8
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.22, 0.10)
    b.inputs["Subsurface Scale"].default_value = 0.10
    b.inputs["Roughness"].default_value = 0.42
    tc = N.new("ShaderNodeTexCoord")
    n1 = N.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value, n1.inputs["Detail"].default_value = 1.6, 5
    L.new(tc.outputs["Object"], n1.inputs["Vector"])
    mp = N.new("ShaderNodeMapRange")
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[6].default_value = (*tone, 1)
    mix.inputs[7].default_value = (min(1, tone[0] * 1.2), tone[1] * 0.72, tone[2] * 0.72, 1)
    L.new(n1.outputs[0], mp.inputs["Value"])
    mp.inputs["From Min"].default_value, mp.inputs["From Max"].default_value = 0.38, 0.62
    L.new(mp.outputs[0], mix.inputs[0])
    # ash: small flecks and a soft film
    v = N.new("ShaderNodeTexVoronoi")
    v.inputs["Scale"].default_value = 60
    n2 = N.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value, n2.inputs["Detail"].default_value = 3.2, 8
    L.new(tc.outputs["Object"], v.inputs["Vector"])
    L.new(tc.outputs["Object"], n2.inputs["Vector"])
    fl = N.new("ShaderNodeMapRange")
    fl.inputs["From Min"].default_value, fl.inputs["From Max"].default_value = 0.46, 0.60
    fl.inputs["To Min"].default_value, fl.inputs["To Max"].default_value = 0.0, dust
    L.new(n2.outputs[0], fl.inputs["Value"])
    ms = N.new("ShaderNodeMath")
    ms.operation = "MULTIPLY"
    inv = N.new("ShaderNodeMath")
    inv.operation = "LESS_THAN"
    inv.inputs[1].default_value = 0.42
    L.new(v.outputs[0], inv.inputs[0])
    L.new(fl.outputs[0], ms.inputs[0])
    L.new(inv.outputs[0], ms.inputs[1])
    mix2 = N.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    mix2.inputs[7].default_value = (0.42, 0.42, 0.42, 1)
    L.new(mix.outputs[2], mix2.inputs[6])
    L.new(ms.outputs[0], mix2.inputs[0])
    L.new(mix2.outputs[2], b.inputs["Base Color"])
    # skin lines: stretched noise across the back of the hand, plus pores
    mpg = N.new("ShaderNodeMapping")
    mpg.inputs["Scale"].default_value = (1.0, 9.0, 1.0)
    L.new(tc.outputs["Object"], mpg.inputs["Vector"])
    n3 = N.new("ShaderNodeTexNoise")
    n3.inputs["Scale"].default_value, n3.inputs["Detail"].default_value = 7, 8
    n3.inputs["Roughness"].default_value = 0.65
    L.new(mpg.outputs[0], n3.inputs["Vector"])
    n4 = N.new("ShaderNodeTexNoise")
    n4.inputs["Scale"].default_value, n4.inputs["Detail"].default_value = 70, 6
    L.new(tc.outputs["Object"], n4.inputs["Vector"])
    add = N.new("ShaderNodeMath")
    add.operation = "ADD"
    L.new(n3.outputs[0], add.inputs[0])
    mm = N.new("ShaderNodeMath")
    mm.operation = "MULTIPLY"
    mm.inputs[1].default_value = 0.35
    L.new(n4.outputs[0], mm.inputs[0])
    L.new(mm.outputs[0], add.inputs[1])
    bm = N.new("ShaderNodeBump")
    bm.inputs["Strength"].default_value, bm.inputs["Distance"].default_value = 0.8, 0.05
    L.new(add.outputs[0], bm.inputs["Height"])
    L.new(bm.outputs[0], b.inputs["Normal"])
    return m


def nail_mat():
    m = bpy.data.materials.new("nail")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.60, 0.34, 0.28, 1)
    b.inputs["Roughness"].default_value = 0.22
    return m


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


class Hand:
    """Right hand palm down, wrist at the origin, fingers towards +Y, thumb towards -X. curl: three joint angles in degrees per finger."""

    FING = [(-0.64, 2.42, 2.45, 0.165), (-0.21, 2.54, 2.72, 0.172), (0.22, 2.46, 2.52, 0.162), (0.63, 2.22, 2.00, 0.140)]

    def __init__(self, curl=None, splay=(-9, -2, 4, 12), thumb=(-52, 18), lift=0.62):
        self.balls = []
        self.tips = []
        self.nails = []
        curl = curl or [(12, 16, 10)] * 4
        for yy in np.arange(-0.2, 2.45, 0.28):
            hw = 0.60 + 0.16 * np.clip(yy, 0, 2) / 2
            for xx in np.linspace(-hw, hw, 5):
                self.balls.append(((xx, yy, lift + 0.08 * (1 - (xx / hw) ** 2)), 0.30))
        # tendons: faint ridges from the wrist to each knuckle
        for bx, by, _, _ in self.FING:
            for t in np.linspace(0.15, 0.95, 9):
                self.balls.append(((bx * (0.45 + 0.55 * t), by * t, lift + 0.20), 0.105))
        for i, (bx, by, ln, r) in enumerate(self.FING):
            yaw = math.radians(splay[i])
            d = np.array([math.sin(yaw), math.cos(yaw), 0.0])
            p = np.array([bx, by, lift + 0.05])
            self.balls.append((tuple(p + np.array([0, 0, 0.08])), r * 1.75))   # knuckle
            pitch = 0
            segs = (0.46, 0.30, 0.24)
            for k in range(3):
                pitch += math.radians(curl[i][k])
                dir3 = np.array([d[0] * math.cos(pitch), d[1] * math.cos(pitch), -math.sin(pitch)])
                n = 7
                for t in range(n):
                    p = p + dir3 * ln * segs[k] / n
                    bump = 1.12 if t >= n - 1 and k < 2 else 1.0   # joints sit a little proud
                    self.balls.append((tuple(p), r * bump * (1 - 0.12 * (k + t / n) / 3)))
            self.tips.append(p.copy())
            self.nails.append((p - dir3 * 0.15 + np.array([0, 0, r * 1.20]), d, pitch, r))
        # thumb
        ta = math.radians(thumb[0])
        d = np.array([math.sin(ta), math.cos(ta), -0.12])
        d /= np.linalg.norm(d)
        p = np.array([-0.56, 0.30, lift - 0.05])
        for t in range(9):
            p = p + d * 0.17
            self.balls.append((tuple(p), 0.29 - 0.011 * t))
        ta2 = math.radians(thumb[0] + thumb[1])
        d2 = np.array([math.sin(ta2), math.cos(ta2), -0.22])
        d2 /= np.linalg.norm(d2)
        for t in range(9):
            p = p + d2 * 0.17
            self.balls.append((tuple(p), 0.20 - 0.006 * t))
        self.tips.append(p.copy())
        self.nails.append((p - d2 * 0.14 + np.array([0.0, 0.0, 0.14]), d2, 0.2, 0.15))
        # forearm, flattened: two rows
        for yy in np.arange(-0.3, -13, -0.36):
            w = 0.40 + min(0.26, max(0.0, (-yy - 0.8) * 0.055))
            for xx in (-w, 0, w):
                self.balls.append(((xx, yy, lift - 0.04), 0.33 + min(0.1, -yy * 0.012)))

    def add(self, loc=(0, 0, 0), ang=0.0, flip=False, s=1.0, mat=None, name="hand"):
        """Puts the hand in the scene. ang in degrees, counter-clockwise on screen, fingers point +Y at 0."""
        mb = bpy.data.metaballs.new(name)
        mb.resolution = 0.05
        mb.render_resolution = 0.03
        mb.threshold = 0.6
        R = rz(math.radians(ang))
        fx = -1.0 if flip else 1.0
        loc = np.array(loc, float)
        for co, r in self.balls:
            q = np.array([co[0] * fx, co[1], co[2]]) * s
            e = mb.elements.new(type="BALL")
            e.co = tuple(R @ q + loc)
            e.radius = r * s * 1.9
            e.stiffness = 2.2
        ob = bpy.data.objects.new(name, mb)
        bpy.context.scene.collection.objects.link(ob)
        mb.materials.append(mat or skin())
        nm = nail_mat()
        for co, d, pitch, r in self.nails:
            q = np.array([co[0] * fx, co[1], co[2]]) * s
            dd = R @ np.array([d[0] * fx, d[1], 0])
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1, location=tuple(R @ q + loc))
            nl = bpy.context.object
            nl.scale = (r * 0.92 * s, r * 1.25 * s, r * 0.16 * s)
            nl.rotation_euler = (math.radians(-math.degrees(pitch) * 0.85), 0, math.atan2(-dd[0], dd[1]))
            nl.data.materials.append(nm)
            bpy.ops.object.shade_smooth()
        return ob

    def tip(self, i, loc=(0, 0, 0), ang=0.0, flip=False, s=1.0):
        fx = -1.0 if flip else 1.0
        q = self.tips[i] * np.array([fx, 1, 1]) * s
        return rz(math.radians(ang)) @ q + np.array(loc, float)
