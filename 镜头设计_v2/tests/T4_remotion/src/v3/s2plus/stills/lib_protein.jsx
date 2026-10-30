// Stills 4, 5, 13: the baked CDK20 stipple from make_protein_points.py on a device-scale 2D canvas, the ghost around it, and a public-file probe.
// Dots are in design px for a 1920x1080 frame. Colour is not baked: each dot takes its residue's real score through BAR_MODES, so a dot and its bar cannot disagree.
import React, {useEffect, useLayoutEffect, useRef, useState} from "react";
import {flushSync} from "react-dom";
import {continueRender, delayRender, staticFile} from "remotion";
import {K, W, H, M, N_RES, PLDDT, BAR_MODES, Foot} from "../kit";
import META from "../data/protein_points.json";

// ---------- public-file probe ----------
// true or false once known, null before. The handle stays open until the answer is committed, so the branch it picks can place its own delayRender first.
export const useStaticFile = name => {
  const [ok, set] = useState(null), [h] = useState(() => delayRender(`probe ${name}`));
  useEffect(() => { fetch(staticFile(name)).then(r => set(r.ok), () => set(false)); }, [name]);
  useEffect(() => { if (ok !== null) continueRender(h); }, [ok, h]);
  return ok;
};

// ---------- dots ----------
let baked = null;  // one fetch, shared by the dots and the ghost
const loadDots = () => baked ??= fetch(staticFile(META.file)).then(async r => {
  if (!r.ok) throw new Error(`${META.file}: ${r.status}`);
  const buf = await r.arrayBuffer(), n = META.n;
  if (buf.byteLength !== 10 * n) throw new Error(`${META.file}: ${buf.byteLength} bytes, want ${10 * n}: re-run make_protein_points.py`);
  return {xs: new Float32Array(buf, 0, n), ys: new Float32Array(buf, 4 * n, n), rs: new Uint16Array(buf, 8 * n, n)};
});

// One flat colour per pass, flushed in batches: a single path of 30k circles is slow to fill.
const pass = (g, xs, ys, rs, last, sure, ink, rad) => {
  g.fillStyle = ink; g.beginPath();
  for (let i = 0, k = 0; i < rs.length; i++) {
    if (rs[i] > last || PLDDT[rs[i] - 1] >= META.cutoff !== sure) continue;
    g.moveTo(xs[i] + rad, ys[i]); g.arc(xs[i], ys[i], rad, 0, 2 * Math.PI);
    if (++k % 4096 === 0) { g.fill(); g.beginPath(); }
  }
  g.fill();
};

/**
 * Full-frame canvas, so it maps 1:1 to device pixels at --scale=2. scale, x, y move the dots: screen = x + scale * dot.
 * last drops residues after it. tight and loose are dot radii in design px, not scaled with the model. mode is a BAR_MODES key, as on the barcode.
 */
export const ProteinPoints = ({scale = 1, x = 0, y = 0, last = N_RES, tight = 0.8, loose = 1.75, mode = "splat", style}) => {
  const ref = useRef(null), [missing, setMissing] = useState(false);
  useLayoutEffect(() => {
    const h = delayRender(META.file, {timeoutInMilliseconds: 60000});
    (async () => {
      const {xs, ys, rs} = await loadDots();
      const c = ref.current, ss = Math.max(window.devicePixelRatio || 1, 2), g = c.getContext("2d");
      c.width = W * ss; c.height = H * ss;
      g.setTransform(ss * scale, 0, 0, ss * scale, ss * x, ss * y);
      pass(g, xs, ys, rs, last, true, BAR_MODES[mode](100), tight / scale);
      pass(g, xs, ys, rs, last, false, BAR_MODES[mode](0), loose / scale);
    })().catch(e => { console.error(e); flushSync(() => setMissing(true)); }).finally(() => continueRender(h));
  }, [scale, x, y, last, tight, loose, mode]);
  return <>
    <canvas ref={ref} style={{position: "absolute", left: 0, top: 0, width: W, height: H, ...style}}/>
    {missing ? <Foot x={M} y={H / 2}>FALLBACK · {META.file} missing: run make_protein_points.py</Foot> : null}
  </>;
};

// ---------- ghost ----------
// A smooth closed line around every dot, tail outliers included. Dashes in the plate grammar mean schematic; it carries no measured data, and as a plain blob it hints at no result.
const SECTORS = 180, REACH = 6;  // 2-degree sectors, smoothed over 12 degrees each side
const ringAvg = (a, f) => a.map((_, i) => { const v = []; for (let j = -REACH; j <= REACH; j++) v.push(a[(i + j + SECTORS) % SECTORS]); return f(v); });

// Largest radius per sector, then a max filter, then a mean over the same span: the mean of a max filter never drops below the peak it started from, so the clearance holds after smoothing.
const envelope = ({xs, ys}, scale, x, y, gap) => {
  let cx = 0, cy = 0;
  for (let i = 0; i < xs.length; i++) { cx += x + scale * xs[i]; cy += y + scale * ys[i]; }
  cx /= xs.length; cy /= xs.length;
  const far = new Array(SECTORS).fill(0);
  for (let i = 0; i < xs.length; i++) {
    const dx = x + scale * xs[i] - cx, dy = y + scale * ys[i] - cy, s = Math.floor((Math.atan2(dy, dx) + Math.PI) / (2 * Math.PI) * SECTORS) % SECTORS;
    far[s] = Math.max(far[s], Math.hypot(dx, dy) + gap);
  }
  const ring = ringAvg(ringAvg(far, v => Math.max(...v)), v => v.reduce((a, b) => a + b) / v.length);
  return ring.map((r, i) => { const t = -Math.PI + (i + 0.5) * 2 * Math.PI / SECTORS; return `${i ? "L" : "M"}${(cx + r * Math.cos(t)).toFixed(1)} ${(cy + r * Math.sin(t)).toFixed(1)}`; }).join("") + "Z";
};

/** Place with the same scale, x, y as the dots. clear: least screen px between the line and any dot's edge. The 2 px on top is the 1.5 px dot radius plus the chord between two sectors. */
export const Ghost = ({scale = 1, x = 0, y = 0, clear = 12, weight = 1.5, dash = "14 10"}) => {
  const [d, set] = useState(null), [h] = useState(() => delayRender("ghost"));
  useEffect(() => { loadDots().then(p => set(envelope(p, scale, x, y, clear + 2)), e => { console.error(e); set(""); }); }, [scale, x, y, clear]);
  useEffect(() => { if (d !== null) continueRender(h); }, [d, h]);
  return <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
    <path d={d ?? ""} fill="none" stroke={K.bone} strokeWidth={weight} strokeDasharray={dash}/>
  </svg>;
};
