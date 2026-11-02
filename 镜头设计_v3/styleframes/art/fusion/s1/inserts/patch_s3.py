"""HKBU SCIE1007 coursework science video. S3 review clips: makes entry_s3.jsx, a copy of entry.jsx with one more composition, the lock and key take with the print, the words and the marks over it. Everything sits at screen positions over the take, because the take holds on its full views while the words come. Run: python patch_s3.py"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__)).replace(chr(92), "/")
TRACK = json.load(open(HERE + "/frames/p_track.json"))
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
      <Mark x={1812} y={508} at={309.5}/>
      {t > 309.5 && <Leader pts={[[1812, 466], [1812, 272]]} at={309.6} onColour/>}
      <Keyed x={1490} y={240} size={92} at={310.0} dur={0.6} w={420} parts={["", "selectivity"]}/>
      <Source x={96} y={1062} at={286.6}>Illustration · Lengauer 2007</Source>
    </svg>
    {review && l && <div style={{position: "absolute", left: 120, right: 120, top: 22, textAlign: "center", fontFamily: SANS, fontWeight: 500, fontSize: 24, lineHeight: 1.3, color: SOFT}}><b style={{color: INK}}>{l[2]}</b>  {l[3]}</div>}
  </AbsoluteFill></Clock.Provider>;
};

const L_LINES = [
  [310, 312, "D", "...That's called selectivity."],
  [312, 330, "D", "Our lock is CDK20. It's an enzyme, a protein with a chemical job. Its keyhole is a pocket where it normally grabs a small molecule called ATP. Plug that pocket with the right key, and the enzyme can't do its job."],
];
const TRACK = %TRACK%;
const pocketAt = t => {     // where the pocket's mouth is on screen; the track holds one point per tenth of a second from 313.2 s
  const u = Math.max(0, (t - 313.2) * 10), i = Math.min(Math.floor(u), TRACK.length - 2), k = Math.min(1, u - i);
  return [0, 1].map(j => TRACK[i][j] + (TRACK[i + 1][j] - TRACK[i][j]) * k);
};
const S3L = ({review = true, still = ""}) => {
  const f = useCurrentFrame(), t = 310 + f / 60, l = L_LINES.find(([a, b]) => t >= a && t < b);
  const [px, py] = pocketAt(t), ring = out((t - 318.6) / 0.7), R = 104;
  const line = [[px - R, py], [772, py]];
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile("fusion_s1/take_l.mp4")} muted/>
    <div style={{position: "absolute", left: 0, top: 0, width: W, height: H, opacity: after(t, 313.15, 0.15)}}><OffthreadVideo src={staticFile("fusion_s1/take_p.mp4")} muted/></div>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={1 - after(t, 312.0, 0.3)}>
        <Leader pts={[[640, 330], [640, 150], [700, 150]]} at={299.9} fill={KLEIN} onColour/>
        <Ink x={710} y={165} size={44} at={300.3} fill={KLEIN} weight={700} w={420}>target (a protein)</Ink>
        <Leader pts={[[130, 610], [130, 900], [190, 900]]} at={301.5} fill={DARK} onColour/>
        <Ink x={200} y={915} size={44} at={301.9} fill={DARK} weight={700} w={620}>candidate (a small molecule)</Ink>
        <Mark x={640} y={556} at={304.2} yes/>
        <Mark x={1812} y={508} at={309.5}/>
        <Leader pts={[[1812, 466], [1812, 272]]} at={309.6} onColour/>
        <Keyed x={1490} y={240} size={92} at={310.0} dur={0.6} w={420} parts={["", "selectivity"]}/>
        <Source x={96} y={1062} at={286.6}>Illustration · Lengauer 2007</Source>
      </g>
      <Keyed x={96} y={240} size={92} at={314.4} dur={0.6} w={760} parts={["Our lock is ", "CDK20"]}/>
      <g opacity={1 - after(t, 318.2, 0.3)}>
        <Ink x={96} y={350} size={58} at={315.8} font={SERIF} w={760}>an enzyme:</Ink>
        <Ink x={96} y={424} size={58} at={316.2} font={SERIF} w={760}>a protein with a chemical job</Ink>
      </g>
      {ring > 0 && <circle cx={px} cy={py} r={R} fill="none" stroke={BONE} strokeWidth={5} strokeDasharray={2 * Math.PI * R} strokeDashoffset={2 * Math.PI * R * (1 - ring)} transform={`rotate(180 ${px} ${py})`}/>}
      {t > 319.2 && <Leader pts={line} at={319.2} onColour/>}
      <Ink x={760} y={py + 15} size={44} at={319.5} fill={KLEIN} weight={700} anchor="end" w={420}>ATP pocket</Ink>
      <Ink x={760} y={py + 87} size={44} at={326.5} fill={DARK} weight={700} anchor="end" w={420}>the right key</Ink>
      <Ink x={760} y={py + 170} size={58} at={327.2} font={SERIF} anchor="end" w={500}>can't do its job</Ink>
      <Tag x={96} y={1000} at={315.2} size={36}>predicted model (AlphaFold DB v6)</Tag>
      <Source x={96} y={1062} at={315.2}>Illustration · Ren et al. 2023</Source>
    </svg>
    {review && l && <div style={{position: "absolute", left: 120, right: 120, top: 22, textAlign: "center", fontFamily: SANS, fontWeight: 500, fontSize: 24, lineHeight: 1.3, color: SOFT}}><b style={{color: INK}}>{l[2]}</b>  {l[3]}</div>}
  </AbsoluteFill></Clock.Provider>;
};

'''
comp = comp.replace("%TRACK%", json.dumps(TRACK))
s = s.replace(tail, comp + tail, 1)
head = '  <Composition id="S3Board"'
assert s.count(head) == 1
s = s.replace(head, '  <Composition id="S3K" component={S3K} durationInFrames={1740} fps={60} width={W} height={H}/>\n  <Composition id="S3L" component={S3L} durationInFrames={1200} fps={60} width={W} height={H}/>\n' + head, 1)
a = "AbsoluteFill, OffthreadVideo,"
assert s.count(a) == 1
s = s.replace(a, "AbsoluteFill, Img, OffthreadVideo,", 1)
open(A + "entry_s3.jsx", "w", encoding="utf8").write(s)
print("ok")
