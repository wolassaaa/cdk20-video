// HKBU SCIE1007 coursework science video. S5's 5-01, 5-07 and 5-10 on the 3D table (11-10, Claude): the words, numbers and pen notes over bl_s5b.py's takes.
// Helpers are copied from s5.jsx (itself from entry.jsx); s5.jsx is left alone. Every number on screen is in s4/<段号>_数字对照 tables with its page in Ren 2023.
// Positions come from the take's camera (bl_s5b.py BL_S5B_PROJ prints where each object lands on screen while the camera holds).
import React from "react";
import {registerRoot, Composition, AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";

const W = 1920, H = 1080;
const INK = "#111113", SOFT = "#545458", RED = "#E8190F", DARK = INK, KLEIN = "#002FA7", BONE = "#EDEBE4";
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

const Title = ({t, at = 1.0}) => <g opacity={after(t, at)}><text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 2 / Results</text></g>;
const SourceR = ({t, at = 1.0, lines}) => <g opacity={after(t, at)}>{lines.map((s, i) => <text key={i} x={1848} y={1024 + 30 * i} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">{s}</text>)}</g>;
const VO = ({t, lines, review}) => review && t >= 1.0 ? <text x={64} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT}>VO (C): {[...lines].reverse().find(([a]) => t >= a)[1]}</text> : null;
/** A pen line drawn from a to b, with an arrowhead at b (the hand has no arrow glyph). */
const Pen = ({x1, y1, x2, y2, at, dur = 0.4, fill = INK, w = 3, head = 0}) => {
  const t = useT(), p = smooth((t - at) / dur);
  if (p <= 0) return null;
  const x = x1 + (x2 - x1) * p, y = y1 + (y2 - y1) * p, a = Math.atan2(y2 - y1, x2 - x1), k = head;
  return <g stroke={fill} strokeWidth={w} strokeLinecap="round" fill="none">
    <line x1={x1} y1={y1} x2={x} y2={y}/>
    {k > 0 && p > 0.95 && <path d={`M${x - k * Math.cos(a - 0.5)} ${y - k * Math.sin(a - 0.5)} L${x} ${y} L${x - k * Math.cos(a + 0.5)} ${y - k * Math.sin(a + 0.5)}`}/>}
  </g>;
};

// ================================================================ 5-01 · the seven, each with its Kd (10:25-10:42, 17 s)
// bl_s5b.py s501: seven paper cards (Fig. 5's structures, cut from the paper, not redrawn) drop into a row; the camera holds from 3.0 s.
// Card centres on screen while it holds (BL_S5B_PROJ=6): x 299 + 237.5 i, the near edge at y 688, the far edge at y 571.
const S501_LINES = [[0, "So, the moment of truth."], [1.8, "Seven real molecules, made in a real lab."], [5.0, "Do any actually grab CDK20?"], [7.2, "Grip is measured as Kd:"], [9.0, "roughly, how much molecule it takes to grab half the protein."], [13.4, "Lower means tighter."]];
const S501_CARDS = [["001", "Kd 9.2 µM"], ["004", "Kd > 30 µM"], ["007", "Kd > 30 µM"], ["009", "Kd > 30 µM"], ["015", "Kd > 30 µM"], ["019", "Kd > 30 µM"], ["025", "Kd > 30 µM"]];
const S501_LAND = i => 2.6 + 0.22 * i;          // bl_s5b.py: T_LAND0 + T_STAG * i
const S501 = ({file = "fusion_s5b/s501_3d.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps;
  const made = 1 - after(t, 7.0, 0.4);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <Title t={t}/>
      {/* each card's number above it as it lands; its Kd under it when "Kd" is said (Fig. 5's own labels, set in type) */}
      {S501_CARDS.map(([id, kd], i) => { const x = 299 + 237.5 * i; return <g key={id}>
        <Ink x={x} y={548} size={28} at={Math.max(S501_LAND(i) + 0.1, 3.05)} anchor="middle" w={90} dur={0.3}>{id}</Ink>
        <Ink x={x} y={734} size={26} at={7.6 + 0.12 * i} anchor="middle" w={170} weight={500} dur={0.35}>{kd}</Ink>
      </g>; })}
      {made > 0 && <g opacity={made}><Note x={150} y={250} size={50} at={2.4} rot={-1.5}>seven real molecules, made in a lab</Note></g>}
      <Ink x={150} y={200} size={30} at={9.2} w={560}>Kd = how much molecule it takes</Ink>
      <Ink x={150} y={242} size={30} at={9.8} w={560}>to grab half the protein</Ink>
      {/* the gauge: a short rule, lower on the left, and the line over it */}
      <Keyed x={150} y={350} size={64} at={13.4} dur={0.9} w={700} parts={["Kd: lower = ", "tighter"]}/>
      <Pen x1={560} y1={392} x2={160} y2={392} at={13.6} dur={0.5} head={16}/>
      {[0, 1, 2, 3, 4].map(k => <Pen key={k} x1={160 + 100 * k} y1={384} x2={160 + 100 * k} y2={400} at={13.7 + 0.05 * k} dur={0.15}/>)}
      <Ink x={160} y={430} size={24} at={14.1} w={120} weight={500} fill={SOFT}>lower</Ink>
      <Ink x={560} y={430} size={24} at={14.2} anchor="end" w={120} weight={500} fill={SOFT}>higher</Ink>
      <VO t={t} lines={S501_LINES} review={review}/>
      <SourceR t={t} lines={["Illustration · structures and Kd: Ren 2023, Fig. 5, p. 1447", "binding assay · cards cut from the paper's figure, not redrawn"]}/>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

// ================================================================ 5-07 · round two (11:33-11:53, 20 s)
// bl_s5b.py s507: from 5-04's last frame (the enzyme tube, close) the camera pulls back to cell 20; 16 new keys grow there (9.6 s), 10 shrink away, 6 slide into a row (12.9 s).
// Where things sit while it holds (BL_S5B_PROJ=15): the tube at 1591, 444; the 4x4 keys x 352-1007, y 289-621; the row of six at y 796, x 342-973.
const S507_LINES = [[0, "Not at all."], [1.0, "This is where the loop kicks in again, now with real lab data inside."], [5.0, "The results went back in, with a predicted pose of how 001 sat in the pocket."], [9.6, "Sixteen new designs."], [11.3, "Six made and tested."], [13.2, "All within 30 days of that first hit."]];
/** A pen arc from the tube back to the design cell: drawn along its length, with an arrowhead once it arrives. */
const Loop = ({d, at, dur = 0.9, end, ang}) => {
  const t = useT(), p = smooth((t - at) / dur);
  if (p <= 0) return null;
  return <g stroke={INK} strokeWidth={3.5} fill="none" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} pathLength={1} strokeDasharray={`${p} 1`}/>
    {p > 0.97 && <path d={`M${end[0] + 20 * Math.cos(ang - 0.45)} ${end[1] + 20 * Math.sin(ang - 0.45)} L${end[0]} ${end[1]} L${end[0] + 20 * Math.cos(ang + 0.45)} ${end[1] + 20 * Math.sin(ang + 0.45)}`}/>}
  </g>;
};
const S507 = ({file = "fusion_s5b/s507_3d.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps;
  const notes = 1 - after(t, 9.2, 0.4);
  ruler.font = `400 60px "${SERIF}"`;
  const w1 = ruler.measureText("Round 2: 16 designed ").width, w2 = ruler.measureText("→ ").width, w3 = ruler.measureText("6 tested").width;
  const red = smooth((t - 11.9) / 0.5);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <Title t={t}/>
      {/* the loop: the tube's result goes back to the design side */}
      <Loop d="M1560 250 Q1310 90 1060 290" at={5.2} end={[1060, 290]} ang={-2.2}/>
      {notes > 0 && <g opacity={notes}>
        <Note x={420} y={430} size={48} at={5.6} rot={-1.5}>lab results back in</Note>
        <Note x={420} y={500} size={48} at={7.0} rot={-1.5}>+ a predicted pose of 001</Note>
      </g>}
      <Ink x={220} y={185} size={60} at={9.6} font={SERIF} w={w1 + 30} dur={0.6}>Round 2: 16 designed</Ink>
      <Ink x={220 + w1} y={185} size={60} at={11.3} font={SERIF} w={w2 + w3 + 30} dur={0.5}>→ 6 tested</Ink>
      {red > 0 && <rect x={220 + w1 + w2} y={198} width={w3 * red} height={5} fill={RED}/>}
      <Ink x={226} y={340} size={30} at={13.3} w={520}>within 30 days of the first hit</Ink>
      <VO t={t} lines={S507_LINES} review={review}/>
      <SourceR t={t} lines={["Illustration · 16 designed, 6 made and tested, within 30 days: Ren 2023, p. 1448", "predicted binding mode as the guide: p. 1444 · keys, tube and loop drawn"]}/>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

const Root5b = () => <>
  <Composition id="S501" component={S501} durationInFrames={510} fps={30} width={W} height={H}/>
  <Composition id="S507" component={S507} durationInFrames={600} fps={30} width={W} height={H}/>
</>;
registerRoot(Root5b);
