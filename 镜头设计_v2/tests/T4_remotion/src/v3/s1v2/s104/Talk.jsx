// 1-05 to 1-07 (00:52-01:00): D asks, B answers, C caps it with "ten-to-seventeen-years hard".
// Four layouts for three on-cam cards from three corners. Card = v3/oncam/Card.jsx, timeline = v3/oncam/props.jsx PropTimeline.
// The card is frozen in its grown (half-screen) state and re-placed with an outer transform, so every layout uses the real card.
import React from "react";
import {AbsoluteFill, staticFile} from "remotion";
import {W, H, C} from "../../core";
import {OnCamCard, CW, CH} from "../../oncam/Card";
import {useCurrentFrame} from "remotion";
import {ramp, clamp01, outCubic, handLine} from "../../core";
import {InkLine} from "../../ink";
import {InkPath} from "../../ink";
import {HandArrow} from "../../marks";
import {K, T, M, GROT, Print} from "./common";

const FOOT = "placeholder_hand.mp4";
const LINES = {
  D: {beat: "1-05", text: "So... why not just make a better one?"},
  B: {beat: "1-06", text: "Because that's way harder than it sounds."},
  C: {beat: "1-07", text: "Like, ten-to-seventeen-years hard."},
};
const HALF = {A: [490, 540], B: [1430, 540], C: [490, 540], D: [1430, 540]};
const CARD = 0.96; // card scale when grown
const VSTART = {B: 40, C: 110, D: 180};

/** The real card, grown, moved so its centre sits at (cx, cy) with on-screen width ~ w px. */
const Placed = ({who, cx, cy, w = 560, rot = 0, dim = 0, children}) => {
  const [hx, hy] = HALF[who], k = w / (CW * CARD);
  return <AbsoluteFill style={{transform: `translate(${cx - hx}px, ${cy - hy}px) rotate(${rot}deg) scale(${k})`, transformOrigin: `${hx}px ${hy}px`,
    filter: dim ? `brightness(${1 - 0.6 * dim}) saturate(${1 - 0.5 * dim})` : undefined}}>
    <OnCamCard who={who} src={staticFile(FOOT)} videoStart={VSTART[who]} dur={600}>{children}</OnCamCard>
  </AbsoluteFill>;
};
const Over = ({children}) => <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>{children}</svg>;
const Label = ({who, x, y, anchor = "start", on}) =>
  <M x={x} y={y} size={14} anchor={anchor} ls={3} color={on ? K.ink : K.dim}>{`MEMBER ${who}`}</M>;
const BeatTag = ({who, opt}) => <g>
  <M x={64} y={H - 40} size={13} color="rgba(237,235,228,0.4)" ls={1.5}>{`${LINES[who].beat} · ${who}: "${LINES[who].text}"`}</M>
  <M x={W - 64} y={H - 40} size={12} anchor="end" color="rgba(237,235,228,0.3)" ls={2}>{`${opt} · PLACEHOLDER FOOTAGE`}</M>
</g>;
const Quote = ({x, y, who, size = 34, anchor = "start", w = 300, color = K.ink, maxW}) =>
  <T x={x} y={y} size={size} w={w} anchor={anchor} color={color} ls={-0.5}>“{LINES[who].text}”</T>;

/** PropTimeline (oncam/props.jsx) with the same ink line, ticks and bracket, but the Knewave lettering swapped for the
 *  grotesk + mono of the L3 panels, so all four layouts share one type system. Card-local coords, origin = left end. */
const TimelineG = ({x, y, s = 1, start = 0}) => {
  const f = useCurrentFrame() - start;
  if (f < 0) return null;
  const L = 1150, d = outCubic(ramp(f, 0, 14)), u = L / 17.4;
  return <g transform={`translate(${x} ${y}) scale(${s})`}>
    <g filter="url(#oc-ink)">
      <InkPath points={handLine([0, 0], [L, -8], {bow: -6, over: 4})} seed={100} size={8} progress={d} pressure="nib"/>
      <circle cx={0} cy={0} r={9} fill={C.ink} opacity={clamp01(f / 3)}/>
      {Array.from({length: 17}, (_, i) => {
        const tx = u * (i + 1), late = i >= 9;
        if (tx > L * d) return null;
        return <InkLine key={i} from={[tx, late ? -30 : -18]} to={[tx, late ? 30 : 18]} seed={110 + i} size={late ? 6 : 4} color={late ? K.verm : C.ink} pressure="marker"/>;
      })}
      <InkPath points={[[u * 10, -60], [u * 10, -80], [u * 17, -82], [u * 17, -62]]} seed={130} size={6} color={K.verm} progress={ramp(f, 14, 22)} pressure="marker"/>
    </g>
    <T x={u * 13.5} y={-106} size={84} w={700} anchor="middle" color={K.ink} ls={-2} op={ramp(f, 14, 20)}>10–17 YEARS</T>
    {[0, 5, 10, 15, 17].map(n => <M key={n} x={n === 0 ? 0 : u * n} y={64} size={20} anchor="middle" ls={0} color={n >= 10 ? K.verm : K.dim} op={ramp(f, 4, 10)}>{n}</M>)}
    <M x={L + 20} y={64} size={16} ls={3} color={K.dim} op={ramp(f, 4, 10)}>YEARS</M>
  </g>;
};

