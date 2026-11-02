"""HKBU SCIE1007 coursework science video. S1 and S2 table shots: makes entry_cut.jsx, a copy of entry.jsx with one more composition, the film with its takes laid over it and the torn strip patched into the full view. The takes start and end on the full view's own frame, so only the words fade. Run: python patch_entry.py"""
A = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/"
s = open(A + "entry.jsx", encoding="utf8").read()
tail = '  <Composition id="S3Board"'
assert tail in s
a = s.index("const S1 = (")
b = s.index("\n};\n", a) + 4
one = s[a:b].replace("const S1 = (", "const Cut = (")
for old, new in (
    ('      <svg width={W} height={H}', '''      {t >= 38.4 && t < 52.2 && <Img src={staticFile("fusion_s1/patch_top.png")} style={{position: "absolute", left: 3840 - cx + W / 2, top: 0, width: W, height: H}}/>}
      {UNDER.filter(([, p, q]) => f >= p && f < q).map(([k, p, q]) => <Take key={k} k={k} a={p} b={q} f={f}/>)}
      <svg width={W} height={H}'''),
    ("<Road/>", "<g opacity={gone(t, 78.9, 93.3)}><Road/></g>"),
    ("<Pin xy={TL.world.pwh} at={119.8}>Sha Tin</Pin>", "<g opacity={gone(t, 146.0, 152.4)}><Pin xy={TL.world.pwh} at={119.8}>Sha Tin</Pin></g>"),
    ("<Pin xy={TL.world.hkstp} at={122.0}>Pak Shek Kok</Pin>", "<g opacity={gone(t, 146.0, 152.4)}><Pin xy={TL.world.hkstp} at={122.0}>Pak Shek Kok</Pin></g>"),
    ("      {review && <Review/>}", "      <Takes f={f}/>\n      {review && <Review/>}"),
):
    assert one.count(old) == 1, old
    one = one.replace(old, new)
comp = '''const OVER = [["p", 1926, 2327], ["c", 2601, 2911], ["h", 13470, 14124]];   // film frames; these cover the type
const UNDER = [["f", 4728, 5688], ["g", 8760, 9174]];                        // these sit under the type
const gone = (t, a, b) => 1 - after(t, a, 0.3) + after(t, b, 0.4);           // 1 outside a to b
const WORDS = [[80.7, "Target"], [81.9, "Hit"], [84.3, "Improve"], [85.6, "Cells & animals"], [88.1, "Clinical trials 1-2-3"], [91.6, "Approval"]];
const Take = ({k, a, b, f}) => <Sequence from={a} durationInFrames={b - a} layout="none">
  <AbsoluteFill style={{opacity: smooth(Math.min(clamp((f - a) / 12), clamp((b - 1 - f) / 15)))}}><OffthreadVideo src={staticFile(`fusion_s1/take_${k}.mp4`)} muted/></AbsoluteFill>
</Sequence>;
const Takes = ({f}) => {
  const t = useT(), on = OVER.find(([, a, b]) => f >= a && f < b), k = on ? on[0] : "";
  return <>
    {on && <Take k={k} a={on[1]} b={on[2]} f={f}/>}
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
      {(k === "p" || k === "c") && <Source x={96} y={1062} at={33.0}>Illustration · Ren 2023 · HKCaR 2022</Source>}
      {t > 80 && t < 93 && WORDS.map(([at, word], i) => <g key={i} opacity={1 - after(t, i < 5 ? WORDS[i + 1][0] - 0.2 : 92.2, 0.2)}><Ink x={96} y={250} size={92} at={at} font={SERIF} w={900} dur={0.5}>{word}</Ink></g>)}
    </svg>
  </>;
};

'''
s = s[:a] + comp + one + s[a:]
s = s.replace(tail, '  <Composition id="Cut" component={Cut} durationInFrames={N} fps={FPS} width={W} height={H} defaultProps={{file: "fusion_s1/clip_1_0_141.mp4"}}/>\n' + tail, 1)
s = s.replace("AbsoluteFill, OffthreadVideo,", "AbsoluteFill, Img, OffthreadVideo,", 1)
open(A + "entry_cut.jsx", "w", encoding="utf8").write(s)
print("ok")
