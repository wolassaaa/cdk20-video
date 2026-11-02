"""HKBU SCIE1007 coursework science video. Matter test: makes entry_matter.jsx, a copy of entry.jsx with one more composition that lays the type over the TouchDesigner picture. The type follows the 3D spots poses.py projects to the screen. Run: python patch_entry.py"""
A = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/"
s = open(A + "entry.jsx", encoding="utf8").read()
head = 'import {registerRoot, Composition,'
assert head in s
s = s.replace(head, 'import MK from "./matter_marks.json";\n' + head, 1)
tail = '  <Composition id="S3Board"'
assert tail in s
comp = '''const Matter = ({file = "fusion_s1/matter_1.mp4"}) => {
  const f = useCurrentFrame(), t = 25 + f / 60, spot = (k) => MK[k][Math.min(f, MK[k].length - 1)];
  const [nx, ny, nk] = spot("nexavar"), [cx, cy, ck] = spot("combo"), [tx, ty, tk] = spot("three");
  return <Clock.Provider value={t}><Zoom.Provider value={1}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={after(t, 33.2) * (1 - after(t, 35.2, 0.6))}><text x={nx} y={ny} textAnchor="middle" fontFamily={SERIF} fontSize={88 * nk} fill={INK}>Nexavar</text></g>
      <g opacity={after(t, 36.4) * (1 - after(t, 40.6, 0.6))}>
        <text x={cx} y={cy} fontFamily={SERIF} fontSize={70 * ck} fill={INK}>atezolizumab</text>
        <text x={cx} y={cy + 72 * ck} fontFamily={SERIF} fontSize={70 * ck} fill={INK}>+ bevacizumab</text>
        <text x={cx} y={cy + 128 * ck} fontFamily={SANS} fontWeight={500} fontSize={36 * ck} fill={SOFT} opacity={after(t, 37.2)}>first-line, advanced HCC</text>
      </g>
      <g opacity={after(t, 46.2)}>
        <text x={tx} y={ty} fontFamily={SERIF} fontSize={150 * tk * 1.6} fill={RED}>~3 in 10</text>
        <text x={tx} y={ty + 70 * tk * 1.6} fontFamily={SANS} fontWeight={600} fontSize={44 * tk * 1.6} fill={INK} opacity={after(t, 46.8)}>5-year relative survival</text>
        <text x={tx} y={ty + 116 * tk * 1.6} fontFamily={SANS} fontWeight={500} fontSize={34 * tk * 1.6} fill={SOFT} opacity={after(t, 46.8)}>HK, 2010-2021</text>
      </g>
      <Tag kind="schematic" x={1640} y={70} at={33.2}>schematic</Tag>
      <Source x={96} y={1036} at={33.2}>Ren 2023 · HKCaR 2022 · liver: BodyParts3D, DBCLS, CC BY 4.0</Source>
    </svg>
  </AbsoluteFill></Zoom.Provider></Clock.Provider>;
};

'''
i = s.rindex(chr(10) + "const ", 0, s.index(tail)) + 1
s = s[:i] + comp + s[i:]
s = s.replace(tail, '  <Composition id="Matter" component={Matter} durationInFrames={1620} fps={60} width={W} height={H}/>\n' + tail, 1)
open(A + "entry_matter.jsx", "w", encoding="utf8").write(s)
print("ok")
