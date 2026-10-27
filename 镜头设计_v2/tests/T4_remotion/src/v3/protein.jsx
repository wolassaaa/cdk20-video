// Hand-drawn protein "lock": lumpy surface, cartoon ribbons, hatching, and a pocket carved around a real ligand.
import React from "react";
import {C, catmull, hash, loopPts, quad} from "./core";
import {InkPath, Hatch, RoughPolygon} from "./ink";
import {Halftone} from "./texture";

/** Lumpy, slightly scalloped blob outline (molecular-surface feel). */
export const blobPts = (cx, cy, rx, ry, seed = 1, n = 180) => Array.from({length: n}, (_, i) => {
  const a = (i / n) * Math.PI * 2;
  const r = 1 + 0.055 * Math.sin(3 * a + seed) + 0.035 * Math.sin(5 * a + seed * 2.1) + 0.02 * Math.sin(8 * a + seed * 0.7) + 0.012 * Math.abs(Math.sin(15 * a));
  return [cx + Math.cos(a) * rx * r, cy + Math.sin(a) * ry * r];
});

/** Helix as a hand-drawn coil between two points. */
export const helixPts = (a, b, turns = 5, amp = 26) => {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L, nx = -uy, ny = ux;
  const n = turns * 24;
  return Array.from({length: n + 1}, (_, i) => {
    const t = i / n, ph = t * turns * Math.PI * 2;
    const along = t * L + Math.cos(ph) * amp * 0.55, side = Math.sin(ph) * amp;
    return [a[0] + ux * along + nx * side, a[1] + uy * along + ny * side];
  });
};

/** Beta strand: flat arrow outline. */
export const strandPts = (a, b, w = 30) => {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L, nx = -uy, ny = ux;
  const hl = w * 1.3, P = (s, t) => [a[0] + ux * s + nx * t, a[1] + uy * s + ny * t];
  return [P(0, -w / 2), P(L - hl, -w / 2), P(L - hl, -w), P(L, 0), P(L - hl, w), P(L - hl, w / 2), P(0, w / 2), P(0, -w / 2)];
};

/**
 * The lock. pocket = screen points of the ligand's atoms; the pocket is the union of circles of radius pocketR
 * (drawn with the stroke-then-fill trick, so only the scalloped union boundary survives).
 */
export const ProteinLock = ({cx, cy, rx, ry, pocket = [], pocketR = 58, seed = 7, progress = 1, ribbons = [], id = "lock", halftone = true}) => {
  const outline = blobPts(cx, cy, rx, ry, seed);
  const closed = [...outline, outline[0]];
  const d = outline.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("") + "Z";
  const near = (x, y) => { let m = 1e9; for (const p of pocket) m = Math.min(m, Math.hypot(x - p[0], y - p[1])); return m; };
  return <g>
    <defs>
      <clipPath id={`${id}-in`}><path d={d}/></clipPath>
      <mask id={`${id}-nopocket`} maskUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080">
        <rect width="1920" height="1080" fill="white"/>
        {pocket.map((p, i) => <circle key={i} cx={p[0]} cy={p[1]} r={pocketR - 4} fill="black"/>)}
      </mask>
    </defs>
    <g clipPath={`url(#${id}-in)`}>
      {/* depth: halftone thickens toward the pocket rim */}
      {halftone && <Halftone bounds={[cx - rx * 1.15, cy - ry * 1.15, rx * 2.3, ry * 2.3]} field={(x, y) => { const q = near(x, y); return q < pocketR ? 0 : Math.max(0, 1 - (q - pocketR) / 150) ** 1.2; }}
        cell={11} angle={0.3} color={C.verm} opacity={0.95}/>}
      <Hatch poly={outline} angle={-0.85} gap={17} size={2.4} color={C.verm} seed={seed * 10} progress={progress} opacity={0.75}/>
      <g opacity={0.92}>
        {ribbons.map((r, i) => r.kind === "helix"
          ? <InkPath key={i} points={helixPts(r.a, r.b, r.turns, r.amp)} seed={seed * 30 + i} size={4.2} pressure="brush" jitter={1.2} progress={progress}/>
          : r.kind === "strand"
            ? <RoughPolygon key={i} points={strandPts(r.a, r.b, r.w).slice(0, -1)} seed={seed * 30 + i} size={3.6} progress={progress} options={{roughness: 1.1, bowing: 1.2}}/>
            : <InkPath key={i} points={catmull(r.pts, false, 10)} seed={seed * 30 + i} size={3.4} pressure="nib" jitter={1.5} progress={progress}/>)}
      </g>
      {/* pocket rim: every circle stroked, then every circle filled black -> scalloped union outline */}
      {pocket.map((p, i) => <InkPath key={`r${i}`} points={loopPts(p[0], p[1], pocketR, pocketR, {turns: 1.05, a0: hash(i, seed) * 6, n: 48, spiral: 0.02, seed: i})}
        seed={seed * 50 + i} size={7} pressure="marker" jitter={1.4} progress={progress}/>)}
      {pocket.map((p, i) => <circle key={`f${i}`} cx={p[0]} cy={p[1]} r={pocketR - 3.5} fill={C.bg}/>)}
    </g>
    <g mask={`url(#${id}-nopocket)`}>
      <InkPath points={closed} seed={seed + 1} size={11} pressure="brush" thinning={0.5} jitter={2.4} ghost={0.25} progress={progress}/>
    </g>
  </g>;
};

export {quad};
