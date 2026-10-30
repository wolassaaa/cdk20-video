// Helpers for the S5 stills (07, 08, 10). Flat vector only: no ink jitter, no glow, no gradient.
// Nothing here is imported from ../../molecule.jsx, which pulls ../core and its Knewave/HAND fonts.
import React from "react";
import {K, DIM} from "../kit";

// ---------- skeletal formula, fitted to a box ----------
const bbox = atoms => {
  const xs = atoms.map(a => a.x), ys = atoms.map(a => a.y);
  return {x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys)};
};
const ringCentre = (mol, P, a, b) => {
  const rs = (mol.rings || []).filter(r => r.includes(a) && r.includes(b));
  if (!rs.length) return null;
  const r = rs.sort((p, q) => p.length - q.length)[0];
  return r.reduce((s, i) => [s[0] + P[i][0] / r.length, s[1] + P[i][1] / r.length], [0, 0]);
};

/**
 * Flat skeletal drawing of a molecule from make_fig5.py / molecules.json coordinates.
 * Scaled to fit {w, h} with the structure centred; heteroatoms are lettered and their bonds shortened.
 */
export const Mol = ({mol, x, y, w, h, color = K.bone, pad = 12, weight, label, opacity = 1}) => {
  const bb = bbox(mol.atoms), bw = bb.x1 - bb.x0, bh = bb.y1 - bb.y0;
  const s = Math.min((w - 2 * pad) / (bw || 1), (h - 2 * pad) / (bh || 1));
  const ox = x + w / 2 - (bb.x0 + bw / 2) * s, oy = y + h / 2 - (bb.y0 + bh / 2) * s;
  const P = mol.atoms.map(a => [ox + a.x * s, oy + a.y * s]);
  const sw = weight ?? Math.max(1.5, s * 0.075);
  const fs = label ?? Math.max(11, s * 0.52);
  const lettered = mol.atoms.map(a => a.el !== "C");
  const lines = [];
  mol.bonds.forEach((bd, i) => {
    let A = P[bd.a], B = P[bd.b];
    const dx = B[0] - A[0], dy = B[1] - A[1], L = Math.hypot(dx, dy) || 1;
    const ux = dx / L, uy = dy / L, nx = -uy, ny = ux, cut = s * 0.3;
    if (lettered[bd.a]) A = [A[0] + ux * cut, A[1] + uy * cut];
    if (lettered[bd.b]) B = [B[0] - ux * cut, B[1] - uy * cut];
    const seg = (a, b, k, wt = sw) => lines.push(
      <line key={`${i}-${k}`} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke={color} strokeWidth={wt} strokeLinecap="butt"/>);
    if (bd.order !== 2) { seg(A, B, 0); return; }
    const rc = ringCentre(mol, P, bd.a, bd.b);
    if (rc) {
      // ring double bond: the second line sits inside the ring and is trimmed at both ends
      const mx = (A[0] + B[0]) / 2, my = (A[1] + B[1]) / 2;
      const side = Math.sign((rc[0] - mx) * nx + (rc[1] - my) * ny) || 1, off = s * 0.16 * side, tr = L * 0.16;
      seg(A, B, 0);
      seg([A[0] + nx * off + ux * tr, A[1] + ny * off + uy * tr], [B[0] + nx * off - ux * tr, B[1] + ny * off - uy * tr], 1, sw * 0.9);
    } else {
      const off = s * 0.08;
      seg([A[0] + nx * off, A[1] + ny * off], [B[0] + nx * off, B[1] + ny * off], 0);
      seg([A[0] - nx * off, A[1] - ny * off], [B[0] - nx * off, B[1] - ny * off], 1);
    }
  });
  return <g opacity={opacity}>
    {lines}
    {mol.atoms.map((a, i) => {
      if (!lettered[i]) return null;
      // the H is its own glyph, set out along the side with no bond, so it lands on neither a bond nor the atom's letter
      let fx = 0, fy = 0;
      mol.bonds.forEach(bd => {
        if (bd.a !== i && bd.b !== i) return;
        const j = bd.a === i ? bd.b : bd.a, dx = P[j][0] - P[i][0], dy = P[j][1] - P[i][1], L = Math.hypot(dx, dy) || 1;
        fx -= dx / L; fy -= dy / L;
      });
      const free = Math.hypot(fx, fy), ux = free > 0.2 ? fx / free : 0, uy = free > 0.2 ? fy / free : -1, hs = fs * 0.84;
      const glyph = {textAnchor: "middle", fontFamily: "inherit", fill: color, stroke: K.bg, strokeWidth: 4, paintOrder: "stroke"};  // black knockout keeps a letter clear of any line next to it
      return <React.Fragment key={`a${i}`}>
        <text x={P[i][0]} y={P[i][1] + fs * 0.35} fontSize={fs} {...glyph}>{a.el}</text>
        {a.h > 0 ? <text x={P[i][0] + ux * fs * 0.95} y={P[i][1] + uy * fs * 0.95 + hs * 0.35} fontSize={hs} {...glyph}>H</text> : null}
      </React.Fragment>;
    })}
  </g>;
};

