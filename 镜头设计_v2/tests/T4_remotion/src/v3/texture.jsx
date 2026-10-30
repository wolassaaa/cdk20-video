// Surface: black stage with print grain, ink-edge filters, halftone fields, dust.
import React, {createContext, useContext} from "react";
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from "remotion";
import {C, W, H, hash, useBoil, rotPt} from "./core";

/**
 * Filters every v3 scene needs. Put once inside the scene's main <svg>.
 * v3-boil-text: crawling edges for hand lettering (seed changes with the boil clock)
 * v3-ink: dry-brush edge + speckle holes, for whole ink layers
 * v3-tint-cyan / v3-tint-verm: recolour a layer (used for misregistration copies on impact frames)
 */
export const InkDefs = ({textScale = 4.5, inkScale = 2.6}) => {
  const b = useBoil();
  const s = (b % 997) + 1;
  return <defs>
    <filter id="v3-boil-text" x="-10%" y="-30%" width="120%" height="160%">
      <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" seed={s} result="n"/>
      <feDisplacementMap in="SourceGraphic" in2="n" scale={textScale} xChannelSelector="R" yChannelSelector="G" result="d"/>
      <feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="1" seed={s + 3} result="g"/>
      <feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -3.2 0 0 0 2.75" result="m"/>
      <feComposite in="d" in2="m" operator="in"/>
    </filter>
    <filter id="v3-ink" x="0" y="0" width={W} height={H} filterUnits="userSpaceOnUse">
      <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="1" seed={s + 11} result="n"/>
      <feDisplacementMap in="SourceGraphic" in2="n" scale={inkScale} xChannelSelector="R" yChannelSelector="G" result="d"/>
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="1" seed={s + 17} result="g"/>
      <feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -3.6 0 0 0 3.05" result="m"/>
      <feComposite in="d" in2="m" operator="in"/>
    </filter>
  </defs>;
};

/** Grain: light specks on black, re-seeded on the boil clock (the whole sheet is "re-printed" with each re-draw). */
/** Multiplies every Grain's opacity below it (a reel can calm all its modules at once). */
export const GrainScale = createContext(1);

/**
 * Folder under public/ holding baked noise plates; null = live filters (default, today's look).
 * A plate is one noise layer alone on transparent at full strength, 3840x2160 RGBA PNG, baked and used with --scale=2 so it lands 1:1 on the 4K frame.
 * Names: grain-<seed>-<freq>, blotch-<seed>, print-band-<seed>, print-dark-<seed>, print-grain-<seed> (the seed each live filter would use).
 * Plates hold one seed, so they only fit a frozen boil: a running boil asks for seeds that were never baked and <Img> stops the render.
 */
export const BakedNoise = createContext(null);
export const useNoisePlate = () => {
  const dir = useContext(BakedNoise);
  return dir ? name => staticFile(`${dir}/${name}.png`) : null;
};
export const NoisePlate = ({src, opacity}) => <Img src={src} style={{position: "absolute", left: 0, top: 0, width: W, height: H, opacity, pointerEvents: "none"}}/>;

export const Grain = ({opacity = 0.22, freq = 0.8}) => {
  const s = useBoil() % 997 + 1;
  const plate = useNoisePlate();
  opacity *= useContext(GrainScale);
  if (opacity <= 0) return null;
  if (plate) return <NoisePlate src={plate(`grain-${s}-${freq}`)} opacity={opacity}/>;
  return <AbsoluteFill style={{pointerEvents: "none"}}>
    <svg width={W} height={H}>
      <filter id={`v3-grain-${s}`} x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency={freq} numOctaves="2" seed={s} stitchTiles="stitch"/>
        <feColorMatrix type="matrix" values="0 0 0 0 0.93  0 0 0 0 0.92  0 0 0 0 0.89  3.4 0 0 0 -1.55"/>
      </filter>
      <rect width={W} height={H} filter={`url(#v3-grain-${s})`} opacity={opacity}/>
    </svg>
  </AbsoluteFill>;
};

