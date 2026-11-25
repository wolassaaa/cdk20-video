# HKBU SCIE1007 coursework science video. Arena direction: T4 pin, T5 people and stone, T2 stand-in reads as a person.
ROOT = 'D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/arena/code/'
p = ROOT + 'scene.py'
s = open(p, encoding='utf8').read()
a = '    spot((22, -170, 9), tuple(pocket + np.array([0, -2, 0])), R, 9e6, 1.3, 0.4, 0.2)\n'
assert a in s
s = s.replace(a, '    spot((18, -100, 6), tuple(pocket + np.array([0, -2, 0])), R, 4e6, 1.3, 0.4, 0.2)\n')
a = '''    person(c0[0] - 9, c0[1] + 5, 1.75)
    person(c0[0] - 12.5, c0[1] + 4.4, 1.75)
    ruler((c0[0] - 5, c0[1] + 3), 10, 0.0, width=0.1)
'''
assert a in s
s = s.replace(a, '''    # the near floor is out of frame, so the people stand further back, against the light of the wall on the floor
    person(-3, 8, 1.75)
    person(-6.4, 7.4, 1.75)
    ruler((-1, 5), 10, 0.0, width=0.1)
''')
open(p, 'w', encoding='utf8').write(s)

p = ROOT + 'grade.py'
s = open(p, encoding='utf8').read()
a = 'PITCH = {"T2": 3, "T5": 4}'
assert a in s
s = s.replace(a, 'PITCH = {"T2": 3, "T5": 3}')
a = '"T5": (("F2FFFB", 1.0),'
assert a in s
s = s.replace(a, '"T5": (("F2FFFB", 0.62),')
open(p, 'w', encoding='utf8').write(s)

p = ROOT + 'bust.py'
s = open(p, encoding='utf8').read()
s = s.replace('H = 0.0085\n', 'H = 0.006\n')
a = '''me = bpy.data.meshes.new("b")
me.from_pydata(verts.tolist(), [], quads.tolist())
'''
assert a in s
s = s.replace(a, a + '''# paint by position, so the stand-in has hair, a jumper, brows, eyes and a mouth. Still a stand-in, but it reads as a person on a wall
vx, vy, vz = verts[:, 0], verts[:, 1], verts[:, 2]
col = np.tile(np.array([.46, .42, .40]), (len(verts), 1))
col[vz < 1.355 + .4 * np.abs(vx)] = (.10, .115, .15)
col[vz > 1.71 - .9 * np.clip(vy + .10, 0, None)] = (.045, .04, .036)
col[(np.abs(vz - 1.502) < .007) & (np.abs(vx) < .031) & (vy < -.09)] = (.30, .17, .15)
for sx in (-1, 1):
    col[(((vx - sx * .050) / .019) ** 2 + ((vz - 1.621) / .0105) ** 2 < 1) & (vy < -.08)] = (.03, .025, .022)
    bx = np.abs(vx - sx * .052) < .037
    col[bx & (np.abs(vz - 1.657 - .12 * (np.abs(vx) - .05)) < .0065) & (vy < -.07)] = (.05, .04, .035)
''')
a = 'for po in me.polygons:\n    po.use_smooth = True\nme.update()\n'
assert a in s
s = s.replace(a, '''for po in me.polygons:
    po.use_smooth = True
at_ = me.attributes.new("col", "FLOAT_COLOR", "POINT")
at_.data.foreach_set("color", np.c_[col, np.ones(len(col))].astype(np.float32).ravel().tolist())
me.update()
''')
a = 'p.inputs["Base Color"].default_value = (.42, .41, .40, 1); p.inputs["Roughness"].default_value = .5\n'
assert a in s
s = s.replace(a, '''p.inputs["Roughness"].default_value = .55
an = m.node_tree.nodes.new("ShaderNodeAttribute"); an.attribute_name = "col"
m.node_tree.links.new(an.outputs["Color"], p.inputs["Base Color"])
''')
open(p, 'w', encoding='utf8').write(s)

p = 'D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/art/arena/layers.jsx'
s = open(p, encoding='utf8').read()
a = '<T x={186} y={232} size={96} font={BIG} weight={800} color="#fff" lh={1}>Enzyme IC50</T>'
assert a in s
s = s.replace(a, '<T x={186} y={222} size={84} font={BIG} weight={800} color="#fff" lh={1}>Enzyme IC50</T>')
a = '<T x={182} y={318} size={170}'
assert a in s
s = s.replace(a, '<T x={182} y={326} size={170}')
open(p, 'w', encoding='utf8').write(s)
print('ok')
