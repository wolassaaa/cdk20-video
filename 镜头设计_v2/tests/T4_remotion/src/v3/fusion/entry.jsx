// HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: type, marks and photo prints on the table.
// The picture under it (base.mp4) comes from 镜头设计_v3/styleframes/art/fusion/s1/code/base.py. Both read the same camera, so everything here is placed in table coordinates and moves with the table.
// Words on screen follow script_v3.3.md. Times are seconds on the script's clock, the same as timeline.py; TL.u turns each frame of the film into that clock, from 节奏表.csv. Props: review shows the script line along the top; base=false leaves the type on bone for quick stills.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import TL from "./s1_timeline.json";

const FPS = TL.fps, N = TL.n, W = 1920, H = 1080;
const INK = "#111113", SOFT = "#545458", RED = "#E8190F", DARK = "#9A0E08", KLEIN = "#002FA7", BONE = "#EDEBE4";
const SERIF = "Instrument Serif", SANS = "Inter Tight";

const faces = [new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Regular.ttf")})`), new FontFace(SANS, `url(${staticFile("fusion_s1/fonts/InterTight.ttf")})`, {weight: "100 900"})];
const fontHandle = delayRender("fonts");
Promise.all(faces.map(f => f.load())).then(l => { l.forEach(f => document.fonts.add(f)); continueRender(fontHandle); });

const clamp = x => Math.min(1, Math.max(0, x));
const smooth = x => { x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10); };
const out = x => 1 - Math.pow(1 - clamp(x), 3);
const Clock = React.createContext(0), Zoom = React.createContext(1);
const useT = () => React.useContext(Clock);
const after = (t, at, d = 0.5) => out((t - at) / d);

// ---------------------------------------------------------------- type printed on the table
let wipeId = 0;
/** Words that print left to right, as if a press ran over them. w is a generous width. */
const Ink = ({x, y, size, at, font = SANS, weight = 600, fill = INK, anchor = "start", w, dur = 0.5, children}) => {
  const t = useT(), p = smooth((t - at) / dur);
  if (p <= 0) return null;
  const width = w || String(children).length * size * 0.62 + 40;
  const left = anchor === "start" ? x - 20 : anchor === "end" ? x - width : x - width / 2;
  const id = React.useMemo(() => `wipe${wipeId++}`, []);
  return <g>
    <clipPath id={id}><rect x={left} y={y - size * 1.2} width={width * p} height={size * 1.6}/></clipPath>
    <text x={x} y={y} fontFamily={font} fontSize={size} fontWeight={font === SERIF ? 400 : weight} fill={fill} textAnchor={anchor} clipPath={`url(#${id})`}>{children}</text>
  </g>;
};

/** Textbook leader: a thin line grows from the object to the word, then the dot sits on the object. */
const Leader = ({pts, at, fill = INK, onColour}) => {
  const t = useT(), p = smooth((t - at) / 0.45);
  if (p <= 0) return null;
  const L = pts.slice(1).reduce((s, q, i) => s + Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]), 0);
  return <g>
    <polyline points={pts.map(q => q.join(",")).join(" ")} fill="none" stroke={fill} strokeWidth={2} strokeDasharray={`${L * p} ${L}`}/>
    <circle cx={pts[0][0]} cy={pts[0][1]} r={6} fill={onColour ? BONE : fill} stroke={onColour ? INK : "none"} strokeWidth={1.5}/>
  </g>;
};

/** Evidence kinds differ by mark shape: hatched square for schematic, dashed circle for predicted. */
const Tag = ({kind, x, y, at, size = 30, children}) => {
  const t = useT(), a = after(t, at);
  if (a <= 0) return null;
  const r = size / 2, cx = x + r, cy = y - size * 0.36;
  return <g opacity={a}>
    {kind === "schematic" && <g fill="none" stroke={INK} strokeWidth={2.5}>
      <rect x={cx - r} y={cy - r} width={size} height={size}/>
      {[-0.7, 0, 0.7].map(o => <line key={o} x1={cx - r + Math.max(0, o * r)} y1={cy + r + Math.min(0, o * r)} x2={cx + r + Math.min(0, o * r)} y2={cy - r + Math.max(0, o * r)} strokeWidth={2}/>)}
    </g>}
    {kind === "predicted" && <circle cx={cx} cy={cy} r={r} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>}
    <text x={x + size + 14} y={y} fontFamily={SANS} fontSize={size} fontWeight={600} fill={INK}>{children}</text>
  </g>;
};

