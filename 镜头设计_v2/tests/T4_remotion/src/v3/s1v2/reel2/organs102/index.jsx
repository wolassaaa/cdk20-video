// 1-02 v2 (00:08–00:25, A voice-over): glass organs on one black plinth.
// One continuous Cycles camera move (organs102/organs102.mp4, 510 frames, rendered by
// 镜头设计_v3/styleframes/S1/v2/_code/reel2/organs102/organs.py): close on the glass liver -> pull back, glass lung and
// glass colon materialise either side (HK top 3) -> pull back again, oesophagus / stomach / prostate join, the other reds
// drain to clear glass and only the liver stays red (world 6th / 3rd). Organ labels follow the 3D anchors in labels.json.
import React from "react";
import {AbsoluteFill, OffthreadVideo, staticFile, interpolate} from "remotion";
import {C, W, H, ramp, inOut} from "../../../core";
import {Grain} from "../../../texture";
import {useFrame30, Hold30} from "../../../time30";
import {T, Src, GM, SRC_HK, SRC_WORLD} from "../../s102/lib";
import LAB from "./labels.json";  // copied from the Blender run (projected label anchors per frame)

export const DUR_102 = 510;
const RED = C.verm;
const SRC_HK23 = "SOURCE  Hong Kong Cancer Registry, Hospital Authority";

// local frame windows (beat starts at 00:08): line 1 "1,412" 0–5 s, line 2 "top 3" 5–10.7 s, line 3 "world" 10.7–17 s
const A1 = 150, B0 = 172, B1 = 322, C0 = 352;
const fadeWin = (f, a, b, k = 14) => Math.min(ramp(f, a, a + k), 1 - ramp(f, b - k, b));

const ORGANS = [
  ["oesophagus", "OESOPHAGUS", 2], ["stomach", "STOMACH", 2], ["lung", "LUNG", 1],
  ["liver", "LIVER", 0], ["colon", "COLORECTAL", 1], ["prostate", "PROSTATE", 2],
];

const Labels = ({f}) => {
  const i = Math.min(Math.floor(f), LAB.organs.liver.base.length - 1);
  return <g>{ORGANS.map(([k, name, tier], n) => {
    const x = LAB.organs[k].base[i][0], y = LAB.organs.liver.base[i][1] + 30;  // one label line just under the liver (front-most) base
    // tier 0/1: from the "Top 3" line on; tier 2: from the world line on (staggered left to right)
    const on = tier < 2 ? fadeWin(f, B0 + 10 + 6 * n, 9999, 16) : ramp(f, C0 + 10 + 5 * n, C0 + 26 + 5 * n);
    if (on <= 0 || x < -200 || x > W + 200) return null;
    const hero = k === "liver";
    return <g key={k} opacity={on}>
      <line x1={x} x2={x} y1={y - 14} y2={y - 2} stroke={hero ? RED : C.ink} strokeWidth={1.2} opacity={hero ? 1 : 0.55}/>
      <T x={x} y={y + 20} size={15} weight={hero ? 500 : 400} font={GM} anchor="middle" ls={3}
        color={hero ? RED : C.ink} opacity={hero ? 1 : 0.7}>{name}</T>
    </g>;
  })}</g>;
};

const Spot = ({f, on}) => {
  const i = Math.min(Math.floor(f), LAB.organs.liver.base.length - 1);
  const [x, y] = LAB.organs.liver.base[i];
  return <AbsoluteFill style={{opacity: on * 0.85, background:
    `radial-gradient(ellipse 760px 620px at ${x}px ${y - 190}px, rgba(0,0,0,0) 35%, rgba(0,0,0,0.5) 100%)`}}/>;
};

export const Beat102 = () => {
  const f = useFrame30();
  const a = 1 - ramp(f, A1 - 14, A1 + 2);
  const b = fadeWin(f, B0, B1, 16);
  const c = ramp(f, C0, C0 + 16);
  const credA = 1 - ramp(f, 140, 170), credB = ramp(f, 180, 210);
  return <AbsoluteFill style={{background: "#000", overflow: "hidden"}}>
    <Hold30><OffthreadVideo src={staticFile("organs102/organs102.mp4")} style={{width: W, height: H}} muted/></Hold30>
    {/* left shade only while the type sits beside the close liver */}
    <AbsoluteFill style={{opacity: a, background: "linear-gradient(90deg, rgba(6,6,6,0.85) 0%, rgba(6,6,6,0.45) 27%, rgba(6,6,6,0) 42%)"}}/>
    <AbsoluteFill style={{background: "linear-gradient(0deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 9%)"}}/>
    {/* top-3 line: a soft pool of light on the liver so it stays the hero beside the red lung and colon */}
    <Spot f={f} on={fadeWin(f, B0 - 10, C0 + 20, 30)}/>
    <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
      {/* 1 · 1,412 (as v1) */}
      <g opacity={a}>
        <T x={92} y={560} size={250} weight={100} ls={-10}>1,412</T>
        <T x={104} y={630} size={42} weight={300}>deaths in Hong Kong, 2022</T>
        <rect x={106} y={662} width={64 * inOut(ramp(f, 10, 40))} height={3} fill={RED}/>
        <Src>{SRC_HK}</Src>
      </g>
      {/* 2 · top 3 in Hong Kong: one editorial line above the three vitrines */}
      <g opacity={b}>
        <T x={104} y={118} size={22} weight={400} font={GM} ls={5} opacity={0.7}>HONG KONG</T>
        <T x={92} y={262} size={150} weight={100} ls={-6}>Top 3</T>
        <T x={470} y={262} size={44} weight={300}>deadliest cancers</T>
        <Src>{SRC_HK23}</Src>
      </g>
      {/* 3 · world */}
      <g opacity={c}>
        <T x={104} y={118} size={22} weight={400} font={GM} ls={5} opacity={0.7}>WORLD</T>
        <T x={92} y={262} size={150} weight={100} ls={-6}>6<tspan fontSize={64} dy={-66}>th</tspan></T>
        <T x={262} y={262} size={44} weight={300}>most common</T>
        <T x={92} y={420} size={150} weight={100} ls={-6} color={RED}>3<tspan fontSize={64} dy={-66}>rd</tspan></T>
        <T x={262} y={420} size={44} weight={300}>deadliest</T>
        <Src>{SRC_WORLD}</Src>
      </g>
      <Labels f={f}/>
      <g opacity={credA}><T x={1840} y={1036} size={13} weight={400} font={GM} anchor="end" opacity={0.5} ls={1}>BODYPARTS3D © DBCLS, CC BY 4.0 · RED PORTAL VEIN · BLUE HEPATIC VEINS</T></g>
      <g opacity={credB}><T x={1840} y={1036} size={13} weight={400} font={GM} anchor="end" opacity={0.5} ls={1}>BODYPARTS3D © DBCLS, CC BY 4.0 · TRUE RELATIVE SCALE</T></g>
    </svg>
    <Grain opacity={0.14}/>
  </AbsoluteFill>;
};
