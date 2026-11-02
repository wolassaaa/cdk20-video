"""HKBU SCIE1007 coursework science video. S3's third to fifth pieces, 330-412 s: makes entry_q.jsx, a copy of entry.jsx with one more composition, the take of shot q with the prints, the words and the dark over it. Everything sits at screen positions; words that sit on the table leave with the camera. Run: python patch_q.py"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__)).replace(chr(92), "/")
TRACK = json.load(open(HERE + "/frames/p_track.json"))
A = "D:/。hkbu/molecular science/镜头设计_v2/tests/T4_remotion/src/v3/fusion/"
s = open(A + "entry.jsx", encoding="utf8").read()
tail = "const Root = () => <>"
assert s.count(tail) == 1
comp = '''const Q_LINES = [
  [330, 352, "D", "Why this lock? Remember the Hong Kong team. In 36 of 52 liver tumours, CDK20 was higher than in nearby non-tumour tissue. High levels went with later-stage tumours and shorter survival. And turning CDK20 down in liver cancer cells slowed their growth."],
  [352, 359, "D · on camera", "So: a strong suspect. Not the only cause of liver cancer, but a lock worth trying."],
  [359, 383, "B", "In 2023, an AI platform called PandaOmics backed that hunch. It combed ten liver cancer data sets, over a thousand tumour samples and hundreds of healthy ones, plus research papers. People checked its top 20 by hand, and CDK20 came out on top, with no approved drug against it yet."],
  [383, 406, "B", "But here's the problem. To design a key, you need to see the lock. And no one had measured CDK20's shape. That takes a lot of hard lab work, and only a small fraction of proteins have ever been measured. Without a 3D shape, even computer predictions of binding get expensive, slow and difficult."],
  [406, 412, "B · on camera", "So you've got a lock nobody can see. How do you cut a key in the dark?"],
];
const END_P = %END%;
const S3Q = ({review = true}) => {
  const f = useCurrentFrame(), t = 330 + f / 60, l = Q_LINES.find(([a, b]) => t >= a && t < b);
  const [px, py] = END_P, R = 104;
  const n = Math.max(0, Math.min(36, Math.floor((t - 334.05) / 0.1) + 1));
  const leaveR = 1920 * smooth((t - 367.6) / 2.4), leaveL = 2680 * smooth((t - 382.6) / 2.0);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile("fusion_s1/take_q.mp4")} muted/>
    {t < 330.3 && <Img src={staticFile("fusion_s1/q_join.png")} style={{position: "absolute", left: 0, top: 0, width: W, height: H, opacity: 1 - smooth((t - 330) / 0.3)}}/>}
    {t >= 390 && t < 394 && <Img src={staticFile("fusion_s1/q_model.png")} style={{position: "absolute", left: 0, top: 0, width: W, height: H, opacity: 1 - smooth((t - 390) / 4)}}/>}
    <div style={{position: "absolute", left: 0, top: 0, width: W, height: H, background: "#050506", opacity: 0.9 * smooth((t - 404.6) / 4.5)}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      {/* the last piece's words go as the camera leaves */}
      <g opacity={1 - after(t, 330.0, 0.4)}>
        <Keyed x={96} y={240} size={92} at={314.4} dur={0.6} w={760} parts={["Our lock is ", "CDK20"]}/>
        <circle cx={px} cy={py} r={R} fill="none" stroke={BONE} strokeWidth={5}/>
        <Leader pts={[[px - R, py], [772, py]]} at={319.2} onColour/>
        <Ink x={760} y={py + 15} size={44} at={319.5} fill={KLEIN} weight={700} anchor="end" w={420}>ATP pocket</Ink>
        <Ink x={760} y={py + 87} size={44} at={326.5} fill={DARK} weight={700} anchor="end" w={420}>the right key</Ink>
        <Ink x={760} y={py + 170} size={58} at={327.2} font={SERIF} anchor="end" w={500}>can't do its job</Ink>
        <Tag x={96} y={1000} at={315.2} size={36}>predicted model (AlphaFold DB v6)</Tag>
        <Source x={96} y={1062} at={315.2}>Illustration · Ren et al. 2023</Source>
      </g>

      {/* third piece: the tally */}
      <g opacity={1 - after(t, 333.2, 0.3)}>
        <Keyed x={96} y={170} size={92} at={330.5} dur={0.6} w={700} parts={["Why this ", "lock", "?"]}/>
        <Ink x={96} y={250} size={44} at={331.5} weight={600} fill={SOFT} w={600}>the Hong Kong team</Ink>
      </g>
      <g opacity={after(t, 333.5, 0.3) * (1 - after(t, 350.3, 0.3))}>
        <text x={96} y={170} fontFamily={SERIF} fontSize={120}><tspan fill={RED}>{n}</tspan><tspan fill={INK}> of 52</tspan></text>
        <Ink x={96} y={250} size={58} at={335.2} font={SERIF} w={900}>liver tumours with more CDK20</Ink>
        <Ink x={96} y={318} size={58} at={335.7} font={SERIF} w={900}>than the tissue next to them</Ink>
        <Ink x={470} y={170} size={120} at={338.3} font={SERIF} fill={INK} w={340}>= 69%</Ink>
        <Ink x={1240} y={120} size={44} at={340.4} fill={DARK} weight={700} w={560}>→ later stage</Ink>
        <Ink x={1240} y={190} size={44} at={342.2} fill={DARK} weight={700} w={560}>→ shorter survival</Ink>
        <Ink x={1240} y={260} size={44} at={345.4} fill={DARK} weight={700} w={640}>CDK20 down → slower growth</Ink>
      </g>
      <Source x={96} y={1062} at={330.6} until={359.0}>Illustration · Feng et al. 2011</Source>

      <g transform={`translate(${-2200 * smooth((t - 358.6) / 2.0)} 0)`}>
        {t >= 352 && t < 361 && <Print who="D" x={72} y={168} w={620} h={744} at={352.0} rot={-1.0}/>}
      </g>
      <g opacity={1 - after(t, 358.4, 0.3)}>
        <Keyed x={780} y={150} size={92} at={352.8} dur={0.6} w={700} parts={["a strong ", "suspect"]}/>
        <Ink x={780} y={226} size={44} at={354.6} fill={SOFT} weight={600} w={700}>not the only cause</Ink>
      </g>

      {/* fourth piece: many streams, one name */}
      <g transform={`translate(${-leaveR} 0)`}>
        <g opacity={1 - after(t, 363.0, 0.3)}>
          <Keyed x={1210} y={260} size={92} at={360.2} dur={0.6} w={640} parts={["", "PandaOmics"]}/>
          <Ink x={1210} y={330} size={44} at={361.0} fill={SOFT} weight={600} w={640}>an AI platform, 2023</Ink>
        </g>
        <Ink x={1210} y={260} size={92} at={363.3} font={SERIF} w={640}>10 data sets</Ink>
        <Ink x={1210} y={800} size={44} at={365.0} fill={KLEIN} weight={700} w={640}>1,133 tumour samples</Ink>
        <Ink x={1210} y={870} size={44} at={366.0} fill={KLEIN} weight={700} w={640}>674 healthy samples</Ink>
      </g>
      <g transform={`translate(${-leaveL} 0)`}>
        <Keyed x={420} y={140} size={92} at={371.2} dur={0.8} w={1100} parts={["People checked the ", "top 20"]}/>
        <Ink x={464} y={%ROW%} size={36} at={373.6} fill={RED} weight={700} w={200}>CDK20</Ink>
        {t > 374.6 && <ellipse cx={520} cy={%RING%} rx={92} ry={34} fill="none" stroke={RED} strokeWidth={3.5} pathLength={1} strokeDasharray={`${smooth((t - 374.6) / 0.7)} 1`}/>}
        <Ink x={1540} y={420} size={58} at={378.0} font={SERIF} w={380}>no approved</Ink>
        <Ink x={1540} y={490} size={58} at={378.4} font={SERIF} w={380}>drug against</Ink>
        <Ink x={1540} y={560} size={58} at={378.8} font={SERIF} w={380}>it yet</Ink>
        <Ink x={%ROADX%} y={892} size={36} at={380.2} fill={DARK} weight={700} anchor="middle" w={220}>Target</Ink>
        <Source x={96} y={1062} at={371.4}>Illustration · the other 19 names are not in the paper · Ren et al. 2023</Source>
      </g>
      <Source x={1210} y={1062} at={360.0} until={367.4}>Illustration · Ren et al. 2023</Source>

      {/* fifth piece: the empty cells */}
      <g opacity={1 - after(t, 392.8, 0.3)}>
        <Keyed x={960 - 400} y={1016} size={72} at={388.4} dur={0.8} w={900} parts={["no one had ", "measured", " its shape"]}/>
      </g>
      <g opacity={1 - after(t, 397.6, 0.3)}>
        <Ink x={960} y={1016} size={72} at={393.2} font={SERIF} anchor="middle" w={1400}>only a small fraction of proteins have been measured</Ink>
        <Ink x={960} y={%CELL%} size={36} at={387.6} fill={RED} weight={700} anchor="middle" w={200}>CDK20</Ink>
        <Leader pts={[[960, 464], [960, 400]]} at={387.4} fill={RED}/>
      </g>
      <g opacity={1 - after(t, 404.6, 0.4)}>
        <Ink x={520} y={620} size={54} at={401.2} font={SERIF} w={480}>without a 3D shape,</Ink>
        <Ink x={520} y={690} size={54} at={401.9} font={SERIF} w={480}>predictions get</Ink>
        <Keyed x={520} y={760} size={54} at={402.6} dur={0.8} w={480} parts={["", "expensive, slow, difficult"]}/>
      </g>
      <Source x={96} y={1062} at={385.2} until={404.8}>Illustration · Ren et al. 2023</Source>

      {t >= 406 && <Print who="B" x={72} y={168} w={620} h={744} at={406.0} rot={1.0}/>}
    </svg>
    {review && l && <div style={{position: "absolute", left: 120, right: 120, top: 22, textAlign: "center", fontFamily: SANS, fontWeight: 500, fontSize: 24, lineHeight: 1.3, color: t > 407 ? "#B8B6AE" : SOFT}}><b style={{color: t > 407 ? BONE : INK}}>{l[2]}</b>  {l[3]}</div>}
  </AbsoluteFill></Clock.Provider>;
};

'''
comp = comp.replace("%END%", json.dumps(TRACK[-1])).replace("%ROW%", "278").replace("%RING%", "266").replace("%ROADX%", "-").replace("%CELL%", "388")
comp = comp.replace("x={-}", "x={%d}" % (960 + (111.6 - 113.6) * 200))
s = s.replace(tail, comp + tail, 1)
head = '  <Composition id="S3Board"'
assert s.count(head) == 1
s = s.replace(head, '  <Composition id="S3Q" component={S3Q} durationInFrames={4920} fps={60} width={W} height={H}/>\n' + head, 1)
a = "AbsoluteFill, OffthreadVideo,"
assert s.count(a) == 1
s = s.replace(a, "AbsoluteFill, Img, OffthreadVideo,", 1)
open(A + "entry_q.jsx", "w", encoding="utf8").write(s)
print("ok")