const Source = ({x, y, at, until = 1e9, children}) => {
  const t = useT(), a = after(t, at) * (1 - after(t, until));
  return a > 0 ? <text x={x} y={y} fontFamily={SANS} fontSize={26} fontWeight={500} fill={SOFT} opacity={a}>{children}</text> : null;
};

// ---------------------------------------------------------------- the phone clip on a print
const HALF = [[0, 435], [60, 420], [98, 360], [104, 300], [92, 235], [62, 185], [52, 150], [56, 120], [100, 92], [210, 62], [270, 30], [300, -30], [315, -120], [330, -300], [340, -560]];
const PERSON = (() => {
  const c = [...HALF, ...HALF.slice(1).reverse().map(([x, y]) => [-x, y])], n = c.length, pts = [];
  for (let i = 0; i < n; i++) {
    const [a, b, d, e] = [-1, 0, 1, 2].map(k => c[(i + k + n) % n]);
    for (let s = 0; s < 8; s++) {
      const u = s / 8;
      pts.push([0, 1].map(j => 0.5 * (2 * b[j] + (d[j] - a[j]) * u + (2 * a[j] - 5 * b[j] + 4 * d[j] - e[j]) * u * u + (3 * b[j] - a[j] - 3 * d[j] + e[j]) * u * u * u)));
    }
  }
  return pts.map(p => `${p[0].toFixed(1)},${(-p[1]).toFixed(1)}`).join(" ");
})();

/** The stand-in until the real clips come on 11-12. Warm, because people are warm; it lands on the table like a thrown print. */
const Print = ({who, x, y, w, h, at, rot}) => {
  const t = useT(), p = out((t - at) / 0.5);
  if (t < at) return null;
  const lift = 1 - p, cx = x + w / 2, cy = y + h / 2, k = (w - 40) / 760, id = `photo${who}${at}`;
  const talk = Math.sin(t * 2.1 + at) * 3;
  return <g transform={`translate(${cx - 60 * lift} ${cy + 130 * lift}) rotate(${rot + 5 * lift}) scale(${1 + 0.05 * lift})`} opacity={clamp((t - at) / 0.08)}>
    <rect x={-w / 2 + 12 + 18 * lift} y={-h / 2 + 16 + 24 * lift} width={w} height={h} fill="#3C3228" opacity={0.3 - 0.12 * lift} style={{filter: "blur(14px)"}}/>
    <rect x={-w / 2} y={-h / 2} width={w} height={h} fill="#F7F3EA"/>
    <clipPath id={id}><rect x={-w / 2 + 20} y={-h / 2 + 20} width={w - 40} height={h - 40}/></clipPath>
    <g clipPath={`url(#${id})`}>
      <rect x={-w / 2 + 20} y={-h / 2 + 20} width={w - 40} height={h - 40} fill="#D3BFA5"/>
      <rect x={-w / 2 + 20} y={-h / 2 + 20} width={(w - 40) * 0.4} height={h - 40} fill="#DCCBB3"/>
      <g transform={`translate(0 ${h * 0.03 + talk * k}) scale(${k * 0.95})`}><polygon points={PERSON} fill="#7E6A58"/></g>
    </g>
    <text x={-w / 2 + 44} y={h / 2 - 46} fontFamily={SANS} fontSize={26} fontWeight={600} fill="#F7F3EA">stand-in · {who}</text>
  </g>;
};

// ---------------------------------------------------------------- the stations
const ST1 = 1920, ST2 = 3840, ST5 = 9600;

