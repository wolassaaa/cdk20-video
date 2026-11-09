// HKBU SCIE1007 coursework science video. S7 (15:15-16:04, A) and S8 (16:04-17:10, C, B, D, A): the review cut of the table layer, after
// 镜头设计_v3/styleframes/art/fusion/s7s8/00_S7S8分镜_v1.md. Old objects come back on the one bone table; next steps stay dashed. Words follow script_v3.3.md.
// One world per section, in table pixels; a camera glides over it (keys [t, x, y, zoom]). The three 3D seconds (7-02 dishes, 7-03 bin, 7-04 stopwatches) are
// full-frame inserts from inserts/bl_s78.py; until a render exists the insert prop is left empty and a placeholder card stands in. People are stand-in prints until 11-12.
// Render: npx remotion bundle src/v3/fusion/s78.jsx --out-dir=<dir> --public-dir=<镜头设计_v3/remotion_public>, then render S7 / S8 (30 fps, 1920x1080).
import React from "react";
import {registerRoot, Composition, AbsoluteFill, OffthreadVideo, Sequence, Img, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import OUTLINE from "./s78_cdk20_outline.json";

const W = 1920, H = 1080;
const INK = "#111113", SOFT = "#545458", RED = "#E8190F", DARK = "#9A0E08", KLEIN = "#002FA7", BONE = "#EDEBE4", GREY = "#9A9AA0", SHEET = "#EEE9E4";
const SERIF = "Instrument Serif", SANS = "Inter Tight", HAND = "Caveat";

const faces = [new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Regular.ttf")})`), new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Italic.ttf")})`, {style: "italic"}), new FontFace(SANS, `url(${staticFile("fusion_s1/fonts/InterTight.ttf")})`, {weight: "100 900"}), new FontFace(HAND, `url(${staticFile("fusion_s1/fonts/Caveat.ttf")})`, {weight: "400 700"})];
const fontHandle = delayRender("fonts");
Promise.all(faces.map(f => f.load())).then(l => { l.forEach(f => document.fonts.add(f)); continueRender(fontHandle); });

const clamp = x => Math.min(1, Math.max(0, x));
const smooth = x => { x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10); };
const out = x => 1 - Math.pow(1 - clamp(x), 3);
const Clock = React.createContext(0);
const useT = () => React.useContext(Clock);
const after = (t, at, d = 0.5) => out((t - at) / d);
const win = (t, a, b, d = 0.3) => after(t, a, d) * (1 - after(t, b, d));

// ---------------------------------------------------------------- type and pen, as in entry.jsx
let wipeId = 0;
const Ink = ({x, y, size, at, font = SANS, weight = 600, fill = INK, anchor = "start", w, dur = 0.5, children}) => {
  const t = useT(), p = smooth((t - at) / dur);
  const id = React.useMemo(() => `wipe${wipeId++}`, []);
  if (p <= 0) return null;
  const width = w || String(children).length * size * 0.62 + 40;
  const left = anchor === "start" ? x - 20 : anchor === "end" ? x - width : x - width / 2;
  return <g>
    <clipPath id={id}><rect x={left} y={y - size * 1.2} width={width * p} height={size * 1.6}/></clipPath>
    <text x={x} y={y} fontFamily={font} fontSize={size} fontWeight={font === SERIF ? 400 : weight} fill={fill} textAnchor={anchor} clipPath={`url(#${id})`}>{children}</text>
  </g>;
};

const ruler = document.createElement("canvas").getContext("2d");
/** A serif line with its key words in italic and one red rule under them (at most one per screen). */
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

/** A pen note in Caveat; "→" is drawn as a pen stroke, the hand has no arrow. */
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

/** A pen stroke that draws itself along its path. */
const Stroke = ({d, at, dur = 0.5, fill = RED, w = 6, dash}) => {
  const t = useT(), p = smooth((t - at) / dur);
  if (p <= 0) return null;
  return <g>
    {dash && <clipPath id={`sc${at}${d.length}`}/>}
    <path d={d} pathLength={1} fill="none" stroke={fill} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={`${p} 1`}/>
  </g>;
};

/** A dashed pen line: drawn left to right by a clip, so the dashes keep their spacing. */
const Dashed = ({x1, y1, x2, y2, at, dur = 0.6, fill = RED, w = 5, dash = "16 12"}) => {
  const t = useT(), p = smooth((t - at) / dur);
  if (p <= 0) return null;
  return <line x1={x1} y1={y1} x2={x1 + (x2 - x1) * p} y2={y1 + (y2 - y1) * p} stroke={fill} strokeWidth={w} strokeDasharray={dash} strokeLinecap="round"/>;
};

const Source = ({x, y, at, until = 1e9, size = 26, anchor = "start", children}) => {
  const t = useT(), a = after(t, at) * (1 - after(t, until));
  return a > 0 ? <text x={x} y={y} fontFamily={SANS} fontSize={size} fontWeight={500} fill={SOFT} textAnchor={anchor} opacity={a}>{children}</text> : null;
};

