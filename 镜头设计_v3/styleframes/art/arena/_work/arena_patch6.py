p = 'D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/arena/code/scene.py'
s = open(p, encoding='utf8').read()

# a light that lights surfaces but leaves no shaft in the haze
s = s.replace('def fan(pos, tgt, ch, power, n, spread', '''def quiet(ob):
    ob.visible_volume_scatter = False
    return ob


def fan(pos, tgt, ch, power, n, spread''')

# T1
s = s.replace('spot((-16, 16, 116), (-16, 16, 74), R, 4e6, 22, 0.7, 2.0)', 'quiet(spot((-16, 16, 116), (-16, 16, 74), R, 4e6, 22, 0.7, 2.0))')

# T2
s = s.replace('''for x, yy in ((-26, -66), (-23.2, -66.6), (9, -74), (31, -58), (47, -70), (-52, -62)):
        person(x, yy, 1.75)
    spot((-20, -30, 110), (-2, -66, 0), R, 8e6, 13, 0.7, 1.0)''', '''for x, yy in ((-30.2, -66), (-27.6, -66.6), (9, -74), (21, -58), (13.4, -60)):
        person(x, yy, 1.75)
    spot((-29, -66, 112), (-29, -66, 0), R, 5e6, 3.6, 0.6, 0.6)''')

# T5
s = s.replace('m = lifted_stone("pocket", 0.13, 0.8, axis=(0.15, -0.72, 0.68), low=0.55)', 'm = lifted_stone("pocket", 0.075, 0.8, axis=(0.15, -0.72, 0.68), low=0.45)')
a = s.index('    # white on the key and the pocket together'); b = s.index('    # beams only outside the wall, so the number stays clean')
s = s[:a] + '''    # white on the key and the pocket together, from high left, so the walls cast real shadows. No shaft: nothing may cross the number. R fader
    c0 = L.mean(0)
    quiet(spot((c0[0] - 44, -126, 86), tuple(c0 + np.array([0, 0, 1.0])), R, 9e6, 9.5, 0.5, 0.6))
    # teal rakes the pocket walls from the right, low, G fader
    quiet(spot((c0[0] + 74, c0[1] - 14, c0[2] + 8), tuple(c0), G, 3.2e6, 16, 0.5, 1.0))
    quiet(spot((c0[0] - 60, c0[1] - 20, c0[2] - 16), tuple(c0), G, 0.9e6, 14, 0.5, 1.0))
''' + s[b:]

# T6
s = s.replace('''    for x in (-210, -170, -130, -90, -50, -10):
        spot((x * 0.8, 40, 94), (x, 168, 16), G, 7e6, 10, 0.5, 1.0)
''', '''    for x, y2 in ((-190, 140), (-90, 160)):
        quiet(spot((x, 20, 90), (x, y2, 12), G, 12e6, 34, 0.9, 2.0))
''')
open(p, 'w', encoding='utf8').write(s)

p = 'D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/arena/code/make_led.py'
s = open(p, encoding='utf8').read()
s = s.replace('* np.array([1.20, 0.95, 0.70]) * 1.5', '* np.array([1.25, 0.86, 0.56]) * 0.95')
open(p, 'w', encoding='utf8').write(s)

p = 'D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/art/arena/layers.jsx'
s = open(p, encoding='utf8').read()
s = s.replace('left: stops[i][0] - 260 + (i === 0 ? 70 : i === 5 ? -50 : 0)', 'left: stops[i][0] - 260 + (i === 0 ? 70 : i === 4 ? -44 : i === 5 ? 14 : 0)')
open(p, 'w', encoding='utf8').write(s)
print('ok')
