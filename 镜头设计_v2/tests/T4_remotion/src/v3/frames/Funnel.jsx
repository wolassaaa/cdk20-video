// V3-Funnel: 8,918 -> 54 -> 7 -> 1. Digital pixels go in, a hand-drawn funnel squeezes, the counts get struck out.
import React from "react";
import {C, W, H, catmull, hash, loopPts, clamp01} from "../core";
import {InkPath, InkLine, RoughPolygon, RoughCircle} from "../ink";
import {HandArrow, HandCircle, StrikeOut, Highlight} from "../marks";
import {HandText, Mono, monoW} from "../type";
import {Stage, InkDefs, Dust, Halftone, linear} from "../texture";
import {Chrome} from "../chrome";
import {InkMolecule, M001} from "../molecule";

// funnel geometry (shared with the demo)
export const FUN = {
  top: [[110, 330], [420, 350], [720, 410], [1000, 500], [1180, 572], [1430, 618], [1560, 628]],
  bot: [[110, 900], [420, 880], [720, 830], [1000, 740], [1180, 690], [1430, 664], [1560, 660]],
  gates: [720, 1180, 1430],
};
const yAt = (curve, x) => {
  for (let i = 1; i < curve.length; i++) if (x <= curve[i][0]) {
    const a = curve[i - 1], b = curve[i], t = (x - a[0]) / (b[0] - a[0]);
    return a[1] + (b[1] - a[1]) * t;
  }
  return curve[curve.length - 1][1];
};
export const funnelSpan = x => [yAt(FUN.top, x), yAt(FUN.bot, x)];
export const funnelD = () => { const t = catmull(FUN.top, false, 12), b = catmull(FUN.bot, false, 12).reverse(); return [...t, ...b].map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("") + "Z"; };

/** Exactly n crisp cyan pixels scattered in the funnel mouth (x0..x1), as one path. */
export const PixelCloud = ({n = 8918, x0 = 128, x1 = 700, size = 2.6, color = C.cyan, reveal = 1, seed = 1, opacity = 1, squeeze = 0}) => {
  const cand = [];
  const step = 4.9;
  for (let x = x0; x < x1; x += step) {
    const [a, b] = funnelSpan(x);
    const u = (x - x0) / (x1 - x0), edge = Math.max(0, u - 0.7) * 2.6 + Math.max(0, 0.06 - u) * 8;
    for (let y = a + 12; y < b - 12; y += step) cand.push([x + (hash(cand.length, seed) - 0.5) * step * 0.8, y + (hash(cand.length, seed + 1) - 0.5) * step * 0.8, hash(cand.length, seed + 2) * (1 + edge)]);
  }
  cand.sort((p, q) => p[2] - q[2]);
  const pts = cand.slice(0, n);
  const m = Math.floor(pts.length * clamp01(reveal));
  let d = "";
  for (let i = 0; i < m; i++) {
    let [x, y] = pts[i];
    if (squeeze) { // pull toward the first gate (used by the demo when the funnel squeezes)
      const [a, b] = funnelSpan(x1 + 40);
      const k = squeeze * (0.4 + 0.6 * pts[i][2]);
      x = x + (x1 + 40 - x) * k; y = y + ((a + b) / 2 + (y - (a + b) / 2) * 0.25 - y) * k;
    }
    d += `M${x.toFixed(1)},${y.toFixed(1)}h${size}v${size}h${-size}z`;
  }
  return <path d={d} fill={color} opacity={opacity}/>;
};

const scatter = (n, x0, x1, pad, seed, minD) => {
  const out = [];
  for (let k = 0; out.length < n && k < 5000; k++) {
    const x = x0 + hash(k, seed) * (x1 - x0), [a, b] = funnelSpan(x);
    const y = a + pad + hash(k, seed + 1) * (b - a - 2 * pad);
    if (out.every(p => Math.hypot(p[0] - x, p[1] - y) > minD)) out.push([x, y]);
  }
  return out;
};
// a synthesised compound: rough.js hexagon (re-inked with pressure) with vermilion hachure = made in the lab
export const HexMark = ({x, y, r = 22, seed = 1, color = C.ink, size = 3.4, progress = 1, fill = C.verm}) => {
  const pts = Array.from({length: 6}, (_, i) => { const a = Math.PI / 6 + i * Math.PI / 3; return [x + Math.cos(a) * r, y + Math.sin(a) * r]; });
  return <RoughPolygon points={pts} seed={seed} size={size} color={color} fillColor={fill} fillSize={1.5} progress={progress}
    options={{roughness: 1.2, bowing: 1.4, fillStyle: "hachure", hachureGap: 5.5, hachureAngle: -35}}/>;
};