/** AlphaFold's predicted structure keeps its dashed circle. */
const Tag = ({x, y, at, size = 30, children}) => {
  const t = useT(), a = after(t, at);
  if (a <= 0) return null;
  const r = size / 2;
  return <g opacity={a}>
    <circle cx={x + r} cy={y - size * 0.36} r={r} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
    <text x={x + size * 1.45} y={y} fontFamily={SANS} fontSize={size} fontWeight={600} fill={INK}>{children}</text>
  </g>;
};

// ---------------------------------------------------------------- the stand-in print (entry.jsx), until the clips come on 11-12
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

/** from: where it slides in from, as an offset (a print that slides, not one that is thrown); otherwise it lands like a thrown print. */
const Print = ({who, x, y, w, h, at, rot = 0, until = 1e9, from, slide = 0.7}) => {
  const t = useT();
  if (t < at || t > until + 0.4) return null;
  const p = out((t - at) / (from ? slide : 0.5)), lift = from ? 0 : 1 - p, gone = after(t, until, 0.4);
  const ox = from ? from[0] * (1 - smooth((t - at) / slide)) : -60 * lift, oy = from ? from[1] * (1 - smooth((t - at) / slide)) : 130 * lift;
  const cx = x + w / 2 + ox, cy = y + h / 2 + oy, k = (w - 40) / 760, id = `photo${who}${at}`;
  const talk = Math.sin(t * 2.1 + at) * 3;
  return <g transform={`translate(${cx} ${cy}) rotate(${rot + 5 * lift}) scale(${1 + 0.05 * lift})`} opacity={(from ? 1 : clamp((t - at) / 0.08)) * (1 - gone)}>
    <rect x={-w / 2 + 12 + 18 * lift} y={-h / 2 + 16 + 24 * lift} width={w} height={h} fill="#3C3228" opacity={0.3 - 0.12 * lift} style={{filter: "blur(14px)"}}/>
    <rect x={-w / 2} y={-h / 2} width={w} height={h} fill="#F7F3EA"/>
    <clipPath id={id}><rect x={-w / 2 + 20} y={-h / 2 + 20} width={w - 40} height={h - 40}/></clipPath>
    <g clipPath={`url(#${id})`}>
      <rect x={-w / 2 + 20} y={-h / 2 + 20} width={w - 40} height={h - 40} fill="#D3BFA5"/>
      <rect x={-w / 2 + 20} y={-h / 2 + 20} width={(w - 40) * 0.4} height={h - 40} fill="#DCCBB3"/>
      <g transform={`translate(0 ${h * 0.03 + talk * k}) scale(${k * 0.95})`}><polygon points={PERSON} fill="#7E6A58"/></g>
    </g>
    <text x={-w / 2 + 44} y={h / 2 - 46} fontFamily={SANS} fontSize={Math.max(20, 26 * w / 620)} fontWeight={600} fill="#F7F3EA">stand-in · {who}</text>
  </g>;
};

// ---------------------------------------------------------------- the road: six glass bulbs, red filled to where 048 stands (F6: three full, the fourth half)
const STATIONS = ["Target", "Hit", "Improve", "Cells & animals", "Clinical trials", "Approval"];
const Road = ({x, y, gap, r = 46, fill = 3.5, labels = true, size = 34, at = -1, id = "rd"}) => {
  const t = useT(), a = after(t, at, 0.6);
  if (a <= 0) return null;
  const xs = STATIONS.map((_, k) => x + gap * k), xr = x + gap * (fill - 0.5) + (fill % 1 ? 0.5 * gap - r * 0 : 0);
  const redEnd = fill % 1 ? x + gap * Math.floor(fill) : x + gap * (fill - 1);
  return <g opacity={a}>
    <defs>
      <radialGradient id={`${id}g`} cx="0.38" cy="0.32" r="0.75"><stop offset="0" stopColor="#FFFFFF"/><stop offset="0.6" stopColor="#ECEAE4"/><stop offset="1" stopColor="#CFCCC4"/></radialGradient>
      <radialGradient id={`${id}r`} cx="0.38" cy="0.32" r="0.75"><stop offset="0" stopColor="#FF8A80"/><stop offset="0.35" stopColor={RED}/><stop offset="1" stopColor="#8E0A05"/></radialGradient>
    </defs>
    <line x1={x - gap * 0.6} y1={y} x2={xs[5] + gap * 0.3} y2={y} stroke="#CFCCC4" strokeWidth={r * 0.14}/>
    <line x1={x - gap * 0.6} y1={y} x2={redEnd} y2={y} stroke={RED} strokeWidth={r * 0.2} strokeLinecap="round"/>
    {xs.map((cx, k) => {
      const full = k + 1 <= fill, half = !full && k < fill, cid = `${id}c${k}`;
      return <g key={k}>
        <ellipse cx={cx + r * 0.18} cy={y + r * 0.95} rx={r * 0.9} ry={r * 0.22} fill="#3C3228" opacity={0.12} style={{filter: "blur(4px)"}}/>
        <circle cx={cx} cy={y} r={r} fill={`url(#${id}g)`}/>
        {full && <circle cx={cx} cy={y} r={r * 0.86} fill={`url(#${id}r)`}/>}
        {half && <g><clipPath id={cid}><rect x={cx - r} y={y - r} width={r} height={2 * r}/></clipPath><circle cx={cx} cy={y} r={r * 0.86} fill={`url(#${id}r)`} clipPath={`url(#${cid})`}/></g>}
        <circle cx={cx} cy={y} r={r} fill="none" stroke="#2E2E31" strokeWidth={r * 0.13}/>
        <ellipse cx={cx - r * 0.3} cy={y - r * 0.42} rx={r * 0.26} ry={r * 0.13} fill="#FFFFFF" opacity={0.85} transform={`rotate(-25 ${cx - r * 0.3} ${y - r * 0.42})`}/>
        {labels && <text x={cx} y={y + r + size * 1.4} textAnchor="middle" fontFamily={SANS} fontSize={size} fontWeight={600} fill={INK}>{STATIONS[k]}</text>}
      </g>;
    })}
  </g>;
};

