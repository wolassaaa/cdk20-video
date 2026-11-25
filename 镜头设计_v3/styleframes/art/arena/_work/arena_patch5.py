p = 'D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/arena/code/scene.py'
s = open(p, encoding='utf8').read()

# floor panels: 10 m seams, one tile = 1 nm at the hall's scale
s = s.replace('FLOOR = mat("floor", 0.035, 0.34, 0.5)\n', '''FLOOR = mat("floor", 0.035, 0.34, 0.5)


def floor_seams():
    """10 m panels: at this hall's scale one tile is 1 nm. A seam is a matte line, so it only shows where the floor reflects light."""
    nt = FLOOR.node_tree
    pr = nt.nodes["Principled BSDF"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])

    def line(sock):
        dv = nt.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = 10.0
        nt.links.new(sock, dv.inputs[0])
        fr = nt.nodes.new("ShaderNodeMath"); fr.operation = "FRACT"
        nt.links.new(dv.outputs[0], fr.inputs[0])
        pp = nt.nodes.new("ShaderNodeMath"); pp.operation = "PINGPONG"; pp.inputs[1].default_value = 0.5
        nt.links.new(fr.outputs[0], pp.inputs[0])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.006
        nt.links.new(pp.outputs[0], lt.inputs[0])
        return lt.outputs[0]

    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
    nt.links.new(line(sep.outputs["X"]), mx.inputs[0]); nt.links.new(line(sep.outputs["Y"]), mx.inputs[1])
    rg = nt.nodes.new("ShaderNodeMapRange")
    rg.inputs["To Min"].default_value, rg.inputs["To Max"].default_value = 0.34, 0.8
    nt.links.new(mx.outputs[0], rg.inputs["Value"])
    nt.links.new(rg.outputs[0], pr.inputs["Roughness"])
    ab = nt.nodes.new("ShaderNodeMapRange")
    ab.inputs["To Min"].default_value, ab.inputs["To Max"].default_value = 0.035, 0.0
    nt.links.new(mx.outputs[0], ab.inputs["Value"])
    cb = nt.nodes.new("ShaderNodeCombineColor")
    for k in range(3):
        nt.links.new(ab.outputs[0], cb.inputs[k])
    nt.links.new(cb.outputs[0], pr.inputs["Base Color"])


floor_seams()
''', 1)

# lifted stone: contour planes may tilt toward the camera, so the lines wander with depth and show relief
s = s.replace('def lifted_stone(name, base=0.36, pitch=1.0):', 'def lifted_stone(name, base=0.36, pitch=1.0, axis=(0, 0, 1), low=0.22):')
s = s.replace('''    geo, sepz = nt.nodes.new("ShaderNodeNewGeometry"), nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sepz.inputs[0])
    dv = nt.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = pitch
    nt.links.new(sepz.outputs["Z"], dv.inputs[0])
''', '''    geo = nt.nodes.new("ShaderNodeNewGeometry")
    dt = nt.nodes.new("ShaderNodeVectorMath"); dt.operation = "DOT_PRODUCT"
    nt.links.new(geo.outputs["Position"], dt.inputs[0])
    dt.inputs[1].default_value = tuple(Vector(axis).normalized())
    dv = nt.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = pitch
    nt.links.new(dt.outputs["Value"], dv.inputs[0])
''')
s = s.replace('''gr.inputs["To Min"].default_value, gr.inputs["To Max"].default_value = 0.22, 1.0
    nt.links.new(tri.outputs[0], gr.inputs["Value"])
    mu = nt.nodes.new("ShaderNodeMixRGB"); mu.blend_type = "MULTIPLY"; mu.inputs[0].default_value = 1.0
    mu.inputs[1].default_value = (base, base, base, 1)''', '''gr.inputs["To Min"].default_value, gr.inputs["To Max"].default_value = low, 1.0
    nt.links.new(tri.outputs[0], gr.inputs["Value"])
    mu = nt.nodes.new("ShaderNodeMixRGB"); mu.blend_type = "MULTIPLY"; mu.inputs[0].default_value = 1.0
    mu.inputs[1].default_value = (base, base, base, 1)''')

