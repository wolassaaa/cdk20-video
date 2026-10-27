import React from "react";
import {AbsoluteFill} from "remotion";
import {loadFont as loadMono} from "@remotion/google-fonts/JetBrainsMono";
import {loadFont as loadAnton} from "@remotion/google-fonts/Anton";
import {loadFont as loadSerif} from "@remotion/google-fonts/Fraunces";
import {loadFont as loadHand} from "@remotion/google-fonts/Caveat";
import plan from "../mv/mv2_plan.json";
import rhythm from "../mv/mv2_rhythm.json";

// Shared pieces for the v2 'Carbon vs Silicon' cut: themes, easing, the music clock (bars, beats, hit layers).
export {plan, rhythm};
export const FPS = plan.fps;
export const MONO = loadMono().fontFamily, ANTON = loadAnton().fontFamily, SERIF = loadSerif().fontFamily, HAND = loadHand().fontFamily;

// silicon: the computer's world. carbon: the body and the lab. mix: where the two meet.
export const SI = {bg: "#02060B", ink: "#EEF4F8", accent: "#7FE3FA", hot: "#FF8A4C", quiet: "#6F8796", line: "rgba(127,227,250,0.16)"};
export const C = {bg: "#130A07", ink: "#F6E8D6", amber: "#FFB04A", magenta: "#FF5C8A", quiet: "#A88A74", paper: "#1E120C"};

