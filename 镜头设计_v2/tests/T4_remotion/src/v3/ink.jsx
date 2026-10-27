// Ink primitives: perfect-freehand pressure strokes, rough.js wrappers (seeded by the boil clock), hatching, scribble fills.
import React from "react";
import {getStroke} from "perfect-freehand";
import rough from "roughjs";
import {C, useBoil, hash, vnoise, resample, cutAt, wobble, handLine, scanSegments, clamp01, rotPt} from "./core";

const avg = (a, b) => (a + b) / 2;
// perfect-freehand outline polygon -> smooth closed SVG path (from the library README)
export const outlineToD = pts => {
  const n = pts.length;
  if (n < 4) return "";
  let a = pts[0], b = pts[1];
  const c = pts[2];
  let d = `M${a[0].toFixed(1)},${a[1].toFixed(1)} Q${b[0].toFixed(1)},${b[1].toFixed(1)} ${avg(b[0], c[0]).toFixed(1)},${avg(b[1], c[1]).toFixed(1)} T`;
  for (let i = 2; i < n - 1; i++) { a = pts[i]; b = pts[i + 1]; d += `${avg(a[0], b[0]).toFixed(1)},${avg(a[1], b[1]).toFixed(1)} `; }
  return d + "Z";
};

// pressure profiles: brush = swell in the middle, marker = nearly flat, nib = heavy start
const PRESS = {
  brush: (t, n) => 0.32 + 0.6 * Math.pow(Math.sin(Math.PI * Math.min(1, 0.08 + t * 0.95)), 0.7) + 0.1 * n,
  marker: (t, n) => 0.78 + 0.08 * n,
  nib: (t, n) => 0.9 - 0.45 * t + 0.1 * n,
  flick: (t, n) => 0.95 - 0.8 * Math.pow(t, 1.5) + 0.05 * n,
};

/**
 * Build the SVG path for an ink stroke.
 * points: [[x,y], ...] centreline. Returns "" if nothing to draw yet.
 */
export const inkD = (points, {size = 6, seed = 1, jitter = 1.4, progress = 1, thinning = 0.6, pressure = "brush",
  taperStart, taperEnd, spacing, smoothing = 0.55, streamline = 0.25, freq} = {}) => {
  if (!points || points.length < 2 || progress <= 0) return "";
  let pts = resample(points, spacing ?? Math.max(3, size * 0.8));
  if (pts.length < 2) return "";
  pts = wobble(pts, seed, jitter, freq);
  const prof = PRESS[pressure] || PRESS.brush;
  const n = pts.length;
  pts = pts.map((p, i) => [p[0], p[1], clamp01(prof(i / (n - 1), vnoise(i * 0.31, seed + 77)))]);
  const cut = cutAt(pts, progress);
  if (cut.length < 2) return "";
  const done = progress >= 1;
  const outline = getStroke(cut, {
    size, thinning, smoothing, streamline, simulatePressure: false, last: done,
    start: {taper: taperStart ?? size * 1.5, cap: true},
    end: {taper: done ? (taperEnd ?? size * 2.5) : size * 0.6, cap: true},
  });
  return outlineToD(outline);
};

/** One ink stroke. `seed` keeps strokes distinct; the boil clock re-jitters it every 2-3 frames. */
export const InkPath = ({points, seed = 1, boil = true, color = C.ink, opacity = 1, ghost = 0, style, ...o}) => {
  const b = useBoil();
  const s = (seed * 7919 + (boil ? b * 104729 : 0)) | 0;
  const d = inkD(points, {...o, seed: s});
  if (!d) return null;
  if (!ghost) return <path d={d} fill={color} opacity={opacity} style={style}/>;
  // ghost: the previous drawing left faintly underneath (onion skin)
  const g = inkD(points, {...o, seed: (seed * 7919 + (b - 1) * 104729) | 0, jitter: (o.jitter ?? 1.4) * 1.6});
  return <g style={style}><path d={g} fill={color} opacity={opacity * ghost}/><path d={d} fill={color} opacity={opacity}/></g>;
};