# T1: black hall, the numeral is the brightest thing on the floor
s = s.replace('ld.energy, ld.color = 900000, B', 'ld.energy, ld.color = 150000, B')
s = s.replace('spot((-6, 16, 116), (-4, 16, 70), R, 6e6, 34, 0.7, 2.0)', 'spot((-16, 16, 116), (-16, 16, 74), R, 4e6, 22, 0.7, 2.0)')
s = s.replace('spot((-130, -40, 104), (-30, 4, 58), R, 14e6, 15, 0.9, 2.0)', 'spot((-130, -40, 104), (-30, 4, 58), R, 7e6, 13, 0.9, 2.0)')
s = s.replace('haze(0.0024, 0.9, 12)\n    d = os.path.join(V3', 'haze(0.0016, 0.6, 12)\n    d = os.path.join(V3')
s = s.replace('e.inputs["Strength"].default_value = 3.0\n    nt.links.new(tx.outputs["Alpha"]', 'e.inputs["Strength"].default_value = 5.0\n    nt.links.new(tx.outputs["Alpha"]')

# T2: wall spill stronger, wall foot lower, figures in front of it, a cold pool for them
s = s.replace('x0, x1, z0, z1, y = -86, 86, 5, 73, 78', 'x0, x1, z0, z1, y = -86, 86, 5, 73, 78')
s = s.replace('wall(x0, x1, z0, z1, y, 1.0, os.path.join(WORK, "T2wall.png")', 'wall(x0, x1, z0, z1, y, 2.2, os.path.join(WORK, "T2wall.png")')
s = s.replace('for x, yy in ((-26, 22), (-22.5, 21.4), (31, 18), (58, 14), (-61, 12)):\n        person(x, yy, 1.75)', '''for x, yy in ((-26, -66), (-23.2, -66.6), (9, -74), (31, -58), (47, -70), (-52, -62)):
        person(x, yy, 1.75)
    spot((-20, -30, 110), (-2, -66, 0), R, 8e6, 13, 0.7, 1.0)''')

# T5: pocket dark stone with tilted contour lines, white key, teal only as raking edge
s = s.replace('m = lifted_stone("pocket", 0.30, 1.0)', 'm = lifted_stone("pocket", 0.13, 0.8, axis=(0.15, -0.72, 0.68), low=0.55)')
a = s.index('    # white pins on the key, R fader'); b = s.index('    # beams only outside the wall, so the number stays clean')
s = s[:a] + '''    # white on the key and the pocket together, from high left, so the walls cast real shadows, R fader
    c0 = L.mean(0)
    spot((c0[0] - 44, -126, 86), tuple(c0 + np.array([0, 0, 1.0])), R, 13e6, 9.5, 0.5, 0.6)
    # teal rakes the pocket walls from the right, low, G fader
    spot((c0[0] + 74, c0[1] - 14, c0[2] + 8), tuple(c0), G, 1.8e6, 16, 0.5, 1.0)
    spot((c0[0] - 60, c0[1] - 20, c0[2] - 16), tuple(c0), G, 0.5e6, 14, 0.5, 1.0)
''' + s[b:]
s = s.replace('origin = np.array([18.0, -48.0, 13.0])', 'origin = np.array([18.0, -48.0, 12.4])')
s = s.replace('BONE = mat("bone", 0.9, 0.42, 0.3)', 'BONE = mat("bone", 0.92, 0.42, 0.3)')

# T6: the hall behind, sea-green only on the columns and the far seats on the lit side
s = s.replace('    person(c[0] - 2.2, c[1] - 7.5, 1.75)\n    META["stops"]', '''    person(c[0] - 2.2, c[1] - 7.5, 1.75)
    for x, yy in ((at(ts[1])[0] + 11, at(ts[1])[1] - 7), (at(ts[2])[0] - 10, at(ts[2])[1] + 8), (at(ts[2])[0] - 13, at(ts[2])[1] + 7.2)):
        person(x, yy, 1.75)
    for x in (-210, -170, -130, -90, -50, -10):
        spot((x * 0.8, 40, 94), (x, 168, 16), G, 7e6, 10, 0.5, 1.0)
    META["stops"]''')
