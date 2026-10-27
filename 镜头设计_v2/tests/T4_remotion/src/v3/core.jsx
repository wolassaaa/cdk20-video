// v3 "INK / SIGNAL" design system: tokens, seeded randomness, boil clock, geometry helpers.
import React, {createContext, useContext} from "react";
import {useCurrentFrame} from "remotion";
import {loadFont as loadHand} from "@remotion/google-fonts/Knewave";
import {loadFont as loadMono} from "@remotion/google-fonts/MartianMono";

// ---------- tokens ----------
export const HAND = loadHand("normal", {weights: ["400"], subsets: ["latin"]}).fontFamily;
export const MONO = loadMono("normal", {weights: ["400", "700", "800"], subsets: ["latin"]}).fontFamily;

export const C = {
  bg: "#060606",        // black stage
  ink: "#EDEBE4",       // off-white ink
  verm: "#FF3B1F",      // body / blood
  cyan: "#29F0FF",      // AI / computation
  acid: "#E8FF3A",      // rare highlight
  dim: "rgba(237,235,228,0.55)",
  faint: "rgba(237,235,228,0.2)",
};
export const W = 1920, H = 1080, FPS = 30;

// ---------- seeded randomness ----------
export const hash = (a, b = 0, c = 0) => {
  let h = Math.imul((a | 0) ^ 0x9e3779b9, 0x85ebca6b) ^ Math.imul((b | 0) + 0x7f4a7c15, 0xc2b2ae35) ^ Math.imul((c | 0) + 0x165667b1, 0x27d4eb2f);
  h ^= h >>> 15; h = Math.imul(h, 0x2c1b3c6d); h ^= h >>> 12; h = Math.imul(h, 0x297a2d39); h ^= h >>> 15;
  return (h >>> 0) / 4294967296;
};
export const rng = seed => {
  let s = (seed | 0) || 1;
  return () => { s = (s + 0x6d2b79f5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
};
// smooth value noise in [-1, 1]
export const vnoise = (x, seed = 0) => {
  const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
  const a = hash(i, seed) * 2 - 1, b = hash(i + 1, seed) * 2 - 1;
  return a + (b - a) * u;
};

// ---------- boil clock ----------
// Lines are re-drawn with fresh jitter every `rate` frames. 2.5 -> alternating 3,2,3,2 frame holds (feels hand-timed).
export const BoilCtx = createContext({rate: 2.5, frozen: false});
export const BoilProvider = ({rate = 2.5, frozen = false, children}) => React.createElement(BoilCtx.Provider, {value: {rate, frozen}}, children);
export const useBoil = () => {
  const f = useCurrentFrame();
  const {rate, frozen} = useContext(BoilCtx);
  return frozen ? 0 : Math.floor(f / rate);
};

// ---------- easing ----------
export const clamp01 = x => Math.min(1, Math.max(0, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const ramp = (f, a, b) => clamp01((f - a) / (b - a));
export const outCubic = x => 1 - Math.pow(1 - clamp01(x), 3);
export const outExpo = x => (x = clamp01(x)) === 1 ? 1 : 1 - Math.pow(2, -10 * x);
export const inOut = x => { x = clamp01(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
export const outBack = (x, k = 1.9) => { x = clamp01(x); return 1 + (k + 1) * Math.pow(x - 1, 3) + k * Math.pow(x - 1, 2); };

// ---------- geometry ----------
export const dist = (a, b) => Math.hypot(b[0] - a[0], b[1] - a[1]);
export const polyLen = pts => { let L = 0; for (let i = 1; i < pts.length; i++) L += dist(pts[i - 1], pts[i]); return L; };

// uniform arc-length resampling; carries an optional 3rd value (pressure) along
export const resample = (pts, step) => {
  if (pts.length < 2) return pts.slice();
  const out = [pts[0].slice()];
  let carry = 0;
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i], d = dist(a, b);
    if (d === 0) continue;
    let t = step - carry;
    while (t <= d) {
      const u = t / d;
      out.push([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, ...(a.length > 2 ? [a[2] + (b[2] - a[2]) * u] : [])]);
      t += step;
    }
    carry = d - (t - step);
  }
  const last = pts[pts.length - 1];
  if (dist(out[out.length - 1], last) > step * 0.25) out.push(last.slice());
  return out;
};

// keep the first t (0..1) of a polyline by arc length, interpolating the end point
export const cutAt = (pts, t) => {
  if (t >= 1) return pts;
  if (t <= 0 || pts.length < 2) return [];
  const total = polyLen(pts), target = total * t;
  const out = [pts[0]];
  let L = 0;
  for (let i = 1; i < pts.length; i++) {
    const a = pts[i - 1], b = pts[i], d = dist(a, b);
    if (L + d >= target) {
      const u = d ? (target - L) / d : 0;
      out.push(a.map((v, k) => v + ((b[k] ?? v) - v) * u));
      return out;
    }
    out.push(b); L += d;
  }
  return out;
};

// Catmull-Rom spline through points
export const catmull = (pts, closed = false, seg = 10) => {
  const n = pts.length, out = [];
  const P = i => closed ? pts[(i + n) % n] : pts[Math.max(0, Math.min(n - 1, i))];
  const last = closed ? n : n - 1;
  for (let i = 0; i < last; i++) {
    const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
    for (let s = 0; s < seg; s++) {
      const t = s / seg, t2 = t * t, t3 = t2 * t;
      out.push([0, 1].map(k => 0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)));
    }
  }
  out.push(closed ? pts[0].slice() : pts[n - 1].slice());
  return out;
};

export const quad = (a, c, b, n = 24) => Array.from({length: n + 1}, (_, i) => {
  const t = i / n, u = 1 - t;
  return [u * u * a[0] + 2 * u * t * c[0] + t * t * b[0], u * u * a[1] + 2 * u * t * c[1] + t * t * b[1]];
});

// a hand line from a to b: slight bow, optional overshoot at both ends
export const handLine = (a, b, {bow = 0, over = 0, n = 16} = {}) => {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, ux = dx / L, uy = dy / L;
  const A = [a[0] - ux * over, a[1] - uy * over], B = [b[0] + ux * over, b[1] + uy * over];
  const c = [(A[0] + B[0]) / 2 - uy * bow, (A[1] + B[1]) / 2 + ux * bow];
  return quad(A, c, B, n);
};

// ellipse / loop: turns > 1 overshoots like a real hand circle; spiral drifts the radius so ends don't meet
export const loopPts = (cx, cy, rx, ry, {a0 = -2.3, turns = 1.12, n = 90, rot = 0, spiral = 0.06, seed = 0, wob = 0.03} = {}) => {
  const cr = Math.cos(rot), sr = Math.sin(rot);
  return Array.from({length: n + 1}, (_, i) => {
    const t = i / n, a = a0 + t * turns * Math.PI * 2;
    const k = 1 + spiral * (t - 0.5) + wob * vnoise(t * 5, seed);
    const x = Math.cos(a) * rx * k, y = Math.sin(a) * ry * k;
    return [cx + x * cr - y * sr, cy + x * sr + y * cr];
  });
};

// low + high frequency jitter along the arc (the "boil")
export const wobble = (pts, seed, amp, freq = 1 / 110) => {
  if (!amp) return pts;
  let L = 0;
  return pts.map((p, i) => {
    if (i) L += dist(pts[i - 1], p);
    const x = p[0] + amp * (vnoise(L * freq, seed * 4 + 1) + 0.3 * vnoise(L * freq * 5, seed * 4 + 2));
    const y = p[1] + amp * (vnoise(L * freq, seed * 4 + 3) + 0.3 * vnoise(L * freq * 5, seed * 4 + 4));
    return p.length > 2 ? [x, y, p[2]] : [x, y];
  });
};

export const rotPt = (p, c, a) => {
  const s = Math.sin(a), co = Math.cos(a), x = p[0] - c[0], y = p[1] - c[1];
  return [c[0] + x * co - y * s, c[1] + x * s + y * co];
};

// polygon x horizontal-line intersections, for hand hatching (works for any simple polygon)
export const scanSegments = (poly, angle, gap, inset = 0) => {
  const c = poly.reduce((s, p) => [s[0] + p[0] / poly.length, s[1] + p[1] / poly.length], [0, 0]);
  const R = poly.map(p => rotPt(p, c, -angle));
  const ys = R.map(p => p[1]);
  const y0 = Math.min(...ys), y1 = Math.max(...ys);
  const segs = [];
  for (let y = y0 + gap * 0.5; y < y1; y += gap) {
    const xs = [];
    for (let i = 0; i < R.length; i++) {
      const a = R[i], b = R[(i + 1) % R.length];
      if ((a[1] <= y && b[1] > y) || (b[1] <= y && a[1] > y)) xs.push(a[0] + (y - a[1]) / (b[1] - a[1]) * (b[0] - a[0]));
    }
    xs.sort((p, q) => p - q);
    for (let i = 0; i + 1 < xs.length; i += 2) {
      if (xs[i + 1] - xs[i] < inset * 2 + 2) continue;
      segs.push([rotPt([xs[i] + inset, y], c, angle), rotPt([xs[i + 1] - inset, y], c, angle)]);
    }
  }
  return segs;
};

export const pathD = (pts, closed = false) => pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("") + (closed ? "Z" : "");
