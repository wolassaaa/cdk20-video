// HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: type, marks and photo prints on the table.
// The picture under it (base.mp4) comes from 镜头设计_v3/styleframes/art/fusion/s1/code/base.py. Both read the same camera, so everything here is placed in table coordinates and moves with the table.
// Words on screen follow script_v3.3.md. Times are seconds on the script's clock, the same as timeline.py; TL.u turns each frame of the film into that clock, from 节奏表.csv. Props: review shows the script line along the top; base=false leaves the type on bone for quick stills.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import TL from "./s1_timeline.json";
import W3C from "./w3_count.json";

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
    {kind === "schematic" && <g fill="none" stroke={INK} strokeWidth={size / 12}>
      <rect x={cx - r} y={cy - r} width={size} height={size}/>
      {[-0.7, 0, 0.7].map(o => <line key={o} x1={cx - r + Math.max(0, o * r)} y1={cy + r + Math.min(0, o * r)} x2={cx + r + Math.min(0, o * r)} y2={cy - r + Math.max(0, o * r)} strokeWidth={size / 15}/>)}
    </g>}
    {kind === "predicted" && <circle cx={cx} cy={cy} r={r} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>}
    <text x={x + size * 1.45} y={y} fontFamily={SANS} fontSize={size} fontWeight={600} fill={INK}>{children}</text>
  </g>;
};

const Source = ({x, y, at, until = 1e9, size = 26, children}) => {
  const t = useT(), a = after(t, at) * (1 - after(t, until));
  return a > 0 ? <text x={x} y={y} fontFamily={SANS} fontSize={size} fontWeight={500} fill={SOFT} opacity={a}>{children}</text> : null;
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
    <text x={x + 260} y={490} textAnchor="middle" fontFamily={SERIF} fontSize={72} fill={INK} opacity={after(t, 33.0) * (1 - 0.6 * grey)}>Nexavar</text>
    {arrow > 0 && <g stroke={RED} strokeWidth={5} fill="none">
      <line x1={x + 510} y1={235} x2={x + 510 + 120 * arrow} y2={235}/>
      <polyline points={`${x + 510 + 120 * arrow - 18},${217} ${x + 510 + 120 * arrow},${235} ${x + 510 + 120 * arrow - 18},${253}`} opacity={arrow}/>
    </g>}
    <Ink x={x + 1100} y={490} size={72} at={35.3} font={SERIF} anchor="middle" w={960} dur={0.9}>atezolizumab + bevacizumab</Ink>
    <Ink x={x + 1100} y={540} size={36} at={37.0} weight={500} fill={SOFT} anchor="middle" w={520}>first-line, advanced HCC</Ink>
    <Ink x={x + 96} y={730} size={170} at={46.2} font={SERIF} fill={RED} w={620} dur={0.6}>~3 in 10</Ink>
    <Ink x={x + 660} y={680} size={46} at={46.8}>5-year relative survival</Ink>
    <Ink x={x + 660} y={730} size={36} at={47.2} weight={500} fill={SOFT}>HK, 2010-2021</Ink>
    <Tag kind="schematic" x={x + 1520} y={120} at={35.6}>schematic</Tag>
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

// ---------------------------------------------------------------- S2: Hong Kong, the question, the sources
const K3 = 1 / 3;    // the map scenes run at zoom 3, so sizes here are screen sizes over 3

const Stories = () => {
  return <g>
    <Ink x={14040} y={1416} size={84 * K3} at={143.2} font={SERIF} fill={RED} w={100}>2011</Ink>
    <Ink x={14040} y={1440} size={40 * K3} at={144.2} w={260}>Chinese University of Hong Kong</Ink>
    <Ink x={14040} y={1458} size={40 * K3} at={145.2} w={260}>Prince of Wales Hospital</Ink>
    <Ink x={14040} y={1476} size={36 * K3} at={146.4} weight={500} fill={SOFT} w={260}>liver tumours from patients</Ink>
    <Ink x={14040} y={1546} size={120 * K3} at={153.0} font={SERIF} fill={DARK} w={320} dur={0.8}>CCRK = CDK20</Ink>
    <Tag kind="schematic" x={14108} y={1668} at={147.6} size={10}>schematic</Tag>
    <Source x={14040} y={1712} at={146.4} until={158.4} size={27 * K3}>Feng 2011</Source>
    <Ink x={14446} y={1476} size={84 * K3} at={158.8} font={SERIF} fill={RED} w={100}>2023</Ink>
    <Ink x={14446} y={1500} size={40 * K3} at={160.6} w={240}>AI drug-discovery study</Ink>
    <Ink x={14446} y={1518} size={36 * K3} at={162.2} weight={500} fill={SOFT} w={240}>the same protein</Ink>
    <Ink x={14446} y={1536} size={40 * K3} at={166.0} w={240}>Insilico Medicine, Hong Kong</Ink>
    <Ink x={14446} y={1554} size={36 * K3} at={168.6} weight={500} fill={SOFT} w={240}>Science Park</Ink>
    <Source x={14060} y={1622} at={166.0} until={172.8} size={27 * K3}>Ren 2023</Source>
  </g>;
};

const Question = () => {
  const x = 15360, y = 1080;
  return <g>
    <Ink x={x + 960} y={y + 210} size={44} at={175.8} fill={SOFT} weight={500}>Our research question</Ink>
    {["How can computer-aided", "methods help scientists", "find and assess potential", "cancer drug candidates?"].map((s, i) =>
      <Ink key={i} x={x + 960} y={y + 320 + i * 96} size={84} at={177.0 + i * 1.6} font={SERIF} w={900} dur={1.5}>{s}</Ink>)}
    <Ink x={x + 960} y={y + 760} size={46} at={184.8} fill={DARK} w={900} dur={1.0}>A case study of CDK20 in liver cancer</Ink>
  </g>;
};

const OBJ = [["Identify the major", "computer-aided methods", "used in cancer drug discovery"], ["Evaluate how these methods", "help scientists assess", "potential drug candidates"]];
const Objectives = () => {
  const x = 17280, y = 1080, t = useT(), gone = 1 - smooth((t - 206.0) / 0.6), tags = smooth((t - 206.4) / 0.6);
  return <g>
    <Print who="C" x={x + 96} y={y + 168} w={620} h={744} at={190.05} rot={-0.9}/>
    <g opacity={gone}>
      {OBJ.map((lines, i) => <g key={i}>
        <Ink x={x + 800} y={y + 340 + i * 380} size={170} at={190.6 + i * 0.5} font={SERIF} fill={RED} w={110}>{i + 1}</Ink>
        {lines.map((s, j) => <Ink key={j} x={x + 930} y={y + 240 + i * 380 + j * 60} size={46} at={(i ? 199.6 : 193.4) + j * 1.4} w={760} dur={1.2}>{s}</Ink>)}
      </g>)}
    </g>
    {tags > 0 && <g opacity={tags} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK}>
      <text x={x + 96} y={y + 100}><tspan fill={RED}>1</tspan> Identify methods</text>
      <text x={x + 96} y={y + 146}><tspan fill={RED}>2</tspan> Evaluate candidates</text>
    </g>}
  </g>;
};