export const clamp01 = x => Math.min(1, Math.max(0, x));
export const outCubic = x => 1 - Math.pow(1 - clamp01(x), 3);
export const inOut = x => { x = clamp01(x); return x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
export const outBack = x => { x = clamp01(x); const c = 1.7; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
export const lerp = (a, b, x) => a + (b - a) * x;
export const hash = (a, b = 0) => { let h = Math.imul(a ^ 0x9e3779b9, 0x85ebca6b) ^ Math.imul(b + 0x7f4a7c15, 0xc2b2ae35); h ^= h >>> 15; h = Math.imul(h, 0x2c1b3c6d); h ^= h >>> 12; return (h >>> 0) / 4294967296; };

// number of sorted values <= t
export const countBefore = (arr, t) => { let lo = 0, hi = arr.length; while (lo < hi) { const m = (lo + hi) >> 1; if (arr[m] <= t) lo = m + 1; else hi = m; } return lo; };
export const lastBefore = (arr, t) => { const n = countBefore(arr, t); return n ? arr[n - 1] : null; };
// n-th downbeat / beat at or after t0
export const nthDown = (t0, n) => { const i = countBefore(plan.downbeats, t0 - 0.03); return plan.downbeats[Math.min(plan.downbeats.length - 1, i + n)] ?? t0; };
export const nthBeat = (t0, n) => { const i = countBefore(plan.beats, t0 - 0.03); return plan.beats[Math.min(plan.beats.length - 1, i + n)] ?? t0; };

// hit layers: times (optionally only hits above a strength), and the decaying envelope at a frame
const HITS = {};
export const hits = (layer, minS = 0) => (HITS[layer + minS] ??= rhythm.layers[layer].filter(h => h.s >= minS).map(h => h.t));
export const env = (layer, f) => { const e = rhythm.env[layer]; return e[Math.min(e.length - 1, Math.max(0, f))]; };
// eased step counter: how many hits since t0, with the latest one still easing in (for snap moves)
export const stepper = (times, t0, t, dur = 0.09) => {
  const n = countBefore(times, t) - countBefore(times, t0);
  if (n <= 0) return 0;
  return n - 1 + outCubic((t - times[countBefore(times, t) - 1]) / dur);
};

// element tiles, top right: which world a shot belongs to (Si 14 / C 6)
const Tile = ({sym, num, name, color, on}) => (
  <div style={{width: 74, height: 84, border: `2px solid ${color}`, borderRadius: 6, padding: "6px 8px", opacity: on ? 1 : 0.22,
    fontFamily: MONO, color, background: on ? "rgba(0,0,0,0.35)" : "transparent"}}>
    <div style={{fontSize: 13}}>{num}</div>
    <div style={{fontSize: 34, fontWeight: 700, lineHeight: 1}}>{sym}</div>
    <div style={{fontSize: 11, marginTop: 4}}>{name}</div>
  </div>
);
export const WorldTiles = ({world}) => (
  <div style={{position: "absolute", right: 48, bottom: 44, display: "flex", gap: 10}}>
    <Tile sym="C" num={6} name="carbon" color={C.amber} on={world !== "si"}/>
    <Tile sym="Si" num={14} name="silicon" color={SI.accent} on={world !== "c"}/>
  </div>
);

// silicon backdrop: dark, faint grid, scanlines; a short digital glitch on entry
export const SiBack = ({f, local, children, grid = true}) => {
  const k = env("kick", f);
  const g = local < 0.14 ? 1 - local / 0.14 : 0;
  const bands = g > 0 ? Array.from({length: 6}, (_, i) => ({y: hash(i, Math.floor(local * 60)) * 1080, h: 8 + hash(i, 3) * 40,
    c: i % 2 ? "rgba(255,60,120,0.35)" : "rgba(127,227,250,0.35)"})) : [];
  return <AbsoluteFill style={{background: SI.bg, overflow: "hidden"}}>
    {grid ? <AbsoluteFill style={{backgroundImage: `linear-gradient(${SI.line} 1px, transparent 1px), linear-gradient(90deg, ${SI.line} 1px, transparent 1px)`,
      backgroundSize: "80px 80px", opacity: 0.35 + 0.35 * k}}/> : null}
    <AbsoluteFill style={{transform: g ? `translateX(${(hash(7, Math.floor(local * 60)) - 0.5) * 60 * g}px)` : undefined}}>{children}</AbsoluteFill>
    <AbsoluteFill style={{backgroundImage: "repeating-linear-gradient(0deg, rgba(0,0,0,0.22) 0 1px, transparent 1px 3px)", pointerEvents: "none"}}/>
    {bands.map((b, i) => <div key={i} style={{position: "absolute", left: 0, right: 0, top: b.y, height: b.h, background: b.c, mixBlendMode: "screen"}}/>)}
    <AbsoluteFill style={{background: "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.6))"}}/>
  </AbsoluteFill>;
};

// carbon backdrop: warm dark, living film grain, a warm light leak on entry
export const CBack = ({f, local, children}) => {
  const leak = Math.exp(-local * 5);
  return <AbsoluteFill style={{background: C.bg, overflow: "hidden"}}>
    <AbsoluteFill style={{background: `radial-gradient(ellipse at 30% 40%, rgba(255,140,60,0.10), transparent 60%)`}}/>
    {children}
    <svg width="1920" height="1080" style={{position: "absolute", inset: 0, opacity: 0.10, mixBlendMode: "overlay", pointerEvents: "none"}}>
      <filter id={"grain" + f}><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed={f % 97}/></filter>
      <rect width="1920" height="1080" filter={`url(#grain${f})`}/>
    </svg>
    <AbsoluteFill style={{background: `radial-gradient(circle at 15% 20%, rgba(255,170,80,${0.55 * leak}), transparent 55%)`, mixBlendMode: "screen"}}/>
    <AbsoluteFill style={{background: "radial-gradient(ellipse at center, transparent 50%, rgba(10,4,2,0.7))"}}/>
  </AbsoluteFill>;
};

// boiling hand-drawn line: re-seeded every few frames like redrawn animation
export const Boil = ({id, f, scale = 3.5}) => (
  <filter id={id} filterUnits="userSpaceOnUse" x="0" y="0" width="1920" height="1080"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed={Math.floor(f / 4) % 50}/>
    <feDisplacementMap in="SourceGraphic" scale={scale}/></filter>
);

// text lines that land on successive beats from the scene start. silicon types, carbon fades in like ink
export const SiLines = ({lines, t, at, x = 96, y = 150, size = 54}) => (
  <div style={{position: "absolute", left: x, top: y, fontFamily: MONO, maxWidth: 1300}}>
    {lines.map((line, i) => {
      const a = nthBeat(at, i * 2), n = Math.floor(clamp01((t - a) / Math.max(0.2, line.length * 0.022)) * line.length);
      if (t < a) return null;
      return <div key={i} style={{fontSize: i ? size * 0.74 : size, fontWeight: i ? 500 : 700, color: i ? SI.ink : SI.accent, lineHeight: 1.3,
        textShadow: "0 2px 18px rgba(0,0,0,0.9)", whiteSpace: "pre"}}>{line.slice(0, n)}{n < line.length ? "▋" : ""}</div>;
    })}
  </div>
);
export const CLines = ({lines, t, at, x = 110, y = 140, size = 68}) => (
  <div style={{position: "absolute", left: x, top: y, fontFamily: SERIF, maxWidth: 1300}}>
    {lines.map((line, i) => {
      const a = nthBeat(at, i * 2), p = outCubic((t - a) / 0.5);
      return <div key={i} style={{fontSize: i ? size * 0.78 : size, fontStyle: i ? "italic" : "normal", fontWeight: i ? 400 : 600, color: i ? C.ink : C.amber,
        lineHeight: 1.25, opacity: p, filter: `blur(${(1 - p) * 8}px)`, transform: `translateY(${(1 - p) * 16}px)`, textShadow: "0 2px 24px rgba(0,0,0,0.85)"}}>{line}</div>;
    })}
  </div>
);