/** A photo-like object made from a frame of S3 or S4, laid on the table. It slides in from dx, dy. */
const Obj = ({src, x, y, w, at, dx = 0, dy = 0, dur = 0.7, until = 1e9}) => {
  const t = useT(), p = smooth((t - at) / dur);
  if (p <= 0) return null;
  return <image href={staticFile(`fusion_s78/${src}`)} x={x + dx * (1 - p)} y={y + dy * (1 - p)} width={w} opacity={clamp((t - at) / 0.15) * (1 - after(t, until, 0.4))}/>;
};

/** The camera: keys [t, x, y, zoom], the point (x, y) of the table at the middle of the frame. */
const cam = (keys, t) => {
  if (t <= keys[0][0]) return keys[0].slice(1);
  for (let i = 1; i < keys.length; i++) if (t <= keys[i][0]) {
    const a = keys[i - 1], b = keys[i], q = smooth((t - a[0]) / (b[0] - a[0]));
    return [a[1] + (b[1] - a[1]) * q, a[2] + (b[2] - a[2]) * q, Math.exp(Math.log(a[3]) + (Math.log(b[3]) - Math.log(a[3])) * q)];
  }
  return keys[keys.length - 1].slice(1);
};

/** The bone table under everything: a flat colour, a faint grain and a soft fall-off at the edges, in screen space. */
const Table = () => <>
  <rect width={W} height={H} fill={BONE}/>
  <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7"/><feColorMatrix values="0 0 0 0 0.25  0 0 0 0 0.22  0 0 0 0 0.18  0 0 0 0.05 0"/></filter>
  <rect width={W} height={H} filter="url(#grain)"/>
  <radialGradient id="fall" cx="0.5" cy="0.45" r="0.8"><stop offset="0.6" stopColor="#000" stopOpacity="0"/><stop offset="1" stopColor="#3C3228" stopOpacity="0.07"/></radialGradient>
  <rect width={W} height={H} fill="url(#fall)"/>
</>;

/** A 3D insert over the whole frame: the Blender pass when there is one, a grey card until then. */
const Insert = ({from, to, file, label, fps}) => {
  const t = useT(), a = win(t, from, to, 0.3);
  if (a <= 0) return null;
  return <AbsoluteFill style={{opacity: a}}>
    {file ? <Sequence from={Math.round((from - 0.3) * fps)} layout="none"><OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/></Sequence>
      : <svg width={W} height={H}><rect width={W} height={H} fill="#D9D6CE"/><rect x={60} y={60} width={W - 120} height={H - 120} fill="none" stroke={GREY} strokeWidth={3} strokeDasharray="18 14"/>
        <text x={W / 2} y={H / 2} textAnchor="middle" fontFamily={SANS} fontSize={44} fontWeight={600} fill={SOFT}>{label}</text></svg>}
  </AbsoluteFill>;
};

const Line = ({lines, who}) => {
  const t = useT(), l = [...lines].reverse().find(([a]) => t >= a);
  return l ? <text x={64} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>{l[2] || who}: {l[1]}</text> : null;
};

// ================================================================ S7 · next steps (15:15-16:04, 49 s). t = 0 at 15:15.
const S7_LINES = [[0, "So, what should happen next? We'd suggest three things.", "A · on camera"], [3.0, "One: walk 048 further."], [5.2, "It's public now, so anyone could try."], [7.6, "Test it in more liver cancer cells and normal liver cells,"], [11.4, "then animals,"], [12.6, "and check how the body handles it and what else it hits."], [16.6, "The authors had already listed these steps."], [22.0, "Two: check the AlphaFold model against a lab-measured structure, once one exists."], [28.6, "And feed every result, including the failures, back into the next round."], [35.0, "Three: race them."], [36.4, "An AI route and a classic route, same target, same budget, same definition of a hit."], [42.6, "Then we'd know exactly how much faster AI really is."], [47.0, "(music breath)", "-"]];
// the table: 7-01 at x 0-1920, the first step at 2200-5900 (the road, then the dishes), the second at 6000-7900, the third at 8000-9900
const R7 = {x: 2300, y: 560, gap: 330};          // the road as S6 leaves it
const S7_CAM = [[0, 960, 540, 1], [2.95, 960, 540, 1], [3.6, 1010, 560, 2.2], [4.3, 3125, 540, 1], [6.6, 3125, 540, 1], [7.3, 5040, 540, 1], [21.6, 5040, 540, 1], [22.5, 6960, 540, 1],
  [34.7, 6960, 540, 1], [35.2, 8960, 540, 1], [46.8, 8960, 540, 1], [48.2, 5000, 560, 0.19], [49, 5000, 560, 0.19]];
