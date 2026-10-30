// SCAN extra still: 1-02 "Top 3 deadliest in HK: lung · colorectal · liver".
// Same language as the test: hairline sections of light, 0.25 mm apart, same camera, true relative scale.
// One scan line crosses all three organs; each shows the real section under the line in blood red.
import React, {useEffect, useLayoutEffect, useRef, useState} from "react";
import {AbsoluteFill, continueRender, delayRender, staticFile} from "remotion";
import {K, W, H, GROT, T, fmt, makeCam} from "./lib";

const SS = 2, LW = 0.5, TONE = 0.085, IT = 0.03;
const CAMA = {yaw: -6 * Math.PI / 180, el: 20 * Math.PI / 180};
const S = 2.2, Y0 = 500;                                  // px/mm; the scan line
const ORD = [["lung", 380, 1236], ["colorectal", 966, 948], ["liver", 1530, 1110]];   // name, screen x, z under the line

let P = null;
const load = () => P || (P = (async () => {
  const [j, b] = await Promise.all([fetch(staticFile("trio.json")).then(r => r.json()), fetch(staticFile("trio.bin")).then(r => r.arrayBuffer())]);
  return {...j, bin: new Int16Array(b)};
})());

const paint = (ctx, D) => {
  const off = document.createElement("canvas"); off.width = W * SS; off.height = H * SS;
  const c = off.getContext("2d");
  c.fillStyle = "#000"; c.fillRect(0, 0, W * SS, H * SS);
  c.setTransform(SS, 0, 0, SS, 0, 0);
  c.globalCompositeOperation = "lighter"; c.lineWidth = LW; c.lineJoin = "round";
  const dec = ([o, n]) => { const A = new Float64Array(n * 2); for (let i = 0; i < n * 2; i++) A[i] = D.bin[o + i] / D.q; return A; };
  const red = [];
  for (const [name, x, zl] of ORD) {
    const O = D.org[name];
    const m = [(O.bmin[0] + O.bmax[0]) / 2, (O.bmin[1] + O.bmax[1]) / 2, zl];
    const cam = makeCam({...CAMA, s: S, cx: x, cy: Y0, m});
    for (let k = O.sec.length - 1; k >= 0; k--) {
      const s = O.sec[k];
      c.strokeStyle = `rgba(255,255,255,${name === "colorectal" ? 0.12 : TONE})`;
      for (const r of s.s) c.stroke(new Path2D(cam.path(dec(r), s.z, false)));
      c.strokeStyle = `rgba(255,255,255,${IT})`;
      for (const r of s.i) c.stroke(new Path2D(cam.path(dec(r), s.z, false)));
    }
    const k = Math.round((O.sec[0].z - zl) / D.dz);
    const s = O.sec[k];
    const fill = new Path2D(), ves = new Path2D();
    for (const r of s.s) fill.addPath(new Path2D(cam.path(dec(r), s.z, true)));
    for (const r of s.i) ves.addPath(new Path2D(cam.path(dec(r), s.z, false)));
    red.push({fill, ves});
  }
  ctx.globalCompositeOperation = "copy";
  ctx.imageSmoothingQuality = "high";
  ctx.drawImage(off, 0, 0, W, H);
  ctx.globalCompositeOperation = "source-over";
  const im = ctx.getImageData(0, 0, W, H), d = im.data;
  const bone = [237, 235, 228];
  for (let i = 0; i < d.length; i += 4) for (let c2 = 0; c2 < 3; c2++) d[i + c2] = 6 + (bone[c2] - 6) * Math.pow(d[i + c2] / 255, 0.94);
  ctx.putImageData(im, 0, 0);
  for (const {fill, ves} of red) {
    ctx.fillStyle = K.red; ctx.fill(fill, "evenodd");
    ctx.strokeStyle = K.bg; ctx.lineWidth = 0.7; ctx.stroke(ves);
  }
};

export const ScanExtra = () => {
  const [D, setD] = useState(null);
  const [h] = useState(() => delayRender("trio"));
  const ref = useRef(null);
  useEffect(() => { load().then(setD); }, []);
  useLayoutEffect(() => {
    if (!D || !ref.current) return;
    paint(ref.current.getContext("2d", {willReadFrequently: true}), D);
    continueRender(h);
  }, [D, h]);
  const y = Y0 + 0.5;
  return <AbsoluteFill style={{backgroundColor: K.bg}}>
    <canvas ref={ref} width={W} height={H} style={{position: "absolute", left: 0, top: 0}}/>
    {D ? <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <line x1={0} y1={y} x2={W} y2={y} stroke={K.red} strokeOpacity={0.85} strokeWidth={1}/>
      {ORD.map(([name, x, zl]) => {
        const O = D.org[name];
        const s = O.sec[Math.round((O.sec[0].z - zl) / D.dz)];
        return <g key={name}>
          <T x={x} y={918} anchor="middle" size={13} ls={1.5} op={0.6}>{`Z ${fmt(s.z, 1)} MM · A ${fmt(s.a)} MM²`}</T>
        </g>;
      })}
      <text x={960} y={80} textAnchor="middle" fontFamily={GROT} fontWeight={300} fontSize={40} fill={K.bone}>Top 3 deadliest in HK: lung · colorectal · liver</text>
    </svg> : null}
  </AbsoluteFill>;
};
