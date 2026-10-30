// W2 motion test: a loose blue cloud condenses into CDK20 along the chain. Sure residues land hard and turn bone; the tail never lands. Ends on still 04.
// Each residue's bar is drawn the moment its dots arrive, so the barcode is a live readout of the same 346 scores.
// The tail's drift is smooth and slow, a sum of sines on time: it reads as loose, not as noise, and it stays clean frame to frame.
import React, {useLayoutEffect, useRef, useState} from "react";
import {continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {Stage, Plate, Barcode, K, W, H, M, N_RES, PLDDT} from "../kit";
import META from "../data/protein_points.json";

const START = 0.6, SWEEP = 6.2, TRAVEL = 1.1;  // seconds: first residue leaves, last one leaves after SWEEP, each takes TRAVEL
const PLATE_AT = 8.2;                          // the one label cuts in once the shape has settled
const TIGHT = 1.1, LOOSE = 1.75;               // dot radii, as still 04
const REACH = 520, DRIFT = 7;                  // px: how far out the cloud starts, how far the tail wanders

const hash = (i, k) => { const s = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return s - Math.floor(s); };
const smooth = x => { x = Math.min(1, Math.max(0, x)); return x * x * x * (x * (x * 6 - 15) + 10); };
const leaves = r => START + SWEEP * (r - 1) / (N_RES - 1);

let baked = null;
const load = () => baked ??= fetch(staticFile(META.file)).then(r => r.arrayBuffer()).then(buf => {
  const n = META.n, xs = new Float32Array(buf, 0, n), ys = new Float32Array(buf, 4 * n, n), rs = new Uint16Array(buf, 8 * n, n);
  const ox = new Float32Array(n), oy = new Float32Array(n), ph = new Float32Array(n);
  for (let i = 0; i < n; i++) {
    const a = hash(i, 1) * 2 * Math.PI, d = REACH * Math.sqrt(hash(i, 2));
    ox[i] = Math.cos(a) * d; oy[i] = Math.sin(a) * d; ph[i] = hash(i, 3) * 2 * Math.PI;
  }
  return {xs, ys, rs, ox, oy, ph};
});

const Cloud = ({t}) => {
  const ref = useRef(null), [d, set] = useState(null), [h] = useState(() => delayRender(META.file, {timeoutInMilliseconds: 60000}));
  useLayoutEffect(() => { load().then(v => { set(v); continueRender(h); }); }, [h]);
  useLayoutEffect(() => {
    if (!d) return;
    const c = ref.current, ss = Math.max(window.devicePixelRatio || 1, 2), g = c.getContext("2d");
    c.width = W * ss; c.height = H * ss;
    g.setTransform(ss, 0, 0, ss, 0, 0);
    // one pass per colour, flushed in batches: a single path of 30k circles is slow to fill
    const draw = (ink, rad, want) => {
      g.fillStyle = ink; g.beginPath();
      for (let i = 0, k = 0; i < d.rs.length; i++) {
        const r = d.rs[i], sure = PLDDT[r - 1] >= META.cutoff, p = smooth((t - leaves(r) - hash(i, 4) * 0.25) / TRAVEL), landed = sure && p >= 1;
        if (landed !== want) continue;
        const w = sure ? 0 : DRIFT, dx = w * Math.sin(0.5 * t + d.ph[i]), dy = w * Math.cos(0.37 * t + 1.7 * d.ph[i]);
        const x = d.xs[i] + d.ox[i] * (1 - p) + dx, y = d.ys[i] + d.oy[i] * (1 - p) + dy;
        g.moveTo(x + rad, y); g.arc(x, y, rad, 0, 2 * Math.PI);
        if (++k % 4096 === 0) { g.fill(); g.beginPath(); }
      }
      g.fill();
    };
    draw(K.blue, LOOSE, false);
    draw(K.bone, TIGHT, true);
  }, [d, t]);
  return <canvas ref={ref} style={{position: "absolute", left: 0, top: 0, width: W, height: H}}/>;
};

export default () => {
  const f = useCurrentFrame(), {fps} = useVideoConfig(), t = f / fps;
  // bars grow out from the left as their residues land
  const lit = Math.min(N_RES, Math.max(0, Math.floor((t - START - TRAVEL) / SWEEP * (N_RES - 1)) + 1));
  return <Stage>
    <Cloud t={t}/>
    {t >= PLATE_AT ? <Plate kind="ai" x={M} y={M}>AlphaFold DB v6 · predicted</Plate> : null}
    <div style={{position: "absolute", left: M, top: 936, width: 1730 * lit / N_RES, height: 48, overflow: "hidden"}}>
      <Barcode height={48} bar={2}/>
    </div>
  </Stage>;
};
