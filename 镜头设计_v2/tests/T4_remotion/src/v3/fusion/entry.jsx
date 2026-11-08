// HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: type, marks and photo prints on the table.
// The picture under it (base.mp4) comes from 镜头设计_v3/styleframes/art/fusion/s1/code/base.py. Both read the same camera, so everything here is placed in table coordinates and moves with the table.
// Words on screen follow script_v3.3.md. Times are seconds on the script's clock, the same as timeline.py; TL.u turns each frame of the film into that clock, from 节奏表.csv. Props: review shows the script line along the top; base=false leaves the type on bone for quick stills.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import TL from "./s1_timeline.json";
import W3C from "./w3_count.json";
import HK from "./hk_track.json";

const FPS = TL.fps, N = TL.n, W = 1920, H = 1080;
const INK = "#111113", SOFT = "#545458", RED = "#E8190F", DARK = "#9A0E08", KLEIN = "#002FA7", BONE = "#EDEBE4";
const SERIF = "Instrument Serif", SANS = "Inter Tight", HAND = "Caveat", ZH = "Noto Serif SC";

const faces = [new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Regular.ttf")})`), new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Italic.ttf")})`, {style: "italic"}), new FontFace(SANS, `url(${staticFile("fusion_s1/fonts/InterTight.ttf")})`, {weight: "100 900"}), new FontFace(HAND, `url(${staticFile("fusion_s1/fonts/Caveat.ttf")})`, {weight: "400 700"}), new FontFace(ZH, `url(${staticFile("fusion_s1/fonts/NotoSerifSC-VF.ttf")})`, {weight: "200 900"})];
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

const ruler = document.createElement("canvas").getContext("2d");
/** A serif line with its key words in italic; a red rule draws under them once the line has printed. parts is the words before, the key words, the words after. */
const Keyed = ({x, y, size, at, dur = 1.2, fill = INK, w = 1000, parts: [a, key, b = ""]}) => {
  const t = useT(), p = smooth((t - at - dur) / 0.5), k = size / 66;
  ruler.font = `400 ${size}px "${SERIF}"`;
  const x0 = x + ruler.measureText(a).width;
  ruler.font = `italic 400 ${size}px "${SERIF}"`;
  const len = ruler.measureText(key).width;
  return <g>
    <Ink x={x} y={y} size={size} at={at} font={SERIF} fill={fill} w={w} dur={dur}>{a}<tspan fontStyle="italic">{key}</tspan>{b}</Ink>
    {p > 0 && <rect x={x0} y={y + 13 * k} width={len * p} height={5 * k} fill={RED}/>}
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

/** AI-predicted structures carry a dashed circle. Drawn scenes wear no mark: their source line starts with Illustration. */
const Tag = ({x, y, at, size = 30, children}) => {
  const t = useT(), a = after(t, at);
  if (a <= 0) return null;
  const r = size / 2, cx = x + r, cy = y - size * 0.36;
  return <g opacity={a}>
    <circle cx={cx} cy={cy} r={r} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
    <text x={x + size * 1.45} y={y} fontFamily={SANS} fontSize={size} fontWeight={600} fill={INK}>{children}</text>
  </g>;
};

/** A pen note in Caveat, written on the table like a margin note: slightly tilted, appearing left to right at writing speed. The hand has no arrow, so each "→" in the text is drawn as a pen stroke. */
const Note = ({x, y, size, at, fill = DARK, anchor = "start", rot = -2, dur, children}) => {
  const t = useT(), text = String(children), p = smooth((t - at) / (dur || 0.3 + text.length * 0.03));
  const id = React.useMemo(() => `pen${wipeId++}`, []);
  if (p <= 0) return null;
  ruler.font = `600 ${size}px "${HAND}"`;
  const gap = size * 0.22, len = size * 0.95, bits = [];
  text.split("→").forEach((s, i, all) => {
    if (s.trim()) bits.push({s: s.trim(), w: ruler.measureText(s.trim()).width});
    if (i < all.length - 1) bits.push({w: len});
  });
  const total = bits.reduce((s, b) => s + b.w, 0) + gap * (bits.length - 1);
  const left = anchor === "start" ? x : anchor === "end" ? x - total : x - total / 2;
  let cx = left;
  const marks = bits.map((b, i) => {
    const a = cx;
    cx += b.w + gap;
    if (b.s) return <text key={i} x={a} y={y} fontFamily={HAND} fontSize={size} fontWeight={600} fill={fill}>{b.s}</text>;
    const h = y - size * 0.26, k = size * 0.2;
    return <path key={i} d={`M${a} ${h + 2} Q${a + b.w * 0.5} ${h - 3} ${a + b.w} ${h} M${a + b.w - k} ${h - k * 0.8} L${a + b.w} ${h} L${a + b.w - k * 0.95} ${h + k * 0.75}`} fill="none" stroke={fill} strokeWidth={size * 0.065} strokeLinecap="round" strokeLinejoin="round"/>;
  });
  return <g transform={`rotate(${rot} ${x} ${y})`}>
    <clipPath id={id}><rect x={left - 10} y={y - size * 1.1} width={(total + 20) * p} height={size * 1.5}/></clipPath>
    <g clipPath={`url(#${id})`}>{marks}</g>
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
    <g opacity={1 - after(t, 24.7, 0.3)}>{/* clears the column before A's print lands, so print and figure never touch */}
      <Ink x={x + 96} y={460} size={250} at={8.9} font={SERIF} fill={RED} w={760} dur={0.7}>1,412</Ink>
      <Ink x={x + 104} y={546} size={70} at={9.7} font={SERIF} w={760}>deaths in Hong Kong, 2022</Ink>
      <Note x={x + 340} y={668} size={48} at={11.0} fill={DARK}>about four a day</Note>
      <Ink x={x + 104} y={760} size={56} at={13.0} font={SERIF} w={760}>Top 3 deadliest in HK</Ink>
      <Note x={x + 104} y={808} size={48} at={13.5}>lung · colorectal · liver</Note>
      <Ink x={x + 104} y={878} size={56} at={20.0} font={SERIF} w={760}>World: 6th most common</Ink>
      <Ink x={x + 104} y={938} size={56} at={20.8} font={SERIF} w={760}>3rd deadliest</Ink>
    </g>
    <Leader pts={[[x + 1262, 700], [x + 1176, 862], [x + 1146, 862]]} at={12.6} fill={RED}/>
    <Note x={x + 1134} y={875} size={53} at={13.0} fill={DARK} anchor="end">portal vein</Note>
    <Leader pts={[[x + 1184, 296], [x + 1240, 110], [x + 1300, 110]]} at={16.6} fill={KLEIN}/>
    <Note x={x + 1310} y={123} size={53} at={17.0} fill={KLEIN}>hepatic veins</Note>
    <Leader pts={[[x + 1640, 352], [x + 1640, 196], [x + 1696, 196]]} at={18.6}/>
    <Note x={x + 1708} y={209} size={53} at={19.0}>liver</Note>
    {a > 0 && <g opacity={a}>
      {tan.map((s, i) => <line key={i} x1={s[0][0]} y1={s[0][1]} x2={s[1][0]} y2={s[1][1]} stroke={INK} strokeWidth={1.5}/>)}
      <circle cx={ring[0]} cy={ring[1]} r={rr} fill="none" stroke={INK} strokeWidth={2.5}/>
    </g>}
    <clipPath id="lensclip"><circle cx={lc[0]} cy={lc[1]} r={lr - 4}/></clipPath>
    <g clipPath="url(#lensclip)">
      {cells.slice(0, 12).map(([, cx, cy], i) => { const c = smooth((t - 22.4 - i * 0.08) / 0.5);
        return c > 0 ? <g key={i} opacity={c}><polygon points={hex(lc[0] + cx, lc[1] + cy, 51)} fill="#DDD9CE" strokeLinejoin="round"/><circle cx={lc[0] + cx} cy={lc[1] + cy} r={15} fill="#BCB7AA"/></g> : null; })}
    </g>
    <Source x={x + 96} y={1062} at={9.8}>Illustration · HKCaR 2022 · GLOBOCAN 2020 · BodyParts3D, DBCLS, CC BY 4.0</Source>
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
    <Note x={x + 1100} y={540} size={48} at={37.0} fill={DARK} anchor="middle">first-line, advanced HCC</Note>
    <Ink x={x + 96} y={730} size={170} at={46.2} font={SERIF} fill={RED} w={620} dur={0.6}>~3 in 10</Ink>
    <Ink x={x + 660} y={680} size={64} at={46.8} font={SERIF} w={760}>5-year relative survival</Ink>
    <Note x={x + 660} y={730} size={48} at={47.2} fill={DARK}>HK, 2010-2021</Note>
    <Source x={x + 96} y={1062} at={33.0}>Illustration · Ren 2023 · HKCaR 2022</Source>
  </g>;
};