/** Straight-ish hand line between two points. */
export const InkLine = ({from, to, bow = 0, over = 0, ...p}) => <InkPath points={handLine(from, to, {bow, over})} {...p}/>;

// ---------- rough.js ----------
const gen = rough.generator();

// rough op sets -> polylines (bezier segments sampled), so rough geometry can be re-inked with pressure
export const roughToPolylines = drawable => {
  const lines = [];
  for (const set of drawable.sets) {
    if (set.type === "fillPath") continue;
    let cur = null, last = null;
    for (const op of set.ops) {
      if (op.op === "move") { if (cur && cur.length > 1) lines.push({pts: cur, fill: set.type === "fillSketch"}); cur = [[op.data[0], op.data[1]]]; last = cur[0]; }
      else if (op.op === "lineTo") { cur.push([op.data[0], op.data[1]]); last = cur[cur.length - 1]; }
      else if (op.op === "bcurveTo") {
        const [x1, y1, x2, y2, x, y] = op.data;
        for (let i = 1; i <= 8; i++) {
          const t = i / 8, u = 1 - t;
          cur.push([u * u * u * last[0] + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t * t * t * x, u * u * u * last[1] + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t * y]);
        }
        last = cur[cur.length - 1];
      }
    }
    if (cur && cur.length > 1) lines.push({pts: cur, fill: set.type === "fillSketch"});
  }
  return lines;
};

/**
 * Generic rough wrapper. make(gen, opts) returns a rough drawable.
 * mode "svg": rough's own paths (uniform width, crisp) — used for the 'digital-sketch' look.
 * mode "ink": rough geometry re-stroked with perfect-freehand pressure — used for the hand look.
 * progress draws the strokes on in order.
 */
export const Rough = ({make, seed = 1, options = {}, mode = "ink", progress = 1, size = 4, fillSize = 2, color = C.ink, fillColor, opacity = 1, boil = true}) => {
  const b = useBoil();
  const rs = ((seed * 131 + (boil ? b : 0)) % 2147483000) + 1;
  const opts = {roughness: 1.4, bowing: 1.1, stroke: color, strokeWidth: size, fillWeight: fillSize, hachureGap: 9, seed: rs, ...options};
  if (fillColor) opts.fill = fillColor;
  const dr = make(gen, opts);
  if (mode === "svg") {
    const paths = gen.toPaths(dr);
    return <g opacity={opacity}>{paths.map((p, i) => {
      const local = clamp01(progress * paths.length - i);
      if (local <= 0) return null;
      return <path key={i} d={p.d} stroke={p.stroke} strokeWidth={p.strokeWidth} fill={p.fill || "none"} strokeLinecap="round" strokeLinejoin="round"
        pathLength={1} strokeDasharray={local < 1 ? "1 1" : undefined} strokeDashoffset={local < 1 ? 1 - local : undefined}/>;
    })}</g>;
  }
  const lines = roughToPolylines(dr);
  const N = lines.length;
  return <g opacity={opacity}>{lines.map((l, i) => {
    const local = clamp01(progress * N - i);
    return <InkPath key={i} points={l.pts} seed={seed * 17 + i} boil={false} jitter={0.4} size={l.fill ? fillSize : size}
      color={l.fill ? (fillColor || color) : color} progress={local} pressure={l.fill ? "marker" : "brush"} thinning={l.fill ? 0.3 : 0.55}/>;
  })}</g>;
};

export const RoughLine = ({x1, y1, x2, y2, ...p}) => <Rough make={(g, o) => g.line(x1, y1, x2, y2, o)} {...p}/>;
export const RoughRect = ({x, y, w, h, ...p}) => <Rough make={(g, o) => g.rectangle(x, y, w, h, o)} {...p}/>;
export const RoughEllipse = ({cx, cy, w, h, ...p}) => <Rough make={(g, o) => g.ellipse(cx, cy, w, h, o)} {...p}/>;
export const RoughCircle = ({cx, cy, d, ...p}) => <Rough make={(g, o) => g.circle(cx, cy, d, o)} {...p}/>;
export const RoughPolygon = ({points, ...p}) => <Rough make={(g, o) => g.polygon(points, o)} {...p}/>;
export const RoughCurve = ({points, ...p}) => <Rough make={(g, o) => g.curve(points, o)} {...p}/>;
export const RoughSvgPath = ({d, ...p}) => <Rough make={(g, o) => g.path(d, o)} {...p}/>;

