// HKBU SCIE1007 coursework science video. S5's 5-03 and 5-08 on the 3D table (11-10, Claude): the words, numbers and pen notes over bl_s5c.py's takes.
// Helpers are a copy of s5b.jsx's (itself from s5.jsx / entry.jsx); s5b.jsx belongs to the 5-01 / 5-07 / 5-10 worker and is left alone.
// Every number on screen is in s4/<段号>_数字对照.md with its page in Ren 2023.
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


// ================================================================ 5-01's last frame, held (5-03 starts on it)
// The same marks s5b.jsx's S501 has on screen at its end (positions from bl_s5b.py's card view). 5-03 fades them as its camera leaves the cards.
const S501_CARDS_END = [["001", "Kd 9.2 µM"], ["004", "Kd > 30 µM"], ["007", "Kd > 30 µM"], ["009", "Kd > 30 µM"], ["015", "Kd > 30 µM"], ["019", "Kd > 30 µM"], ["025", "Kd > 30 µM"]];
const S501End = () => <Clock.Provider value={99}>
  {S501_CARDS_END.map(([id, kd], i) => { const x = 299 + 237.5 * i; return <g key={id}>
    <Ink x={x} y={548} size={28} at={0} anchor="middle" w={90} dur={0.3}>{id}</Ink>
    <Ink x={x} y={734} size={26} at={0} anchor="middle" w={170} weight={500} dur={0.35}>{kd}</Ink>
  </g>; })}
  <Ink x={150} y={200} size={30} at={0} w={560}>Kd = how much molecule it takes</Ink>
  <Ink x={150} y={242} size={30} at={0} w={560}>to grab half the protein</Ink>
  <Keyed x={150} y={350} size={64} at={0} dur={0.9} w={700} parts={["Kd: lower = ", "tighter"]}/>
  <Pen x1={560} y1={392} x2={160} y2={392} at={0} dur={0.5} head={16}/>
  {[0, 1, 2, 3, 4].map(k => <Pen key={k} x1={160 + 100 * k} y1={384} x2={160 + 100 * k} y2={400} at={0} dur={0.15}/>)}
  <Ink x={160} y={430} size={24} at={0} w={120} weight={500} fill={SOFT}>lower</Ink>
  <Ink x={560} y={430} size={24} at={0} anchor="end" w={120} weight={500} fill={SOFT}>higher</Ink>
  {["Illustration · structures and Kd: Ren 2023, Fig. 5, p. 1447", "binding assay · cards cut from the paper's figure, not redrawn"].map((s, i) => <text key={i} x={1848} y={1024 + 30 * i} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">{s}</text>)}
</Clock.Provider>;

// ================================================================ 5-03 · 9.2 µM, and 30 days (10:48-11:02, 14 s)
// bl_s5c.py s503: 0-1 s 5-01's card view, held; 1.0-4.6 s the camera drops to CDK20's pocket (the cards lift away); 001 sits in the pocket in OUR
// re-docked pose (poses.json mode 3); 6.6-9.2 s it backs off to 5-04's opening view and holds. Numbers: Ren 2023 p1447 (Kd 9.2 ± 0.5 µM, n = 3; the other six > 30 µM, Fig. 5)
// and p1443 / p1447 (30 days from target selection to the hit); see s4/5-03_数字对照.md. The molecule sits at x 742-1150, y 445-603 in the pocket view.
const S503_T = {m1: 1.0, kd: 1.4, six: 3.0, tag: 4.8, out: 6.3, cal: 9.4, calEnd: 12.6};
const S503_LINES = [[0, "001's Kd: 9.2 micromolar."], [2.8, "The other six? All above 30. Much weaker."], [6.3, "And here's the wild part."], [8.0, "The clock read just 30 days, from picking the target to this first confirmed hit."]];
const CAL = {x: 94, y: 560, c: 56, cols: 6, rows: 5};
const Calendar = ({t, at}) => {
  const grid = smooth((t - at) / 0.6);
  const cells = [];
  for (let k = 0; k < 30; k++) {
    const cx = CAL.x + (k % CAL.cols) * CAL.c, cy = CAL.y + Math.floor(k / CAL.cols) * CAL.c;
    const p = smooth((t - (at + 0.7 + k * 0.06)) / 0.12);          // each day crossed off, one after the other: 30 strokes in about 2 s
    if (p > 0) cells.push(<line key={k} x1={cx + 12} y1={cy + CAL.c - 12} x2={cx + 12 + (CAL.c - 24) * p} y2={cy + CAL.c - 12 - (CAL.c - 24) * p} stroke={INK} strokeWidth={3} strokeLinecap="round"/>);
  }
  const W_ = CAL.cols * CAL.c, H_ = CAL.rows * CAL.c, L = 2 * (W_ + H_);
  const last = smooth((t - (at + 0.7 + 30 * 0.06 + 0.1)) / 0.5);
  const lx = CAL.x + 5.5 * CAL.c, ly = CAL.y + 4.5 * CAL.c;
  return <g>
    <rect x={CAL.x} y={CAL.y} width={W_} height={H_} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray={`${L * grid} ${L}`}/>
    {grid > 0.6 && [1, 2, 3, 4, 5].map(i => <line key={"v" + i} x1={CAL.x + i * CAL.c} y1={CAL.y} x2={CAL.x + i * CAL.c} y2={CAL.y + H_ * smooth((grid - 0.6) / 0.4)} stroke={INK} strokeWidth={1.5}/>)}
    {grid > 0.6 && [1, 2, 3, 4].map(i => <line key={"h" + i} x1={CAL.x} y1={CAL.y + i * CAL.c} x2={CAL.x + W_ * smooth((grid - 0.6) / 0.4)} y2={CAL.y + i * CAL.c} stroke={INK} strokeWidth={1.5}/>)}
    {cells}
    {last > 0 && <ellipse cx={lx} cy={ly} rx={CAL.c * 0.62} ry={CAL.c * 0.55} fill="none" stroke={INK} strokeWidth={3.5} strokeDasharray={`${260 * last} 400`} transform={`rotate(-8 ${lx} ${ly})`}/>}
  </g>;
};
const S503 = ({file = "fusion_s5c/s503_3d.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps, T = S503_T;
  const prev = 1 - after(t, T.m1, 0.4);
  const pocket = 1 - after(t, T.out, 0.4);
  const cal = 1 - after(t, T.calEnd, 0.4);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={cal}><Title t={t} at={-1}/></g>
      {prev > 0 && <g opacity={prev}><S501End/></g>}
      {pocket > 0 && t >= T.kd && <g opacity={pocket}>
        <Ink x={84} y={150} size={28} at={T.kd} w={420} weight={500} fill={SOFT}>001 · binding to CDK20</Ink>
        <Keyed x={80} y={236} size={84} at={T.kd + 0.2} dur={0.8} w={760} parts={["Kd = ", "9.2", " ± 0.5 µM"]}/>
        <Ink x={84} y={282} size={28} at={T.kd + 0.8} w={200} weight={500}>(n = 3)</Ink>
        <Ink x={84} y={352} size={34} at={T.six} w={520}>the other six: Kd &gt; 30 µM</Ink>
        <Note x={88} y={418} size={50} at={T.six + 0.7} rot={-1.5}>much weaker</Note>
        <Leader pts={[[760, 610], [700, 700]]} at={T.tag}/>
        <Tag x={560} y={748} at={T.tag + 0.3} size={30}>OUR RE-DOCKING (AutoDock Vina)</Tag>
        <Ink x={606} y={786} size={24} at={T.tag + 0.6} w={460} weight={500} fill={SOFT}>not the authors' coordinates</Ink>
        <g opacity={after(t, T.kd)}>
          <text x={1848} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Kd: Ren 2023, Fig. 5, p. 1447 · pose: our AutoDock Vina re-docking into the AlphaFold model</text>
          <text x={1848} y={1054} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">predicted · CDK20 surface shown see-through</text>
        </g>
      </g>}
      {cal > 0 && t >= T.cal - 0.1 && <g opacity={cal}>
        <Keyed x={90} y={470} size={110} at={T.cal} dur={0.6} w={460} parts={["", "30", " days"]}/>
        <Ink x={94} y={520} size={28} at={T.cal + 0.4} w={720}>from picking the target to the first confirmed hit</Ink>
        <Calendar t={t} at={T.cal + 0.2}/>
        <g opacity={after(t, T.cal)}>
          <text x={1848} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · 30 days: Ren 2023, pp. 1443, 1447</text>
        </g>
      </g>}
      <VO t={t} lines={S503_LINES} review={review}/>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

// ================================================================ 5-07's last frame, held (5-08 starts on it)
// The marks s5b.jsx's S507 has on screen at its end, drawn the same way. 5-08 fades them as its camera leaves for the pocket.
const Loop = ({d, at, dur = 0.9, end, ang}) => {
  const t = useT(), p = smooth((t - at) / dur);
  if (p <= 0) return null;
  return <g stroke={INK} strokeWidth={3.5} fill="none" strokeLinecap="round" strokeLinejoin="round">
    <path d={d} pathLength={1} strokeDasharray={`${p} 1`}/>
    {p > 0.97 && <path d={`M${end[0] + 20 * Math.cos(ang - 0.45)} ${end[1] + 20 * Math.sin(ang - 0.45)} L${end[0]} ${end[1]} L${end[0] + 20 * Math.cos(ang + 0.45)} ${end[1] + 20 * Math.sin(ang + 0.45)}`}/>}
  </g>;
};
const S507End = () => {          // as s5b.jsx S507 (5-07 v2, 11-10) shows it at its end
  ruler.font = `400 72px "${SERIF}"`;
  const w3 = ruler.measureText("6 tested").width, w2 = ruler.measureText("→ ").width;
  return <Clock.Provider value={99}>
    <Loop d="M1780 290 Q1640 120 1470 190" at={0} end={[1470, 190]} ang={-2.75}/>
    <Ink x={142} y={330} size={30} at={0} w={200}>Round 2</Ink>
    <Ink x={140} y={420} size={72} at={0} font={SERIF} w={380} dur={0.6}>16 designed</Ink>
    <Ink x={140} y={505} size={72} at={0} font={SERIF} w={380} dur={0.5}>→ 6 tested</Ink>
    <rect x={140 + w2} y={520} width={w3} height={5} fill={RED}/>
    <Ink x={142} y={580} size={28} at={0} w={440}>within 30 days</Ink>
    <Ink x={142} y={618} size={28} at={0} w={440}>of the first hit</Ink>
    {["Illustration · 16 designed, 6 made and tested, within 30 days: Ren 2023, p. 1448", "predicted binding mode as the guide: p. 1444 · keys, tube and loop drawn"].map((s, i) => <text key={i} x={1848} y={1024 + 30 * i} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">{s}</text>)}
  </Clock.Provider>;
};

// ================================================================ 5-08 · 048: tighter, and the enzyme test (11:53-12:09, 16 s)
// bl_s5c.py s508: 0-1 s 5-07's view, held; 1.0-4.6 s the camera drops to CDK20's pocket: 048 in OUR re-docked pose (poses.json mode 2), Lys33's side chain
// and the hydrogen bond between them as ink dashes (3.4 A in our docking); 6.8-9.4 s it backs off to 5-04's enzyme-test close-up (cell 21) and holds.
// Pocket view: the molecule spans x 726-1138, y 342-657; Lys33's NZ is at (1230, 363), the bond's ligand end at (1138, 380).
// Numbers: Kd 566.7 ± 256.2 nM, 15-fold, 049 360.0 ± 14.1 nM, IC50 33.4 ± 22.6 nM: Ren 2023 p1448; 001 > 6,000 nM: p1447. See s4/5-08_数字对照.md.
const S508_T = {m1: 1.0, kd: 1.4, fold: 2.6, tag: 4.6, lys: 4.8, f049: 5.4, out: 6.6, test: 9.5, b001: 9.8, b048: 11.6};
const S508_LINES = [[0, "And one of them, 048, grabbed about fifteen times tighter."], [4.6, "Then the enzyme test."], [6.4, "Remember, 001 needed more than 6,000 nanomolar."], [10.8, "048 needed just 33.4."]];
const BAR = {x: 150, len: 300, max: 6000};          // stops short of the tube (x ~560 in this view)
const S508 = ({file = "fusion_s5c/s508_3d.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps, T = S508_T;
  const prev = 1 - after(t, T.m1, 0.4);
  const pocket = 1 - after(t, T.out, 0.4);
  const g1 = smooth((t - T.b001) / 0.9), g2 = smooth((t - T.b048) / 0.3);
  const w048 = Math.max(3, BAR.len * 33.4 / BAR.max);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <Title t={t} at={-1}/>
      {prev > 0 && <g opacity={prev}><S507End/></g>}
      {pocket > 0 && t >= T.kd && <g opacity={pocket}>
        <Ink x={84} y={150} size={28} at={T.kd} w={420} weight={500} fill={SOFT}>048 · binding to CDK20</Ink>
        <Ink x={80} y={232} size={76} at={T.kd + 0.2} font={SERIF} w={760} dur={0.8}>Kd = 566.7 ± 256.2 nM</Ink>
        <Keyed x={84} y={300} size={48} at={T.fold} dur={0.7} w={700} parts={["about ", "15×", " tighter than 001"]}/>
        <Leader pts={[[745, 600], [640, 700]]} at={T.tag}/>
        <Tag x={480} y={748} at={T.tag + 0.3} size={30}>OUR RE-DOCKING (AutoDock Vina)</Tag>
        <Ink x={526} y={786} size={24} at={T.tag + 0.6} w={460} weight={500} fill={SOFT}>not the authors' coordinates</Ink>
        <Leader pts={[[1232, 352], [1300, 250]]} at={T.lys}/>
        <Ink x={1310} y={244} size={34} at={T.lys + 0.3} w={160}>Lys33</Ink>
        <Note x={1310} y={196} size={44} at={T.lys + 0.6} rot={-2}>hydrogen bond</Note>
        <Ink x={84} y={900} size={24} at={T.f049} w={1000} weight={500}>049: 360.0 ± 14.1 nM — also tighter than 001; the cell test went to 048</Ink>
        <g opacity={after(t, T.kd)}>
          <text x={1848} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Kd, 15×, 049: Ren 2023, p. 1448 · pose and Lys33 bond: our AutoDock Vina re-docking into the AlphaFold model</text>
          <text x={1848} y={1054} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">predicted · CDK20 surface shown see-through</text>
        </g>
      </g>}
      {t >= T.test && <g>
        <Ink x={64} y={250} size={34} at={T.test} w={560}>enzyme test (IC50)</Ink>
        <Ink x={64} y={292} size={26} at={T.test + 0.3} w={460} weight={500} fill={SOFT}>the dose that halves its activity</Ink>
        <Ink x={64} y={420} size={44} at={T.b001 - 0.2} font={SERIF} w={100}>001</Ink>
        {g1 > 0 && <g>
          <rect x={BAR.x} y={392} width={BAR.len * g1} height={28} fill={INK}/>
          {g1 > 0.98 && <path d={`M${BAR.x + BAR.len + 6} 406 h44 M${BAR.x + BAR.len + 38} 394 l12 12 l-12 12`} stroke={INK} strokeWidth={3} fill="none" strokeDasharray="8 6"/>}
        </g>}
        <Ink x={BAR.x} y={486} size={56} at={T.b001 + 0.6} font={SERIF} w={360}>&gt; 6,000 nM</Ink>
        <Ink x={64} y={620} size={44} at={T.b048 - 0.2} font={SERIF} w={100}>048</Ink>
        {g2 > 0 && <rect x={BAR.x} y={592} width={w048 * g2} height={28} fill={INK}/>}
        <Keyed x={BAR.x + 24} y={620} size={56} at={T.b048 + 0.3} dur={0.6} w={480} parts={["= ", "33.4", " ± 22.6 nM"]}/>
        <Ink x={64} y={700} size={24} at={T.b048 + 1.2} w={520} weight={500} fill={SOFT}>bars to the same scale · lower = stronger</Ink>
        <g opacity={after(t, T.test)}>
          <text x={1848} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · IC50: 001 &gt; 6,000 nM, Ren 2023, p. 1447 · 048 = 33.4 ± 22.6 nM (n = 3), p. 1448</text>
          <text x={1848} y={1054} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">kinase activity assay · tube and dose rule drawn</text>
        </g>
      </g>}
      <VO t={t} lines={S508_LINES} review={review}/>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

const Root5c = () => <>
  {/* 5-03 on the 3D table: the Blender pass (shot s503 in bl_s5c.py) with the type over it */}
  <Composition id="S503" component={S503} durationInFrames={420} fps={30} width={W} height={H}/>
  {/* 5-08 on the 3D table: the Blender pass (shot s508 in bl_s5c.py) with the type over it */}
  <Composition id="S508" component={S508} durationInFrames={480} fps={30} width={W} height={H}/>
</>;
registerRoot(Root5c);