const Ruler = () => {
  const t = useT(), [x0, x1, y] = TL.world.ruler, st = (x1 - x0) / 17;
    const yrs = [...Array(18).keys()];
  return <g>
    {yrs.map(i => { const a = clamp((t - 59.9 - i * (5.5 / 17)) / 0.25), big = i === 0 || i === 10 || i === 17;
      return a > 0 ? <line key={i} x1={x0 + i * st} y1={y + 18} x2={x0 + i * st} y2={y + 18 + (big ? 44 : 22) * a} stroke={INK} strokeWidth={big ? 3 : 2}/> : null; })}
    <Ink x={x0 + 10 * st} y={y + 104} size={60} at={63.2} font={SERIF} anchor="middle" w={100}>10</Ink>
    <Ink x={x0 + 17 * st} y={y + 104} size={60} at={65.4} font={SERIF} anchor="middle" w={100}>17</Ink>
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
    <Source x={x0 + 30} y={y + 200} at={60.6}>Illustration · Wang 2023</Source>
  </g>;
};

const Cost = () => {
  const x = ST5;
  return <g>
    <Ink x={x + 96} y={420} size={190} at={67.2} font={SERIF} fill={RED} w={1100} dur={0.8}>~US$2.8 billion</Ink>
    <Ink x={x + 96} y={784} size={84} at={73.0} font={SERIF} w={900} dur={0.7}>about 1 in 10</Ink>
    <Keyed x={x + 96} y={856} size={62} at={73.6} w={1100} parts={["of drugs tested in people ", "reaches the market"]}/>
    <Source x={x + 96} y={1062} at={67.2}>Illustration · Wang 2023</Source>
  </g>;
};

