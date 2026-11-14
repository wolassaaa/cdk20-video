// HKBU SCIE1007 coursework video: reusable on-camera layout kit (approved sample v2 = OnCam2Test.jsx).
// Rules: 镜头设计_v3/script/出镜新版式_v1.md. Entry 10 f, exit 8 f, graphic 3-8 f before its word, one element moving at a time.
import React from "react";
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame, delayRender, continueRender} from "remotion";
import {ramp, outCubic, vnoise} from "../core";

export const W = 1920, H = 1080, FPS = 30;
export const INK = "#111113", RED = "#E8190F", CYAN = "#0E8C9A"; // same constants as the sample
export const SERIF = "Instrument Serif";

const face = new FontFace(SERIF, `url(${staticFile("oncam2/fonts/InstrumentSerif-Regular.ttf")})`);
const fontHandle = delayRender("oncam2 kit font");
face.load().then(f => { document.fonts.add(f); continueRender(fontHandle); });

/** word time in seconds -> clip frame at 30 fps */
export const wf = s => Math.round(s * FPS);
export const enter = (f, t0, len = 10) => outCubic(ramp(f, t0, t0 + len));
export const exitK = (f, out, len = 8) => 1 - ramp(f, out - len, out);
export const edgeVol = (len, k = 2) => f => Math.min(1, (f + 1) / k, (len - f) / k);

/** Serif word that rises 26 px and fades in over 10 f (as in the sample). */
export const Word = ({x, y, size, f, t0, children, anchor = "start", color = INK, opacity = 1}) => {
  const k = enter(f, t0);
  if (k <= 0) return null;
  return <text x={x} y={y + (1 - k) * 26} fontFamily={SERIF} fontSize={size} fill={color} opacity={k * opacity} textAnchor={anchor}>{children}</text>;
};

let _ctx;
/** width of a string in Instrument Serif at size px (font is loaded before the first frame renders) */
export const textW = (s, size) => {
  _ctx = _ctx || document.createElement("canvas").getContext("2d");
  _ctx.font = `${size}px "${SERIF}"`;
  return _ctx.measureText(s).width;
};

export const Full = ({children, opacity = 1}) =>
  <svg width={W} height={H} style={{position: "absolute", inset: 0, opacity}}>{children}</svg>;

const Inner = ({render}) => render(useCurrentFrame());

/**
 * One on-camera segment from a config: {id, src, in, out, G}.
 * in / out are clip frames at 30 fps; G gets f = clip frame (same clock as the word times) and out.
 */
export const segLen = s => s.out - s.in;
export const Segment = ({seg}) => {
  const len = segLen(seg), G = seg.G;
  return <AbsoluteFill style={{background: "#EAEAE1"}}>
    <OffthreadVideo src={staticFile(seg.src)} startFrom={seg.in} volume={edgeVol(len, 3)}/>
    <Inner render={lf => <G f={lf + seg.in} out={seg.out}/>}/>
  </AbsoluteFill>;
};

/** Several segments in order, separated by black gaps (gap frames). */
export const reelLen = (segs, gap) => segs.reduce((a, s) => a + segLen(s), 0) + gap * (segs.length - 1);
export const Reel = ({segs, gap}) => {
  let t = 0;
  return <AbsoluteFill style={{background: "#000"}}>
    {segs.map(s => {
      const from = t; t += segLen(s) + gap;
      return <Sequence key={s.id} from={from} durationInFrames={segLen(s)}><Segment seg={s}/></Sequence>;
    })}
  </AbsoluteFill>;
};

// ---- wet ink edge, copied from sample v2 (OnCam2Test.jsx) ----
export const INK_OUT = 21; // 0.7 s
export const inkPoly = (edgeX, fromRight, t) => {
  const pts = [];
  for (let y = -40; y <= H + 40; y += 12) {
    const n = 70 * vnoise(y / 170, 11) + 22 * vnoise(y / 55 + t * 0.12, 23) + 5 * vnoise(y / 20, 37);
    pts.push([edgeX + (fromRight ? -n : n), y]);
  }
  const far = fromRight ? W + 400 : -400;
  return [[far, -40], ...pts, [far, H + 40]];
};
export const toD = pts => "M" + pts.map(p => p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" L") + " Z";
const InkDefs = ({id, seed}) => <defs>
  <filter id={id + "-body"} x="-10%" y="-10%" width="120%" height="120%">
    <feTurbulence type="fractalNoise" baseFrequency="0.012 0.02" numOctaves="2" seed={seed} result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="14" xChannelSelector="R" yChannelSelector="G" result="d"/>
    <feGaussianBlur in="d" stdDeviation="1.6"/>
  </filter>
  <filter id={id + "-halo"} x="-10%" y="-10%" width="120%" height="120%">
    <feTurbulence type="fractalNoise" baseFrequency="0.02 0.03" numOctaves="2" seed={seed + 3} result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="22" xChannelSelector="R" yChannelSelector="G" result="d"/>
    <feGaussianBlur in="d" stdDeviation="9"/>
  </filter>
  <filter id={id + "-grain"} x="0" y="0" width="100%" height="100%">
    <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="2" seed={seed + 7} result="n"/>
    <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.067  0 0 0 0 0.067  0 0 0 0 0.075  0 0 0 9 -5.2"/>
  </filter>
</defs>;
export const InkSheet = ({edgeX, fromRight, t, id, seed}) => {
  const lead = fromRight ? -1 : 1;
  const body = toD(inkPoly(edgeX, fromRight, t));
  const halo = toD(inkPoly(edgeX + lead * 38, fromRight, t + 2));
  const halo2 = toD(inkPoly(edgeX + lead * 20, fromRight, t + 1));
  return <svg width={W} height={H} style={{position: "absolute", inset: 0}}>
    <InkDefs id={id} seed={seed}/>
    <clipPath id={id + "-band"}><path d={halo}/></clipPath>
    <path d={halo} fill={INK} opacity={0.18} filter={`url(#${id}-halo)`}/>
    <path d={halo2} fill={INK} opacity={0.30} filter={`url(#${id}-halo)`}/>
    <g clipPath={`url(#${id}-band)`}><rect x={0} y={0} width={W} height={H} filter={`url(#${id}-grain)`} opacity={0.85}/></g>
    <path d={body} fill={INK} filter={`url(#${id}-body)`}/>
  </svg>;
};