const CARDS = [["original study", "Feng et al.", "J. Clin. Invest. 2011", 225.0], ["method paper", "Jumper et al.", "Nature 2021", 227.0], ["method paper", "Ivanenkov et al.", "J. Chem. Inf. Model. 2023", 227.7], ["review", "Wang et al.", "Pharmaceuticals 2023", 229.6], ["book chapter", "Lengauer", "Bioinformatics, Wiley-VCH 2007", 231.2], ["Perspective (abstract only)", "Bender et al.", "Nat. Rev. Drug Discov. 2026", 233.2]];
const PAGE = {x: 19296, y: 1190, w: 600, h: 850};
const TICKS = [243.7, 245.3, 246.9, 248.5, 249.9, 251.5];

const Card = ({c, i}) => {
  const t = useT(), p = out((t - c[3]) / 0.8);
  if (p <= 0) return null;
  const col = i % 2, row = Math.floor(i / 2), W_ = 520, H_ = 170, tx = 19960 + col * 540, ty = 1280 + row * 186;
  const sx = PAGE.x + PAGE.w / 2 - W_ / 2, sy = PAGE.y + PAGE.h / 2 - H_ / 2, x = sx + (tx - sx) * p, y = sy + (ty - sy) * p, r = (1 - p) * (i - 2.5) * 3;
  const tick = smooth((t - TICKS[i]) / 0.3);
  return <g transform={`translate(${x} ${y}) rotate(${r} ${W_ / 2} ${H_ / 2})`}>
    <rect x={8} y={12} width={W_} height={H_} fill="#3C3228" opacity={0.2} style={{filter: "blur(12px)"}}/>
    <rect width={W_} height={H_} fill="#F7F3EA"/>
    <text x={24} y={54} fontFamily={SANS} fontSize={36} fontWeight={700} fill={INK}>{c[0]}</text>
    <text x={24} y={100} fontFamily={SANS} fontSize={28} fontWeight={500} fill={SOFT}>{c[1]}</text>
    <text x={24} y={138} fontFamily={SANS} fontSize={28} fontWeight={500} fill={SOFT}>{c[2]}</text>
    {tick > 0 && <path d="M 462 118 L 476 134 L 502 100" fill="none" stroke={KLEIN} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={80} strokeDashoffset={80 * (1 - tick)}/>}
  </g>;
};