const Liver = () => {
  const x = ST1, t = useT();
  const ring = [x + 1610, 432], rr = 30, lc = [3640, 770], lr = 150;
  const a = smooth((t - 22.0) / 0.6);
  const dx = lc[0] - ring[0], dy = lc[1] - ring[1], L = Math.hypot(dx, dy), base = Math.atan2(dy, dx), off = Math.acos((rr - lr) / L);
  const tan = [1, -1].map(s => { const q = base + s * off; return [[ring[0] + rr * Math.cos(q), ring[1] + rr * Math.sin(q)], [lc[0] + lr * Math.cos(q), lc[1] + lr * Math.sin(q)]]; });
  const hex = (cx, cy, R) => [...Array(6)].map((_, k) => `${cx + R * Math.sin(k * Math.PI / 3)},${cy + R * Math.cos(k * Math.PI / 3)}`).join(" ");
  const cells = [];
  for (let j = -4; j <= 4; j++) for (let i = -4; i <= 4; i++) { const w = Math.sqrt(3) * 55, cx = (i + (j & 1 ? 0.5 : 0)) * w, cy = j * 1.5 * 55 + 55; cells.push([Math.hypot(cx, cy), cx, cy]); }
  cells.sort((p, q) => p[0] - q[0]);
  return <g>
    <Ink x={x + 96} y={460} size={250} at={8.9} font={SERIF} fill={RED} w={760} dur={0.7}>1,412</Ink>
    <Ink x={x + 104} y={546} size={50} at={9.7} weight={500}>deaths in Hong Kong, 2022</Ink>
    <Ink x={x + 340} y={668} size={36} at={11.0} weight={500} fill={SOFT}>about four a day</Ink>
    <Ink x={x + 104} y={760} size={40} at={13.0}>Top 3 deadliest in HK</Ink>
    <Ink x={x + 104} y={808} size={36} at={13.5} weight={500}>lung · colorectal · liver</Ink>
    <Ink x={x + 104} y={884} size={40} at={20.0}>World: 6th most common</Ink>
    <Ink x={x + 104} y={932} size={40} at={20.8}>3rd deadliest</Ink>
    <Leader pts={[[x + 1262, 700], [x + 1176, 862], [x + 1146, 862]]} at={12.6} fill={RED}/>
    <Ink x={x + 1134} y={875} size={40} at={13.0} fill={DARK} anchor="end">portal vein</Ink>
    <Leader pts={[[x + 1184, 296], [x + 1240, 110], [x + 1300, 110]]} at={16.6} fill={KLEIN}/>
    <Ink x={x + 1310} y={123} size={40} at={17.0} fill={KLEIN}>hepatic veins</Ink>
    <Leader pts={[[x + 1640, 352], [x + 1640, 196], [x + 1696, 196]]} at={18.6}/>
    <Ink x={x + 1708} y={209} size={40} at={19.0}>liver</Ink>
    {a > 0 && <g opacity={a}>
      {tan.map((s, i) => <line key={i} x1={s[0][0]} y1={s[0][1]} x2={s[1][0]} y2={s[1][1]} stroke={INK} strokeWidth={1.5}/>)}
      <circle cx={ring[0]} cy={ring[1]} r={rr} fill="none" stroke={INK} strokeWidth={2.5}/>
    </g>}
    <clipPath id="lensclip"><circle cx={lc[0]} cy={lc[1]} r={lr - 4}/></clipPath>
    <g clipPath="url(#lensclip)">
      {cells.slice(0, 12).map(([, cx, cy], i) => { const c = smooth((t - 22.4 - i * 0.08) / 0.5);
        return c > 0 ? <g key={i} opacity={c}><polygon points={hex(lc[0] + cx, lc[1] + cy, 51)} fill="#DDD9CE" strokeLinejoin="round"/><circle cx={lc[0] + cx} cy={lc[1] + cy} r={15} fill="#BCB7AA"/></g> : null; })}
    </g>
    {a > 0 && <line x1={lc[0]} y1={lc[1] + lr + 3} x2={lc[0]} y2={942} stroke={INK} strokeWidth={2} opacity={a}/>}
    <Tag kind="schematic" x={lc[0] - 90} y={984} at={23.2} size={34}>schematic</Tag>
    <Tag kind="schematic" x={x + 640} y={668} at={11.2} size={26}>schematic</Tag>
    <Source x={x + 96} y={1062} at={9.8}>HKCaR 2022 · GLOBOCAN 2020 · BodyParts3D, DBCLS, CC BY 4.0</Source>
  </g>;
};