const S7_INS = {dish: [6.8, 11.5], bin: [29.4, 34.8], watch: [36.3, 39.6]};
const DISH_ROWS = [["liver cancer cells", 380, "#E9B9B4"], ["normal liver cells", 620, "#F4F1EA"]];

const S7World = () => {
  const t = useT(), r = R7, x4 = r.x + 3 * r.gap;
  const hand = (t0, k = 1) => (t > t0 ? (t - t0) * 60 * k : 0);
  return <g>
    {/* 7-01: A's print on the left; the pen writes 1, 2, 3 on the bare table */}
    <Print who="A" x={96} y={168} w={760} h={912 - 168} at={0.05} rot={-0.8}/>
    {[1, 2, 3].map((n, i) => <Note key={n} x={1060 + i * 280} y={620} size={170} at={1.9 + i * 0.35} dur={0.3} fill={RED} rot={-3}>{n}</Note>)}

    {/* 7-02 · the road as S6 left it; a flag on station 4, its empty half ringed in dashes */}
    <Road {...r} fill={3.5} id="r7"/>
    <Note x={r.x - 140} y={250} size={150} at={3.6} dur={0.25} fill={RED} rot={-3}>1</Note>
    <g opacity={after(t, 3.9, 0.4)}>
      <line x1={x4} y1={r.y - 50} x2={x4} y2={r.y - 50 - 210 * smooth((t - 3.9) / 0.5)} stroke={INK} strokeWidth={5}/>
      <path d={`M${x4} ${r.y - 260} L${x4 + 100 * smooth((t - 4.3) / 0.4)} ${r.y - 232} L${x4} ${r.y - 204} Z`} fill={RED}/>
    </g>
    {t > 4.4 && <path d={`M${x4} ${r.y - 58} A58 58 0 0 1 ${x4} ${r.y + 58}`} fill="none" stroke={RED} strokeWidth={5} strokeDasharray="12 9" pathLength={100} opacity={after(t, 4.4)}/>}
    <Note x={x4 + 74} y={r.y - 92} size={54} at={4.6}>next</Note>
    <Ink x={x4 - 64} y={r.y - 300} size={96} at={3.4} font={SERIF} fill={RED} anchor="end" w={300}>048</Ink>
    {/* "It's public now": a stamp by 048's tag */}
    {t > 5.4 && <g transform={`translate(${x4 - 230} ${r.y - 400}) rotate(-6) scale(${1 + 0.06 * (1 - out((t - 5.4) / 0.3))})`} opacity={clamp((t - 5.4) / 0.1)}>
      <rect x={-92} y={-32} width={184} height={64} fill="none" stroke={RED} strokeWidth={4}/>
      <text x={0} y={13} textAnchor="middle" fontFamily={SANS} fontSize={36} fontWeight={700} fill={RED}>public</text>
    </g>}
    <Source x={R7.x - 120} y={1062} at={3.4} until={7.0}>Illustration · Ren 2023 (Results, Conclusions) · GEN 2023</Source>

    {/* the dishes as the 3D insert leaves them: two rows of four, seen from above; then a mouse drawn in ink, and the two checks */}
    {DISH_ROWS.map(([name, y, tint], j) => <g key={j} opacity={after(t, S7_INS.dish[1] - 0.3, 0.2)}>
      <text x={4180} y={y - 96} fontFamily={SANS} fontSize={34} fontWeight={600} fill={INK}>{name}</text>
      {[0, 1, 2, 3].map(i => <g key={i}>
        <ellipse cx={4260 + i * 190} cy={y + 8} rx={82} ry={30} fill="#3C3228" opacity={0.10} style={{filter: "blur(6px)"}}/>
        <ellipse cx={4250 + i * 190} cy={y} rx={78} ry={28} fill={tint} stroke="#8D8A82" strokeWidth={3}/>
        <ellipse cx={4250 + i * 190} cy={y - 4} rx={62} ry={20} fill="none" stroke="#FFFFFF" strokeWidth={2} opacity={0.7}/>
      </g>)}
    </g>)}
    {/* a mouse, one ink line */}
    <Stroke at={11.5} dur={1.0} fill={INK} w={4} d="M5180 520 C5190 440 5280 400 5370 410 C5440 418 5480 450 5500 480 C5530 470 5560 480 5575 500 C5560 515 5540 520 5520 522 L5190 522 C5160 530 5130 545 5100 560 C5085 568 5090 580 5110 575"/>
    <Stroke at={12.3} dur={0.3} fill={INK} w={4} d="M5480 452 C5490 430 5512 428 5518 446"/>
    <circle cx={5532} cy={492} r={5} fill={INK} opacity={after(t, 12.5, 0.2)}/>
    <Note x={5250} y={600} size={50} at={11.6}>then animals</Note>
    <Ink x={4180} y={820} size={56} at={12.8} font={SERIF} w={260}>ADME</Ink>
    <Note x={4400} y={820} size={50} at={13.3}>how the body handles it</Note>
    <Ink x={4180} y={910} size={56} at={15.0} font={SERIF} w={300}>selectivity</Ink>
    <Note x={4480} y={910} size={50} at={15.4}>what else it hits</Note>
    <Note x={5250} y={910} size={44} at={17.0} fill={SOFT} rot={-1.5}>the authors' own next steps</Note>
    <Source x={4180} y={1062} at={11.6} until={21.8}>Illustration · Ren 2023 (Results, Conclusions) · GEN 2023</Source>

    {/* 7-03 · the predicted model beside an empty dashed ghost of the same shape */}
    <Note x={6100} y={230} size={150} at={22.4} dur={0.25} fill={RED} rot={-3}>2</Note>
    <Obj src="obj_cdk20.png" x={6260} y={250} w={480} at={22.4} dy={-40}/>
    <Tag x={6300} y={820} at={23.0}>AlphaFold DB v6 · predicted</Tag>
    {(() => {
      const p = smooth((t - 24.6) / 1.4), k = 480 / OUTLINE.w;
      if (p <= 0) return null;
      const pts = OUTLINE.pts.map(([px, py]) => `${(7100 + px * k).toFixed(1)},${(250 + py * k).toFixed(1)}`).join(" ");
      return <polygon points={pts} fill="none" stroke={GREY} strokeWidth={5} strokeDasharray="16 12" pathLength={1000} style={{strokeDashoffset: 0}} opacity={p} strokeLinejoin="round"/>;
    })()}
    <Ink x={7170} y={820} size={30} at={25.6} w={420}>measured structure</Ink>
    <Note x={7470} y={826} size={64} at={26.4} fill={RED} rot={4}>?</Note>
    <Note x={7170} y={890} size={46} at={26.8}>once one exists</Note>
    <Source x={6100} y={1062} at={22.6} until={34.6}>Illustration · AlphaFold DB AF-Q8IZL9-F1 v6 · our proposal</Source>

    {/* 7-04 · one start line, two lanes, a stopwatch on each; the finish is dashed, nobody has run it yet */}
    <Note x={8100} y={230} size={150} at={35.1} dur={0.25} fill={RED} rot={-3}>3</Note>
    <Stroke at={35.6} dur={0.4} d="M8420 420 L8420 900" w={7}/>
    {[[480, "AI route"], [720, "classic route"]].map(([y, name], i) => <g key={i}>
      <Stroke at={35.9 + i * 0.2} dur={0.5} fill={INK} w={3} d={`M8420 ${y + 120} L9660 ${y + 120}`}/>
      <Ink x={8640} y={y + 74} size={38} at={36.4 + i * 0.6} w={360}>{name}</Ink>
      {/* the stopwatch after the insert: an ink dial whose red hand keeps going */}
      {t > S7_INS.watch[1] - 0.3 && <g transform={`translate(8520 ${y + 60})`} opacity={after(t, S7_INS.watch[1] - 0.3, 0.3)}>
        <circle r={44} fill="#F7F3EA" stroke={INK} strokeWidth={4}/>
        <rect x={-8} y={-62} width={16} height={14} fill={INK}/>
        <line x1={0} y1={0} x2={0} y2={-34} stroke={RED} strokeWidth={4} strokeLinecap="round" transform={`rotate(${hand(S7_INS.watch[0] + 1.2)})`}/>
        <circle r={4} fill={INK}/>
      </g>}
    </g>)}
    <Keyed x={8420} y={330} size={66} at={39.7} dur={1.6} w={1300} parts={["", "same", " target · same budget · same definition of a hit"]}/>
    <Dashed x1={9660} y1={420} x2={9660} y2={900} at={42.6} dur={0.6} fill={INK} w={4} dash="12 12"/>
    <Note x={9700} y={720} size={110} at={43.4} fill={RED} rot={5}>?</Note>
    <Note x={9300} y={980} size={44} at={44.6} anchor="end" rot={-1.5}>nobody has run this race yet</Note>
    <Source x={8100} y={1062} at={35.4} until={46.8}>Our proposal · Bender 2026 (abstract)</Source>
  </g>;
};