const TITLE = ["AlphaFold accelerates artificial", "intelligence powered drug", "discovery: efficient discovery", "of a novel CDK20 small", "molecule inhibitor"];
const Paper = () => {
  const t = useT(), at = 209.0, p = out((t - at) / 0.5), {x, y, w, h} = PAGE;
  if (t < at) return null;
  const lift = 1 - p, stamp = clamp((t - 217.2) / 0.1), sk = 1 + 0.08 * (1 - out((t - 217.2) / 0.3)), bracket = smooth((t - 256.6) / 0.5);
  return <g transform={`translate(${-60 * lift} ${130 * lift})`} opacity={clamp((t - at) / 0.08)}>
    <rect x={x + 12} y={y + 16} width={w} height={h} fill="#3C3228" opacity={0.3} style={{filter: "blur(14px)"}}/>
    <rect x={x} y={y} width={w} height={h} fill="#F7F3EA"/>
    <text x={x + 40} y={y + 62} fontFamily={SANS} fontSize={26} fontWeight={600} fill={SOFT}>Chemical Science · 2023</text>
    {TITLE.map((s, i) => <text key={i} x={x + 40} y={y + 124 + i * 44} fontFamily={SERIF} fontSize={38} fill={INK}>{s}</text>)}
    <text x={x + 40} y={y + 348} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK}>Ren et al.</text>
    {[0, 1, 2, 3].map(i => <rect key={i} x={x + 40} y={y + 382 + i * 20} width={w - 80 - (i === 3 ? 180 : 0)} height={7} fill="#D8D4C8"/>)}
    <text x={x + 40} y={y + 498} fontFamily={SANS} fontSize={30} fontWeight={700} fill={INK}>Conflicts of interest</text>
    {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => <rect key={i} x={x + 40} y={y + 526 + i * 20} width={w - 80 - (i % 4 === 3 ? 140 : 0)} height={7} fill="#D8D4C8"/>)}
    {bracket > 0 && <path d={`M ${x + 30} ${y + 468} h -14 v 42 h 14`} fill="none" stroke={INK} strokeWidth={3} opacity={bracket}/>}
    {stamp > 0 && <g transform={`translate(${x + 410} ${y + 338}) rotate(-6) scale(${sk})`} opacity={stamp}>
      <rect x={-150} y={-34} width={300} height={68} fill="none" stroke={RED} strokeWidth={4}/>
      <text x={0} y={13} textAnchor="middle" fontFamily={SANS} fontSize={36} fontWeight={700} fill={RED}>original research</text>
    </g>}
  </g>;
};

const glide = (keys, t) => {
  if (t <= keys[0][0]) return keys[0].slice(1);
  for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) {
    const a = keys[i - 1], b = keys[i], q = smooth((t - a[0]) / (b[0] - a[0]));
    return [a[1] + (b[1] - a[1]) * q, a[2] + (b[2] - a[2]) * q];
  }
  return keys[keys.length - 1].slice(1);
};

const Lens = ({keys}) => {
  const t = useT();
  if (t < keys[0][0] || t > keys[keys.length - 1][0]) return null;
  const [x, y] = glide(keys, t);
  return <g transform={`translate(${x} ${y})`}>
    <line x1={72} y1={72} x2={170} y2={170} stroke="#3C3228" opacity={0.25} strokeWidth={20} strokeLinecap="round" style={{filter: "blur(10px)"}} transform="translate(14 18)"/>
    <circle r={96} fill="#FFFFFF" fillOpacity={0.16} stroke={INK} strokeWidth={7}/>
    <line x1={70} y1={70} x2={170} y2={170} stroke={INK} strokeWidth={16} strokeLinecap="round"/>
  </g>;
};

