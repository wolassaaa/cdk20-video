// 1-03 (00:25–00:31, A ON-CAM): "Here's the thing. We already have medicines. Just not good enough ones."
// A's warm photo card at its half-screen state (left half); the options are what sits beside / around it.
import React from "react";
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from "remotion";
import {C, handLine} from "../../core";
import {InkPath, Hatch} from "../../ink";
import {InkDefs, Stage} from "../../texture";
import {Seq30 as Sequence} from "../../time30";  // CARD_DUR counts at 30 fps
import {OnCamCard} from "../../oncam/Card";
import {GM, BONE, RED, T, Tag, PrintGrain, Svg} from "./lib";

export const CARD_DUR = 180;
const Card = () => <OnCamCard who="A" src={staticFile("placeholder_hand.mp4")} videoStart={40} dur={CARD_DUR}/>;
// No BoilProvider of its own: the boil clock comes from whoever hosts the shot, so a frozen reel freezes the card edge too.
const Shell = ({children, bg}) => <Stage grain={0.16}>
  {bg && <Img src={staticFile(bg)} style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080}}/>}
  <Sequence from={0} durationInFrames={CARD_DUR}><AbsoluteFill><Card/></AbsoluteFill></Sequence>
  {children}
  <Svg><T x={960} y={1062} size={13} font={GM} anchor="middle" opacity={0.4} ls={3}>1-03 · A ON-CAM · PLACEHOLDER FOOTAGE</T></Svg>
</Stage>;

// stadium (capsule) outline as a point list, centred at (cx, cy), length L, radius r, rotated a
const stadium = (cx, cy, L, r, a = 0, n = 26) => {
  const h = L / 2 - r, pts = [];
  for (let i = 0; i <= n; i++) { const t = -Math.PI / 2 + Math.PI * i / n; pts.push([h + r * Math.cos(t), r * Math.sin(t)]); }
  for (let i = 0; i <= n; i++) { const t = Math.PI / 2 + Math.PI * i / n; pts.push([-h + r * Math.cos(t), r * Math.sin(t)]); }
  pts.push(pts[0]);
  const c = Math.cos(a), s = Math.sin(a);
  return pts.map(([x, y]) => [cx + x * c - y * s, cy + x * s + y * c]);
};
// the left part of a capsule up to fraction f of its length (for the red fill)
const stadiumPart = (cx, cy, L, r, a, f, n = 20) => {
  const h = L / 2 - r, cut = -L / 2 + L * f, pts = [[cut, -r], [-h, -r]];
  for (let i = 1; i < n; i++) { const t = -Math.PI / 2 - Math.PI * i / n; pts.push([-h + r * Math.cos(t), r * Math.sin(t)]); }
  pts.push([-h, r], [cut, r]);
  const c = Math.cos(a), s = Math.sin(a);
  return pts.map(([x, y]) => [cx + x * c - y * s, cy + x * s + y * c]);
};

// ------------------------------------------------------------------ opt1 ink capsules: two pills, a red line that stops short
export const O1Capsules = () => {
  const caps = [[1300, 450, -0.32], [1610, 560, 0.18]];
  return <Shell>
    <Svg>
      <InkDefs/>
      <g filter="url(#v3-ink)">
        {caps.map(([x, y, a], i) => <g key={i}>
          <InkPath points={stadium(x, y, 300, 62, a)} size={5} seed={10 + i} jitter={1.2} pressure="marker" color={BONE}/>
          <InkPath points={handLine(...seam(x, y, a))} size={3.5} seed={20 + i} color={BONE}/>
        </g>)}
        {/* the "enough" line: bone dashes to the mark, red ink stops at ~55% */}
        <InkPath points={handLine([1180, 720], [1480, 724], {bow: 3})} size={7} seed={31} pressure="flick" color={RED}/>
        {[0, 1, 2, 3, 4, 5].map(k => <InkPath key={k} points={handLine([1512 + k * 40, 724], [1534 + k * 40, 724])} size={3} seed={50 + k} color={BONE} opacity={0.6}/>)}
        <InkPath points={handLine([1762, 700], [1762, 748])} size={4} seed={61} color={BONE}/>
      </g>
    </Svg>
  </Shell>;
};
const seam = (x, y, a) => { const c = Math.cos(a), s = Math.sin(a); return [[x - 62 * -s, y - 62 * c], [x + 62 * -s, y + 62 * c]]; };