const S7 = ({review = true, fps = 30, dish = "", bin = "", watch = ""}) => {
  const t = useCurrentFrame() / fps, [cx, cy, z] = cam(S7_CAM, t);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute"}}>
      <Table/>
      <g transform={`translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})`}><S7World/></g>
    </svg>
    <Insert from={S7_INS.dish[0]} to={S7_INS.dish[1]} file={dish} label="3D insert 7-02 · dishes double (placeholder)" fps={fps}/>
    <Insert from={S7_INS.bin[0]} to={S7_INS.bin[1]} file={bin} label="3D insert 7-03 · the bin tips, keys go back (placeholder)" fps={fps}/>
    <Insert from={S7_INS.watch[0]} to={S7_INS.watch[1]} file={watch} label="3D insert 7-04 · two stopwatches start (placeholder)" fps={fps}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute"}}>
      {/* notes over the inserts, on the bare table they leave at the top */}
      <g opacity={win(t, S7_INS.dish[0] + 0.6, S7_INS.dish[1] - 0.4)}>
        <Note x={120} y={150} size={52} at={S7_INS.dish[0] + 0.8}>liver cancer cells · normal liver cells</Note>
      </g>
      <g opacity={win(t, S7_INS.bin[0] + 0.4, S7_INS.bin[1] - 0.3)}>
        <Note x={120} y={150} size={52} at={S7_INS.bin[0] + 0.6}>every result, failures too → back in</Note>
      </g>
      <g opacity={win(t, S7_INS.watch[0] + 0.4, S7_INS.watch[1] - 0.3)}>
        <Note x={120} y={150} size={52} at={S7_INS.watch[0] + 0.6}>AI route · classic route</Note>
      </g>
      {[S7_INS.dish, S7_INS.bin, S7_INS.watch].map(([a, b], i) => <g key={i} opacity={win(t, a + 0.3, b - 0.2)}>
        <text x={W - 72} y={1054} textAnchor="end" fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT}>{["Illustration · Ren 2023 (Conclusions)", "Illustration · our proposal · E09, E30", "Illustration · our proposal (T2 worksheet Q3)"][i]}</text>
      </g>)}
      {review && <Line lines={S7_LINES} who="VO (A)"/>}
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