/** Uneven black: large soft blotches, like ink printed on rough stock. Static. */
export const Blotch = ({opacity = 0.06, seed = 4}) => {
  const plate = useNoisePlate();
  if (plate) return <NoisePlate src={plate(`blotch-${seed}`)} opacity={opacity}/>;
  return <AbsoluteFill style={{pointerEvents: "none"}}>
    <svg width={W} height={H}>
      <filter id={`v3-blotch-${seed}`} x="0" y="0" width="100%" height="100%">
        <feTurbulence type="fractalNoise" baseFrequency="0.0022" numOctaves="4" seed={seed}/>
        <feColorMatrix type="matrix" values="0 0 0 0 0.93  0 0 0 0 0.92  0 0 0 0 0.89  2.2 0 0 0 -0.9"/>
      </filter>
      <rect width={W} height={H} filter={`url(#v3-blotch-${seed})`} opacity={opacity}/>
    </svg>
  </AbsoluteFill>;
};

/** Dust & hairline scratches that jump with the boil clock. */
export const Dust = ({n = 26, color = C.ink, opacity = 0.5, seed = 9}) => {
  const b = useBoil();
  const els = [];
  for (let i = 0; i < n; i++) {
    const r = k => hash(i * 7 + k, seed, b);
    const x = r(0) * W, y = r(1) * H;
    if (r(2) < 0.12) els.push(<path key={i} d={`M${x},${y}q${(r(3) - 0.5) * 30},${r(4) * 40} ${(r(5) - 0.5) * 20},${40 + r(6) * 90}`} stroke={color} strokeWidth={0.8} fill="none" opacity={0.5}/>);
    else els.push(<circle key={i} cx={x} cy={y} r={0.6 + r(3) * 1.8} fill={color}/>);
  }
  return <g opacity={opacity}>{els}</g>;
};

/**
 * Halftone field: rotated dot grid, dot radius from field(x,y) in 0..1. Rendered as one path (fast).
 * bounds [x,y,w,h]. Use radial() / linear() helpers below for field.
 */
export const Halftone = ({bounds, field, cell = 14, angle = 0.4, color = C.verm, maxR, opacity = 1, jitter = 0, seed = 1}) => {
  const [bx, by, bw, bh] = bounds;
  const c = [bx + bw / 2, by + bh / 2];
  const R = Math.hypot(bw, bh) / 2;
  const mr = maxR ?? cell * 0.62;
  let d = "";
  for (let gy = -R; gy <= R; gy += cell) {
    for (let gx = -R; gx <= R; gx += cell) {
      const [x, y] = rotPt([c[0] + gx, c[1] + gy], c, angle);
      if (x < bx || x > bx + bw || y < by || y > by + bh) continue;
      let v = field(x, y);
      if (jitter) v *= 1 - jitter + jitter * 2 * hash(Math.round(gx), Math.round(gy), seed);
      if (v <= 0.04) continue;
      const r = mr * Math.sqrt(Math.min(1, v));
      d += `M${(x - r).toFixed(1)},${y.toFixed(1)}a${r.toFixed(2)},${r.toFixed(2)} 0 1,0 ${(2 * r).toFixed(2)},0a${r.toFixed(2)},${r.toFixed(2)} 0 1,0 ${(-2 * r).toFixed(2)},0`;
    }
  }
  return <path d={d} fill={color} opacity={opacity}/>;
};
export const radial = (cx, cy, r, power = 1.3) => (x, y) => Math.pow(Math.max(0, 1 - Math.hypot(x - cx, y - cy) / r), power);
export const linear = (x0, y0, x1, y1, power = 1) => (x, y) => {
  const dx = x1 - x0, dy = y1 - y0, L2 = dx * dx + dy * dy;
  return Math.pow(Math.max(0, Math.min(1, 1 - ((x - x0) * dx + (y - y0) * dy) / L2)), power);
};

/** Scene shell: black stage, blotch, content, grain on top. */
export const Stage = ({children, grain = 0.22, blotch = 0.07, bg = C.bg}) => <AbsoluteFill style={{background: bg, overflow: "hidden"}}>
  <Blotch opacity={blotch}/>
  {children}
  <Grain opacity={grain}/>
</AbsoluteFill>;