const Drugs = () => {
  const x = ST2, t = useT();
  const arrow = smooth((t - 34.9) / 0.5), grey = smooth((t - 36.2) / 0.8);
  return <g>
    <text x={x + 96} y={300} fontFamily={SERIF} fontSize={100} fill={INK} opacity={after(t, 33.0) * (1 - 0.6 * grey)}>Nexavar</text>
    {arrow > 0 && <g stroke={RED} strokeWidth={5} fill="none">
      <line x1={x + 450} y1={266} x2={x + 450 + 120 * arrow} y2={266}/>
      <polyline points={`${x + 450 + 120 * arrow - 18},${248} ${x + 450 + 120 * arrow},${266} ${x + 450 + 120 * arrow - 18},${284}`} opacity={arrow}/>
    </g>}
    <Ink x={x + 600} y={300} size={100} at={35.3} font={SERIF} w={1200} dur={0.9}>atezolizumab + bevacizumab</Ink>
    <Ink x={x + 600} y={364} size={40} at={37.0} weight={500} fill={SOFT}>first-line, advanced HCC</Ink>
    <Ink x={x + 96} y={650} size={170} at={46.2} font={SERIF} fill={RED} w={620} dur={0.6}>~3 in 10</Ink>
    <Ink x={x + 660} y={600} size={46} at={46.8}>5-year relative survival</Ink>
    <Ink x={x + 660} y={650} size={36} at={47.2} weight={500} fill={SOFT}>HK, 2010-2021</Ink>
    <Tag kind="schematic" x={x + 1520} y={650} at={47.2}>schematic</Tag>
    <Source x={x + 96} y={1062} at={33.0}>Ren 2023 · HKCaR 2022</Source>
  </g>;
};

const Ruler = () => {
  const t = useT(), [x0, x1, y] = TL.world.ruler, st = (x1 - x0) / 17;
    const yrs = [...Array(18).keys()];
  return <g>
    {yrs.map(i => { const a = clamp((t - 59.9 - i * (5.5 / 17)) / 0.25), big = i === 0 || i === 10 || i === 17;
      return a > 0 ? <line key={i} x1={x0 + i * st} y1={y + 18} x2={x0 + i * st} y2={y + 18 + (big ? 44 : 22) * a} stroke={INK} strokeWidth={big ? 3 : 2}/> : null; })}
    <Ink x={x0 + 10 * st} y={y + 104} size={44} at={63.2} anchor="middle" w={100}>10</Ink>
    <Ink x={x0 + 17 * st} y={y + 104} size={44} at={65.4} anchor="middle" w={100}>17</Ink>
    {t > 65.6 && <g>
      <line x1={x0 + 10 * st} y1={y + 136} x2={x0 + (10 + 7 * smooth((t - 65.6) / 0.6)) * st} y2={y + 136} stroke={RED} strokeWidth={8}/>
      <Ink x={x0 + 13.5 * st} y={y + 200} size={60} at={66.0} font={SERIF} fill={DARK} anchor="middle" w={400}>10-17 years</Ink>
    </g>}
    {/* a plain cradle at year 0 */}
    <g opacity={after(t, 60.0)} fill="none" stroke={INK} strokeWidth={3.5} strokeLinecap="round">
      <path d={`M ${x0 - 52} ${y - 74} A 54 54 0 0 0 ${x0 + 52} ${y - 74}`}/>
      <path d={`M ${x0 - 64} ${y - 74} L ${x0 + 64} ${y - 74}`}/>
      <path d={`M ${x0 - 38} ${y - 16} Q ${x0} ${y - 6} ${x0 + 38} ${y - 16}`}/>
    </g>
    <Tag kind="schematic" x={x0 + 30} y={y + 104} at={60.6} size={30}>schematic</Tag>
    <Source x={x0 + 30} y={y + 200} at={60.6}>Wang 2023</Source>
  </g>;
};

