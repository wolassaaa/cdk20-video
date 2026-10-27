// Hand-drawn marks (arrows, loops, underlines, strikes, ticks, bursts, highlighter) + clean digital marks (scan box, crosshair).
import React from "react";
import {C, MONO, hash, clamp01, quad, handLine, loopPts, useBoil, vnoise, catmull} from "./core";
import {InkPath} from "./ink";

const seg = (p, a, b) => clamp01((p - a) / (b - a));

/** Curved hand arrow: shaft draws first, then the head as one V stroke. bend = sideways bow (fraction of length). */
export const HandArrow = ({from, to, bend = 0.18, size = 7, head = 30, spread = 0.5, color = C.ink, progress = 1, seed = 11, opacity = 1}) => {
  const [x0, y0] = from, [x1, y1] = to;
  const dx = x1 - x0, dy = y1 - y0, L = Math.hypot(dx, dy) || 1, nx = -dy / L, ny = dx / L;
  const c = [(x0 + x1) / 2 + nx * bend * L, (y0 + y1) / 2 + ny * bend * L];
  const shaft = quad(from, c, to, 40);
  const ang = Math.atan2(y1 - c[1], x1 - c[0]);
  const h1 = [x1 - head * Math.cos(ang - spread), y1 - head * Math.sin(ang - spread)];
  const h2 = [x1 - head * 1.08 * Math.cos(ang + spread * 0.9), y1 - head * 1.08 * Math.sin(ang + spread * 0.9)];
  return <g opacity={opacity}>
    <InkPath points={shaft} seed={seed} size={size} color={color} progress={seg(progress, 0, 0.72)} pressure="nib"/>
    <InkPath points={[...quad(h1, [(h1[0] + x1) / 2, (h1[1] + y1) / 2], to, 6), ...quad(to, [(h2[0] + x1) / 2, (h2[1] + y1) / 2], h2, 6).slice(1)]}
      seed={seed + 1} size={size * 0.95} color={color} progress={seg(progress, 0.72, 1)} pressure="brush" taperStart={3}/>
  </g>;
};

/** Hand loop around something (overshooting ellipse). */
export const HandCircle = ({cx, cy, rx, ry, size = 7, color = C.ink, progress = 1, seed = 21, turns = 1.15, rot = -0.08, a0 = -2.4, opacity = 1, spiral = 0.13}) =>
  <InkPath points={loopPts(cx, cy, rx, ry, {turns, rot, a0, seed, n: 120, spiral, wob: 0.05})} seed={seed} size={size} color={color} progress={progress} pressure="brush" opacity={opacity}/>;

/** Underline: single, double, or wave. */
export const HandUnderline = ({x, y, w, size = 7, color = C.ink, progress = 1, seed = 31, kind = "single", tilt = -0.012, opacity = 1}) => {
  const a = [x, y], b = [x + w, y + w * tilt];
  if (kind === "wave") {
    const pts = Array.from({length: 61}, (_, i) => { const t = i / 60; return [x + w * t, y + w * tilt * t + Math.sin(t * Math.PI * 2 * Math.max(2, w / 70)) * 7]; });
    return <InkPath points={pts} seed={seed} size={size} color={color} progress={progress} pressure="marker" opacity={opacity}/>;
  }
  if (kind === "double") {
    return <g opacity={opacity}>
      <InkPath points={handLine(a, b, {bow: -4, over: 6})} seed={seed} size={size} color={color} progress={seg(progress, 0, 0.55)} pressure="nib"/>
      <InkPath points={handLine([x + w * 0.06, y + 14], [x + w * 0.92, y + 14 + w * tilt * 0.6], {bow: 3})} seed={seed + 1} size={size * 0.8} color={color} progress={seg(progress, 0.5, 1)} pressure="nib"/>
    </g>;
  }
  return <InkPath points={handLine(a, b, {bow: -5, over: 8})} seed={seed} size={size} color={color} progress={progress} pressure="nib" opacity={opacity}/>;
};

/** Aggressive strike-through over a box: two slashes + a zigzag scribble. */
export const StrikeOut = ({x, y, w, h, size = 12, color = C.verm, progress = 1, seed = 41, kind = "slash", opacity = 1}) => {
  const b = useBoil();
  const r = k => hash(k, seed, 0) - 0.5;
  if (kind === "scribble") {
    const n = Math.max(4, Math.round(w / 55));
    const pts = [];
    for (let i = 0; i <= n; i++) {
      const t = i / n;
      pts.push([x + w * t + r(i) * 20, (i % 2 ? y + h * 0.18 : y + h * 0.82) + r(i + 50) * h * 0.2]);
    }
    return <InkPath points={catmull(pts, false, 6)} seed={seed} size={size} color={color} progress={progress} pressure="marker" thinning={0.3} opacity={opacity}/>;
  }
  // two crossing slashes, overshooting the box
  const s1 = handLine([x - 18, y + h * (0.62 + r(1) * 0.2)], [x + w + 22, y + h * (0.3 + r(2) * 0.2)], {bow: 10 + r(3) * 10, over: 6});
  const s2 = handLine([x - 8, y + h * (0.38 + r(4) * 0.15)], [x + w + 14, y + h * (0.6 + r(5) * 0.15)], {bow: -8, over: 4});
  return <g opacity={opacity}>
    <InkPath points={s1} seed={seed} size={size} color={color} progress={seg(progress, 0, 0.6)} pressure="flick" thinning={0.45}/>
    {kind === "x" || kind === "double" ? <InkPath points={s2} seed={seed + 1} size={size * 0.8} color={color} progress={seg(progress, 0.45, 1)} pressure="flick" thinning={0.45}/> : null}
  </g>;
};

