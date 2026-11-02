"""HKBU SCIE1007 coursework science video. S1 insert shots: makes entry_cut.jsx, a copy of entry.jsx with one more composition. It plays the current seconds 25-52 and hard-cuts to each insert, with the drug's name set on the insert. Run: python patch_entry.py"""
A = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/"
s = open(A + "entry.jsx", encoding="utf8").read()
tail = '  <Composition id="S3Board"'
assert tail in s
comp = '''const SHOTS = [["a", 33.0, 35.3], ["b", 35.3, 37.9], ["c", 44.4, 47.4]];
const Cut = ({base = "fusion_s1/before_25_52.mp4"}) => {
  const f = useCurrentFrame(), t = 25 + f / 60, on = SHOTS.find(([, a, b]) => t >= a && t < b);
  return <Clock.Provider value={t}><Zoom.Provider value={1}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(base)} muted/>
    {SHOTS.map(([k, a, b]) => <Sequence key={k} from={Math.round((a - 25) * 60)} durationInFrames={Math.round((b - a) * 60)} layout="none">
      <AbsoluteFill><OffthreadVideo src={staticFile(`fusion_s1/insert_${k}.mp4`)} muted/></AbsoluteFill>
    </Sequence>)}
    {on && <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      {on[0] === "a" && <Ink x={96} y={250} size={92} at={33.25} font={SERIF} w={460} dur={0.6}>Nexavar</Ink>}
      {on[0] === "b" && <g>
        <Ink x={96} y={250} size={84} at={35.55} font={SERIF} w={560} dur={0.6}>atezolizumab</Ink>
        <Ink x={96} y={340} size={84} at={35.85} font={SERIF} w={620} dur={0.6}>+ bevacizumab</Ink>
      </g>}
      <Tag kind="schematic" x={1610} y={1062} at={on[1] - 1}>schematic</Tag>
      <Source x={96} y={1062} at={on[1] - 1}>Ren 2023 · HKCaR 2022</Source>
    </svg>}
    {on && <Review/>}
  </AbsoluteFill></Zoom.Provider></Clock.Provider>;
};

'''
i = s.rindex(chr(10) + "const ", 0, s.index(tail)) + 1
s = s[:i] + comp + s[i:]
s = s.replace(tail, '  <Composition id="Cut" component={Cut} durationInFrames={1620} fps={60} width={W} height={H}/>\n' + tail, 1)
open(A + "entry_cut.jsx", "w", encoding="utf8").write(s)
print("ok")
