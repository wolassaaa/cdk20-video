// Real molecules (RDKit 2D depiction of the actual SMILES, see molecules.json) drawn as ink.
import React from "react";
import {C, HAND, clamp01, outBack, hash, handLine, MONO} from "./core";
import {InkPath} from "./ink";
import MOLS from "./molecules.json";

export {MOLS};
export const M001 = MOLS.m001, M048 = MOLS.m048;
export const NEW_048 = new Set(M048.newAtoms); // the pyrazole added in round 2

export const bbox = mol => {
  const xs = mol.atoms.map(a => a.x), ys = mol.atoms.map(a => a.y);
  return {x0: Math.min(...xs), x1: Math.max(...xs), y0: Math.min(...ys), y1: Math.max(...ys),
    cx: (Math.min(...xs) + Math.max(...xs)) / 2, cy: (Math.min(...ys) + Math.max(...ys)) / 2};
};

/** Screen positions of atoms. center = unit-space point placed at (x,y); defaults to bbox centre. */
export const molPoints = (mol, x, y, scale, center) => {
  const c = center || (({cx, cy}) => [cx, cy])(bbox(mol));
  return mol.atoms.map(a => [x + (a.x - c[0]) * scale, y + (a.y - c[1]) * scale]);
};

// BFS order from atom 0 so the molecule draws on as one continuous gesture
const drawOrder = mol => {
  const adj = mol.atoms.map(() => []);
  mol.bonds.forEach((b, i) => { adj[b.a].push([b.b, i]); adj[b.b].push([b.a, i]); });
  const seen = new Set([0]), q = [0], order = [], dir = {};
  const used = new Set();
  while (q.length) {
    const u = q.shift();
    for (const [v, bi] of adj[u]) {
      if (used.has(bi)) continue;
      used.add(bi); order.push(bi); dir[bi] = u;
      if (!seen.has(v)) { seen.add(v); q.push(v); }
    }
  }
  return {order, dir};
};
const ORDER_CACHE = new Map();
const getOrder = mol => { if (!ORDER_CACHE.has(mol)) ORDER_CACHE.set(mol, drawOrder(mol)); return ORDER_CACHE.get(mol); };

const ringCenter = (mol, P, a, b) => {
  const rs = mol.rings.filter(r => r.includes(a) && r.includes(b));
  if (!rs.length) return null;
  const r = rs.sort((p, q) => p.length - q.length)[0];
  return r.reduce((s, i) => [s[0] + P[i][0] / r.length, s[1] + P[i][1] / r.length], [0, 0]);
};

/**
 * Ink skeletal formula.
 * progress: 0..1 draws bonds in BFS order. bondProgress(bondIndex, defaultLocal) can override per bond.
 * tint(atomIndex) -> colour for labels/bonds touching that atom (e.g. cyan for the round-2 pyrazole).
 * hide(atomIndex) -> true to skip atoms (and their bonds) entirely.
 */
