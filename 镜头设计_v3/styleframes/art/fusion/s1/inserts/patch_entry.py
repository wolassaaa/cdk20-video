"""HKBU SCIE1007 coursework science video. S1 table shots: makes entry_cut.jsx, a copy of entry.jsx with one more composition, S1 itself with two takes laid over it and the torn strip patched into the full view. The takes start and end on the full view's own frame, so only the words fade. Run: python patch_entry.py"""
A = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/"
s = open(A + "entry.jsx", encoding="utf8").read()
tail = '  <Composition id="S3Board"'
assert tail in s
a = s.index("const S1 = (")
b = s.index("\n};\n", a) + 4
one = s[a:b].replace("const S1 = (", "const Cut = (")
one = one.replace('      <svg width={W} height={H}', '''      {t >= 38.4 && t < 52.2 && <Img src={staticFile("fusion_s1/patch_top.png")} style={{position: "absolute", left: 3840 - cx + W / 2, top: 0}}/>}
      <svg width={W} height={H}''', 1)
one = one.replace("      {review && <Review/>}", "      <Takes f={f}/>\n      {review && <Review/>}", 1)
comp = '''const TAKES = [["p", 1926, 2327], ["c", 2601, 2911]];   // film frames
const Takes = ({f}) => {
  const t = useT(), on = TAKES.find(([, a, b]) => f >= a && f < b);
  if (!on) return null;
  const [k, a, b] = on, seen = Math.min(clamp((f - a) / 12), clamp((b - 1 - f) / 15));
  return <>
    <Sequence from={a} durationInFrames={b - a} layout="none">
      <AbsoluteFill style={{opacity: smooth(seen)}}><OffthreadVideo src={staticFile(`fusion_s1/take_${k}.mp4`)} muted/></AbsoluteFill>
    </Sequence>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      {k === "p" && <g opacity={1 - after(t, 35.1, 0.14)}><Ink x={96} y={250} size={92} at={33.25} font={SERIF} w={460} dur={0.6}>Nexavar</Ink></g>}
      {k === "p" && <g opacity={1 - after(t, 37.5, 0.3)}>
        <Ink x={96} y={250} size={84} at={35.55} font={SERIF} w={560} dur={0.6}>atezolizumab</Ink>
        <Ink x={96} y={340} size={84} at={35.85} font={SERIF} w={620} dur={0.6}>+ bevacizumab</Ink>
      </g>}
      {k === "c" && <g opacity={1 - after(t, 47.25, 0.3)}>{/* top left, as in the other shots: the row never crosses it, and it leaves before the camera climbs */}
        <Ink x={96} y={300} size={170} at={46.2} font={SERIF} fill={RED} w={620} dur={0.6}>~3 in 10</Ink>
        <Ink x={660} y={250} size={46} at={46.5}>5-year relative survival</Ink>
        <Ink x={660} y={300} size={36} at={46.8} weight={500} fill={SOFT}>HK, 2010-2021</Ink>
      </g>}
      <Source x={96} y={1062} at={33.0}>Illustration · Ren 2023 · HKCaR 2022</Source>
    </svg>
  </>;
};

'''
s = s[:a] + comp + one + s[a:]
s = s.replace(tail, '  <Composition id="Cut" component={Cut} durationInFrames={N} fps={FPS} width={W} height={H} defaultProps={{file: "fusion_s1/clip_1_0_141.mp4"}}/>\n' + tail, 1)
s = s.replace("AbsoluteFill, OffthreadVideo,", "AbsoluteFill, Img, OffthreadVideo,", 1)
open(A + "entry_cut.jsx", "w", encoding="utf8").write(s)
print("ok")