open(p, 'w', encoding='utf8').write(s)

p = 'D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/arena/code/bust.py'
s = open(p, encoding='utf8').read()
s = s.replace('E(0, .012, 1.37, .066, .070, .13, 3.5)', 'E(0, .012, 1.42, .070, .074, .10, 3.5)')
s = s.replace('E(0, .03, 1.265, .15, .082, .070, 3)', 'E(0, .03, 1.345, .155, .085, .065, 3)')
s = s.replace('E(0, .03, 1.10, .225, .125, .18, 2.5)', 'E(0, .03, 1.18, .225, .125, .18, 2.5)')
s = s.replace('E(.245, .03, 1.165, .080, .085, .090, 3); E(-.245, .03, 1.165, .080, .085, .090, 3)', 'E(.245, .03, 1.245, .080, .085, .090, 3); E(-.245, .03, 1.245, .080, .085, .090, 3)')
s = s.replace('E(.285, .03, .94, .066, .074, .22, 3); E(-.285, .03, .94, .066, .074, .22, 3)', 'E(.285, .03, 1.02, .066, .074, .22, 3); E(-.285, .03, 1.02, .066, .074, .22, 3)')
s = s.replace('E(0, .04, .82, .215, .13, .24, 2.5)', 'E(0, .04, .90, .215, .13, .24, 2.5)')
s = s.replace('solid((.62, .50, .38))', 'solid((.30, .23, .17))')
s = s.replace('location=(1.15, 1.58, 1.55)', 'location=(1.75, 1.58, 1.55)')
s = s.replace('cd.dof.focus_distance, cd.dof.aperture_fstop = True, 2.3, 1.6', 'cd.dof.focus_distance, cd.dof.aperture_fstop = True, 2.36, 2.8')
s = s.replace('((-1.6, -2.2, 2.0), 90, 1.8, (1, .86, .70))', '((-1.5, -2.0, 2.0), 70, 1.2, (1, .86, .70))')
s = s.replace('((1.8, -1.0, 1.3), 18, 1.0, (1, .62, .36))', '((1.8, -0.6, 1.5), 16, 0.8, (1, .62, .36))')
open(p, 'w', encoding='utf8').write(s)

p = 'D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/arena/code/make_led.py'
s = open(p, encoding='utf8').read()
s = s.replace('crop_h = 590', 'crop_h = 640').replace('cx, top = 500, 175', 'cx, top = 500, 165')
s = s.replace('* np.array([1.20, 0.95, 0.70]) * 0.9', '* np.array([1.20, 0.95, 0.70]) * 1.5')
open(p, 'w', encoding='utf8').write(s)

p = 'D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/arena/code/grade.py'
s = open(p, encoding='utf8').read()
s = s.replace('    tile /= tile.mean()\n', '    tile = 0.5 + 0.5 * tile / tile.mean()    # the dark gaps stay part lit, as on a real wall seen through haze, so a player scaling the picture finds little to beat against\n    tile /= tile.mean()\n')
s = s.replace('img = img * (1 - m) + (led_grid(pic, 3) + beams) * m', 'img = img * (1 - m) + (led_grid(pic, PITCH[shot]) + beams) * m')
s = s.replace('DESK = {\n', 'PITCH = {"T2": 3, "T5": 4}     # px at 1080p, doubled at 4K, always whole pixels\nDESK = {\n')
s = s.replace('"T1": (("C9CFD6", 0.6), ("C4122A", 1.2), ("E3172D", 0.55), 1.0, 0.10)', '"T1": (("C9CFD6", 0.6), ("C4122A", 1.2), ("E3172D", 0.8), 1.0, 0.07)')
s = s.replace('"T2": (("7F6BFF", 0.9), ("3D3BE8", 1.0), ("FFB27A", 0.5), 1.0, 0.08)', '"T2": (("7F6BFF", 0.9), ("9A3FD0", 1.0), ("FFB27A", 0.8), 1.0, 0.08)')
s = s.replace('"T6": (("3BC9A5", 0.8), ("3BC9A5", 0.8), ("FFC85A", 1.0), 1.0, 0.09)', '"T6": (("3BC9A5", 1.5), ("3BC9A5", 1.0), ("FFC85A", 1.0), 1.0, 0.09)')
open(p, 'w', encoding='utf8').write(s)