/** Check mark. */
export const Tick = ({x, y, s = 60, size = 9, color = C.ink, progress = 1, seed = 51, opacity = 1}) => {
  const pts = [...quad([x - s * 0.45, y - s * 0.02], [x - s * 0.3, y + s * 0.18], [x - s * 0.12, y + s * 0.36], 8),
    ...quad([x - s * 0.12, y + s * 0.36], [x + s * 0.1, y - s * 0.1], [x + s * 0.6, y - s * 0.62], 14).slice(1)];
  return <InkPath points={pts} seed={seed} size={size} color={color} progress={progress} pressure="nib" thinning={0.6} taperStart={4} opacity={opacity}/>;
};

/** Hand X. */
export const Cross = ({x, y, s = 50, size = 9, color = C.verm, progress = 1, seed = 61}) => <g>
  <InkPath points={handLine([x - s / 2, y - s / 2], [x + s / 2, y + s / 2], {bow: 4, over: 3})} seed={seed} size={size} color={color} progress={seg(progress, 0, 0.5)} pressure="flick"/>
  <InkPath points={handLine([x + s / 2, y - s / 2], [x - s / 2, y + s / 2], {bow: -3, over: 3})} seed={seed + 1} size={size} color={color} progress={seg(progress, 0.5, 1)} pressure="flick"/>
</g>;

/**
 * Impact burst: radiating ink spikes. phase 0..1: spikes shoot out (0-0.4) then retract from the inside (0.4-1).
 */
export const ScribbleBurst = ({cx, cy, r0 = 70, r1 = 190, n = 14, size = 8, color = C.ink, phase = 0.35, seed = 71, opacity = 1}) => {
  if (phase <= 0 || phase >= 1) return null;
  const out = [];
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + (hash(i, seed) - 0.5) * 0.5;
    const ri = r0 * (0.8 + hash(i, seed, 1) * 0.5), ro = r1 * (0.6 + hash(i, seed, 2) * 0.6);
    const head = clamp01(phase / 0.35), tail = clamp01((phase - 0.35) / 0.65);
    const a0 = ri + (ro - ri) * tail, a1 = ri + (ro - ri) * head;
    if (a1 - a0 < 2) continue;
    const p0 = [cx + Math.cos(a) * a0, cy + Math.sin(a) * a0], p1 = [cx + Math.cos(a) * a1, cy + Math.sin(a) * a1];
    out.push(<InkPath key={i} points={handLine(p0, p1, {bow: (hash(i, seed, 3) - 0.5) * 10})} seed={seed * 50 + i} size={size * (0.6 + hash(i, seed, 4) * 0.7)}
      color={color} pressure="flick" jitter={0.8} taperStart={1}/>);
  }
  return <g opacity={opacity}>{out}</g>;
};

/** Acid-yellow marker swash behind text. Put dark text on top. */
export const Highlight = ({x, y, w, h, color = C.acid, progress = 1, seed = 81, tilt = -0.02, opacity = 1}) => {
  const pts = handLine([x, y + h / 2], [x + w, y + h / 2 + w * tilt], {bow: -3, over: 0});
  return <InkPath points={pts} seed={seed} size={h} color={color} progress={progress} pressure="marker" thinning={0.08} jitter={h * 0.04} spacing={6}
    taperStart={h * 0.12} taperEnd={h * 0.18} opacity={opacity} smoothing={0.7}/>;
};

// ---------- clean digital marks (no boil: they are the computer) ----------
/** Corner-bracket selection box with a mono label tab. */
export const ScanBox = ({x, y, w, h, color = C.cyan, label, sub, len = 26, sw = 2.5, progress = 1, dashed = false}) => {
  const p = clamp01(progress);
  const L = len * p;
  const corners = `M${x},${y + L}V${y}H${x + L} M${x + w - L},${y}H${x + w}V${y + L} M${x + w},${y + h - L}V${y + h}H${x + w - L} M${x + L},${y + h}H${x}V${y + h - L}`;
  return <g>
    <path d={corners} stroke={color} strokeWidth={sw} fill="none"/>
    {dashed && <rect x={x} y={y} width={w} height={h} stroke={color} strokeWidth={1} fill="none" strokeDasharray="4 6" opacity={0.6 * p}/>}
    {label && p > 0.6 ? <g>
      <rect x={x} y={y - 34} width={label.length * 11.7 + 20} height={28} fill={color}/>
      <text x={x + 10} y={y - 14} fontFamily={MONO} fontSize={16} fontWeight={700} fill={C.bg} letterSpacing={0.5}>{label}</text>
    </g> : null}
    {sub && p > 0.6 ? <g><rect x={x} y={y + h + 8} width={sub.length * 11 + 16} height={26} fill={C.bg}/><text x={x + 8} y={y + h + 27} fontFamily={MONO} fontSize={15} fill={color} letterSpacing={0.5}>{sub}</text></g> : null}
  </g>;
};

/** Registration crosshair. */
export const Crosshair = ({x, y, r = 14, color = C.ink, sw = 1.5, opacity = 0.6}) => <g stroke={color} strokeWidth={sw} fill="none" opacity={opacity}>
  <circle cx={x} cy={y} r={r * 0.55}/><path d={`M${x - r},${y}H${x + r}M${x},${y - r}V${y + r}`}/>
</g>;

/** Tick ruler (clean). */
export const Ruler = ({x, y, len, step = 12, major = 5, color = C.ink, vertical = false, opacity = 0.45}) => {
  let d = "";
  for (let i = 0, k = 0; i <= len; i += step, k++) {
    const t = k % major === 0 ? 12 : 6;
    d += vertical ? `M${x},${y + i}h${t}` : `M${x + i},${y}v${-t}`;
  }
  return <path d={d} stroke={color} strokeWidth={1.2} opacity={opacity}/>;
};

export {vnoise};
