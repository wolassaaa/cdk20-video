// s102 shared bits: type (Geist grotesk + Geist Mono), source lines, tags, print grain.
import React from "react";
import {AbsoluteFill} from "remotion";
import {loadFont as loadGeist} from "@remotion/google-fonts/Geist";
import {loadFont as loadGeistMono} from "@remotion/google-fonts/GeistMono";
import {C, W, H} from "../../core";

export const SANS = loadGeist("normal", {weights: ["100", "200", "300", "400", "500"], subsets: ["latin"]}).fontFamily;
export const GM = loadGeistMono("normal", {weights: ["300", "400", "500"], subsets: ["latin"]}).fontFamily;

export const BLUE = "#1F3BFF", IKB = "#002FA7", BONE = C.ink, RED = C.verm, BG = C.bg;

// sources (wording per script_v3.3 1-02)
export const SRC_HK = "SOURCE  Hong Kong Cancer Registry, Hospital Authority: Liver Cancer in 2022 (Oct 2024)";
export const SRC_WORLD = "SOURCE  GLOBOCAN 2020, via Ren et al., Chem. Sci. 2023";

export const T = ({x, y, size = 40, weight = 300, color = BONE, anchor = "start", ls = 0, font = SANS, opacity = 1, children, style}) =>
  <text x={x} y={y} fontFamily={font} fontSize={size} fontWeight={weight} fill={color} textAnchor={anchor} letterSpacing={ls}
    opacity={opacity} style={{fontVariantNumeric: "tabular-nums", fontFeatureSettings: '"tnum","ss01"', ...style}}>{children}</text>;

export const Src = ({x = 80, y = 1036, children, color = BONE, anchor = "start"}) =>
  <T x={x} y={y} size={15} weight={400} font={GM} color={color} opacity={0.62} ls={0.6} anchor={anchor}>{children}</T>;

export const Tag = ({x = 1840, y = 1036, children = "ILLUSTRATIVE", color = BONE}) =>
  <T x={x} y={y} size={14} weight={500} font={GM} color={color} opacity={0.6} ls={2.5} anchor="end">{children}</T>;

/** Print grain: fine monochrome noise, multiplied+screened so blacks get lifted specks and colour fields get tooth. */
export const PrintGrain = ({id = "pg", amount = 0.22, freq = 0.9, seed = 3}) => <AbsoluteFill style={{pointerEvents: "none"}}>
  <svg width={W} height={H}>
    <filter id={id} x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency={freq} numOctaves="2" seed={seed} stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
      <feComponentTransfer><feFuncA type="linear" slope="0" intercept="1"/></feComponentTransfer>
    </filter>
    <rect width={W} height={H} filter={`url(#${id})`} opacity={amount} style={{mixBlendMode: "overlay"}}/>
  </svg>
</AbsoluteFill>;

export const Vignette = ({k = 0.55}) => <AbsoluteFill style={{pointerEvents: "none",
  background: `radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 50%, rgba(0,0,0,${k}) 100%)`}}/>;

export const Svg = ({children, style}) => <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0, ...style}}>{children}</svg>;