// ================================================================ S8 · the answer (16:04-17:10, 66 s). t = 0 at 16:04.
const S8_LINES = [[0, "So, back to where we started.", "C · on camera"], [2.0, "How can computer-aided methods help scientists find and assess cancer drug candidates?", "VO (C)"], [7.8, "In this case, at four points.", "VO (C)"], [10.0, "Picking a target from data.", "VO (C)"], [12.2, "Predicting the lock's shape.", "VO (C)"], [14.2, "Designing new keys.", "VO (C)"], [16.0, "And ranking which ones to make.", "VO (C)"], [18.6, "That's our first objective, met for this case.", "VO (C)"],
  [23.0, "And our second?", "VO (C)"], [24.4, "These methods helped the team assess candidates fast.", "VO (C)"], [27.8, "Screening by the millions became thirteen molecules made.", "VO (C)"], [31.8, "And on a road measured in years, the first hit came in 30 days,", "VO (C)"], [36.4, "and round two made the key turn.", "VO (C)"],
  [40.0, "This works in cells, not yet in people. The computer narrows the search. Experiments still decide.", "C · on camera"], [47.0, "So next time you see a headline like 'AI discovers a cancer drug'...", "B · on camera"], [52.0, "...ask where it really is on the road: computer, protein, cells, animals, or patients?", "D · on camera"],
  [59.0, "AI didn't replace the scientists. It gave them trial and error at light speed. Thanks for watching.", "A · on camera"]];
const R8 = {x: 330, y: 760, gap: 270, r: 40};
const S8_CAM = [[0, 1100, 640, 0.62], [0.4, 1100, 640, 0.62], [2.0, 960, 540, 1], [22.6, 960, 540, 1], [23.6, 960, 860, 1], [39.4, 960, 860, 1], [40.0, 2880 + 960, 540, 1],
  [46.6, 2880 + 960, 540, 1], [47.2, 4800 + 960, 540, 1], [51.6, 4800 + 960, 540, 1], [52.2, 6720 + 960, 540, 1], [58.6, 6720 + 960, 540, 1], [59.2, 8640 + 960, 540, 1],
  [64.4, 8640 + 960, 540, 1], [65.8, 8640 + 1585, 570, 5.0], [66.0, 8640 + 1585, 570, 5.0]];
const OBJ8 = [["obj_rack.png", 250, 470, 300, 10.0, "target from data"], ["obj_cdk20.png", 580, 400, 230, 12.2, "the lock's shape"], ["obj_key.png", 860, 450, 200, 14.2, "new keys"], ["obj_tubes.png", 1150, 400, 130, 16.0, "ranking"]];
const TICK = (x, y, s = 1) => `M${x} ${y} L${x + 18 * s} ${y + 22 * s} L${x + 58 * s} ${y - 30 * s}`;
const ROAD_WORDS = [["computer", 0.5, 55.0], ["protein", 1, 55.8], ["cells", 2.8, 56.6], ["animals", 3.2, 57.4], ["patients", 4, 58.2]];

