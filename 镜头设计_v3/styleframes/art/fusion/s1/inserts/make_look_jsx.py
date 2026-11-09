"""HKBU SCIE1007 coursework science video. Look test on shot k: makes look.jsx, a copy of entry.jsx whose Root holds only LookK, the words of the S3 lock-and-key clip
(as patch_s3.py's S3K) over a new take, from 287.0 to 312.0 s at 30 fps. The white tick and cross badges are gone: a red pen draws a tick and a cross instead, stroke by
stroke, like the Caveat notes. entry.jsx is read, never changed. Run: python make_look_jsx.py"""
import os

A = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/"
s = open(A + "entry.jsx", encoding="utf8").read()
root = "const Root = () => <>"
assert s.count(root) == 1
s = s[:s.index(root)]
s += r'''/** A pen mark, tick or cross, drawn in strokes at writing speed, slightly tilted like the notes. size is its height in px. */
const PenMark = ({x, y, at, yes, size = 84, fill = RED, rot = -4}) => {
  const t = useT(), k = size / 2;
  const strokes = yes ? [[`M${-0.46 * k} ${-0.04 * k} Q${-0.3 * k} ${0.12 * k} ${-0.13 * k} ${0.44 * k} Q${0.1 * k} ${-0.1 * k} ${0.62 * k} ${-0.56 * k}`, 0.0, 0.34]]
    : [[`M${-0.42 * k} ${-0.46 * k} Q${0.02 * k} ${-0.06 * k} ${0.44 * k} ${0.46 * k}`, 0.0, 0.2], [`M${0.4 * k} ${-0.48 * k} Q${-0.06 * k} ${0.02 * k} ${-0.4 * k} ${0.44 * k}`, 0.28, 0.2]];
  if (t < at) return null;
  return <g transform={`translate(${x} ${y}) rotate(${rot})`}>
    {strokes.map(([d, a, dur], i) => {
      const p = smooth((t - at - a) / dur);
      return p > 0 ? <path key={i} d={d} pathLength={1} strokeDasharray={`${p} 1`} fill="none" stroke={fill} strokeWidth={size * 0.072} strokeLinecap="round" strokeLinejoin="round"/> : null;
    })}
  </g>;
};
const LookK = ({file, tick = [640, 556], cross = [1812, 508], lead = [[1812, 466], [1812, 272]]}) => {
  const f = useCurrentFrame(), t = 287 + f / 30;
  const labels = 1 - after(t, 305.15, 0.3) + after(t, 309.4, 0.4);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g transform={`translate(${-752 * smooth(t - 287)} 0)`}>
        {t < 288 && <Print who="D" x={72} y={168} w={620} h={744} at={283.1} rot={-1.0}/>}
      </g>
      <g opacity={1 - after(t, 291.0, 0.25)}><Ink x={96} y={250} size={92} at={288.9} font={SERIF} w={500} dur={0.5}>protein</Ink></g>
      <g opacity={1 - after(t, 296.9, 0.3)}><Ink x={96} y={250} size={92} at={291.4} font={SERIF} w={500} dur={0.5}>drug</Ink></g>
      <g opacity={t > 299 ? labels : 0}>
        <Leader pts={[[640, 330], [640, 150], [700, 150]]} at={299.9} fill={KLEIN} onColour/>
        <Note x={710} y={165} size={58} at={300.3} fill={KLEIN}>target (a protein)</Note>
        <Leader pts={[[130, 610], [130, 900], [190, 900]]} at={301.5} fill={DARK} onColour/>
        <Note x={200} y={915} size={58} at={301.9} fill={DARK}>candidate (a small molecule)</Note>
        <PenMark x={tick[0]} y={tick[1]} at={304.2} size={130} yes/>
      </g>
      <PenMark x={cross[0]} y={cross[1]} at={309.5} size={100}/>
      {t > 309.5 && <Leader pts={lead} at={309.6} onColour/>}
      <Keyed x={1490} y={240} size={92} at={310.0} dur={0.6} w={420} parts={["", "selectivity"]}/>
      <Source x={96} y={1062} at={286.6}>Illustration · Lengauer 2007</Source>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

const Root = () => <>
  <Composition id="LookK" component={LookK} durationInFrames={750} fps={30} width={W} height={H} defaultProps={{file: "fusion_s1/look_take.mp4"}}/>
</>;
registerRoot(Root);
'''
open(A + "look.jsx", "w", encoding="utf8").write(s)
print("LOOK_JSX_OK")