p = 'D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/art/arena/layers.jsx'
s = open(p, encoding='utf8').read()
s = s.replace('<T x={1168} y={640} size={40} {...anchor}>10 cm</T>', '<T x={1130} y={688} size={40} {...anchor}>10 cm</T>')
a = s.index('export const Layers = {')
s = s[:a] + '''// T6: labels over the gates, frame px from the T6 anchors. Dark stations stay readable but step back.
const stops = [[165, 604], [475, 522], [785, 442], [1085, 365], [1370, 292], [1640, 225]];
const stn = ["Target", "Hit", "Improve", "Cells & animals", "Clinical trials 1-2-3", "Approval"];
const T6over = () => <Fill>
  {stn.map((n, i) => <div key={n} style={{position: "absolute", left: stops[i][0] - 260 + (i === 0 ? 70 : i === 5 ? -50 : 0), top: stops[i][1] - (i > 2 ? 112 : 66), width: 520, textAlign: "center", fontFamily: BAR}}>
    <div style={{fontSize: 46, fontWeight: 600, color: i < 3 ? "#FFF6E4" : "#CFD3D8", lineHeight: 1.1, textShadow: anchor.shadow}}>{n}</div>
    {i > 2 ? <div style={{fontSize: 36, fontWeight: 500, color: "#AEB4BA", lineHeight: 1.15}}>not reported</div> : null}
  </div>)}
  <T x={1002} y={524} size={66} font={BIG} weight={800} color="#FFF6E4" {...anchor}>048</T>
</Fill>;

// colour script type: section, running time, the two lamps
const cs = [["S1", "2:21", 141, "#E3172D", "#C9CFD6"], ["S2", "2:22", 142, "#7F6BFF", "#9A3FD0"], ["S3", "2:09", 129, "#1F2BFF", "#C8D4FF"], ["S4", "3:33", 213, "#1E6BFF", "#DCF3FF"],
  ["S5", "2:19", 139, "#00C4AE", "#F2FFFB"], ["S6", "2:31", 151, "#3BC9A5", "#FFC85A"], ["S7", "0:49", 49, "#FFC85A", "#FF9E3D"], ["S8", "1:39", 99, "#FF9E3D", "#FFE3C2"]];
const CS = () => { let x = 0; const tot = cs.reduce((a, c) => a + c[2], 0); return <Fill>
  {cs.map(([s, t, d, a, b]) => { const w = d / tot * 1920; const el = <div key={s} style={{position: "absolute", left: x, top: 396, width: w, height: 84, borderLeft: x ? "1px solid #3a3a3a" : "none", boxSizing: "border-box", padding: "8px 0 0 10px", color: ink, fontFamily: BAR, background: "#0A0A0B"}}>
    <div style={{fontSize: 26, fontWeight: 600, lineHeight: 1}}>{s}{w > 70 ? <span style={{fontWeight: 500, color: "#AEB4BA"}}> {t}</span> : null}</div>
    <div style={{display: "flex", marginTop: 10}}><div style={{width: 30, height: 26, background: a}} /><div style={{width: 30, height: 26, background: b}} /></div>
  </div>; x += w; return el; })}
</Fill>; };

''' + s[a:]
s = s.replace('  T5over: {w: 1920, h: 1080, C: T5over},\n', '  T5over: {w: 1920, h: 1080, C: T5over},\n  T6over: {w: 1920, h: 1080, C: T6over},\n  CS: {w: 1920, h: 480, C: CS},\n')
open(p, 'w', encoding='utf8').write(s)
print('ok')