export const FunnelBody = ({progress = 1, seed = 500}) => <g>
  <InkPath points={catmull(FUN.top, false, 12)} seed={seed} size={12} pressure="brush" thinning={0.4} jitter={2.6} ghost={0.3} progress={progress}/>
  <InkPath points={catmull(FUN.bot, false, 12)} seed={seed + 1} size={12} pressure="brush" thinning={0.4} jitter={2.6} ghost={0.3} progress={progress}/>
  {FUN.gates.map((gx, i) => {
    const [a, b] = funnelSpan(gx);
    // sieve: a dashed hand line, each dash its own stroke
    const n = Math.max(3, Math.round((b - a) / 34));
    return <g key={i}>{Array.from({length: n}, (_, k) => {
      const y0 = a + (b - a) * (k + 0.18) / n, y1 = a + (b - a) * (k + 0.72) / n;
      return <InkLine key={k} from={[gx + (hash(k, i) - 0.5) * 6, y0]} to={[gx + (hash(k, i + 9) - 0.5) * 6, y1]} seed={seed + 10 + i * 40 + k} size={4} pressure="marker"
        progress={clamp01(progress * 1.4 - 0.4)} opacity={0.7}/>;
    })}</g>;
  })}
</g>;

export const V3Funnel = () => {
  const s2 = scatter(54, 745, 1160, 22, 3, 21);
  const s3 = scatter(7, 1200, 1415, 14, 8, 34);
  const big = 150, ny = 228;
  const nums = [
    {x: 110, v: "8,918", label: "AI-DESIGNED"},
    {x: 760, v: "54", label: "SELECTED"},
    {x: 1180, v: "7", label: "SYNTHESISED"},
    {x: 1540, v: "1", label: "FIRST HIT"},
  ];
  return <Stage>
    <svg width={W} height={H} style={{position: "absolute"}}>
      <InkDefs/>
      <clipPath id="fun-in"><path d={funnelD()}/></clipPath>
      <g clipPath="url(#fun-in)"><Halftone bounds={[110, 300, 1460, 640]} field={linear(1560, 640, 110, 640, 1.5)} cell={13} angle={0.6} color={C.cyan} opacity={0.16}/></g>
      <PixelCloud/>
      <g filter="url(#v3-ink)">
        <FunnelBody/>
        {s2.map((p, i) => <RoughCircle key={i} cx={p[0]} cy={p[1]} d={17} seed={600 + i} size={3} options={{roughness: 1.4, bowing: 1}}/>)}
        {s3.map((p, i) => <HexMark key={i} x={p[0]} y={p[1]} r={20} seed={700 + i}/>)}
        {/* the one that came out */}
        <InkMolecule mol={M001} x={1690} y={812} scale={27} seed={11} size={4.2} labelSize={19}/>
        <HandArrow from={[1575, 676]} to={[1640, 760]} bend={0.25} size={6} head={20} seed={81}/>
      </g>
      {/* counts */}
      {nums.map((n, i) => <g key={i}>
        <Mono x={n.x} y={ny} size={big} weight={800} color={i === 3 ? C.ink : C.ink}>{n.v}</Mono>
        <Mono x={n.x + 4} y={ny + 58} size={20} weight={700} color={i === 0 ? C.cyan : C.dim} letterSpacing={3}>{n.label}</Mono>
      </g>)}
      <g filter="url(#v3-ink)">
        <StrikeOut x={110} y={ny - 110} w={monoW("8,918", big)} h={110} size={16} seed={3} kind="double"/>
        <StrikeOut x={760} y={ny - 110} w={monoW("54", big)} h={110} size={15} seed={5} kind="double"/>
        <StrikeOut x={1180} y={ny - 110} w={monoW("7", big)} h={110} size={14} seed={9} kind="x"/>
        <HandCircle cx={1540 + monoW("1", big) / 2} cy={ny - 56} rx={86} ry={88} size={9} color={C.acid} seed={31} turns={1.25}/>
        <HandArrow from={[690, 160]} to={[745, 160]} bend={-0.4} size={6} head={18} seed={90} opacity={0.8}/>
        <HandArrow from={[1100, 160]} to={[1160, 160]} bend={-0.4} size={6} head={18} seed={91} opacity={0.8}/>
        <HandArrow from={[1350, 160]} to={[1510, 160]} bend={-0.3} size={6} head={18} seed={92} opacity={0.8}/>
      </g>
      <HandText x={1700} y={748} size={62} seed={14}>001</HandText>

      {/* timeline */}
      <g filter="url(#v3-ink)">
        <HandArrow from={[120, 965]} to={[1400, 958]} bend={0.012} size={7} head={26} seed={95}/>
      </g>
      <rect x={640} y={925} width={300} height={70} fill={C.bg}/>
      <HandText x={790} y={985} size={72} seed={21} anchor="middle" color={C.verm}>30 DAYS</HandText>
      <Mono x={120} y={1000} size={16} color={C.dim} letterSpacing={2}>ROUND 1</Mono>
      <rect x={1460} y={928} width={360} height={46} fill="none" stroke={C.cyan} strokeWidth={2}/>
      <Mono x={1476} y={958} size={18} weight={700} color={C.cyan} letterSpacing={1}>ROUND 2 · 16 → 6 → 048</Mono>
      <Dust/>
      <Chrome fig="01" smiles={false}/>
    </svg>
  </Stage>;
};