const Cost = () => {
  const x = ST5;
  return <g>
    <Ink x={x + 96} y={420} size={190} at={67.2} font={SERIF} fill={RED} w={1100} dur={0.8}>~US$2.8 billion</Ink>
    <Ink x={x + 96} y={784} size={84} at={73.0} font={SERIF} w={900} dur={0.7}>about 1 in 10</Ink>
    <Ink x={x + 96} y={846} size={44} at={73.6}>of drugs tested in people reaches the market</Ink>
    <Tag kind="schematic" x={x + 1500} y={784} at={73.0}>schematic</Tag>
    <Source x={x + 96} y={1062} at={67.2}>Wang 2023</Source>
  </g>;
};

const Road = () => {
  const r = TL.world.road, t = useT();
  const names = [[80.7, ["Target"]], [81.9, ["Hit"]], [84.3, ["Improve"]], [85.6, ["Cells & animals"]], [88.1, ["Clinical trials", "1-2-3"]], [91.6, ["Approval"]]];
  return <g>
    {names.map(([at, lines], i) => <g key={i}>
      {lines.map((s, j) => <Ink key={j} x={r[i][0]} y={670 + j * 46} size={40} at={at + j * 0.9} anchor="middle" w={340}>{s}</Ink>)}
    </g>)}
    <Ink x={W / 2 + 11520} y={900} size={84} at={93.1} font={SERIF} anchor="middle" w={900}>Any step can fail.</Ink>
  </g>;
};

const Protein = () => {
  const x = 11520, y = 1080;
  return <g>
    <Ink x={x + 1450} y={y + 700} size={68} at={98.8} font={SERIF} w={460}>Nobel Prize</Ink>
    <Ink x={x + 1450} y={y + 770} size={68} at={99.2} font={SERIF} w={460}>in Chemistry</Ink>
    <Ink x={x + 1450} y={y + 840} size={68} at={99.6} font={SERIF} w={460}>2024</Ink>
    <Ink x={x + 1450} y={y + 900} size={36} at={101.2} weight={500}>Demis Hassabis</Ink>
    <Ink x={x + 1450} y={y + 944} size={36} at={101.8} weight={500}>John Jumper</Ink>
    <Tag kind="predicted" x={x + 96} y={y + 1012} at={99.0}>AlphaFold DB v6 · predicted</Tag>
  </g>;
};

const Pin = ({xy, at, children, dy = 0}) => {
  const t = useT(), z = React.useContext(Zoom), k = 1 / Math.max(1, z), a = after(t, at);
  return a > 0 ? <g opacity={a}>
    <circle cx={xy[0]} cy={xy[1]} r={7 * k} fill={INK}/>
    <text x={xy[0] - 18 * k} y={xy[1] + (13 + dy) * k} textAnchor="end" fontFamily={SANS} fontWeight={600} fontSize={40 * k} fill={INK}>{children}</text>
  </g> : null;
};

// ---------------------------------------------------------------- what lives in screen space
const Title = () => {
  const t = useT(), at = 125.6, land = clamp((t - at) / 0.1), k = 1 + 0.05 * (1 - out((t - at) / 0.3));
  return t < at ? null : <g>
    <g transform={`translate(960 330) scale(${k})`} opacity={land}>
      <text x={0} y={0} textAnchor="middle" fontFamily={SERIF} fontSize={240} fill={INK}>WORTH TESTING<tspan fill={RED}>?</tspan></text>
    </g>
    <text x={960} y={424} textAnchor="middle" fontFamily={SANS} fontWeight={500} fontSize={48} fill={INK} opacity={after(t, at + 0.7)}>How computers help find cancer drug candidates: the CDK20 story</text>
    <text x={960} y={1002} textAnchor="middle" fontFamily={SANS} fontWeight={500} fontSize={30} fill={SOFT} opacity={after(t, at + 1.6)}>SCIE1007 · Section — · Group — · Member A · Member B · Member C · Member D</text>
  </g>;
};