const S8World = () => {
  const t = useT(), r = R8;
  const fx = 8640, grid = [[0, "A", [-1400, 0]], [1, "B", [1400, 0]], [2, "C", [0, 1000]], [3, "D", [0, 1000]]];
  return <g>
    {/* 8-01 / 8-02 · S2's question card, the road, the four old objects */}
    <g opacity={1 - after(t, 23.0, 0.5)}>
      <rect x={168} y={118} width={1120} height={196} fill="#3C3228" opacity={0.14} style={{filter: "blur(12px)"}}/>
      <rect x={160} y={108} width={1120} height={196} fill="#F7F3EA"/>
      <text x={196} y={150} fontFamily={HAND} fontSize={36} fontWeight={600} fill={DARK} transform="rotate(-1.5 196 150)">Our research question</text>
      <text x={196} y={210} fontFamily={SERIF} fontSize={50} fill={INK}>How can computer-aided methods help scientists</text>
      <text x={196} y={268} fontFamily={SERIF} fontSize={50} fill={INK}>find and assess cancer drug candidates?</text>
      {/* "In this case, at four points": four pen ticks under the first stretch */}
      {OBJ8.map(([src, x, y, w, at, word], i) => <g key={i}>
        <Obj src={src} x={x} y={y} w={w} at={at} dx={-260} dur={0.8}/>
        <Note x={x + w / 2} y={680} size={42} at={at + 0.5} anchor="middle" rot={-1.5}>{word}</Note>
      </g>)}
      <Note x={1310} y={560} size={48} at={8.0} rot={-2}>at four points</Note>
    </g>
    <Road {...r} fill={3.5} id="r8"/>
    <Ink x={r.x + 3 * r.gap} y={r.y + 150} size={56} at={-1} font={SERIF} fill={RED} anchor="middle" w={160}>048</Ink>
    {/* 8-01: C's print on the right, clear of the card and the road; it goes when C's voice-over starts */}
    <Print who="C" x={1400} y={110} w={420} h={504} at={0.0} rot={1.2} until={1.9}/>

    {/* 8-03 · one red line: millions → 13 dots → "13"; then the road measured */}
    <Ink x={180} y={1180} size={130} at={27.8} font={SERIF} w={460} dur={0.5}>millions</Ink>
    <Stroke at={28.6} dur={0.4} d="M650 1140 L790 1140 M766 1122 L792 1140 L766 1158" w={6}/>
    {t > 28.6 && <g opacity={after(t, 28.6, 0.3)}>
      <rect x={826} y={1010} width={560} height={315} fill="#3C3228" opacity={0.15} style={{filter: "blur(12px)"}}/>
      <rect x={814} y={998} width={584} height={339} fill="#F7F3EA"/>
      {t > 32.5 && <image href={staticFile("fusion_s78/millions13_last.png")} x={826} y={1010} width={560} height={315}/>}{/* the TD clip's last frame, held: the 13 stay */}
    </g>}
    <Ink x={1470} y={1180} size={130} at={31.3} font={SERIF} fill={RED} w={200} dur={0.4}>13</Ink>
    <Note x={1476} y={1250} size={44} at={31.6}>molecules made</Note>
    {/* 10-17 years over the whole road, 30 days under its first stretch */}
    <Stroke at={32.2} dur={0.6} fill={INK} w={3} d={`M${r.x - 30} ${r.y - 90} L${r.x - 30} ${r.y - 110} L${r.x + 5 * r.gap + 30} ${r.y - 110} L${r.x + 5 * r.gap + 30} ${r.y - 90}`}/>
    <Ink x={r.x + 2.5 * r.gap} y={r.y - 130} size={50} at={32.6} font={SERIF} anchor="middle" w={400}>10–17 years</Ink>
    <Stroke at={33.6} dur={0.5} w={6} d={`M${r.x} ${r.y + 110} L${r.x} ${r.y + 128} L${r.x + r.gap} ${r.y + 128} L${r.x + r.gap} ${r.y + 110}`}/>
    <Note x={r.x - 10} y={r.y + 186} size={50} at={34.0}>first hit in 30 days</Note>
    <Note x={r.x + 3 * r.gap + 90} y={r.y + 186} size={44} at={36.6} rot={-1.5}>round two → the key turns</Note>
    <Source x={180} y={1378} at={27.8} until={39.6}>Illustration · Ren 2023 · Wang 2023 p.1 · dots drawn</Source>

    {/* 8-04 · C alone; nothing moves */}
    <Print who="C" x={2880 + 580} y={168} w={760} h={744} at={40.0} rot={-0.6}/>

    {/* 8-05 · B, and a phone drawn beside the print */}
    <Print who="B" x={4800 + 120} y={168} w={620} h={744} at={47.0} rot={0.8}/>
    <Stroke at={47.8} dur={0.8} fill={RED} w={5} d={`M${4800 + 1060} 200 L${4800 + 1440} 200 Q${4800 + 1480} 200 ${4800 + 1480} 240 L${4800 + 1480} 880 Q${4800 + 1480} 920 ${4800 + 1440} 920 L${4800 + 1060} 920 Q${4800 + 1020} 920 ${4800 + 1020} 880 L${4800 + 1020} 240 Q${4800 + 1020} 200 ${4800 + 1060} 200 Z`}/>
    <Stroke at={48.6} dur={0.4} fill={RED} w={4} d={`M${4800 + 1060} 330 L${4800 + 1440} 330 L${4800 + 1440} 480 L${4800 + 1060} 480 Z`}/>
    <Note x={4800 + 1250} y={392} size={46} at={49.0} anchor="middle" fill={RED} rot={0}>AI discovers</Note>
    <Note x={4800 + 1250} y={450} size={46} at={49.6} anchor="middle" fill={RED} rot={0}>a cancer drug</Note>
    {[560, 610, 660, 710].map((y, i) => <Stroke key={i} at={50.0 + i * 0.12} dur={0.25} fill={RED} w={3} d={`M${4800 + 1070} ${y} L${4800 + 1430 - (i === 3 ? 120 : 0)} ${y}`}/>)}
    <Source x={4800 + 1020} y={1000} at={48.0} until={51.6}>Illustration · no real outlet</Source>

    {/* 8-06 · D, and the road: each word lights its place; 048's red stops at cells */}
    <Print who="D" x={6720 + 80} y={60} w={520} h={624} at={52.0} rot={-1}/>
    {(() => {
      const rr = {x: 6720 + 760, y: 880, gap: 200, r: 34};
      return <g>
        <Road {...rr} fill={3.5} labels={false} id="r86"/>
        <Ink x={rr.x + 3 * rr.gap + 50} y={rr.y + 92} size={50} at={-1} font={SERIF} fill={RED} anchor="start" w={140}>048</Ink>
        {ROAD_WORDS.map(([word, k, at], i) => {
          const x = rr.x + k * rr.gap, top = rr.y - 60 - (i % 2 ? 150 : 70), flash = Math.max(0, 1 - Math.abs(t - at - 0.15) / 0.4);
          return <g key={i}>
            {flash > 0 && <circle cx={x} cy={rr.y} r={rr.r + 18} fill="none" stroke={RED} strokeWidth={4} opacity={flash}/>}
            <Stroke at={at} dur={0.25} fill={DARK} w={3} d={`M${x} ${rr.y - rr.r - 12} L${x} ${top + 12}`}/>
            <Note x={x} y={top} size={46} at={at + 0.1} anchor="middle" dur={0.35}>{word}</Note>
          </g>;
        })}
      </g>;
    })()}
    <Source x={6720 + 760} y={1062} at={52.6} until={58.6}>Illustration · T2 worksheet Q5</Source>

    {/* 8-07 · A, then all four slide into a 2x2 with a gap of 2% between; then the camera goes down onto the blank sheet: W5 starts on it */}
    {grid.map(([i, who, from]) => {
      const cw = 560, ch = 420, g = 0.02 * W, gx = fx + 120 + (i % 2) * (cw + g), gy = 90 + Math.floor(i / 2) * (ch + g);
      if (who === "A") {
        const m = smooth((t - 62.6) / 0.7), x0 = fx + 240, y0 = 168, w0 = 760, h0 = 744;
        return t >= 59.0 && <Print key={who} who={who} x={x0 + (gx - x0) * m} y={y0 + (gy - y0) * m} w={w0 + (cw - w0) * m} h={h0 + (ch - h0) * m} at={59.0} rot={-0.8 * (1 - m)}/>;
      }
      return <Print key={who} who={who} x={gx} y={gy} w={cw} h={ch} at={62.6 + 0.12 * i} from={from} slide={0.8}/>;
    })}
    <rect x={fx + 1380} y={300} width={430} height={560} fill="#3C3228" opacity={0.12} style={{filter: "blur(10px)"}}/>
    <rect x={fx + 1370} y={290} width={430} height={560} fill={SHEET}/>
  </g>;
};