const Sources = () => {
  const x = 19200, y = 1080, t = useT();
  const note = [["Most authors work for", 257.0, INK], ["Insilico Medicine,", 258.4, INK], ["which built its AI tools.", 259.6, INK], ["They say so openly.", 262.2, SOFT], ["Useful evidence,", 264.2, DARK], ["not an independent check.", 265.0, DARK]];
  return <g>
    <Ink x={x + 760} y={y + 160} size={72} at={212.4} font={SERIF} w={520} dur={0.7}>Literature review</Ink>
    <Ink x={x + 1270} y={y + 160} size={40} at={213.8} weight={500} fill={SOFT} w={520}>no lab work of our own</Ink>
    {CARDS.map((c, i) => <Card key={i} c={c} i={i}/>)}
    <Paper/>
    <Ink x={x + 760} y={y + 830} size={40} at={243.0} w={1000} dur={1.2}>What kind? How much did we read?</Ink>
    <Ink x={x + 760} y={y + 884} size={40} at={246.4} w={1000} dur={0.9}>How strong is the evidence?</Ink>
    <Ink x={x + 760} y={y + 938} size={40} at={249.4} w={1000} dur={1.6}>Who did the work? Controls and repeats?</Ink>
    <Lens keys={[[242.4, 21300, 1200], [243.4, 20220, 1365], [245.0, 20760, 1365], [246.6, 20220, 1551], [248.2, 20760, 1551], [249.4, 21300, 1560]]}/>
    <Lens keys={[[248.6, 19800, 2300], [249.6, 20220, 1737], [251.2, 20760, 1737], [252.6, 21300, 1800]]}/>
    <Source x={x + 760} y={y + 996} at={225.0} until={254.4}>Ren 2023 · Feng 2011 · Jumper 2021 · Ivanenkov 2023 · Wang 2023 · Lengauer 2007 · Bender 2026</Source>
    {note.map(([s, at, c], i) => <Ink key={i} x={19270} y={1486 + i * 34 + (i > 2 ? 18 : 0) + (i > 3 ? 18 : 0)} size={21} at={at} anchor="end" fill={c} w={300}>{s}</Ink>)}
  </g>;
};

const Route = () => {
  const r = TL.world.road, t = useT();
  return <g>
    {[272.0, 274.2, 276.6].map((at, i) => { const p = smooth((t - at) / 0.7);
      return p > 0 ? <circle key={i} cx={r[i][0]} cy={r[i][1]} r={84} fill="none" stroke={RED} strokeWidth={7} strokeDasharray={528} strokeDashoffset={528 * (1 - p)} transform={`rotate(-90 ${r[i][0]} ${r[i][1]})`}/> : null; })}
    <Ink x={(r[0][0] + r[2][0]) / 2} y={350} size={84} at={272.2} font={SERIF} fill={RED} anchor="middle" w={520} dur={0.8}>today's route</Ink>
  </g>;
};

// ---------------------------------------------------------------- what lives in screen space
const Title = () => {
  const t = useT(), at = 125.6, land = clamp((t - at) / 0.1), k = 1 + 0.05 * (1 - out((t - at) / 0.3));
  return t < at || t > 142.2 ? null : <g opacity={1 - after(t, 141.0, 1.2)}>
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
  [141, 174, "A", "Hong Kong first. In 2011, a team at the Chinese University of Hong Kong studied liver tumours from patients at the Prince of Wales Hospital. One protein kept showing up raised: CCRK, also called CDK20. Fast forward to 2023: an AI drug-discovery study goes after the same protein, with co-authors at Insilico Medicine's Hong Kong office in Science Park."],
  [174, 184, "A · on camera", "So our research question is: how can computer-aided methods help scientists find and assess potential cancer drug candidates?"],
  [184, 190, "A", "And we'll answer it with one case study: CDK20 in liver cancer."],
  [190, 193, "C · on camera", "We set ourselves two objectives."],
  [193, 208, "C", "One: to identify the major computer-aided methods used in cancer drug discovery. Two: to evaluate how these methods help scientists assess potential drug candidates."],
  [208, 242, "C", "So how did we check all this? We read. A lot. No lab work of our own: this is a literature review. At the centre, one original study by Ren and colleagues in Chemical Science, 2023, with its supplementary data. Around it, the earlier Hong Kong study, papers behind two AI tools, a 2023 review, a textbook chapter, and a 2026 expert Perspective, which we read only as an abstract."],
  [242, 268, "D", "For every source, we asked: what kind is it, how much did we read, and how strong is the evidence? Who did the work? Were there controls and repeats? One thing worth knowing: most authors of the main study work for Insilico Medicine, which built its AI tools. They say so openly. Useful evidence, not an independent check."],
  [268, 281, "A", "So here's where we're going. First, the lock. Then how AI helped cut a key for it. Then what happened in the lab. And finally, the big one: how much did the computers really help?"],
];