const LINES = [
  [2, 8, "A · on camera", "Every day in Hong Kong, about four people die of liver cancer."],
  [8, 25, "A", "That's 1,412 people in 2022 alone. Here, it's one of the three deadliest cancers, alongside lung and colorectal. And it's not just us. Worldwide, it's the sixth most common cancer, and the third deadliest."],
  [25, 31, "A · on camera", "Here's the thing. We already have medicines. Just not good enough ones."],
  [31, 52, "D", "The standard first treatment for advanced liver cancer has already changed once, from Nexavar to a combo, atezolizumab plus bevacizumab. But here, only about three in ten patients are alive five years on. The study we follow calls it a huge unmet need."],
  [52, 55, "D · on camera", "So... why not just make a better one?"],
  [55, 58, "B · on camera", "Because that's way harder than it sounds."],
  [58, 60, "C · on camera", "Like, ten-to-seventeen-years hard."],
  [60, 76, "C", "Start the search the year we were born, and it might only be ready now. It can cost almost 2.8 billion US dollars. And of drugs tested in people, only about one in ten reaches the market."],
  [76, 96, "D", "To see why, let's follow one drug's journey. Every medicine walks the same road. Find a target. Find a hit, a first molecule that works on it. Improve it. Test it in cells, then animals. Then human trials: phase one, two, three. Then approval. Any step can fail."],
  [96, 112, "B", "Now here's where it gets interesting. In 2024, part of the Nobel Prize in Chemistry went to Demis Hassabis and John Jumper, for AlphaFold, an AI that predicts the shape of proteins."],
  [112, 123, "C", "So can AI walk the first steps faster? Let's follow one real case, where AI tools took on liver cancer. And part of it starts right here, in Hong Kong."],
];

const Review = () => {
  const t = useT(), l = LINES.find(([a, b]) => t >= a && t < b);
  return l ? <div style={{position: "absolute", left: 120, right: 120, top: 22, textAlign: "center", fontFamily: SANS, fontWeight: 500, fontSize: 24, lineHeight: 1.3, color: SOFT}}><b style={{color: INK}}>{l[2]}</b>  {l[3]}</div> : null;
};

// ---------------------------------------------------------------- the frame
const S1 = ({review = true, base = true}) => {
  const f = useCurrentFrame(), t = TL.u[f], [cx, cy, z] = TL.cam[f];
  return <Clock.Provider value={t}><Zoom.Provider value={z}>
    <AbsoluteFill style={{background: BONE}}>
      {base && <OffthreadVideo src={staticFile("fusion_s1/base.mp4")} muted/>}
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
        <g transform={`translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})`}>
          <Liver/><Drugs/><Ruler/><Cost/><Road/><Protein/>
          <Print who="A" x={96} y={84} w={760} h={912} at={2.15} rot={-1.2}/>
          <Print who="A" x={ST1 + 96} y={84} w={760} h={912} at={25.05} rot={0.9}/>
          <Print who="D" x={5840} y={170} w={500} h={600} at={52.05} rot={-1.5}/>
          <Print who="B" x={6430} y={170} w={500} h={600} at={55.0} rot={1.0}/>
          <Print who="C" x={7020} y={170} w={500} h={600} at={58.0} rot={-0.8}/>
          <Pin xy={TL.world.pwh} at={119.8}>Sha Tin</Pin>
          <Pin xy={TL.world.hkstp} at={122.0}>Pak Shek Kok</Pin>
        </g>
        <Title/>
        {t > 113.4 && t < 123.2 && <text x={96} y={1050} fontFamily={SANS} fontSize={26} fontWeight={500} fill={SOFT} opacity={after(t, 113.4)}>© OpenStreetMap contributors</text>}
      </svg>
      {review && <Review/>}
    </AbsoluteFill>
  </Zoom.Provider></Clock.Provider>;
};

const Root = () => <Composition id="S1Fusion" component={S1} durationInFrames={N} fps={FPS} width={W} height={H} defaultProps={{review: true, base: true}}/>;
registerRoot(Root);
