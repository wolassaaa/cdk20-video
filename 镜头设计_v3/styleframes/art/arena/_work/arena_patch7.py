p = 'D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/arena/code/scene.py'
s = open(p, encoding='utf8').read()
# T5: floor catches the number; thin razors only in the margins and above the wall
s = s.replace('wall(wx0, wx1, wz0, wz1, wy, 1.0, os.path.join(WORK, "T5wall.png")', 'wall(wx0, wx1, wz0, wz1, wy, 2.4, os.path.join(WORK, "T5wall.png")')
a = s.index('    # beams only outside the wall, so the number stays clean'); b = s.index('    person(c0[0] - 9, c0[1] + 5, 1.75)')
s = s[:a] + '''    # beams only in the margins and over the top of the wall, so the number stays clean
    for x, tx in ((-96, -92), (-101, -110), (96, 92), (101, 112)):
        spot((x, 58, 96), (tx, 30, 0), G, 7e6, 0.9, 0.2)
    spot((-150, 50, 86), (150, 50, 81), G, 16e6, 0.7, 0.2)
    spot((150, 46, 90), (-150, 46, 79), G, 12e6, 0.7, 0.2)
''' + s[b:]
open(p, 'w', encoding='utf8').write(s)

p = 'D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/arena/code/grade.py'
s = open(p, encoding='utf8').read()
s = s.replace('("FFB27A", 0.8), 1.0, 0.08)', '("FFB27A", 0.4), 1.0, 0.08)')
s = s.replace('"T5": (("F2FFFB", 1.0), ("00C4AE", 1.0), ("7FF5DC", 0.5), 1.0, 0.09)', '"T5": (("F2FFFB", 1.0), ("00C4AE", 1.0), ("7FF5DC", 0.7), 1.0, 0.09)')
s = s.replace('"T6": (("3BC9A5", 1.5), ("3BC9A5", 1.0), ("FFC85A", 1.0), 1.0, 0.09)', '"T6": (("3BC9A5", 1.5), ("3BC9A5", 0.35), ("FFC85A", 1.0), 1.0, 0.09)')
open(p, 'w', encoding='utf8').write(s)

p = 'D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/art/arena/layers.jsx'
s = open(p, encoding='utf8').read()
s = s.replace('top: stops[i][1] - (i > 2 ? 112 : 66)', 'top: stops[i][1] - (i > 2 ? 112 : i === 0 ? 66 : 82)')
open(p, 'w', encoding='utf8').write(s)

for name in ('batch.sh', 'gpu_set.sh'):
    p = 'D:/。hkbu/molecular science/镜头设计_v3/styleframes/art/arena/code/' + name
    s = open(p, encoding='utf8').read()
    s = s.replace('${TAG:-_p}', '${TAG-_p}').replace('TAG=${TAG-_p} bash', 'TAG=${TAG-_p} bash')
    s = s.replace('python sheet.py', 'python sheet.py $SHEET')
    open(p, 'w', encoding='utf8').write(s)
print('ok')
