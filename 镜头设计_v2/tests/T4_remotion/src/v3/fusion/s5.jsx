// HKBU SCIE1007 coursework science video. S1 motion test, fusion direction: type, marks and photo prints on the table.
// The picture under it (base.mp4) comes from 镜头设计_v3/styleframes/art/fusion/s1/code/base.py. Both read the same camera, so everything here is placed in table coordinates and moves with the table.
// Words on screen follow script_v3.3.md. Times are seconds on the script's clock, the same as timeline.py; TL.u turns each frame of the film into that clock, from 节奏表.csv. Props: review shows the script line along the top; base=false leaves the type on bone for quick stills.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import TL from "./s1_timeline.json";
import W3C from "./w3_count.json";
import HK from "./hk_track.json";

const FPS = TL.fps, N = TL.n, W = 1920, H = 1080;
// DARK: the pen notes' ink. entry.jsx uses a dark red; here it is INK (04 §6 allows five colours only), because the review (05, round 2, item 4) keeps red for the one thing that matters on screen.
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

// ---------------------------------------------------------------- 4-10 · the wall of designs
/** 4-10 (09:49-10:14, A's voice-over). The AI's answer is a print that lands on the table: 8,918 designs as a halftone field, 98 x 91 dots, which is the count the paper reports.
 * The point of the picture is scale, not the numbers: the field is printed at full size, one dot lifts off and turns into a key, the key is tried in the lock printed on the same sheet
 * and gets a score, then the whole field collapses to a small stamp while the 54 groups stay full size, and seven of those come down onto the table as keys you could pick up. The
 * three counts are set in one column on the left, each at the size of what it counts: 8,918 huge, 54 middle, 7 small and red. All of it is drawn, so the source line says
 * Illustration; 8,918 / 54 / 7 are the paper's (R23 p1444 and p1447, see 4-10_数字对照.md). Starts and ends on the bare bone table. */
const S410_T = {land: 0.0, print: 0.35, count: 0.9, many: 3.1, lift: 5.3, key: 6.6, insert: 8.0, turn: 9.0, score: 10.4,
                grouped: 12.6, short: 14.6, collapse: 15.6, seven: 18.4, keys: 19.4, funnel: 21.6};