const Review = () => {
  const t = useT(), l = LINES.find(([a, b]) => t >= a && t < b);
  return l ? <div style={{position: "absolute", left: 120, right: 120, top: 22, textAlign: "center", fontFamily: SANS, fontWeight: 500, fontSize: 24, lineHeight: 1.3, color: SOFT}}><b style={{color: INK}}>{l[2]}</b>  {l[3]}</div> : null;
};

// ---------------------------------------------------------------- the frame
const S1 = ({review = true, base = true, clear = false, file = "fusion_s1/base.mp4", start = 0}) => {
  const f = useCurrentFrame(), t = TL.u[f], [cx, cy, z] = TL.cam[f];
  return <Clock.Provider value={t}><Zoom.Provider value={z}>
    <AbsoluteFill style={{background: clear ? "transparent" : BONE}}>
      {base && <Sequence from={start} layout="none"><OffthreadVideo src={staticFile(file)} muted/></Sequence>}
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
        <g transform={`translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})`}>
          <Liver/><Drugs/><Ruler/><Cost/><Road/><Protein/><Stories/><Question/><Objectives/><Sources/><Route/>
          <Print who="A" x={96} y={84} w={760} h={912} at={2.15} rot={-1.2}/>
          <Print who="A" x={ST1 + 96} y={84} w={760} h={912} at={25.05} rot={0.9}/>
          <Print who="D" x={5840} y={170} w={500} h={600} at={52.05} rot={-1.5}/>
          <Print who="B" x={6430} y={170} w={500} h={600} at={55.0} rot={1.0}/>
          <Print who="C" x={7020} y={170} w={500} h={600} at={58.0} rot={-0.8}/>
          <Print who="A" x={15456} y={1164} w={760} h={912} at={174.9} rot={-0.9}/>
          <Pin xy={TL.world.pwh} at={119.8}>Sha Tin</Pin>
          <Pin xy={TL.world.hkstp} at={122.0}>Pak Shek Kok</Pin>
        </g>
        <Title/>
        {t > 113.4 && t < 123.2 && <text x={96} y={1050} fontFamily={SANS} fontSize={26} fontWeight={500} fill={SOFT} opacity={after(t, 113.4)}>© OpenStreetMap contributors</text>}
        {t > 143.6 && t < 173.6 && <text x={1824} y={1050} textAnchor="end" fontFamily={SANS} fontSize={26} fontWeight={500} fill={SOFT} opacity={after(t, 143.6) * (1 - after(t, 172.6))}>© OpenStreetMap contributors</text>}
      </svg>
      {review && <Review/>}
    </AbsoluteFill>
  </Zoom.Provider></Clock.Provider>;
};