// ---------- a measured bar on the nM scale (stills 8 and 10) ----------
// One scale for both frames. 0.27 px per nM lands 6,000 nM on the frame at x = 1716, and 048 at the 9 px and +-6 px section 3 S5 asks for. Every length is value x scale.
export const PX_PER_NM = 0.27;

/** Bar from x, length value on the scale, with its +- whisker. The stretch of whisker inside the bar flips to the ground colour, so the whole +- shows. Draw inside an svg. */
export const NmBar = ({x, y, h, value, sd, color = K.bone, cap = h * 0.42}) => {
  const end = x + value * PX_PER_NM, lo = x + (value - sd) * PX_PER_NM, hi = x + (value + sd) * PX_PER_NM, mid = y + h / 2;
  const tick = (at, ink) => <line x1={at} y1={mid - cap} x2={at} y2={mid + cap} stroke={ink} strokeWidth={2}/>;
  return <g>
    <rect x={x} y={y} width={end - x} height={h} fill={color}/>
    <line x1={lo} y1={mid} x2={end} y2={mid} stroke={K.bg} strokeWidth={2}/>
    <line x1={end} y1={mid} x2={hi} y2={mid} stroke={color} strokeWidth={2}/>
    {tick(lo, K.bg)}{tick(hi, color)}
  </g>;
};

// ---------- a dish of lights (still 10) ----------
// Deterministic, so the two dishes differ in pattern but never in count.
const hash32 = (i, seed) => {
  let h = (Math.imul(i + 1, 2654435761) + Math.imul(seed + 1, 40503)) >>> 0;
  h ^= h >>> 15; h = Math.imul(h, 2246822519) >>> 0; h ^= h >>> 13;
  return h >>> 0;
};
/** Exactly n/2 of n indices, picked by hash so the pattern scatters. n must be even. */
export const halfLit = (n, seed) => {
  const order = [...Array(n).keys()].sort((a, b) => hash32(a, seed) - hash32(b, seed));
  return new Set(order.slice(0, n / 2));
};

export const DISH_RINGS = [6, 12, 18, 24];  // 60 lights: half is a whole 30, so "half the signal" is literal
export const DISH_N = DISH_RINGS.reduce((a, b) => a + b, 0);

/** Concentric rings of lights inside a dashed circle. lit = a Set of indices. */
export const Dish = ({cx, cy, r, lit, on = K.red, out = DIM, dot = 12}) => {
  const pts = [];
  DISH_RINGS.forEach((count, ring) => {
    const rr = r * (ring + 1) / (DISH_RINGS.length + 0.35);
    const turn = ring * Math.PI / DISH_RINGS.length;  // stagger so rings do not line up radially
    for (let k = 0; k < count; k++) {
      const t = turn + k * 2 * Math.PI / count;
      pts.push([cx + Math.cos(t) * rr, cy + Math.sin(t) * rr]);
    }
  });
  return <g>
    <circle cx={cx} cy={cy} r={r} fill="none" stroke={out} strokeWidth={2} strokeDasharray="12 10"/>
    {pts.map(([px, py], i) => lit.has(i)
      ? <circle key={i} cx={px} cy={py} r={dot} fill={on}/>
      : <circle key={i} cx={px} cy={py} r={dot} fill="none" stroke={out} strokeWidth={1.5}/>)}
  </g>;
};
