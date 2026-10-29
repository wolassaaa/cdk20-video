// s104 shared: grotesk type, print texture (grain, banding, misregistration), tags. Palette per S1 brief v2.
import React from "react";
import {AbsoluteFill} from "remotion";
import {loadFont as loadGrot} from "@remotion/google-fonts/InterTight";
import {loadFont as loadSerif} from "@remotion/google-fonts/InstrumentSerif";
import {C, MONO, W, H, useBoil} from "../../core";

export const GROT = loadGrot("normal", {weights: ["200", "300", "500", "700", "800"], subsets: ["latin"]}).fontFamily;
export const SERIF = loadSerif("italic", {weights: ["400"], subsets: ["latin"]}).fontFamily;
export const K = {
  bg: C.bg, ink: C.ink, verm: "#F5142B", // crimson-biased red for s104 (10-31 red pass: director banned orange; #FF3B1F read warm)
  dim: "rgba(237,235,228,0.5)", faint: "rgba(237,235,228,0.18)",
  klein: "#002FA7", blue: "#1F3BFF", blue2: "#0A1AFF",
};

export const T = ({x, y, size = 40, w = 400, color = K.ink, font = GROT, anchor = "start", ls = 0, children, op = 1, style, ...r}) =>
  <text x={x} y={y} fontFamily={font} fontSize={size} fontWeight={w} fill={color} textAnchor={anchor} letterSpacing={ls} opacity={op}
    style={{fontVariantNumeric: "tabular-nums", ...style}} {...r}>{children}</text>;
export const M = ({size = 18, ls = 2, w = 400, ...p}) => <T font={MONO} size={size} ls={ls} w={w} {...p}/>;

/** small corner tags: ILLUSTRATIVE + source line + beat id */
export const Tags = ({illustrative = true, source, beat = "1-04", opt, color = K.dim}) => <g>
  {illustrative ? <M x={W - 64} y={64} size={13} anchor="end" color={color} ls={3}>ILLUSTRATIVE</M> : null}
  {source ? <M x={64} y={H - 44} size={12} color={color} ls={1.5}>{source}</M> : null}
  <M x={W - 64} y={H - 44} size={12} anchor="end" color="rgba(237,235,228,0.3)" ls={2}>{`${beat}${opt ? " · " + opt : ""}`}</M>
</g>;

/** Print finish on top of everything: horizontal ink banding, dark + light grain, soft vignette. */
export const Print = ({grain = 0.32, band = 0.1, dark = 0.35, vignette = 0.5, seed = 0}) => {
  const s = (useBoil() % 997) + 1 + seed;
  return <AbsoluteFill style={{pointerEvents: "none"}}>
    <svg width={W} height={H} style={{position: "absolute"}}>
      <defs>
        <filter id={`pb-${s}`} x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.0009 0.09" numOctaves="2" seed={s + 5}/>
          <feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  2.4 0 0 0 -1.0"/>
        </filter>
        <filter id={`pg-${s}`} x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed={s + 9} stitchTiles="stitch"/>
          <feColorMatrix type="matrix" values="0 0 0 0 0.93  0 0 0 0 0.92  0 0 0 0 0.89  3.6 0 0 0 -1.7"/>
        </filter>
        <filter id={`pd-${s}`} x="0" y="0" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.62" numOctaves="2" seed={s + 21} stitchTiles="stitch"/>
          <feColorMatrix type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -3.4 0 0 0 1.75"/>
        </filter>
        <radialGradient id="pv" cx="50%" cy="50%" r="75%">
          <stop offset="0.55" stopColor="#000" stopOpacity="0"/>
          <stop offset="1" stopColor="#000" stopOpacity="1"/>
        </radialGradient>
      </defs>
      <rect width={W} height={H} filter={`url(#pb-${s})`} opacity={band}/>
      <rect width={W} height={H} filter={`url(#pd-${s})`} opacity={dark}/>
      <rect width={W} height={H} filter={`url(#pg-${s})`} opacity={grain}/>
      <rect width={W} height={H} fill="url(#pv)" opacity={vignette}/>
    </svg>
  </AbsoluteFill>;
};

/** Ragged-edge filter for big flat colour fields (screen-printed ink: edge crawl + pinholes). */
export const FieldDefs = ({id = "field", seed = 3, scale = 7}) => <defs>
  <filter id={id} x="-2%" y="-2%" width="104%" height="104%">
    <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="3" seed={seed} result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale={scale} xChannelSelector="R" yChannelSelector="G" result="d"/>
    <feTurbulence type="fractalNoise" baseFrequency="0.75" numOctaves="2" seed={seed + 4} result="g"/>
    <feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -4.2 0 0 0 3.35" result="m"/>
    <feComposite in="d" in2="m" operator="in"/>
  </filter>
</defs>;
