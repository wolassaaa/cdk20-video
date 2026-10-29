// S1 v2 / 1-08 + 1-09 shared bits: fonts, palette, station data, print surface.
import React from "react";
import {AbsoluteFill, Img, staticFile} from "remotion";
import {loadFont as loadGrot} from "@remotion/google-fonts/InterTight";
import {C, MONO, W, H, BoilProvider} from "../../core";
import {Grain, Blotch} from "../../texture";

export const GROT = loadGrot("normal", {weights: ["400", "600", "800", "900"], subsets: ["latin"]}).fontFamily;
export {MONO, C, W, H};
export const NB = String.fromCharCode(160);
export const P = {bg: "#060606", ink: "#EDEBE4", red: "#FF1A2E", blue: "#1F3BFF", deep: "#0A1AFF", klein: "#002FA7", grey: "#3a3a38", dim: "rgba(237,235,228,0.22)"};

// the six stations (names follow script_v3.3 1-09 visual note)
export const ST = [
  {n: "01", name: "TARGET", short: "TARGET"},
  {n: "02", name: "HIT", short: "HIT", sub: "a first molecule that works on it"},
  {n: "03", name: "IMPROVE", short: "IMPROVE"},
  {n: "04", name: "CELLS & ANIMALS", short: "CELLS &\nANIMALS", sub: "cells, then animals"},
  {n: "05", name: "HUMAN TRIALS", short: "HUMAN\nTRIALS", sub: "phase I · II · III"},
  {n: "06", name: "APPROVAL", short: "APPROVAL"},
];
// illustrative survivors entering each station
export const COUNT = [34, 17, 9, 5, 2, 1];

/** print surface: blotchy black, content, grain, faint horizontal banding (screen-print feel) */
export const Print = ({children, bg = P.bg, grain = 0.2, band = 0.05, blotch = 0.06}) => <BoilProvider frozen>
  <AbsoluteFill style={{background: bg, overflow: "hidden"}}>
    <Blotch opacity={blotch}/>
    {children}
    <AbsoluteFill style={{pointerEvents: "none", opacity: band, background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.9) 0px, rgba(0,0,0,0.9) 1px, transparent 1px, transparent 4px)"}}/>
    <Grain opacity={grain}/>
  </AbsoluteFill>
</BoilProvider>;

export const Plate = ({src}) => <AbsoluteFill><Img src={staticFile(src)} style={{width: W, height: H}}/></AbsoluteFill>;

export const Tag = ({x = W - 64, y = H - 52, children = "ILLUSTRATIVE", color = P.ink, anchor = "end"}) =>
  <text x={x} y={y} fontFamily={MONO} fontSize={15} fontWeight={700} letterSpacing={3} fill={color} opacity={0.6} textAnchor={anchor}>{children}</text>;

export const Svg = ({children, style}) => <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", inset: 0, ...style}}>{children}</svg>;

/** multi-line grotesk text */
export const GText = ({x, y, size = 34, weight = 800, color = P.ink, anchor = "start", lh = 1.0, ls = -0.5, opacity = 1, children}) => {
  const lines = typeof children === "string" ? children.split("\n") : [children];
  return <text x={x} y={y} fontFamily={GROT} fontSize={size} fontWeight={weight} fill={color} textAnchor={anchor} letterSpacing={ls} opacity={opacity}>
    {lines.map((l, i) => <tspan key={i} x={x} dy={i ? size * lh : 0}>{l}</tspan>)}
  </text>;
};
export const MText = ({x, y, size = 16, weight = 700, color = P.ink, anchor = "start", ls = 2, opacity = 1, children}) =>
  <text x={x} y={y} fontFamily={MONO} fontSize={size} fontWeight={weight} fill={color} textAnchor={anchor} letterSpacing={ls} opacity={opacity}
    style={{fontVariantNumeric: "tabular-nums"}}>{children}</text>;
