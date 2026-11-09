"""HKBU SCIE1007 coursework science video. Form test on shot k: makes form.jsx, a copy of entry.jsx whose Root holds only FormK, the words of the S3 lock-and-key
clip (as patch_s3.py's S3K: the same words, times, leaders and white tick and cross badges) over one of the fk1-fk3 takes, from 287.0 to 312.0 s at 30 fps.
The camera moves now, so every leader starts from, and every badge sits on, a point tracked through the 3D shot (bl_form.py, FORM_TRACK). entry.jsx is read, never
changed. Run: python make_form_jsx.py <track dir>"""
import json
import sys

A = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/"
D = sys.argv[1]
TRACKS = {v: json.load(open("%s/track_%s.json" % (D, v))) for v in ("fk1", "fk2", "fk3")}
s = open(A + "entry.jsx", encoding="utf8").read()
root = "const Root = () => <>"
assert s.count(root) == 1
s = s[:s.index(root)]
s += "const FORM_TRACKS = " + json.dumps(TRACKS, separators=(",", ":")) + ";\n"
s += r'''const FMark = ({x, y, at, yes}) => {
  const t = useT(), p = out((t - at) / 0.25);
  return p > 0 ? <g transform={`translate(${x} ${y}) scale(${0.7 + 0.3 * p})`} opacity={p}>
    <circle r={42} fill={BONE}/>
    {yes ? <polyline points="-20,2 -6,18 22,-20" fill="none" stroke={INK} strokeWidth={7}/> : <path d="M-20,-20L20,20M20,-20L-20,20" stroke={INK} strokeWidth={8}/>}
  </g> : null;
};
/** The S3K words over a moving take: leaders run from tracked points, up (or down) to a fixed height, then right to the note. */
const FormK = ({file, ver, words = [96, 250], targetY = 150, candY = 900}) => {
  const f = useCurrentFrame(), t = 287 + f / 30, T = FORM_TRACKS[ver];
  const at = k => T[k][Math.min(f, T[k].length - 1)];
  const labels = 1 - after(t, 305.15, 0.3) + after(t, 309.4, 0.4);
  const [lx, ly] = at("lock"), [bx, by] = at("bow"), [tx, ty] = at("tick"), [cx, cy] = at("cross");
  const sel = Math.min(cx - 322, 1920 - 450);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g transform={`translate(${-752 * smooth(t - 287)} 0)`}>
        {t < 288 && <Print who="D" x={72} y={168} w={620} h={744} at={283.1} rot={-1.0}/>}
      </g>
      <g opacity={1 - after(t, 291.0, 0.25)}><Ink x={words[0]} y={words[1]} size={92} at={288.9} font={SERIF} w={500} dur={0.5}>protein</Ink></g>
      <g opacity={1 - after(t, 296.9, 0.3)}><Ink x={words[0]} y={words[1]} size={92} at={291.4} font={SERIF} w={500} dur={0.5}>drug</Ink></g>
      <g opacity={t > 299 ? labels : 0}>
        <Leader pts={[[lx, ly], [lx, targetY], [lx + 60, targetY]]} at={299.9} fill={KLEIN} onColour/>
        <Note x={lx + 70} y={targetY + 15} size={58} at={300.3} fill={KLEIN}>target (a protein)</Note>
        <Leader pts={[[bx, by], [bx, candY], [bx + 60, candY]]} at={301.5} fill={DARK} onColour/>
        <Note x={bx + 70} y={candY + 15} size={58} at={301.9} fill={DARK}>candidate (a small molecule)</Note>
        <FMark x={tx} y={ty} at={304.2} yes/>
      </g>
      <FMark x={cx} y={cy} at={309.5}/>
      {t > 309.5 && <Leader pts={[[cx, cy - 42], [cx, 272]]} at={309.6} onColour/>}
      <Keyed x={sel} y={240} size={92} at={310.0} dur={0.6} w={420} parts={["", "selectivity"]}/>
      <Source x={96} y={1062} at={286.6}>Illustration · Lengauer 2007</Source>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

const Root = () => <>
  <Composition id="FormK" component={FormK} durationInFrames={750} fps={30} width={W} height={H} defaultProps={{file: "fusion_s1/form_take.mp4", ver: "fk1"}}/>
</>;
registerRoot(Root);
'''
open(A + "form.jsx", "w", encoding="utf8").write(s)
print("FORM_JSX_OK")