const S8 = ({review = true, fps = 30}) => {
  const t = useCurrentFrame() / fps, [cx, cy, z] = cam(S8_CAM, t);
  // the TD dot print for "millions → 13", inside its paper, at twice its speed: 8 s in 4
  const m0 = 28.7, mv = t > m0 - 0.1 && t < 39.6;
  const sx = (x, y) => [(x - cx) * z + W / 2, (y - cy) * z + H / 2];
  const [vx, vy] = sx(826, 1010);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute"}}>
      <Table/>
      <g transform={`translate(${W / 2} ${H / 2}) scale(${z}) translate(${-cx} ${-cy})`}><S8World/></g>
    </svg>
    {mv && <Sequence from={Math.round(m0 * fps)} layout="none">
      <div style={{position: "absolute", left: vx, top: vy, width: 560 * z, height: 315 * z, overflow: "hidden", opacity: after(t, m0, 0.3) * (1 - after(t, 39.0, 0.4))}}>
        <OffthreadVideo src={staticFile("fusion_s78/millions13.mp4")} playbackRate={2} muted style={{width: "100%", height: "100%"}}/>
      </div>
    </Sequence>}
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute"}}>
      {/* the objective tags live in screen space, top right, as in S2-S5 */}
      <g opacity={win(t, 2.0, 22.8)}>
        <text x={1780} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end"><tspan fill={RED}>1</tspan> Identify methods</text>
        <Stroke at={18.9} dur={0.35} d={TICK(1800, 70)} w={7}/>
        <Note x={1856} y={150} size={44} at={19.5} anchor="end" rot={-1.5}>(for this case)</Note>
      </g>
      <g opacity={win(t, 23.2, 39.6)}>
        <text x={1780} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end"><tspan fill={RED}>2</tspan> Evaluate candidates</text>
        <Stroke at={38.6} dur={0.35} d={TICK(1800, 70)} w={7}/>
      </g>
      <Source x={W - 72} y={1054} at={2.2} until={22.6} size={22} anchor="end">Ren 2023 · T2 worksheet Q1 · objects from S3 and S4</Source>
      {review && <Line lines={S8_LINES}/>}
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

const Root78 = () => <>
  <Composition id="S7" component={S7} durationInFrames={1470} fps={30} width={W} height={H}/>
  <Composition id="S8" component={S8} durationInFrames={1980} fps={30} width={W} height={H}/>
</>;
registerRoot(Root78);