export const InkMolecule = ({mol, x, y, scale = 64, center, progress = 1, bondProgress, tint = () => C.ink, hide = () => false,
  size, labelSize, seed = 5, opacity = 1, labelFilter = true}) => {
  const P = molPoints(mol, x, y, scale, center);
  const {order, dir} = getOrder(mol);
  const n = order.length;
  const sw = size ?? Math.max(3, scale * 0.105);
  const fs = labelSize ?? scale * 0.62;
  const labelled = mol.atoms.map(a => a.el !== "C");
  const local = {};
  order.forEach((bi, k) => {
    const d = clamp01((progress * (n + 2) - k) / 3);
    local[bi] = bondProgress ? bondProgress(bi, d) : d;
  });
  const out = [];
  mol.bonds.forEach((bd, bi) => {
    if (hide(bd.a) || hide(bd.b)) return;
    const p = local[bi];
    if (p <= 0) return;
    const from = dir[bi] ?? bd.a, to = from === bd.a ? bd.b : bd.a;
    let A = P[from], B = P[to];
    const dx = B[0] - A[0], dy = B[1] - A[1], L = Math.hypot(dx, dy), ux = dx / L, uy = dy / L, nx = -uy, ny = ux;
    const sh = scale * 0.34;
    if (labelled[from]) A = [A[0] + ux * sh, A[1] + uy * sh];
    if (labelled[to]) B = [B[0] - ux * sh, B[1] - uy * sh];
    const col = tint(bd.a) !== C.ink ? tint(bd.a) : tint(bd.b);
    const r = k => hash(bi * 5 + k, seed) - 0.5;
    const key = `b${bi}`;
    // bonds: near-even marker pressure, round start cap, slight overshoot so joints overlap like real pen work
    const line = (a, b, s, k, w = sw) => <InkPath key={key + k} points={handLine(a, b, {bow: r(k) * L * 0.05, over: 1.5 + r(k + 2) * 3})} seed={seed * 100 + bi * 4 + k}
      size={w} color={col} progress={p} pressure="marker" thinning={0.35} jitter={1.0} taperStart={0} taperEnd={w * 0.9}/>;
    if (bd.order === 1) { out.push(line(A, B, 0, 0)); return; }
    if (bd.order === 2) {
      const rc = ringCenter(mol, P, bd.a, bd.b);
      if (rc) {
        const mx = (P[bd.a][0] + P[bd.b][0]) / 2, my = (P[bd.a][1] + P[bd.b][1]) / 2;
        const side = Math.sign((rc[0] - mx) * nx + (rc[1] - my) * ny) || 1;
        const off = scale * 0.18 * side, tr = L * 0.15;
        out.push(line(A, B, 0, 0));
        out.push(line([A[0] + nx * off + ux * tr, A[1] + ny * off + uy * tr], [B[0] + nx * off - ux * tr, B[1] + ny * off - uy * tr], 0, 1, sw * 0.8));
      } else {
        const off = scale * 0.085;
        out.push(line([A[0] + nx * off, A[1] + ny * off], [B[0] + nx * off, B[1] + ny * off], 0, 0));
        out.push(line([A[0] - nx * off, A[1] - ny * off], [B[0] - nx * off, B[1] - ny * off], 0, 1));
      }
      return;
    }
    out.push(line(A, B, 0, 0));
  });
  // hand-lettered heteroatoms, pop on once a touching bond is half drawn
  const labels = [];
  mol.atoms.forEach((a, i) => {
    if (!labelled[i] || hide(i)) return;
    let m = 0, fx = 0, fy = 0;
    mol.bonds.forEach((bd, bi) => {
      if (bd.a !== i && bd.b !== i) return;
      m = Math.max(m, local[bi]);
      const j = bd.a === i ? bd.b : bd.a, dx = P[j][0] - P[i][0], dy = P[j][1] - P[i][1], L = Math.hypot(dx, dy);
      fx -= dx / L; fy -= dy / L;
    });
    const t = clamp01((m - 0.3) / 0.5);
    if (t <= 0) return;
    const s = outBack(t, 2.4);
    const [px, py] = P[i];
    const col = tint(i);
    const rot = (hash(i, seed, 3) - 0.5) * 10;
    let hx = 0, hy = 0;
    if (a.h > 0) {
      if (Math.abs(fx) >= Math.abs(fy) * 0.7) hx = Math.sign(fx || 1) * fs * 0.72; else hy = Math.sign(fy || 1) * fs * 0.86;
    }
    labels.push(<g key={`l${i}`} transform={`translate(${px} ${py}) scale(${s}) rotate(${rot})`} filter={labelFilter ? "url(#v3-boil-text)" : undefined}>
      <text x={0} y={fs * 0.36} textAnchor="middle" fontFamily={HAND} fontSize={fs} fill={col}>{a.el}</text>
      {a.h > 0 ? <text x={hx} y={hy + fs * 0.36} textAnchor="middle" fontFamily={HAND} fontSize={fs * 0.82} fill={col}>H</text> : null}
    </g>);
  });
  return <g opacity={opacity}>{out}{labels}</g>;
};

/** Points that define a pocket around a drawn ligand: atoms + bond midpoints + ring centres. */
export const pocketPoints = (mol, P) => [
  ...P,
  ...mol.bonds.map(b => [(P[b.a][0] + P[b.b][0]) / 2, (P[b.a][1] + P[b.b][1]) / 2]),
  ...mol.rings.map(r => r.reduce((s, i) => [s[0] + P[i][0] / r.length, s[1] + P[i][1] / r.length], [0, 0])),
];

/** Clean cyan wireframe of some bonds (the AI's proposal before it is inked). */
export const MolGhost = ({mol, x, y, scale = 64, center, atoms, progress = 1, color = C.cyan, opacity = 1, nodes = true}) => {
  const P = molPoints(mol, x, y, scale, center);
  const set = new Set(atoms);
  const bonds = mol.bonds.filter(b => set.has(b.a) || set.has(b.b));
  return <g opacity={opacity}>
    {bonds.map((b, i) => {
      const p = clamp01(progress * (bonds.length + 1) - i);
      if (p <= 0) return null;
      const A = P[b.a], B = P[b.b];
      return <line key={i} x1={A[0]} y1={A[1]} x2={A[0] + (B[0] - A[0]) * p} y2={A[1] + (B[1] - A[1]) * p} stroke={color} strokeWidth={1.6} strokeDasharray="5 5"/>;
    })}
    {nodes && atoms.map((a, i) => progress > i / atoms.length ? <g key={`n${a}`}>
      <rect x={P[a][0] - 5} y={P[a][1] - 5} width={10} height={10} fill="none" stroke={color} strokeWidth={1.5}/>
      <text x={P[a][0] + 10} y={P[a][1] - 9} fontFamily={MONO} fontSize={12} fill={color}>{mol.atoms[a].el}{a}</text>
    </g> : null)}
  </g>;
};