// ---------- fills ----------
/**
 * Hand hatching inside a polygon: individual strokes that start/stop a little inside or past the edge.
 * cross adds a second pass. progress sweeps the hatching in.
 */
export const Hatch = ({poly, angle = -0.7, gap = 12, size = 2.4, color = C.verm, seed = 3, cross = false, progress = 1, opacity = 1, slack = 6, boil = true, keep, irregular = 0.3}) => {
  const b = useBoil();
  const passes = cross ? [angle, angle + 1.25] : [angle];
  const out = [];
  passes.forEach((ang, pi) => {
    const segs = scanSegments(poly, ang, gap * (pi ? 1.25 : 1), 0);
    segs.forEach((s, i) => {
      const r = k => hash(i * 3 + k, seed + pi * 99, boil ? b : 0) - 0.5;
      const local = clamp01(progress * (segs.length + 8) / 8 - i / 8);
      if (local <= 0) return;
      const dx = s[1][0] - s[0][0], dy = s[1][1] - s[0][1], L = Math.hypot(dx, dy) || 1;
      const ux = dx / L, uy = dy / L, a0 = r(0) * slack * 2, a1 = r(1) * slack * 2;
      const mid = [(s[0][0] + s[1][0]) / 2, (s[0][1] + s[1][1]) / 2];
      if (keep && hash(i, seed + pi * 7, 5) > keep(mid[0], mid[1])) return;
      // hand irregularity: lines drift sideways and tilt a little
      const off = r(6) * gap * irregular, tilt = r(7) * irregular * 0.12 * L;
      const A = [s[0][0] - ux * a0 - uy * (off - tilt), s[0][1] - uy * a0 + ux * (off - tilt)], B = [s[1][0] + ux * a1 - uy * (off + tilt), s[1][1] + uy * a1 + ux * (off + tilt)];
      out.push(<InkPath key={pi + "-" + i} points={handLine(A, B, {bow: r(2) * 5})} seed={seed * 1000 + pi * 500 + i} size={size} color={color}
        jitter={0.7} pressure="nib" thinning={0.5} progress={local} taperStart={2} taperEnd={6}/>);
    });
  });
  return <g opacity={opacity}>{out}</g>;
};

/**
 * Continuous marker scribble filling a polygon (one back-and-forth stroke), clipped to the shape.
 */
export const Scribble = ({poly, angle = 0.5, gap = 16, size = 9, color = C.verm, seed = 5, progress = 1, opacity = 1, id, loose = 0.35}) => {
  const b = useBoil();
  const segs = scanSegments(poly, angle, gap, 0);
  const pts = [];
  segs.forEach((s, i) => {
    const r = k => hash(i * 5 + k, seed, b) - 0.5;
    const [A, B] = i % 2 ? [s[1], s[0]] : [s[0], s[1]];
    const dx = B[0] - A[0], dy = B[1] - A[1], L = Math.hypot(dx, dy) || 1;
    const o = gap * loose;
    pts.push([A[0] - dx / L * (o + r(0) * o), A[1] - dy / L * (o + r(0) * o)]);
    pts.push([B[0] + dx / L * (o + r(1) * o), B[1] + dy / L * (o + r(1) * o)]);
  });
  const clip = id || `scr-${seed}`;
  return <g opacity={opacity}>
    <clipPath id={clip}><path d={poly.map((p, i) => `${i ? "L" : "M"}${p[0]},${p[1]}`).join("") + "Z"}/></clipPath>
    <g clipPath={`url(#${clip})`}>
      <InkPath points={pts} seed={seed} size={size} color={color} progress={progress} pressure="marker" thinning={0.25} jitter={2} spacing={6}/>
    </g>
  </g>;
};

// rotate a polygon helper re-exported for scene code
export {rotPt};