/** W3: the dots come from TouchDesigner (镜头设计_v3/td/w3); the count is the number that have really landed. */
const W3 = ({file = "fusion_s1/w3_td.mp4"}) => {
  const f = useCurrentFrame(), t = f / 60, n = W3C.count[Math.min(f, W3C.count.length - 1)], land = 7 * 15.7 / 8, done = t >= land;
  const k = 1 + 0.06 * (1 - out((t - land) / 0.4)) * (done ? 1 : 0);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      {n > 0 && <text transform={`translate(960 610) scale(${k})`} textAnchor="middle" fontFamily={SERIF} fontSize={210} fill={done ? RED : INK}>{n.toLocaleString("en-US")}</text>}
      <Ink x={960} y={680} size={44} at={land + 0.2} anchor="middle" w={420}>brand-new designs</Ink>
      <Tag kind="schematic" x={850} y={746} at={land + 0.6}>schematic</Tag>
      <Source x={906} y={796} at={land + 0.6}>Ren 2023</Source>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

const WALL_LINES = [[0, "brand-new designs"], [3, "way too many to make"], [5.6, "tried in a virtual lock"], [8.4, "docking: a predicted fit"], [14.6, "similar designs grouped"], [17.4, "the shortlist"], [20.8, "picked to make"]];
const between = (t, a, b, from, to) => Math.round(from * Math.pow(to / from, smooth((t - a) / (b - a))));

/** 4-10: picks up the W3 wall; 8,918, 54 and 7 are the paper's, the groups are drawn. */
const Wall = ({file = "fusion_s1/wall_td.mp4"}) => {
  const t = useCurrentFrame() / 60;
  const n = t < 20.8 ? between(t, 17.4, 19.2, 8918, 54) : between(t, 20.8, 21.8, 54, 7);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <text x={960} y={610} textAnchor="middle" fontFamily={SERIF} fontSize={210} fill={RED}>{n.toLocaleString("en-US")}</text>
      {WALL_LINES.map(([at, line], i) => <text key={at} x={960} y={680} textAnchor="middle" fontFamily={SANS} fontSize={44} fontWeight={600} fill={INK} opacity={(at ? after(t, at) : 1) * (1 - after(t, WALL_LINES[i + 1]?.[0] ?? 1e9))}>{line}</text>)}
      <Tag kind="schematic" x={850} y={746} at={-1}>schematic</Tag>
      <Source x={906} y={796} at={-1}>Ren 2023</Source>
      <rect x={48} y={50} width={592} height={62} fill={BONE} opacity={0.94 * after(t, 5.4)}/>
      <Ink x={64} y={92} size={36} at={5.6} w={640}>Tool: docking / virtual screening</Ink>
      <Ink x={820} y={1006} size={44} at={17.4} w={160}>8,918</Ink>
      <Ink x={946} y={1006} size={44} at={18.6} w={140}>→ 54</Ink>
      <Ink x={1046} y={1006} size={44} at={20.8} w={120}>→ 7</Ink>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

const LOOP_SPOTS = [["invent", 960, 214, 10.4, "middle"], ["score", 1270, 552, 12.4, "start"], ["learn", 960, 900, 13.8, "middle"], ["go again", 650, 552, 15.0, "end"]];

/** 4-07: the dots come from TouchDesigner; the words are the voice-over's, and they leave once the loop is too fast to read. */
const Loop = ({file = "fusion_s1/loop_td_1.mp4"}) => {
  const t = useCurrentFrame() / 60, words = 1 - after(t, 18, 1), name = after(t, 4.4) * (1 - after(t, 9.6)), hours = after(t, 18.6);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <circle cx={960} cy={540} r={262} fill="none" stroke={SOFT} strokeWidth={2} opacity={0.3 * (1 - after(t, 14, 3))}/>
      <Ink x={64} y={92} size={36} at={0.6} w={560}>Tool: generative design</Ink>
      {LOOP_SPOTS.map(([word, x, y, at, anchor]) => <text key={word} x={x} y={y} textAnchor={anchor} fontFamily={SANS} fontSize={44} fontWeight={600} fill={INK} opacity={after(t, at) * words}>{word}</text>)}
      <g opacity={name} textAnchor="middle">
        <text x={960} y={530} fontFamily={SERIF} fontSize={84} fill={INK}>Chemistry42</text>
        <text x={960} y={590} fontFamily={SANS} fontSize={36} fontWeight={600} fill={SOFT}>dozens of AI models</text>
      </g>
      <g opacity={hours} textAnchor="middle">
        <text x={960} y={530} fontFamily={SERIF} fontSize={72} fill={RED}>within hours</text>
        <text x={960} y={590} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK}>its makers say</text>
        <text x={960} y={636} fontFamily={SANS} fontSize={26} fontWeight={500} fill={SOFT}>Ivanenkov 2023</text>
      </g>
      <Tag kind="schematic" x={1650} y={78} at={0.6}>schematic</Tag>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

/** W2: the one label the script asks for, once the light has reached the corner. */
const W2 = ({file = "fusion_s1/w2_td_1.mp4"}) => <Clock.Provider value={useCurrentFrame() / 60}><AbsoluteFill style={{background: BONE}}>
  <OffthreadVideo src={staticFile(file)} muted/>
  <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
    <Tag kind="predicted" x={96} y={1000} at={21.2} size={36}>AlphaFold DB v6 · predicted</Tag>
  </svg>
</AbsoluteFill></Clock.Provider>;

/** S3 test boards: the beats that have to read in five seconds. Numbers are Feng 2011's; the grid's cells are drawn, so it carries schematic. */
const Tally = () => <g transform="translate(0 110)">
  {Array.from({length: 52}, (_, i) => <rect key={i} x={250 + (i % 26) * 54} y={i < 26 ? 300 : 450} width={26} height={120} rx={13} fill={i < 36 ? RED : "#D4D1C8"}/>)}
  <text x={250} y={210} fontFamily={SERIF} fontSize={150} fill={RED}>36 of 52</text>
  <text x={810} y={210} fontFamily={SERIF} fontSize={150} fill={INK}>= 69%</text>
  <text x={250} y={650} fontFamily={SANS} fontSize={44} fontWeight={600} fill={INK}>liver tumours with more CDK20 than the tissue next to them</text>
  <text x={250} y={770} fontFamily={SANS} fontSize={44} fontWeight={600} fill={DARK}>→ later stage</text>
  <text x={700} y={770} fontFamily={SANS} fontSize={44} fontWeight={600} fill={DARK}>→ shorter survival</text>
  <Source x={250} y={850} at={-1}>Feng 2011</Source>
</g>;

const SEEN = new Set([3, 17, 26, 34]);
const Blanks = () => <g>
  {Array.from({length: 45}, (_, i) => {
    const x = 170 + (i % 9) * 174, y = 120 + Math.floor(i / 9) * 140;
    return <g key={i}>
      <rect x={x} y={y} width={150} height={118} rx={14} fill="none" stroke="#C9C6BC" strokeWidth={3} strokeDasharray={SEEN.has(i) ? "none" : "9 9"}/>
      {SEEN.has(i) && <ellipse cx={x + 75} cy={y + 59} rx={44 + i % 5 * 3} ry={34} fill={KLEIN}/>}
    </g>;
  })}
  <rect x={170 + 4 * 174} y={120 + 2 * 140} width={150} height={118} rx={14} fill={BONE} stroke={RED} strokeWidth={4}/>
  <text x={170 + 4 * 174 + 75} y={120 + 2 * 140 + 72} textAnchor="middle" fontFamily={SANS} fontSize={36} fontWeight={700} fill={RED}>CDK20</text>
  <text x={960} y={896} textAnchor="middle" fontFamily={SERIF} fontSize={72} fill={INK}>no one had measured its shape</text>
  <Tag kind="schematic" x={850} y={960} at={-1}>schematic</Tag>
  <Source x={906} y={1010} at={-1}>Ren 2023</Source>
</g>;

/** 3-07: the paper never prints the 20 names, so only CDK20's row carries one. */
const List = () => <g>
  <text x={170} y={190} fontFamily={SERIF} fontSize={120} fill={INK}>top 20 targets</text>
  {Array.from({length: 20}, (_, i) => {
    const x = 170 + Math.floor(i / 10) * 830, y = 300 + (i % 10) * 60;
    return i ? <rect key={i} x={x} y={y - 25} width={750} height={28} rx={14} fill="#D4D1C8"/> :
      <text key={i} x={x} y={y + 4} fontFamily={SANS} fontSize={48} fontWeight={700} fill={RED}>CDK20</text>;
  })}
  <ellipse cx={250} cy={286} rx={124} ry={41} fill="none" stroke={RED} strokeWidth={4}/>
  <Tag kind="schematic" x={170} y={960} at={-1}>schematic</Tag>
  <Source x={170} y={1020} at={-1}>the other 19 names are not in the paper · Ren 2023</Source>
</g>;

const S3Board = ({beat = "tally"}) => <Clock.Provider value={99}><AbsoluteFill style={{background: BONE}}>
  <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
    {{tally: <Tally/>, blanks: <Blanks/>, list: <List/>}[beat]}
  </svg>
</AbsoluteFill></Clock.Provider>;

const Root = () => <>
  <Composition id="S3Board" component={S3Board} durationInFrames={1} fps={60} width={W} height={H}/>
  <Composition id="S1Fusion" component={S1} durationInFrames={N} fps={FPS} width={W} height={H} defaultProps={{review: true, base: true}}/>
  <Composition id="W3" component={W3} durationInFrames={942} fps={60} width={W} height={H}/>
  <Composition id="Wall" component={Wall} durationInFrames={1500} fps={60} width={W} height={H}/>
  <Composition id="W2" component={W2} durationInFrames={1500} fps={60} width={W} height={H}/>
  <Composition id="Loop" component={Loop} durationInFrames={1620} fps={60} width={W} height={H}/>
</>;
registerRoot(Root);