// ------------------------------------------------------------------ opt2 vessel: a beaker, a third full, the brim far above
export const O2Vessel = () => {
  const x0 = 1300, x1 = 1640, top = 260, bot = 860, lvl = bot - (bot - top) * 0.3;
  const body = [[x0 - 18, top - 10], [x0, top], [x0, bot - 30], [x0 + 30, bot], [x1 - 30, bot], [x1, bot - 30], [x1, top], [x1 + 14, top - 14]];
  return <Shell>
    <Svg>
      <InkDefs/>
      <g filter="url(#v3-ink)">
        <Hatch poly={[[x0 + 4, lvl], [x1 - 4, lvl], [x1 - 4, bot - 32], [x1 - 32, bot - 4], [x0 + 32, bot - 4], [x0 + 4, bot - 32]]} angle={-0.75} gap={8} size={3} color={RED} seed={7} boil={false}/>
        <InkPath points={handLine([x0 + 2, lvl], [x1 - 2, lvl - 2], {bow: 2})} size={4} seed={8} color={RED}/>
        <InkPath points={body} size={5.5} seed={9} pressure="marker" color={BONE}/>
        {[0.15, 0.3, 0.45, 0.6, 0.75].map((f, k) => <InkPath key={k} points={handLine([x0, bot - (bot - top) * f], [x0 + (k % 2 ? 26 : 46), bot - (bot - top) * f])} size={3} seed={70 + k} color={BONE} opacity={0.8}/>)}
      </g>
    </Svg>
  </Shell>;
};

// ------------------------------------------------------------------ opt3 capsule 3D: Blender glass capsule, partly filled
export const O3Capsule3D = () => <Shell>
  <Img src={staticFile("capsule.png")} style={{position: "absolute", left: 960, top: 150, width: 960, height: 720}}/>
  <Svg><Tag x={1840} y={1036}>ILLUSTRATIVE</Tag></Svg>
</Shell>;

// ------------------------------------------------------------------ opt4 words: the line set in type, the underline runs out
export const O4Words = () => <Shell>
  <Svg>
    <InkDefs/>
    <T x={1040} y={470} size={64} weight={200}>We already have medicines.</T>
    <T x={1040} y={590} size={64} weight={200} opacity={0.55}>Just not good enough ones.</T>
    <g filter="url(#v3-ink)">
      <InkPath points={handLine([1040, 622], [1330, 626], {bow: 2})} size={7} seed={3} pressure="flick" color={RED}/>
    </g>
    <rect x={1040} y={626} width={760} height={1} fill={BONE} opacity={0.25}/>
  </Svg>
</Shell>;

// ------------------------------------------------------------------ opt2b beaker 3D: Blender lab beaker, a third full
export const O2Beaker3D = () => <Shell>
  <Img src={staticFile("beaker.png")} style={{position: "absolute", left: 1000, top: 90, width: 900, height: 900}}/>
  <Svg><Tag x={1840} y={1036}>ILLUSTRATIVE</Tag></Svg>
</Shell>;

// ------------------------------------------------------------------ v2 vitrine: the object lit like a museum piece in the same dark room as the card
// Blender renders the whole 1920x1080 room (glossy black plinth, one pool of light, cobalt rim, shallow focus); the card sits over the left half.
export const OVitrine = ({obj = "beaker"}) => <Shell bg={`vitrine_${obj}.png`}>
  <Svg><Tag x={1840} y={1036}>ILLUSTRATIVE</Tag></Svg>
</Shell>;