const S410_LINES = [[0, "It came back with 8,918 brand-new designs."], [3.1, "Way too many to make."], [5.3, "So each key gets tried in a virtual lock."], [10.4, "That's docking: the computer predicts how a molecule might sit in the pocket, and scores the fit."], [17.1, "Similar designs get grouped,"], [18.9, "54 make the shortlist,"], [20.9, "and chemists pick just seven to make."]];
const S410_COLS = 98, S410_ROWS = 91, S410_CELL = 7.0;            // 98 x 91 = 8,918
const S410_FX = 1046, S410_FY = 512;                              // the middle of the printed field
const S410_X0 = S410_FX - (S410_COLS - 1) * S410_CELL / 2, S410_Y0 = S410_FY - (S410_ROWS - 1) * S410_CELL / 2;
const S410_WALL = [];
for (let j = 0; j < S410_ROWS; j++) for (let i = 0; i < S410_COLS; i++) S410_WALL.push([S410_X0 + i * S410_CELL, S410_Y0 + j * S410_CELL]);
const dots = (pts, r = 1.55) => pts.map(([x, y]) => `M${(x - r).toFixed(1)} ${(y - r).toFixed(1)}h${(2 * r).toFixed(1)}v${(2 * r).toFixed(1)}h${(-2 * r).toFixed(1)}z`).join("");
const S410_ALL = dots(S410_WALL);
/** 54 of the 8,918, spread by a fixed seed so every render and every check frame has the same 54. */
const S410_PICK = (() => {
  let s = 8918; const rnd = () => ((s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff), out = [], seen = new Set();
  while (out.length < 54) { const k = Math.floor(rnd() * S410_WALL.length); if (!seen.has(k)) { seen.add(k); out.push(k); } }
  return out;
})();
const S410_GROUP = S410_PICK.map(k => S410_WALL[k]);
const S410_SEVEN = [3, 11, 19, 27, 34, 42, 50].map(i => S410_GROUP[i]);
const S410_FROM = S410_WALL[4444];
/** The 54 come out as a 9 x 6 block on the sheet, at a size you can actually count, and seven of them light up. */
const S410_BLOCK = (() => { const out = []; for (let r = 0; r < 6; r++) for (let c = 0; c < 9; c++) out.push([896 + c * 46, 562 + r * 46]); return out; })();
const S410_SEVEN_AT = new Set([3, 9, 15, 19, 31, 43, 47]);
const S410_KEYS = [0, 1, 2, 3, 4, 5, 6].map(i => [780 + i * 126]);
/** A key drawn in ink: bow, shaft, two teeth. rot is in degrees. */
const Key = ({x, y, s = 1, rot = 0, w = 4.5, opacity = 1}) => <g transform={`translate(${x} ${y}) rotate(${rot}) scale(${s})`} opacity={opacity}
  fill="none" stroke={INK} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round">
  <circle cx={0} cy={0} r={25}/>
  <circle cx={0} cy={0} r={11}/>
  <line x1={25} y1={0} x2={104} y2={0}/>
  <path d="M78 0 L78 22 L90 22 L90 0 M92 0 L92 30 L104 30"/>
</g>;
const S410Flat = ({review = true, fps = 30}) => {
  const t = useCurrentFrame() / fps, V = S410_T;
  const land = smooth((t - V.land) / 0.9);                                         // the print lands on the table
  const press = smooth((t - V.print) / 1.6), pressX = S410_X0 - 60 + press * 780;   // the press runs over the print, left to right
  const count = Math.round(8918 * smooth((t - V.count) / 1.5));
  const lift = smooth((t - V.lift) / 0.9);                                         // one design leaves the field
  const asKey = smooth((t - V.key) / 0.9);                                         // and becomes a key
  const inset = smooth((t - V.insert) / 0.9);                                      // the key goes into the lock
  const turn = Math.min(1, Math.max(0, (t - V.turn) / 0.8));
  const score = smooth((t - V.score) / 1.6);
  const group = smooth((t - V.grouped) / 1.0);                                     // the 54 ring up in place
  const collapse = smooth((t - V.collapse) / 1.4);                                  // 8,918 shrinks to a stamp: the scale is the message
  const block = smooth((t - V.collapse - 0.5) / 0.7);                               // and the 54 come out at full size
  const seven = smooth((t - V.seven) / 0.9);
  const keysIn = smooth((t - V.keys) / 1.2);
  const funnel = smooth((t - V.funnel) / 1.0);
  const sx = 1 - 0.68 * collapse;
  const fx0 = S410_FX, fy0 = S410_FY, fx1 = 864, fy1 = 306;
  const fieldT = `translate(${fx0 + (fx1 - fx0) * collapse} ${fy0 + (fy1 - fy0) * collapse}) scale(${sx}) translate(${-fx0} ${-fy0})`;
  const LOCK = [1520, 392];
  const bug = [1516, 560 - 32 * inset];
  const fx = S410_FROM[0] + (bug[0] - S410_FROM[0]) * inset, fy = S410_FROM[1] + (bug[1] - S410_FROM[1]) * inset;
  const keyRot = -90 + 10 * turn;
  const ringsOut = 1 - smooth((t - V.collapse - 0.3) / 0.5);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 1 / Tool: docking / virtual screening</text>

      {/* the print: the AI's answer is a sheet on the table, with the lock printed beside the field */}
      <g transform={`translate(0 ${-26 * (1 - land)})`} opacity={0.15 + 0.85 * land}>
        <rect x={248} y={182} width={1576} height={700} rx={6} fill="#3C3228" opacity={0.15 * land} style={{filter: "blur(22px)"}}/>
        <rect x={220} y={150} width={1580} height={700} rx={4} fill="#F7F3EA"/>
        <rect x={220} y={150} width={1580} height={700} rx={4} fill="none" stroke="#E1DCD1" strokeWidth={2}/>

        {/* 8,918 designs, printed as a halftone field; it shrinks to a stamp when the funnel starts */}
        <g transform={fieldT}>
          <mask id="s410press"><rect x={S410_X0 - 80} y={S410_Y0 - 80} width={Math.max(0, pressX - S410_X0 + 80)} height={640 + 160} fill="#fff"/></mask>
          <path d={S410_ALL} fill={INK} opacity={0.62} mask="url(#s410press)"/>
        </g>

        {/* the 54: first they ring up where they sit in the field, then they come out as a full-size block */}
        {group > 0 && ringsOut > 0 && S410_GROUP.map(([x, y], i) => {
          const p = smooth((t - V.grouped - i * 0.012) / 0.4), tight = smooth((t - V.grouped - 0.3 - i * 0.01) / 1.0);
          return p > 0 ? <g key={i} opacity={ringsOut}>
            <circle cx={x} cy={y} r={16} fill="#F7F3EA" opacity={0.85 * p}/>
            <circle cx={x} cy={y} r={17 - 5 * tight} fill="none" stroke={INK} strokeWidth={2 + tight} opacity={(0.45 + 0.55 * tight) * p}/>
          </g> : null;
        })}
        {block > 0 && <g opacity={smooth((t - V.collapse - 1.0) / 0.5)} stroke={INK} strokeWidth={2} fill="none">
          <line x1={986} y1={470} x2={986} y2={536} strokeDasharray="5 6"/>
          <path d="M978 528 L986 538 L994 528"/>
        </g>}
        {block > 0 && S410_BLOCK.map(([x, y], i) => {
          const p = smooth((t - V.collapse - 0.5 - i * 0.008) / 0.4), lit = S410_SEVEN_AT.has(i) ? smooth((t - V.seven) / 0.6) : 0;
          return <g key={i} opacity={p}>
            <circle cx={x} cy={y} r={13} fill={lit > 0 ? INK : "none"} opacity={lit}/>
            <circle cx={x} cy={y} r={13} fill="none" stroke={INK} strokeWidth={2} strokeOpacity={0.75}/>
          </g>;
        })}

        {/* the lock, printed on the same sheet: a plate with four screws and a keyhole */}
        <g opacity={after(t, V.lift - 0.6, 0.6) * (1 - 0.3 * funnel)}>
          <text x={LOCK[0]} y={208} textAnchor="middle" fontFamily={SANS} fontSize={26} fontWeight={600} fill={INK}>the pocket</text>
          <rect x={1400} y={224} width={248} height={300} rx={10} fill="#F2EEE4" stroke={INK} strokeWidth={2.5}/>
          <rect x={1408} y={232} width={232} height={284} rx={7} fill="none" stroke={INK} strokeWidth={1} opacity={0.3}/>
          {[[1424, 248], [1624, 248], [1424, 500], [1624, 500]].map(([cx, cy], i) => <g key={i} stroke={INK} strokeWidth={2}>
            <circle cx={cx} cy={cy} r={6.5} fill="none"/>
            <line x1={cx - 4.5} y1={cy + 3} x2={cx + 4.5} y2={cy - 3}/>
          </g>)}
          <circle cx={LOCK[0]} cy={LOCK[1]} r={34} fill="none" stroke={INK} strokeWidth={3.5}/>
          <path d={`M${LOCK[0] - 15} ${LOCK[1] + 29} L${LOCK[0] + 15} ${LOCK[1] + 31} L${LOCK[0] + 28} ${LOCK[1] + 112} L${LOCK[0] - 28} ${LOCK[1] + 112} Z`} fill="none" stroke={INK} strokeWidth={3.5} strokeLinejoin="round"/>
          <line x1={1408} y1={700} x2={1640} y2={700} stroke="#CFC9BC" strokeWidth={4} strokeLinecap="round"/>
          <line x1={1408} y1={700} x2={1408 + 232 * score} y2={700} stroke={INK} strokeWidth={11} strokeLinecap="round"/>
          <text x={1408} y={740} fontFamily={SANS} fontSize={22} fontWeight={600} fill={SOFT}>fit: docking score</text>
        </g>

        {/* the count column: each number set at the size of what it counts */}
        <Ink x={300} y={330} size={132} at={V.count} font={SERIF} w={640} dur={0.5}>{count.toLocaleString("en-US")}</Ink>
        <Ink x={304} y={380} size={30} at={V.count + 0.5} w={470}>designs from the AI</Ink>
        <Note x={304} y={452} size={46} at={V.count + 1.1} rot={-1.5}>one dot = one design</Note>
        <Note x={304} y={546} size={48} at={V.many} rot={-2}>way too many to make</Note>
        <Ink x={300} y={700} size={104} at={V.short} font={SERIF} w={300} dur={0.45}>54</Ink>
        <Ink x={304} y={744} size={30} at={V.short + 0.4} w={420}>make the shortlist</Ink>
        <Ink x={300} y={838} size={96} at={V.seven + 0.5} font={SERIF} fill={RED} w={260} dur={0.45}>7</Ink>
        <Ink x={372} y={838} size={30} at={V.seven + 0.9} w={420}>to make</Ink>

      </g>

      {/* one design: a dot, then a key, then a key in the lock */}
      {lift > 0 && asKey < 1 && <circle cx={fx} cy={fy - 56 * lift} r={4 + 3 * lift} fill={INK}/>}
      {(asKey > 0 || inset > 0) && <Key x={bug[0]} y={bug[1]} s={0.55 + 0.07 * asKey} rot={keyRot} opacity={asKey > 0 ? 1 : 0}/>}

      {/* the seven, on the table in front of the print: things you could pick up */}
      {seven > 0 && S410_KEYS.map(([kx], i) => {
        const p = smooth((t - V.keys - i * 0.09) / 0.5);
        if (p <= 0) return null;
        const ky = 906 - 46 * (1 - p), a = -22 + (i % 2 ? 5 : -5);
        return <g key={i}>
          <ellipse cx={kx + 48} cy={922} rx={64} ry={7} fill={INK} opacity={0.11 * p}/>
          <Key x={kx} y={ky} s={0.86} rot={a} w={5} opacity={p}/>
        </g>;
      })}

      {review && <text x={64} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>VO (A): {[...S410_LINES].reverse().find(([a]) => t >= a)[1]}</text>}
      <text x={W - 72} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · counts 8,918 / 54 / 7: Ren 2023</text>
      <text x={W - 72} y={1056} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">docking and clustering drawn after the paper's description · L07 p.13</text>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

// ---------------------------------------------------------------- 5-04 · the key that barely turns
/** 5-04 (11:02-11:26, C's voice-over). Two things side by side on the table: the lock with 001's key in it, which only rocks a little and never turns; and the enzyme's activity gauge
 * with a dose axis. IC50 is the amount that cuts the activity to half: the gauge drops to the half line while the dose marker runs right, and it keeps running off the edge of the
 * sheet because 001's IC50 is above 6,000 nM, the last tick and then some. The number is the paper's (R23 p1447: "an IC50 value of >6000 nM in CDK20 kinase activity assay"); the
 * gauge is drawn, so the source line says Illustration. The turn and the wobble are the film's own key metaphor, not a measurement. Starts and ends on the bare bone table. */
const S504_T = {seat: 0.8, try: 3.0, ic50: 10.9, half: 12.6, dose: 14.0, past: 18.2, weak: 20.6};
const S504_LINES = [[0, "But then came a second test."], [2.7, "Because grabbing a lock isn't the same as jamming it."], [7.2, "Does 001 actually stop CDK20 from working?"], [10.8, "That's measured as IC50: how much you need to cut the enzyme's activity in half."], [18.0, "For 001? Above 6,000 nanomolar."], [20.3, "Weak."]];
const S504 = ({review = true, fps = 30}) => {
  const t = useCurrentFrame() / fps, V = S504_T;
  const seat = smooth((t - V.seat) / 0.9);                                      // the key slides in
  const push = smooth((t - V.try) / 1.6);                                       // it tries to turn
  const rock = t > V.try ? Math.sin((t - V.try) * 24) * Math.max(0, 1 - (t - V.try) / 2.2) : 0;
  const keyRot = 7 * push + 3 * rock;                                     // never past a few degrees: the lock does not turn
  const ic = smooth((t - V.ic50) / 0.9);                                        // the gauge comes in
  const half = smooth((t - V.half) / 0.8);                                      // the half line
  const dose = smooth((t - V.dose) / 3.4);                                      // the dose marker runs right
  const past = smooth((t - V.past) / 1.2);                                      // and off the edge of the paper
  const weak = smooth((t - V.weak) / 0.8);
  const act = 1 - 0.5 * half;                                                   // activity falls to half, and stops there
  const AX0 = 900, AX1 = 1620, AXY = 780;
  const dx = AX0 + (AX1 - AX0) * dose + 300 * past;
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 2 / Results</text>

      {/* the lock, with 001's key in it */}
      <g>
        <rect x={196} y={172} width={392} height={470} rx={14} fill="#3C3228" opacity={0.13} style={{filter: "blur(18px)"}}/>
        <rect x={180} y={156} width={392} height={470} rx={12} fill="#F7F3EA" stroke="#E1DCD1" strokeWidth={2}/>
        {[[212, 188], [540, 188], [212, 594], [540, 594]].map(([cx, cy], i) => <g key={i} stroke={INK} strokeWidth={2.5}>
          <circle cx={cx} cy={cy} r={8} fill="none"/>
          <line x1={cx - 5.5} y1={cy + 4} x2={cx + 5.5} y2={cy - 4}/>
        </g>)}
        <text x={376} y={214} textAnchor="middle" fontFamily={SANS} fontSize={24} fontWeight={600} fill={SOFT}>CDK20</text>
        <circle cx={376} cy={380} r={50} fill="none" stroke={INK} strokeWidth={5}/>
        <path d={`M${376 - 22} ${380 + 42} L${376 + 22} ${380 + 42} L${376 + 33} ${380 + 180} L${376 - 33} ${380 + 180} Z`} fill="none" stroke={INK} strokeWidth={5} strokeLinejoin="round"/>
        {/* 001's key: bow to the left, shaft across the plate, bit in the keyway — it turns about the keyhole, by a few degrees at most */}
        <g opacity={0.2 + 0.8 * seat} transform={`translate(0 ${260 * (1 - seat)})`}>
          <g transform={`translate(${376} ${380}) rotate(${keyRot}) translate(${-376} ${-380})`}>
            <Key x={376 - 156} y={380} s={1.5} w={4.4}/>
          </g>
        </g>
        <text x={376} y={660} textAnchor="middle" fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK} opacity={after(t, V.seat + 0.4)}>001's key</text>
        {/* the wobble: short strokes either side of the bow, only while it is being forced */}
        {t > V.try + 0.5 && t < V.try + 2.6 && <g stroke={INK} strokeWidth={3} strokeLinecap="round" opacity={0.75}
          transform={`translate(376 520) rotate(${keyRot})`}>
          {[-1, 1].map((s, i) => <g key={i} transform={`translate(${s * 40} 0)`}>
            <path d={`M0 ${-16} q${s * 8} 16 0 32`} fill="none"/>
            <path d={`M${s * 8} ${-22} q${s * 7} 22 0 44`} fill="none" opacity={0.6}/>
          </g>)}
        </g>}
        <g opacity={1 - smooth((t - V.ic50 + 0.6) / 0.8)}><Note x={196} y={740} size={44} at={V.try + 0.9} rot={-1.5}>in the lock, not switching it off</Note></g>
      </g>

      {/* the activity gauge and the dose axis */}
      <g opacity={ic}>
        <text x={AX0 - 148} y={236} fontFamily={SANS} fontSize={28} fontWeight={600} fill={INK}>enzyme activity</text>
        {/* the column: 100% at the top, 0 at the axis */}
        <line x1={AX0 - 120} y1={AXY} x2={AX0 - 120} y2={300} stroke={INK} strokeWidth={3}/>
        <line x1={AX0 - 132} y1={300} x2={AX0 - 108} y2={300} stroke={INK} strokeWidth={3}/>
        <text x={AX0 - 146} y={306} textAnchor="end" fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>100%</text>
        <rect x={AX0 - 132} y={300 + (AXY - 300) * (1 - act)} width={24} height={(AXY - 300) * act} fill={INK} opacity={0.9}/>
        {/* the half line */}
        <g opacity={half}>
          <line x1={AX0 - 150} y1={540} x2={AX1 + 80} y2={540} stroke={INK} strokeWidth={2.5} strokeDasharray="9 8"/>
          <text x={AX1 + 70} y={524} textAnchor="end" fontFamily={SANS} fontSize={24} fontWeight={600} fill={INK}>half</text>
        </g>
        {/* the dose axis */}
        <line x1={AX0} y1={AXY} x2={AX1} y2={AXY} stroke={INK} strokeWidth={3}/>
        {past > 0 && <line x1={AX1} y1={AXY} x2={AX1 + 300 * past} y2={AXY} stroke={INK} strokeWidth={3} strokeDasharray="18 12" opacity={0.8}/>}
        {[0, 1, 2, 3, 4, 5, 6].map(i => {
          const x = AX0 + (AX1 - AX0) * i / 6;
          return <g key={i}><line x1={x} y1={AXY} x2={x} y2={AXY + 14} stroke={INK} strokeWidth={3}/></g>;
        })}
        <text x={AX0} y={AXY + 52} fontFamily={SANS} fontSize={24} fontWeight={600} fill={SOFT}>little</text>
        <text x={AX1} y={AXY + 52} textAnchor="end" fontFamily={SANS} fontSize={24} fontWeight={600} fill={SOFT}>a lot of 001</text>
        {/* the dose marker: runs to the end of the axis, then off the paper */}
        <g opacity={dose > 0 ? 1 : 0}>
          <line x1={dx} y1={AXY - 26} x2={dx} y2={AXY + 30} stroke={INK} strokeWidth={4}/>
          <path d={`M${dx - 10} ${AXY - 40} L${dx} ${AXY - 26} L${dx + 10} ${AXY - 40}`} fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round"/>
        </g>
        <Ink x={AX0} y={900} size={30} at={V.ic50 + 0.6} w={860}>IC50 = the amount that cuts the enzyme's activity in half</Ink>
      </g>

      {/* the number: above the last tick, and the arrow keeps going */}
      <g opacity={after(t, V.past - 0.4)}>
        <Ink x={900} y={610} size={116} at={V.past - 0.3} font={SERIF} w={800} dur={0.5}>&gt; 6,000 nM</Ink>
        <Ink x={906} y={656} size={28} at={V.past + 0.2} w={520}>that is more than 6 µM</Ink>
      </g>
      <g opacity={weak}>
        <Note x={906} y={740} size={86} at={V.weak} rot={-2.5} fill={RED}>weak.</Note>
      </g>

      {review && <text x={64} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT}>VO (C): {[...S504_LINES].reverse().find(([a]) => t >= a)[1]}</text>}
      <text x={W - 72} y={1018} fontFamily={SANS} fontSize={24} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · IC50 &gt; 6,000 nM: Ren 2023</text>
      <text x={W - 72} y={1056} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">kinase activity assay · key and lock drawn</text>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};

/** 4-10 on the table, second version (11-10). The Blender pass is shot `s410` in inserts/bl_s5.py; camera stations in s4/4-10_机位表.md.
 * 0-5 s: W3's last view held, the two key carpets; 5-7.2 s the camera comes down to the lock; the key W3 hovered rises from the carpet, comes in from the left and is
 * pushed up to the keyhole; the three rings click round (the score); it goes back to its place. 16.9-18.9 s the camera backs off to the end view: an empty cell in front,
 * CDK20 and the lock behind. The keys that miss the shortlist rise out of the frame, far rows first, 54 stay; 47 more rise out and seven slide into the empty front cell.
 * Everything physical is the render; this layer is only type, two pen notes and the source line. Counts are the paper's (R23 8,918 / 54 / 7, p1444 and p1447).
 * Type sits in the empty cells on the left (x 50-480, y 170-560), the box given to BL_CAMCHECK as BL_KEEPOUT. Red: only the 7. Nothing moves in the first second. */
const S410 = ({file = "fusion_s1/s5_410_3d.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps;
  const count = Math.round(8918 * smooth((t - 1.0) / 1.6));
  const first = 1 - after(t, 16.9, 0.4);                                  // 8,918 and the two notes leave as the camera backs off; 54 and 7 take their place
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={after(t, 1.0)}><text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 1 / Tool: docking / virtual screening</text></g>
      {first > 0 && <g opacity={first}>
        <Ink x={104} y={290} size={120} at={1.0} font={SERIF} w={380} dur={0.5}>{count.toLocaleString("en-US")}</Ink>
        <Ink x={108} y={334} size={28} at={1.6} w={480}>designs came back from the AI</Ink>
        <Note x={108} y={414} size={46} at={2.2} rot={-1.5}>one design = one key</Note>
        <Note x={108} y={500} size={46} at={3.1} rot={-2}>way too many to make</Note>
      </g>}
      <Ink x={104} y={290} size={104} at={18.9} font={SERIF} w={220} dur={0.45}>54</Ink>
      <Ink x={108} y={334} size={28} at={19.3} w={300}>make the shortlist</Ink>
      <Ink x={104} y={436} size={96} at={20.9} font={SERIF} fill={RED} w={120} dur={0.45}>7</Ink>
      <Ink x={170} y={436} size={28} at={21.3} w={200}>to make</Ink>
      {review && t >= 1.0 && <text x={64} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT}>VO (A): {[...S410_LINES].reverse().find(([a]) => t >= a)[1]}</text>}
      <g opacity={after(t, 1.0)}>
        <text x={1848} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · counts 8,918 / 54 / 7: Ren 2023, pp. 1444, 1447</text>
        <text x={1848} y={1054} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">docking and clustering drawn after the paper's description · L07 p.13</text>
      </g>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};
/** 5-04 on the table, first 3D version (11-10). The Blender pass is shot `s504` in inserts/bl_s5.py; it starts on 4-10's last frame (5-03 is still to be made and should end there).
 * 001's key (the one 4-10 tried, one of the seven) rises from the row and the camera follows it back to the lock; it reaches the keyhole, tries to turn, gets about
 * 7 degrees and stops; the rings click once. Then the camera backs off to cell 21: a glass tube of enzyme activity (Klein blue, CDK20's colour) and an ink dose rule of
 * six steps with no numbers. The marker runs the six steps and the blue drops only a little; it runs past the end of the rule to the cell's rim before the blue reaches
 * the half line. The number is the paper's (R23 p1447, "an IC50 value of >6000 nM in CDK20 kinase activity assay"; see s4/5-04_数字对照.md). Labels sit next to the
 * things they name, at their places in the assay view (projected from the camera in bl_s5.py). Red: only "weak.". Nothing moves in the first second. */
const S504_3D = ({file = "fusion_s1/s5_504_3d.mp4", fps = 30, review = true}) => {
  const t = useCurrentFrame() / fps;
  const lockNote = 1 - after(t, 10.4, 0.4);
  const assay = after(t, 12.4, 0.5);
  return <Clock.Provider value={t}><AbsoluteFill style={{background: BONE}}>
    <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={after(t, 1.0)}><text x={1856} y={92} fontFamily={SANS} fontSize={36} fontWeight={600} fill={INK} textAnchor="end">Objective 2 / Results</text></g>
      {lockNote > 0 && <g opacity={lockNote}>
        <Note x={84} y={420} size={46} at={5.6} rot={-1.5}>in the lock,</Note>
        <Note x={84} y={478} size={46} at={6.3} rot={-2}>not switching it off</Note>
      </g>}
      {assay > 0 && <g opacity={assay}>
        <Ink x={600} y={176} size={28} at={12.6} anchor="middle" w={300}>enzyme activity</Ink>
        <Ink x={684} y={446} size={24} at={13.0} w={120}>half</Ink>
        <Ink x={729} y={852} size={24} at={13.4} anchor="middle" w={160}>little</Ink>
        <Ink x={1585} y={852} size={24} at={13.6} anchor="middle" w={220}>a lot of 001</Ink>
        <Ink x={64} y={300} size={30} at={12.8} w={430}>IC50 = how much it takes</Ink>
        <Ink x={64} y={342} size={30} at={13.1} w={430}>to cut the enzyme's</Ink>
        <Ink x={64} y={384} size={30} at={13.4} w={430}>activity in half</Ink>
      </g>}
      <Ink x={64} y={540} size={96} at={18.0} font={SERIF} w={460} dur={0.5}>&gt; 6,000 nM</Ink>
      <Ink x={68} y={584} size={28} at={18.5} w={400}>that is more than 6 µM</Ink>
      <Note x={70} y={700} size={86} at={20.3} rot={-2.5} fill={RED}>weak.</Note>
      {review && t >= 1.0 && <text x={64} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT}>VO (C): {[...S504_LINES].reverse().find(([a]) => t >= a)[1]}</text>}
      <g opacity={after(t, 1.0)}>
        <text x={1848} y={1024} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">Illustration · IC50 &gt; 6,000 nM: Ren 2023, p. 1447</text>
        <text x={1848} y={1054} fontFamily={SANS} fontSize={22} fontWeight={500} fill={SOFT} textAnchor="end">kinase activity assay · key, lock, tube and dose rule drawn</text>
      </g>
    </svg>
  </AbsoluteFill></Clock.Provider>;
};
const Root5 = () => <>
  {/* 4-10 on the 3D table: the Blender pass (shot s410) with the type over it */}
  <Composition id="S410" component={S410} durationInFrames={750} fps={30} width={W} height={H}/>
  <Composition id="S410-4K" component={S410} durationInFrames={1500} fps={60} width={W} height={H} defaultProps={{file: "fusion_s1/s5_410_3d_60.mp4", fps: 60, review: false}}/>
  {/* the first flat version, kept only for comparison (director: flat paper reads like a slide) */}
  <Composition id="S410Flat" component={S410Flat} durationInFrames={750} fps={30} width={W} height={H}/>
  <Composition id="S504Flat" component={S504} durationInFrames={720} fps={30} width={W} height={H}/>
  {/* 5-04 on the 3D table: the Blender pass (shot s504) with the type over it */}
  <Composition id="S504" component={S504_3D} durationInFrames={720} fps={30} width={W} height={H}/>
  <Composition id="S504-4K" component={S504_3D} durationInFrames={1440} fps={60} width={W} height={H} defaultProps={{file: "fusion_s1/s5_504_3d_60.mp4", fps: 60, review: false}}/>
</>;
registerRoot(Root5);