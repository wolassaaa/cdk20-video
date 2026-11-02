"""HKBU SCIE1007 coursework science video. S3 review clips: makes entry_s3.jsx, a copy of entry.jsx with one more composition, the lock and key take with the print, the words and the marks over it. Everything sits at screen positions over the take, because the take holds on its full views while the words come. Run: python patch_s3.py"""
A = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/"
s = open(A + "entry.jsx", encoding="utf8").read()
tail = "const Root = () => <>"
assert s.count(tail) == 1
comp = '''const K_LINES = [
  [283, 287, "D · on camera", "Okay. To get this, picture a lock and a key."],
  [287, 299, "D", "Inside your cells, proteins do a lot of the work. Most drugs grab one protein tightly and change what it does, slotting into a pocket like a key into a lock."],
  [299, 312, "D", "Scientists call the lock the target, and the key a candidate molecule. A good key fits its own lock tightly, and opens no one else's. That's called selectivity."],
];
const Mark = ({x, y, at, yes}) => {
  const t = useT(), p = out((t - at) / 0.25);
  return p > 0 ? <g transform={`translate(${x} ${y}) scale(${0.7 + 0.3 * p})`} opacity={p}>
    <circle r={42} fill={BONE}/>
    {yes ? <polyline points="-20,2 -6,18 22,-20" fill="none" stroke={INK} strokeWidth={7}/> : <path d="M-20,-20L20,20M20,-20L-20,20" stroke={INK} strokeWidth={8}/>}
  </g> : null;
};
const S3K = ({review = true, still = ""}) => {
  const f = useCurrentFrame(), t = 283 + f / 60, l = K_LINES.find(([a, b]) => t >= a && t < b);
  const labels = 1 - after(t, 305.15, 0.3) + after(t, 309.4, 0.4);     // they leave before the camera falls to the second lock and come back when it has climbed
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    {still ? <Img src={staticFile(still)} style={{width: W, height: H}}/> : <OffthreadVideo src={staticFile("fusion_s1/take_k.mp4")} muted/>}
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g transform={`translate(${-752 * smooth(t - 287)} 0)`}>{/* the same slide as the camera's in the take */}
        {t < 288 && <Print who="D" x={72} y={168} w={620} h={744} at={283.1} rot={-1.0}/>}
      </g>
      <g opacity={1 - after(t, 291.0, 0.25)}><Ink x={96} y={250} size={92} at={288.9} font={SERIF} w={500} dur={0.5}>protein</Ink></g>
      <g opacity={1 - after(t, 296.9, 0.3)}><Ink x={96} y={250} size={92} at={291.4} font={SERIF} w={500} dur={0.5}>drug</Ink></g>
      <g opacity={t > 299 ? labels : 0}>
        <Leader pts={[[640, 330], [640, 150], [700, 150]]} at={299.9} fill={KLEIN} onColour/>
        <Ink x={710} y={165} size={44} at={300.3} fill={KLEIN} weight={700} w={420}>target (a protein)</Ink>
        <Leader pts={[[130, 610], [130, 900], [190, 900]]} at={301.5} fill={DARK} onColour/>
        <Ink x={200} y={915} size={44} at={301.9} fill={DARK} weight={700} w={620}>candidate (a small molecule)</Ink>
        <Mark x={640} y={556} at={304.2} yes/>
      </g>
      <Mark x={1438} y={556} at={309.5}/>
      {t > 309.5 && <Leader pts={[[1438, 512], [1438, 272]]} at={309.6} onColour/>}
      <Keyed x={1270} y={240} size={92} at={310.0} dur={0.6} w={420} parts={["", "selectivity"]}/>
      <Source x={96} y={1062} at={286.6}>Illustration · Lengauer 2007</Source>
    </svg>
    {review && l && <div style={{position: "absolute", left: 120, right: 120, top: 22, textAlign: "center", fontFamily: SANS, fontWeight: 500, fontSize: 24, lineHeight: 1.3, color: SOFT}}><b style={{color: INK}}>{l[2]}</b>  {l[3]}</div>}
  </AbsoluteFill></Clock.Provider>;
};

'''
s = s.replace(tail, comp + tail, 1)
head = '  <Composition id="S3Board"'
assert s.count(head) == 1
s = s.replace(head, '  <Composition id="S3K" component={S3K} durationInFrames={1740} fps={60} width={W} height={H}/>\n' + head, 1)
a = "AbsoluteFill, OffthreadVideo,"
assert s.count(a) == 1
s = s.replace(a, "AbsoluteFill, Img, OffthreadVideo,", 1)
open(A + "entry_s3.jsx", "w", encoding="utf8").write(s)
print("ok")