const Road = () => {
  const r = TL.world.road, t = useT();
  const names = [[80.7, ["Target"]], [81.9, ["Hit"]], [84.3, ["Improve"]], [85.6, ["Cells & animals"]], [88.1, ["Clinical trials", "1-2-3"]], [91.6, ["Approval"]]];
  return <g>
    {names.map(([at, lines], i) => <g key={i}>
      {lines.map((s, j) => <Note key={j} x={r[i][0]} y={670 + j * 46} size={53} at={at + j * 0.9} anchor="middle">{s}</Note>)}
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
    <Note x={x + 1450} y={y + 900} size={48} at={101.2}>Demis Hassabis</Note>
    <Note x={x + 1450} y={y + 944} size={48} at={101.8}>John Jumper</Note>
    <Tag x={x + 96} y={y + 1012} at={99.0}>AlphaFold DB v6 · predicted</Tag>
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
    <Ink x={14040} y={1442} size={56 * K3} at={144.2} font={SERIF} w={260}>Chinese University of Hong Kong</Ink>
    <Ink x={14040} y={1464} size={56 * K3} at={145.2} font={SERIF} w={260}>Prince of Wales Hospital</Ink>
    <Note x={14040} y={1486} size={48 * K3} at={146.4} fill={DARK}>liver tumours from patients</Note>
    <Ink x={14040} y={1546} size={120 * K3} at={153.0} font={SERIF} fill={DARK} w={320} dur={0.8}>CCRK = CDK20</Ink>
    <Source x={14040} y={1712} at={146.4} until={158.4} size={27 * K3}>Illustration · Feng 2011</Source>
    <Ink x={14446} y={1476} size={84 * K3} at={158.8} font={SERIF} fill={RED} w={100}>2023</Ink>
    <Ink x={14446} y={1502} size={56 * K3} at={160.6} font={SERIF} w={240}>AI drug-discovery study</Ink>
    <Note x={14446} y={1522} size={48 * K3} at={162.2} fill={DARK}>the same protein</Note>
    <Ink x={14446} y={1546} size={56 * K3} at={166.0} font={SERIF} w={240}>Insilico Medicine, Hong Kong</Ink>
    <Note x={14446} y={1566} size={48 * K3} at={168.6} fill={DARK}>Science Park</Note>
    <Source x={14060} y={1622} at={166.0} until={172.8} size={27 * K3}>Ren 2023</Source>
  </g>;
};

const Question = () => {
  const x = 15360, y = 1080;
  return <g>
    <Note x={x + 960} y={y + 210} size={58} at={175.8} fill={DARK}>Our research question</Note>
    {["How can computer-aided", "methods help scientists", "find and assess potential", "cancer drug candidates?"].map((s, i) =>
      <Ink key={i} x={x + 960} y={y + 320 + i * 96} size={84} at={177.0 + i * 1.6} font={SERIF} w={900} dur={1.5}>{s}</Ink>)}
    <Keyed x={x + 960} y={y + 760} size={64} at={184.8} fill={DARK} w={900} dur={1.0} parts={["A case study of ", "CDK20 in liver cancer"]}/>
  </g>;
};

const OBJ_KEY = ["computer-aided methods", "potential drug candidates"];
const OBJ = [["Identify the major", "computer-aided methods", "used in cancer drug discovery"], ["Evaluate how these methods", "help scientists assess", "potential drug candidates"]];
const Objectives = () => {
  const x = 17280, y = 1080, t = useT(), gone = 1 - smooth((t - 206.0) / 0.6), tags = smooth((t - 206.4) / 0.6);
  return <g>
    <Print who="C" x={x + 96} y={y + 168} w={620} h={744} at={190.05} rot={-0.9}/>
    <g opacity={gone}>
      {OBJ.map((lines, i) => <g key={i}>
        <Ink x={x + 800} y={y + 340 + i * 380} size={170} at={190.6 + i * 0.5} font={SERIF} fill={RED} w={110}>{i + 1}</Ink>
        {lines.map((s, j) => { const line = {x: x + 930, y: y + 214 + i * 380 + j * 74, size: 66, at: (i ? 199.6 : 193.4) + j * 1.4, w: 860, dur: 1.2};
          return OBJ_KEY.includes(s) ? <Keyed key={j} {...line} parts={["", s]}/> : <Ink key={j} {...line} font={SERIF}>{s}</Ink>; })}
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
    <Note x={x + 1270} y={y + 160} size={53} at={213.8} fill={DARK}>no lab work of our own</Note>
    {CARDS.map((c, i) => <Card key={i} c={c} i={i}/>)}
    <Paper/>
    <Ink x={x + 760} y={y + 826} size={56} at={243.0} font={SERIF} w={1000} dur={1.2}>What kind? How much did we read?</Ink>
    <Ink x={x + 760} y={y + 886} size={56} at={246.4} font={SERIF} w={1000} dur={0.9}>How strong is the evidence?</Ink>
    <Ink x={x + 760} y={y + 946} size={56} at={249.4} font={SERIF} w={1000} dur={1.6}>Who did the work? Controls and repeats?</Ink>
    <Lens keys={[[242.4, 21300, 1200], [243.4, 20220, 1365], [245.0, 20760, 1365], [246.6, 20220, 1551], [248.2, 20760, 1551], [249.4, 21300, 1560]]}/>
    <Lens keys={[[248.6, 19800, 2300], [249.6, 20220, 1737], [251.2, 20760, 1737], [252.6, 21300, 1800]]}/>
    <Source x={x + 760} y={y + 996} at={225.0} until={254.4}>Ren 2023 · Feng 2011 · Jumper 2021 · Ivanenkov 2023 · Wang 2023 · Lengauer 2007 · Bender 2026</Source>
    {note.map(([s, at, c], i) => <Note key={i} x={19270} y={1486 + i * 34 + (i > 2 ? 18 : 0) + (i > 3 ? 18 : 0)} size={28} at={at} anchor="end" fill={c}>{s}</Note>)}
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
    <text x={960} y={424} textAnchor="middle" fontFamily={SERIF} fontSize={66} fill={INK} opacity={after(t, at + 0.7)}>How computers help find cancer drug candidates: the CDK20 story</text>
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
          <Print who="A" x={ST1 + 72} y={168} w={620} h={744} at={25.05} rot={0.9}/>
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
      <Source x={825} y={746} at={land + 0.6}>Illustration · Ren 2023</Source>
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
      {WALL_LINES.map(([at, line], i) => <text key={at} x={960} y={680} textAnchor="middle" fontFamily={SERIF} fontSize={62} fill={INK} opacity={(at ? after(t, at) : 1) * (1 - after(t, WALL_LINES[i + 1]?.[0] ?? 1e9))}>{line}</text>)}
      <Source x={825} y={746} at={-1}>Illustration · Ren 2023</Source>
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
      <Source x={96} y={1062} at={0.6}>Illustration</Source>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

/** W2: the one label the script asks for, once the light has reached the corner. */
const W2 = ({file = "fusion_s1/w2_td_1.mp4"}) => <Clock.Provider value={useCurrentFrame() / 60}><AbsoluteFill style={{background: BONE}}>
  <OffthreadVideo src={staticFile(file)} muted/>
  <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
    <Tag x={96} y={1000} at={21.2} size={36}>AlphaFold DB v6 · predicted</Tag>
  </svg>
</AbsoluteFill></Clock.Provider>;

/** W2 with its captions, version 3 (the director's notes of 11-04 22:30-22:45: captions only where the song is sung, in its rhythm, simple; then not handwritten).
 * The song starts at 50.446 s, so the first sung bar (52.39 s) lands on beat 4, the spring off the table. In these 13 bars the voice sings three 2-bar phrases:
 * beats 4-11 and 36-43 with a two-syllable word on beats 1 and 3 of the bar, beats 20-27 answering on beats 2 and 4 (found by taking the repeating backing out
 * of the audio, 音乐/W2_押韵字幕.md). Each phrase is four two-syllable words, ours, on the song's pattern: a row of verbs, a row of -er words, then the tail.
 * A word inks on its beat; a phrase floats where the picture is empty and fades two beats after its last word.
 * Set in the film's type, Instrument Serif over Noto Serif SC, the last word italic and coloured (version 2 was hand lettering, Caveat and 方正舒体;
 * the director turned it down on 11-04). Beats count from the start of the shot. */
const W2_BEAT = 60 / 123.477;
const W2_PHRASES = [
  {at: [4, 6, 8, 10], zh: ["猜它", "捏它", "翻它", "转它"], en: ["Guess it,", "squeeze it,", "twist it,", "turn it"], pos: [0.62, 0.78], drift: [20, -16], colour: INK},
  {at: [21, 23, 25, 27], zh: ["慢了", "稳了", "定了", "蓝了"], en: ["Slower,", "calmer,", "firmer,", "bluer."], pos: [0.24, 0.85], drift: [14, -8], colour: KLEIN},
  {at: [36, 38, 40, 42], zh: ["没准？", "甩掉！", "留下", "核心"], en: ["Not sure?", "Shake it!", "Keep the", "core."], pos: [0.75, 0.22], drift: [-16, 12], colour: RED},
];
const W2Phrase = ({t, i}) => {
  const {at, zh, en, pos: [cx, cy], drift: [dx, dy], colour} = W2_PHRASES[i];
  const t0 = at[0] * W2_BEAT, t1 = (at[3] + 2) * W2_BEAT;          // gone two beats after the voice stops
  const vis = clamp((t - t0 + 0.2) / 0.15) * (1 - clamp((t - t1) / 0.3));
  if (vis <= 0) return null;
  const u = clamp((t - t0 + 0.2) / (t1 - t0 + 0.5));
  const fx = cx * W - 520 + dx * u + 5 * Math.sin(1.1 * t + i), fy = cy * H - 70 + dy * u + 6 * Math.sin(1.4 * t + 2 * i);
  const ink = k => { const p = out((t - at[k] * W2_BEAT) / 0.08); return {opacity: p, transform: `translateY(${(1 - p) * 10}px) scale(${0.9 + 0.1 * p})`, display: "inline-block", margin: "0 0.22em"}; };
  const tint = k => k === 3 ? colour : INK;          // the last word carries the colour: blue sure, red the tail
  return <div style={{position: "absolute", left: fx, top: fy, width: 1040, textAlign: "center", opacity: vis, transform: `rotate(${0.8 * Math.sin(0.7 * t + i) - 1.5}deg)`, textShadow: `0 0 10px ${BONE}, 0 0 4px ${BONE}`}}>
    <div style={{fontFamily: ZH, fontWeight: 500, fontSize: 54, letterSpacing: 4, lineHeight: "70px"}}>{zh.map((w, k) => <span key={k} style={{...ink(k), color: tint(k)}}>{w}</span>)}</div>
    <div style={{fontFamily: SERIF, fontSize: 66, lineHeight: "70px"}}>{en.map((w, k) => <span key={k} style={{...ink(k), color: tint(k), fontStyle: k === 3 ? "italic" : "normal"}}>{w}</span>)}</div>
  </div>;
};
const W2Lyrics = ({file = "fusion_s1/w2_shake_3.mp4", fps = 30}) => {
  const t = useCurrentFrame() / fps;
  ruler.font = `600 28px "${SANS}"`;
  const W2_TAG_W = ruler.measureText("AlphaFold DB v6 · predicted").width;          // measured once the fonts are in
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={after(t, 0.3)}>
        <circle cx={W - 72 - W2_TAG_W - 26} cy={1018 - 10} r={14} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
        <text x={W - 72} y={1018} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK} textAnchor="end">AlphaFold DB v6 · predicted</text>
        <text x={W - 72} y={1056} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · motion drawn · structure AlphaFold DB v6 · Ren 2023</text>
      </g>
    </svg>
    {W2_PHRASES.map((_, i) => <W2Phrase key={i} t={t} i={i}/>)}
  </AbsoluteFill></Clock.Provider>;
};

/** 4-01 (07:17-07:43, B's voice-over) over shot i: the coil and then the body turn into a chain of blocks, a light runs along it as the sequence stands up, and each block takes
 * its AlphaFold DB v6 confidence colour. Times follow I_VO in bl_inserts.py (the sentences at 0.39 s a word, until the real recording on 11-12). The corner tag sits top right,
 * because S2's blue pebble crosses the top left. The predicted tag and the source line stay where W2 left them. */
const S401_VO = {ai: 4.4, chain: 7.6, order: 13.6, learned: 16.8, sure: 20.0};
const S401_LINES = [[0, "So the team did something that once sounded like science fiction."], [4.4, "They asked an AI to guess the shape."], [7.6, "Imagine a protein as a chain of building blocks that folds into a 3D shape."], [13.6, "The order of the blocks is the sequence."], [16.8, "AlphaFold learned from known structures how sequences fold."], [20.0, "Give it one, and it predicts the shape, plus how sure it is about each part."]];
/** review: the voice-over line being spoken, small at the bottom left, for judging the timing before the recording exists; off in the film. */
const S401 = ({file = "fusion_s1/s4_401_1.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps, V = S401_VO;
  ruler.font = `600 28px "${SANS}"`;
  const tagW = ruler.measureText("AlphaFold DB v6 · predicted").width;
  const legend = after(t, V.sure + 0.6);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <Ink x={1856} y={92} size={36} at={V.ai + 0.2} anchor="end" w={760}>Objective 1 / Tool: structure prediction</Ink>
      <g opacity={1 - after(t, V.order - 0.6)}><Note x={1180} y={300} size={54} at={V.chain + 1.6} rot={-3}>1 block = 1 amino acid</Note></g>
      <g opacity={1 - after(t, V.sure - 0.4)}><Note x={150} y={860} size={50} at={V.order + 2.6} rot={-2}>the sequence: 346 letters, one per block</Note></g>
      {legend > 0 && <g opacity={legend}>
        <text x={1310} y={196} fontFamily={SANS} fontSize={30} fontWeight={600} fill={INK}>AlphaFold confidence (pLDDT)</text>
        <rect x={1310} y={222} width={30} height={30} rx={8} fill={KLEIN}/>
        <text x={1356} y={247} fontFamily={SANS} fontSize={30} fontWeight={500} fill={INK}>70 and up: sure</text>
        <rect x={1310} y={268} width={30} height={30} rx={8} fill={RED}/>
        <text x={1356} y={293} fontFamily={SANS} fontSize={30} fontWeight={500} fill={INK}>below 70: not sure</text>
      </g>}
      <Note x={860} y={250} size={52} at={V.sure + 3.0} fill={KLEIN} rot={-3}>the body: mostly sure</Note>
      <Note x={1440} y={540} size={52} at={V.sure + 3.8} rot={-2}>the tail: mostly not sure</Note>
      {review && <text x={64} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>VO (B): {[...S401_LINES].reverse().find(([a]) => t >= a)[1]}</text>}
      <g>
        <circle cx={W - 72 - tagW - 26} cy={1018 - 10} r={14} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
        <text x={W - 72} y={1018} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK} textAnchor="end">AlphaFold DB v6 · predicted</text>
        <text x={W - 72} y={1056} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · blocks drawn · structure and confidence AlphaFold DB v6 · Jumper 2021 · Ren 2023</text>
      </g>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

/** 4-02 (07:43-08:00, B's voice-over) over shot i2: the camera climbs over S3's grid, where a few cells hold a shape someone measured in a lab, then comes down to CDK20's cell,
 * which now holds the free prediction. The script's split screen (before / now) happens on the table itself: solid rings for measured shapes, a dashed ring for the prediction
 * (the film's mark for AI-predicted structures). Ring spots are the screen points shot i2 prints for its grid view (frames 216-300). Times follow I2_VO. */
const S402_VO = {now: 3.1, downloaded: 3.6, first: 9.0};
const S402_LINES = [[0, "Before, you'd need a lab-measured structure."], [3.1, "Now?"], [3.6, "The team just downloaded a prediction, for free, from a public database."], [9.0, "According to the paper, this was the first time AlphaFold had been used to find a hit like this."]];
const S402_SEEN = [[791, 218], [1657, 501], [1644, 637], [1425, 743]], S402_CDK = [880, 488];
const Ring = ({x, y, r, at, dashed, fill = INK}) => {
  const t = useT(), p = smooth((t - at) / 0.5), L = 2 * Math.PI * r;
  if (p <= 0) return null;
  return dashed
    ? <circle cx={x} cy={y} r={r} fill="none" stroke={fill} strokeWidth={3} strokeDasharray="10 8" opacity={p}/>
    : <circle cx={x} cy={y} r={r} fill="none" stroke={fill} strokeWidth={3} strokeDasharray={`${L * p} ${L}`} transform={`rotate(-90 ${x} ${y})`}/>;
};
const S402 = ({file = "fusion_s1/s4_402_1.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps, V = S402_VO;
  ruler.font = `600 28px "${SANS}"`;
  const tagW = ruler.measureText("AlphaFold DB v6 · predicted").width;
  const grid = 1 - after(t, 5.0, 0.4);          // the grid labels hold while the camera does, and go before it moves down
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 1 / Tool: structure prediction</text>
      <g opacity={grid}>
        {S402_SEEN.map(([x, y], i) => <Ring key={i} x={x} y={y} r={58} at={1.9 + 0.2 * i}/>)}
        <Ink x={96} y={128} size={56} at={1.7} font={SERIF} w={900} dur={1.0}>Before: a lab-measured structure</Ink>
        <Ink x={96} y={176} size={30} at={2.5} w={700}>only a few proteins have one</Ink>
        <Ring x={S402_CDK[0]} y={S402_CDK[1]} r={70} at={V.now} dashed/>
        <Ink x={820} y={640} size={56} at={V.now + 0.3} font={SERIF} anchor="end" w={760} dur={0.9}>Now: a free AlphaFold prediction</Ink>
        <Ink x={820} y={688} size={30} at={V.downloaded + 0.8} anchor="end" w={600}>downloaded from a public database</Ink>
      </g>
      <Note x={1240} y={330} size={56} at={V.first + 3.6} rot={-3}>a first, says the paper</Note>
      {review && <text x={64} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>VO (B): {[...S402_LINES].reverse().find(([a]) => t >= a)[1]}</text>}
      <g>
        <circle cx={W - 72 - tagW - 26} cy={1018 - 10} r={14} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
        <text x={W - 72} y={1018} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK} textAnchor="end">AlphaFold DB v6 · predicted</text>
        <text x={W - 72} y={1056} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · structure AlphaFold DB v6 · Ren 2023</text>
      </g>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

/** 4-03 (08:00-08:18, B's voice-over) over shot i3: "but look closer". The coil's blocks come up red again, a see-through red copy of the tail runs back across the pocket,
 * and one block, Arg305, lights up inside it. Spots are the screen points shot i3 prints (coil at 4.5 s, Arg305 from 11.4 s on). Times follow I3_VO in bl_inserts.py. */
const S403_VO = {tail: 1.5, model: 6.6, block: 10.4, trust: 14.0};
const S403_LINES = [[0, "But look closer."], [1.5, "One end of the protein, a floppy tail, had really low confidence."], [6.6, "And in the model, it lay across the keyhole, with one building block sitting inside the ATP pocket."], [14.0, "Trust it blindly, and you'd cut keys for a blocked door."]];
const S403_COIL = [1301, 658], S403_ARG = [[11.4, 972, 656], [18.0, 973, 671]];          // Arg305 drifts a little as the camera keeps creeping in
const S403 = ({file = "fusion_s1/s4_403_1.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps, V = S403_VO;
  ruler.font = `600 28px "${SANS}"`;
  const tagW = ruler.measureText("AlphaFold DB v6 · predicted").width;
  const tail = 1 - after(t, V.model + 0.1, 0.4);
  const [[t0, x0, y0], [t1, x1, y1]] = S403_ARG, k = Math.min(1, Math.max(0, (t - t0) / (t1 - t0)));
  const ax = x0 + (x1 - x0) * k, ay = y0 + (y1 - y0) * k, lx = 1500, ly = 760;
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 1 / Tool: structure prediction</text>
      <g opacity={tail}>
        <Note x={S403_COIL[0]} y={S403_COIL[1] - 110} size={52} at={V.tail + 3.0} anchor="middle" rot={-2}>the floppy tail: mostly below 70</Note>
      </g>
      <Leader pts={[[ax, ay], [lx - 20, ly - 18]]} at={V.block + 1.0}/>
      <Ink x={lx} y={ly} size={60} at={V.block + 1.3} font={SERIF} w={300} dur={0.6}>Arg305</Ink>
      <Ink x={lx} y={ly + 44} size={30} at={V.block + 1.8} w={420}>one block of the tail,</Ink>
      <Ink x={lx} y={ly + 82} size={30} at={V.block + 2.2} w={420}>inside the ATP pocket</Ink>
      <Note x={150} y={740} size={56} at={V.trust + 2.4} rot={-3}>a blocked door</Note>
      {review && <text x={64} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>VO (B): {[...S403_LINES].reverse().find(([a]) => t >= a)[1]}</text>}
      <g>
        <circle cx={W - 72 - tagW - 26} cy={1018 - 10} r={14} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
        <text x={W - 72} y={1018} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK} textAnchor="end">AlphaFold DB v6 · predicted</text>
        <text x={W - 72} y={1056} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · ghost and blocks drawn · structure and confidence AlphaFold DB v6 · Ren 2023 Fig. 4A</text>
      </g>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

/** Piece 2 of S4's second half in one review clip (08:00-08:28.5): 4-03 over shot i3, a card where C and B go on camera (4-04, 4-05; footage comes 11-12), then shot i4,
 * back on the table as 4-06 starts: the see-through tail breaks into its blocks and they drift away ("they cut the tail off"). */
const S4B = ({fps = 30, review = true, f403 = "fusion_s1/s4_403_1.mp4", f404 = "fusion_s1/s4_404_1.mp4"}) => {
  const f = useCurrentFrame(), t = f / fps;
  ruler.font = `600 28px "${SANS}"`;
  const tagW = ruler.measureText("AlphaFold DB v6 · predicted").width;
  return <AbsoluteFill style={{background: BONE}}>
    <Sequence durationInFrames={18 * fps}><S403 file={f403} fps={fps} review={review}/></Sequence>
    <Sequence from={18 * fps} durationInFrames={7 * fps}><Clock.Provider value={t - 18}><AbsoluteFill style={{background: BONE}}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        <text x={160} y={380} fontFamily={SANS} fontSize={30} fontWeight={600} fill={SOFT}>08:18 · 4-04 · C on camera (footage comes 11-12)</text>
        <text x={160} y={450} fontFamily={SERIF} fontSize={64} fill={INK}>“So what did they do?”</text>
        <text x={160} y={600} fontFamily={SANS} fontSize={30} fontWeight={600} fill={SOFT}>08:20 · 4-05 · B on camera, ink scissors snip in post</text>
        <text x={160} y={670} fontFamily={SERIF} fontSize={64} fill={INK}>“They cut the tail off. The AI made the guess.</text>
        <text x={160} y={745} fontFamily={SERIF} fontSize={64} fill={INK}>A human caught the problem.”</text>
      </svg>
    </AbsoluteFill></Clock.Provider></Sequence>
    <Sequence from={25 * fps} durationInFrames={3.5 * fps}><AbsoluteFill>
      <OffthreadVideo src={staticFile(f404)} muted style={{width: W, height: H}}/>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
        <text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 1 / Tool: structure prediction</text>
        {review && <text x={64} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>VO (A): And this next part honestly blew my mind.</text>}
        <circle cx={W - 72 - tagW - 26} cy={1018 - 10} r={14} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
        <text x={W - 72} y={1018} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK} textAnchor="end">AlphaFold DB v6 · predicted</text>
        <text x={W - 72} y={1056} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · blocks drawn · structure AlphaFold DB v6 · Ren 2023</text>
      </svg>
    </AbsoluteFill></Sequence>
  </AbsoluteFill>;
};

/** Piece 3 of S4's second half, 4-06 and 4-07 (08:28.5-09:10, A's voice-over), over shot lp. Times are on the 4-06 clock (LP_VO in bl_inserts.py); the shot starts 3.5 s in,
 * where shot i4 ends. The loop's words are written one by one as the turntable brings each thing round, in a row at the top like a pen note; time and money label the clock
 * and the coins; 4-07 swaps the corner tag to generative design. Spots are the screen points shot lp prints. Sources: Lengauer 2007 (lab rounds cost time and money),
 * Ivanenkov 2023 (Chemistry42: 40+ generative models, scores fed back, new structures within hours), Ren 2023. */
const LP = {think: 3.0, imagine: 6.4, make: 7.8, test: 8.7, fails: 9.6, tweak: 10.5, again: 11.4, every: 12.6, ai: 18.0, chem: 23.4, invent: 31.0, hours: 39.2};
const LP_LINES = [[0, "And this next part honestly blew my mind."], [3.0, "Think about how chemists have always found a key."], [6.4, "Imagine a molecule."], [7.8, "Make it."], [8.7, "Test it."], [9.6, "It fails."],
  [10.5, "Tweak it."], [11.4, "Try again."], [12.6, "And every single round in a real lab costs time and money."], [18.0, "Generative AI takes that loop and moves it inside a computer."],
  [23.4, "The platform here, Chemistry42, runs dozens of AI models side by side, built on known chemistry."], [31.0, "They invent new molecules for this exact keyhole, score them, learn from the scores, and go again."],
  [39.2, "Its makers say it turns out new structures within hours."]];
const LP_SPOT = {clock: [340, 514], coins: [1638, 759]};          // printed by shot lp at 13.6 s
const S4C = ({file = "fusion_s1/s4_lp_1.mp4", fps = 30, review = true}) => {
  const t = 3.5 + useCurrentFrame() / fps, V = LP;
  ruler.font = `600 28px "${SANS}"`;
  const tagW = ruler.measureText("AlphaFold DB v6 · predicted").width;
  ruler.font = `600 50px "${HAND}"`;
  const words = [["think", V.imagine], ["make", V.make], ["test", V.test], ["fail", V.fails], ["tweak", V.tweak], ["again", V.again]];
  let x = 96;
  const row = words.map(([w, at], i) => {
    const s = (i ? "→ " : "") + w, at_ = at + 0.15, me = {s, x, at: at_};
    x += ruler.measureText(w).width + (i ? 50 * 1.17 : 0) + 30;          // Note draws the arrow as a stroke 0.95 of the size wide, then a 0.22 gap
    return me;
  });
  const loopRow = 1 - after(t, V.ai + 1.6, 0.5);
  const lab = after(t, V.ai + 0.3, 0.6);
  const [cxk, cyk] = LP_SPOT.clock, [cxc, cyc] = LP_SPOT.coins;
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={1 - lab}><text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 1 / Tool: structure prediction</text></g>
      <g opacity={lab * (1 - after(t, V.hours - 1.0, 0.5))}><text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 1 / Tool: generative design</text></g>
      <g opacity={loopRow}>
        {row.map((r, i) => <Note key={i} x={r.x} y={950} size={50} at={r.at} rot={-1.5}>{r.s}</Note>)}
        <g opacity={1 - after(t, V.every + 5.4, 0.4)}>
          <Note x={cxk} y={cyk + 90} size={46} at={V.every + 3.4} anchor="middle" rot={-2}>time</Note>
          <Note x={cxc} y={cyc + 90} size={46} at={V.every + 4.2} anchor="middle" rot={-2}>money</Note>
        </g>
      </g>
      <g opacity={1 - after(t, V.invent - 0.4, 0.4)}>
        <Ink x={96} y={150} size={56} at={V.chem + 2.4} font={SERIF} w={1000} dur={1.0}>Chemistry42: dozens of AI models, side by side</Ink>
        <Ink x={96} y={196} size={30} at={V.chem + 3.4} w={900}>40+ generative models, built on known chemistry (Ivanenkov 2023)</Ink>
      </g>
      <g opacity={1 - after(t, V.hours, 0.4)}>
        <Note x={96} y={150} size={50} at={V.invent + 1.6} rot={-1.5}>invent → score → learn → again</Note>
      </g>
      <Note x={96} y={992} size={50} at={V.hours + 2.4} rot={-1.5}>new structures within hours, says its maker</Note>
      {review && <text x={64} y={t > V.hours + 1.6 ? 1066 : 1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>VO (A): {[...LP_LINES].reverse().find(([a]) => t >= a)[1]}</text>}
      <g opacity={1 - after(t, V.hours - 0.6, 0.3) + after(t, V.hours + 1.4, 0.4)}>{/* dips while the camera rounds the clock, when the rings pass under it */}
        <circle cx={W - 72 - tagW - 26} cy={1018 - 10} r={14} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
        <text x={W - 72} y={1018} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK} textAnchor="end">AlphaFold DB v6 · predicted</text>
        <text x={W - 72} y={1056} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">{t < V.ai ? "Illustration · lab rounds: Lengauer 2007" : "Illustration · Chemistry42: Ivanenkov 2023 · Ren 2023 · structure AlphaFold DB v6"}</text>
      </g>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

/** 4-09 (09:17-09:34, B's voice-over), over shot hz, version A (the director's 11-05 pick). Times are on the 4-09 clock (HZ_VO in bl_inserts.py). The pocket's patch gets a
 * pen note with a leader; Met84's red patch on the body gets a red pen circle (from the back of the cleft it shows as a red band, so the pen makes the circle), a leader to
 * "must grip here" and the hinge's name; over the screen, a note for what is tossed and then for what is scored. HZ_TRACK is what shot hz prints: t, pocket x y, Met84 x y.
 * Sources: Ren 2023 (pocket-based generation, hinge Met84), Ivanenkov 2023 (medicinal-chemistry filters, drug-likeness, synthetic accessibility); the molecules and scores are drawn. */
const HZ = {shape: 0.0, rule: 2.6, hinge: 3.2, filters: 6.2, toss: 7.4, toxic: 8.6, score: 10.6, easy: 12.4, end: 17.0};
const HZ_LINES = [[0, "The team gave it the pocket's shape"], [2.6, "and one rule: every key must grip a spot called the hinge."],
  [6.2, "Its filters are built to toss designs with reactive or possibly toxic groups,"], [10.6, "and to score how drug-like and easy to make each one is."]];
const HZ_TRACK = [[0.0,902,593,900,594],[0.5,904,589,902,590],[1.0,913,567,907,566],[1.5,923,523,913,520],[2.0,927,495,915,490],[2.5,929,488,916,483],[2.8,939,461,924,457],[3.0,947,436,931,432],[3.2,955,416,938,412],[3.5,958,407,941,403],[5.4,958,403,940,400],[5.5,951,408,934,404],[5.6,910,434,896,428],[5.7,819,476,812,467],[5.8,689,505,691,492],[6.0,468,412,484,399],[6.2,439,229,459,221],[6.4,467,146,487,140]];
const hzAt = (t) => {          // the pocket and Met84 on screen at t, read off HZ_TRACK
  const i = Math.max(0, HZ_TRACK.findIndex(r => r[0] > t) - 1), a = HZ_TRACK[i], b = HZ_TRACK[Math.min(i + 1, HZ_TRACK.length - 1)];
  const u = b[0] > a[0] ? Math.min(1, Math.max(0, (t - a[0]) / (b[0] - a[0]))) : 0;
  return a.slice(1).map((v, k) => v + (b[k + 1] - v) * u);
};
/** A red pen loop drawn round a spot: a slightly uneven ellipse that runs a little past where it started, as a hand would. */
const PenLoop = ({x, y, rx, ry, at, dur = 0.6, rot = -8, fill = RED}) => {
  const t = useT(), p = smooth((t - at) / dur);
  if (p <= 0) return null;
  const pts = [];
  for (let i = 0; i <= 64; i++) {
    const a = -Math.PI * 0.6 + i / 64 * Math.PI * 2.25, w = 1 + 0.05 * Math.sin(3 * a + 0.7) + 0.04 * i / 64;
    pts.push([x + rx * w * Math.cos(a), y + ry * w * Math.sin(a)]);
  }
  const L = pts.slice(1).reduce((s, q, i) => s + Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]), 0);
  return <polyline points={pts.map(q => q.join(",")).join(" ")} fill="none" stroke={fill} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round"
    strokeDasharray={`${L * p} ${L}`} transform={`rotate(${rot} ${x} ${y})`}/>;
};
const S4D = ({file = "fusion_s1/s4_hz_1.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps, V = HZ;
  ruler.font = `600 28px "${SANS}"`;
  const tagW = ruler.measureText("AlphaFold DB v6 · predicted").width;
  const [qx, qy, mx, my] = hzAt(t);
  const pocketNotes = 1 - after(t, V.filters - 0.8, 0.3);
  const lead = (at) => Math.min(1, Math.max(0, (t - at) / 0.35));
  const l1 = lead(V.shape + 2.4), l2 = lead(V.hinge + 0.8);
  const nx = 430, ny = 690, hx = 452, hy = 540;          // the notes sit on the bare table left of the body; the leaders run from each note to its spot
  const ex = mx - 112, ey = my + 8;          // the pen loop's left side
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={after(t, V.filters + 1.6, 0.4) * (1 - after(t, V.easy + 1.6, 0.3)) + after(t, V.end - 0.6, 0.4)}><text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 1 / Tool: generative design</text></g>
      <g opacity={pocketNotes}>
        {l1 > 0 && <line x1={nx + 14} y1={ny - 14} x2={nx + 14 + (qx - 60 - nx - 14) * l1} y2={ny - 14 + (qy + 40 - ny + 14) * l1} stroke={DARK} strokeWidth={3} strokeLinecap="round"/>}
        <Note x={nx} y={ny} size={46} at={V.shape + 2.0} anchor="end" rot={-2}>the pocket's shape</Note>
        <PenLoop x={mx + 4} y={my + 4} rx={118} ry={190} at={V.hinge + 0.4}/>
        {l2 > 0 && <line x1={hx + 14} y1={hy - 14} x2={hx + 14 + (ex - hx - 14) * l2} y2={hy - 14 + (ey - hy + 14) * l2} stroke={DARK} strokeWidth={3} strokeLinecap="round"/>}
        <Note x={hx} y={hy} size={50} at={V.hinge + 1.0} anchor="end" rot={-2}>must grip here</Note>
        <Ink x={hx} y={hy + 46} size={28} at={V.hinge + 1.6} anchor="end" w={420}>the hinge · Met84</Ink>
      </g>
      <g opacity={after(t, V.toss + 0.6, 0.3) * (1 - after(t, V.score - 0.2, 0.4))}>
        <Note x={96} y={100} size={44} at={V.toss + 0.6} rot={-1.5}>out: reactive or possibly toxic groups</Note>
      </g>
      <g opacity={1 - after(t, V.end - 2.2, 0.5)}>
        <Note x={96} y={100} size={44} at={V.score + 0.4} rot={-1.5}>scored: drug-like? easy to make?</Note>
      </g>
      {review && <text x={64} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>VO (B): {[...HZ_LINES].reverse().find(([a]) => t >= a)[1]}</text>}
      {/* the tag and the source line sit bottom right while CDK20 and the table fill the frame; over the screen the rings reach the bottom, so the source line
          moves up under the title, on the bare table along the top (CDK20 is out of view there, so its tag goes) */}
      <g opacity={1 - after(t, V.filters - 0.7, 0.3) + after(t, V.end - 0.5, 0.3)}>
        <circle cx={W - 72 - tagW - 26} cy={986 - 10} r={14} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
        <text x={W - 72} y={986} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK} textAnchor="end">AlphaFold DB v6 · predicted</text>
        {/* two short lines, so in the closing wide view it stays on the table, clear of the screen's corner */}
        <text x={W - 72} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · pocket and hinge Met84: Ren 2023</text>
        <text x={W - 72} y={1054} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">filters: Ivanenkov 2023 · structure AlphaFold DB v6</text>
      </g>
      <g opacity={after(t, V.filters + 1.6, 0.4) * (1 - after(t, V.easy + 1.6, 0.3))}>          {/* gone before the pull-back brings CDK20 up into the top right */}
        <text x={1856} y={136} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · pocket and hinge Met84: Ren 2023</text>
        <text x={1856} y={166} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">filters: Ivanenkov 2023 · structure AlphaFold DB v6</text>
      </g>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

/** 4-09 version K (the director's 11-06 note: everyone must follow it), over shot hk. Same clock and voice-over as S4D. The pocket's outline flies off CDK20 and becomes a
 * keyhole on a plate; its blue dot is Met84, the hinge, and one key rests its tip there; keys from the AI's screen ride a belt through a gate, the ones with a red group go
 * in the bin; two tubes behind each key left fill with its scores. Blue is only the hinge, red only the warning. HK is what shot hk writes (frames/hk_track.json):
 * every 0.1 s, the screen position of each anchor. Sources as S4D; the keys, groups and scores are drawn. */
const HK_AT = (t, k) => {
  const i0 = HK.keys.indexOf(k) * 2 + 1, tr = HK.track;
  const i = Math.max(0, tr.findIndex(r => r[0] > t) - 1), a = tr[i], b = tr[Math.min(i + 1, tr.length - 1)];
  const u = b[0] > a[0] ? Math.min(1, Math.max(0, (t - a[0]) / (b[0] - a[0]))) : 0;
  return [a[i0] + (b[i0] - a[i0]) * u, a[i0 + 1] + (b[i0 + 1] - a[i0 + 1]) * u];
};
const BLUE = "#1F3BFF";
/** A pen line from a note to the thing it names, drawn after the note starts. */
const Pen = ({from, to, at, fill = DARK, dur = 0.35}) => {
  const t = useT(), p = smooth((t - at) / dur);
  if (p <= 0) return null;
  return <line x1={from[0]} y1={from[1]} x2={from[0] + (to[0] - from[0]) * p} y2={from[1] + (to[1] - from[1]) * p} stroke={fill} strokeWidth={3} strokeLinecap="round"/>;
};
/** A dashed pen arrow: the outline came up off the pocket. */
const Lift = ({from, to, at, fill = DARK}) => {
  const t = useT(), p = smooth((t - at) / 0.5);
  if (p <= 0) return null;
  const x = from[0] + (to[0] - from[0]) * p, y = from[1] + (to[1] - from[1]) * p, a = Math.atan2(to[1] - from[1], to[0] - from[0]), k = 18;
  return <g stroke={fill} strokeWidth={3.5} strokeLinecap="round" fill="none">
    <line x1={from[0]} y1={from[1]} x2={x} y2={y} strokeDasharray="12 10"/>
    {p > 0.95 && <path d={`M${x - k * Math.cos(a - 0.45)} ${y - k * Math.sin(a - 0.45)} L${x} ${y} L${x - k * Math.cos(a + 0.45)} ${y - k * Math.sin(a + 0.45)}`}/>}
  </g>;
};
const S4K = ({file = "fusion_s1/s4_hk_1.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps, V = HZ;
  ruler.font = `600 28px "${SANS}"`;
  const tagW = ruler.measureText("AlphaFold DB v6 · predicted").width;
  const red = HK_AT(t, "red"), pk = HK_AT(t, "pk"), ol = HK_AT(t, "ol"), dot = HK_AT(t, "dot"), sign = HK_AT(t, "sign"), bin = HK_AT(t, "bin"), t0 = HK_AT(t, "tube0"), t1 = HK_AT(t, "tube1");
  const win = (a, b, d = 0.3) => after(t, a, d) * (1 - after(t, b, d));
  // note spots: beside what they name, on bare table
  const sx = ol[0] - 300, sy = ol[1] + 10;
  const hx = 1410, hy = dot[1] - 150;          // right of the plate, on bare table: the plate is the figure
  const gx = 170, gy = 112;          // top left, over bare table: in close on the gate the sign, the bin and the belt fill the rest
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={win(0.9, 2.2)}>
        <Note x={sx} y={sy} size={48} at={1.0} anchor="end" rot={-2}>the pocket's shape</Note>
        <Pen from={[sx + 14, sy - 14]} to={[ol[0] - 70, ol[1]]} at={1.5}/>
        <Lift from={pk} to={[ol[0] + 10, ol[1] + 70]} at={1.1}/>
      </g>
      <g opacity={win(V.hinge, V.filters - 0.5)}>
        <Note x={hx} y={hy} size={48} at={V.hinge + 0.2} fill={BLUE} rot={-2}>the hinge · Met84</Note>
        <Pen from={[hx - 10, hy + 10]} to={[dot[0] + 14, dot[1] - 12]} at={V.hinge + 0.5} fill={BLUE}/>
        <Note x={hx} y={hy - 66} size={44} at={3.9} dur={0.7} rot={-2}>every key must grip it</Note>
      </g>
      <g opacity={win(V.filters - 0.5, V.toss + 0.4)}>
        <Note x={1110} y={120} size={46} at={V.filters - 0.45} dur={0.6} rot={-1.5}>the AI makes a key in each lit ring</Note>
      </g>
      <g opacity={win(V.toss, 9.45)}>          {/* gone before the camera leaves the gate at 9.6, or the line runs off the left edge */}
        <Note x={gx} y={gy} size={44} at={7.85} dur={0.8} rot={-1.5}>red group: reactive or possibly toxic</Note>
        <Note x={gx + 40} y={gy + 58} size={44} at={8.15} dur={0.5} rot={-1.5}>→ out, into the bin</Note>
        <g opacity={1 - after(t, 8.05, 0.15)}>          {/* the first key with a red group, circled until it leaves the belt (the track is too coarse to follow the toss) */}
          <PenLoop x={red[0]} y={red[1]} rx={30} ry={26} at={V.toss + 0.1} dur={0.4} fill={DARK}/>
        </g>
      </g>
      <g opacity={win(V.score + 0.3, V.end - 1.6)}>
        {/* blind read 4: two labels with leaders meeting in a V were hard to pair with their tubes, so each label now sits at its own height and drops straight onto its own cap */}
        <Note x={t0[0] - 14} y={t0[1] - 196} size={44} at={V.score + 0.4} dur={0.4} anchor="end" rot={-1.5}>drug-like?</Note>
        <Pen from={[t0[0] - 6, t0[1] - 182]} to={[t0[0], t0[1] - 18]} at={V.score + 1.0}/>
        <Note x={t1[0] + 16} y={t1[1] - 104} size={44} at={V.easy} dur={0.5} rot={-1.5}>easy to make?</Note>
        <Pen from={[t1[0] + 8, t1[1] - 92]} to={[t1[0], t1[1] - 18]} at={V.easy + 0.6}/>
        <Note x={t1[0] + 30} y={t1[1] - 56} size={36} at={V.easy + 1.2} dur={0.5} rot={-1.5}>fuller = better</Note>
      </g>
      <g opacity={win(V.score + 0.2, V.end - 0.9) + after(t, V.end - 0.6, 0.4)}><text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 1 / Tool: generative design</text></g>
      {review && <text x={64} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>VO (B): {[...HZ_LINES].reverse().find(([a]) => t >= a)[1]}</text>}
      <g opacity={1 - after(t, 2.2, 0.3)}>          {/* over the pocket CDK20 fills the bottom of the frame, so the tag sits top right */}
        <circle cx={1856 - tagW - 26} cy={92 - 10} r={14} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
        <text x={1856} y={92} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK} textAnchor="end">AlphaFold DB v6 · predicted</text>
      </g>
      <g opacity={after(t, V.end - 0.5, 0.3)}>
        <circle cx={W - 72 - tagW - 26} cy={986 - 10} r={14} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
        <text x={W - 72} y={986} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK} textAnchor="end">AlphaFold DB v6 · predicted</text>
      </g>
      <g opacity={HK_SRC_LOW(t) * (1 - win(7.75, 9.45, 0.2))}>          {/* off while the camera is in close on the gate, where the belt fills the bottom */}
        <text x={W - 72} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · pocket and hinge Met84: Ren 2023</text>
        <text x={W - 72} y={1054} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">filters: Ivanenkov 2023 · structure AlphaFold DB v6</text>
      </g>
      <g opacity={1 - HK_SRC_LOW(t)}>
        <text x={1856} y={136} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · pocket and hinge Met84: Ren 2023</text>
        <text x={1856} y={166} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">filters: Ivanenkov 2023 · structure AlphaFold DB v6</text>
      </g>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};
const HK_SRC_LOW = (t) => after(t, HZ.filters - 0.75, 0.3);          // top right while CDK20 and then the plate and the screen's rings fill the bottom; bottom right once over the belt

/** S3 test boards: the beats that have to read in five seconds. Numbers are Feng 2011's; the grid's cells are drawn, so its source line says Illustration. */
const Tally = () => <g transform="translate(0 110)">
  {Array.from({length: 52}, (_, i) => <rect key={i} x={250 + (i % 26) * 54} y={i < 26 ? 300 : 450} width={26} height={120} rx={13} fill={i < 36 ? RED : "#D4D1C8"}/>)}
  <text x={250} y={210} fontFamily={SERIF} fontSize={150} fill={RED}>36 of 52</text>
  <text x={810} y={210} fontFamily={SERIF} fontSize={150} fill={INK}>= 69%</text>
  <text x={250} y={650} fontFamily={SERIF} fontSize={62} fill={INK}>liver tumours with more CDK20 than the tissue next to them</text>
  <text x={250} y={770} fontFamily={SANS} fontSize={44} fontWeight={600} fill={DARK}>→ later stage</text>
  <text x={700} y={770} fontFamily={SANS} fontSize={44} fontWeight={600} fill={DARK}>→ shorter survival</text>
  <Source x={250} y={850} at={-1}>Illustration · Feng 2011</Source>
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
  <Source x={825} y={960} at={-1}>Illustration · Ren 2023</Source>
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
  <Source x={170} y={1020} at={-1}>Illustration · the other 19 names are not in the paper · Ren 2023</Source>
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
  <Composition id="W2Lyrics" component={W2Lyrics} durationInFrames={759} fps={30} width={W} height={H}/>
  <Composition id="W2Lyrics4K" component={W2Lyrics} durationInFrames={1517} fps={60} width={W} height={H} defaultProps={{file: "fusion_s1/w2_shake_4k.mp4", fps: 60}}/>
  <Composition id="S401" component={S401} durationInFrames={780} fps={30} width={W} height={H}/>
  <Composition id="S402" component={S402} durationInFrames={510} fps={30} width={W} height={H}/>
  <Composition id="S403" component={S403} durationInFrames={540} fps={30} width={W} height={H}/>
  <Composition id="S4B" component={S4B} durationInFrames={855} fps={30} width={W} height={H}/>
  <Composition id="S4C" component={S4C} durationInFrames={1245} fps={30} width={W} height={H}/>
  <Composition id="S4D" component={S4D} durationInFrames={510} fps={30} width={W} height={H}/>
  <Composition id="S4K" component={S4K} durationInFrames={510} fps={30} width={W} height={H}/>
  {/* 4K 60 fps passes of S4's 4-01 to 4-07 (render with --scale=2): every Blender frame, no voice-over line, since the narration comes as sound and the subtitles as an SRT */}
  <Composition id="S401-4K" component={S401} durationInFrames={1560} fps={60} width={W} height={H} defaultProps={{file: "fusion_s1/s4_401_4k.mp4", fps: 60, review: false}}/>
  <Composition id="S402-4K" component={S402} durationInFrames={1020} fps={60} width={W} height={H} defaultProps={{file: "fusion_s1/s4_402_4k.mp4", fps: 60, review: false}}/>
  <Composition id="S4B-4K" component={S4B} durationInFrames={1710} fps={60} width={W} height={H} defaultProps={{f403: "fusion_s1/s4_403_4k.mp4", f404: "fusion_s1/s4_404_4k.mp4", fps: 60, review: false}}/>
  <Composition id="S4C-4K" component={S4C} durationInFrames={2490} fps={60} width={W} height={H} defaultProps={{file: "fusion_s1/s4_lp_4k.mp4", fps: 60, review: false}}/>
  <Composition id="Loop" component={Loop} durationInFrames={1620} fps={60} width={W} height={H}/>
</>;
registerRoot(Root);