// ---------------------------------------------------------------- L1 corner-relay
// Three prints stay in their own corners; the speaker's print leans in and grows, the others recede.
// A thin ink "line of talk" arcs from speaker to the one they answer. C's timeline is pulled out along the bottom edge.
const L1 = ({who}) => {
  const P = {
    D: {B: [1600, 240, 380], C: [330, 840, 380], D: [1380, 700, 560]},
    B: {B: [1380, 380, 560], C: [330, 840, 380], D: [1600, 860, 380]},
    C: {B: [1640, 220, 320], C: [520, 640, 600], D: [1640, 870, 320]},
  }[who];
  const order = ["B", "C", "D"].sort((a, b) => (a === who) - (b === who));
  const arc = {
    D: {from: [1180, 470], to: [1390, 250], bend: -0.3},
    B: {from: [1700, 560], to: [1640, 700], bend: 0.4},
    C: null,
  }[who];
  return <AbsoluteFill style={{background: K.bg}}>
    {order.map(k => <Placed key={k} who={k} cx={P[k][0]} cy={P[k][1]} w={P[k][2]} dim={k === who ? 0 : 0.75}>
      {k === "C" && who === "C" ? <TimelineG x={CW + 40} y={340} s={1.28} start={0}/> : null}
    </Placed>)}
    <Over>
      {arc ? <HandArrow from={arc.from} to={arc.to} bend={arc.bend} size={4} head={22} color={K.ink} seed={who === "D" ? 5 : 9}/> : null}
      {who === "D" ? <Quote x={120} y={300} who="D" size={40} w={300}/> : null}
      {who === "B" ? <Quote x={120} y={300} who="B" size={40} w={300}/> : null}
      <M x={64} y={84} size={13} color="rgba(237,235,228,0.25)" ls={3}>A · OFF</M>
      <BeatTag who={who} opt="L1 corner-relay"/>
    </Over>
    <Print grain={0.2} dark={0.25} band={0.05} vignette={0.35}/>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- L2 table (prints dropped on a table, facing each other)
// The three prints overlap like photos tossed onto a black table, tilted toward the empty centre.
// Whoever speaks is lifted on top. At C's line the ink timeline is laid across all three like a ruler.
const L2 = ({who}) => {
  const P = {B: {cx: 1210, cy: 360, rot: -5}, C: {cx: 640, cy: 650, rot: 6}, D: {cx: 1340, cy: 790, rot: -9}};
  const order = ["B", "D", "C"].filter(k => k !== who).concat(who);
  return <AbsoluteFill style={{background: K.bg}}>
    {order.map(k => <Placed key={k} who={k} {...P[k]} w={k === who ? 640 : 560} dim={k === who ? 0 : 0.45}>
      {k === "C" && who === "C" ? <TimelineG x={-80} y={-60} s={1.7} start={0}/> : null}
    </Placed>)}
    <Over>
      {who === "D" ? <Quote x={110} y={200} who="D" size={36}/> : null}
      {who === "B" ? <Quote x={110} y={200} who="B" size={36}/> : null}
      <BeatTag who={who} opt="L2 table"/>
    </Over>
    <Print grain={0.22} dark={0.28} band={0.06} vignette={0.45}/>
  </AbsoluteFill>;
};

// ---------------------------------------------------------------- L3 conversation-line (three-up strip on one hairline)
// Strict split screen: C | B | D across the frame, staggered by corner (B high, C and D low), all on one hairline at eye height.
// The hairline is the conversation; on C's line it becomes the 10-17 years axis running under all three prints.
const L3 = ({who}) => {
  const X = {C: 340, B: 960, D: 1580}, Y = {C: 590, B: 470, D: 590};
  const eye = 540;
  const order = ["C", "B", "D"];
  return <AbsoluteFill style={{background: K.bg}}>
    <Over>
      <line x1={0} y1={eye} x2={W} y2={eye} stroke={K.ink} strokeWidth={1.2} opacity={who === "C" ? 0 : 0.35}/>
    </Over>
    {order.map(k => <Placed key={k} who={k} cx={X[k]} cy={Y[k] - (who === "C" ? 60 : 0)} w={540} rot={0} dim={k === who ? 0 : 0.55}/>)}
    <Over>
      {who === "C" ? <TimelineAxis y={1010}/> : null}
      {who !== "C" ? <g>
        {/* the speaker's line runs along the hairline toward whoever they're talking to */}
        <circle cx={who === "D" ? 1300 : 680} cy={eye} r={6} fill={K.verm}/>
        <line x1={who === "D" ? 1300 : 680} y1={eye} x2={who === "D" ? 1240 : 620} y2={eye} stroke={K.verm} strokeWidth={3}/>
      </g> : null}
      {who !== "C" ? ["C", "B", "D"].map(k => <Label key={k} who={k} x={X[k]} y={Y[k] + 330} anchor="middle" on={k === who}/>) : null}
      {who !== "C" ? <Quote x={W / 2} y={110} who={who} size={34} anchor="middle"/> : null}
      <BeatTag who={who} opt="L3 conversation-line"/>
    </Over>
    <Print grain={0.2} dark={0.25} band={0.05} vignette={0.3}/>
  </AbsoluteFill>;
};
// L3 variant of the 10-17 years device, after On Kawara's date paintings: seventeen small panels, one per year,
// numerals hand-set in bone; years 10-17 are painted vermilion. Runs under all three prints.
const TimelineAxis = ({y}) => {
  const n = 17, gap = 10, x0 = 110, x1 = 1810, pw = (x1 - x0 - gap * (n - 1)) / n, ph = pw * 0.72;
  return <g>
    {Array.from({length: n}, (_, i) => {
      const yr = i + 1, hot = yr >= 10, x = x0 + i * (pw + gap);
      return <g key={i}>
        <rect x={x} y={y - ph} width={pw} height={ph} fill={hot ? K.verm : "#1A1A1C"} stroke={hot ? "none" : "rgba(237,235,228,0.12)"}/>
        <T x={x + pw / 2} y={y - ph / 2 + 12} size={34} w={500} anchor="middle" color={hot ? K.bg : K.ink} op={hot ? 1 : 0.8}>{yr}</T>
      </g>;
    })}
    <M x={x0} y={y + 34} size={14} color={K.dim} ls={3}>YEAR</M>
    <T x={x1} y={y - ph - 22} size={52} w={700} anchor="end" color={K.ink} ls={-1}>10–17 YEARS</T>
  </g>;
};

// ---------------------------------------------------------------- L4 shot / reverse-shot (one big, two chips)
// Classic: the speaker's print fills its half; the other two shrink to chips in their own corners and "look" at it
// via a short ink eye-line. At C's line, C pulls the existing ink timeline out across the other half, between B's and D's chips.
const L4 = ({who}) => {
  const big = {B: [1400, 540], C: [520, 540], D: [1400, 540]}, chip = {B: [1770, 170], C: [150, 910], D: [1770, 910]};
  const others = ["B", "C", "D"].filter(k => k !== who);
  const eye = {
    D: [[1690, 230], [1590, 300]],  // B chip looks down at D
    B: [[1690, 850], [1590, 780]],  // D chip looks up at B
    C: null,
  }[who];
  return <AbsoluteFill style={{background: K.bg}}>
    <Placed who={who} cx={big[who][0]} cy={big[who][1]} w={who === "C" ? 760 : 780}>
      {who === "C" ? <TimelineG x={CW + 60} y={CH * 0.5} s={0.78} start={0}/> : null}
    </Placed>
    {others.map(k => <Placed key={k} who={k} cx={chip[k][0]} cy={chip[k][1]} w={230} dim={0.4}/>)}
    <Over>
      {eye ? <HandArrow from={eye[0]} to={eye[1]} bend={0.2} size={3.5} head={16} color={K.ink} seed={3}/> : null}
      {who !== "C" ? <Quote x={120} y={540} who={who} size={38}/> : null}
      <BeatTag who={who} opt="L4 shot-reverse"/>
    </Over>
    <Print grain={0.2} dark={0.25} band={0.05} vignette={0.3}/>
  </AbsoluteFill>;
};

export const LAYOUTS = [
  {id: "L1", C: L1, slug: "opt1_corner-relay"},
  {id: "L2", C: L2, slug: "opt2_table"},
  {id: "L3", C: L3, slug: "opt3_conversation-line"},
  {id: "L4", C: L4, slug: "opt4_shot-reverse"},
];
