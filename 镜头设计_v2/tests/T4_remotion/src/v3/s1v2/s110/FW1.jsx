// W1 title-card options. Title text exactly as the script: "WORTH TESTING?" / SUB.
import React from "react";
import {AbsoluteFill} from "remotion";
import {Plate, T, Tag, Credit, Finish, RoadFaint, Members, K, GROT, SERIF, MONO, TITLE, SUB, COURSE, MEMBERS, STATIONS, AF_CREDIT, W, H} from "./lib";

// 1. fogged glass, title wiped by a finger (Blender); subtitle crisp below
export const W1Fog = () => <AbsoluteFill style={{background: K.bg}}>
  <Plate src="w_fog.png"/>
  <RoadFaint y={986} color="rgba(237,235,228,0.16)" label={false}/>
  <div style={{position: "absolute", left: 0, top: 900, width: W, textAlign: "center", fontFamily: GROT, fontSize: 30, fontWeight: 400, color: K.ink, letterSpacing: 0.3}}>{SUB}</div>
  <T x={96} y={1030} size={12} ls={2.5} color={K.dim}>{COURSE}</T>
  <Members x={1824} y={1030} size={12} anchor="right"/>
  <Finish grain={0.14} vignette={0.35}/>
</AbsoluteFill>;

// 2. Swiss / International: huge grotesk, flush left, hairline grid, faint road map
export const W1Swiss = () => <AbsoluteFill style={{background: K.bg}}>
  <svg width={W} height={H} style={{position: "absolute"}}>
    {[96, 576, 1056, 1536].map(x => <line key={x} x1={x} y1={0} x2={x} y2={H} stroke="rgba(237,235,228,0.07)"/>)}
    <line x1={0} y1={96} x2={W} y2={96} stroke="rgba(237,235,228,0.07)"/>
  </svg>
  <RoadFaint y={760} x0={576} x1={1776} color="rgba(237,235,228,0.2)"/>
  <div style={{position: "absolute", left: 82, top: 110, fontFamily: GROT, fontWeight: 900, fontSize: 300, lineHeight: 0.82, letterSpacing: -14, color: K.ink}}>
    WORTH<br/>TESTING<span style={{color: K.verm}}>?</span>
  </div>
  <T x={96} y={850} size={34} font={GROT} weight={400} ls={-0.5} w={980} style={{whiteSpace: "normal", lineHeight: 1.2}}>{SUB}</T>
  <T x={1056} y={850} size={13} ls={2.5} color={K.dim}>{COURSE}</T>
  {MEMBERS.map((m, i) => <T key={i} x={1056 + (i % 2) * 240} y={890 + Math.floor(i / 2) * 26} size={13} ls={2.5}>{m}</T>)}
  <T x={1536} y={110} size={13} ls={2.5} color={K.dim}>01 / 08</T>
  <Finish grain={0.16} vignette={0}/>
</AbsoluteFill>;

// 3. Contemporary-art catalogue cover: small mono type, lots of black, one small plate
export const W1Catalogue = () => <AbsoluteFill style={{background: "#050505"}}>
  <div style={{position: "absolute", left: 836, top: 380, width: 248, height: 140, overflow: "hidden", outline: "1px solid rgba(237,235,228,0.15)"}}>
    <img src={require("remotion").staticFile("p_xray.png")} style={{width: 248, height: 140, objectFit: "cover", transform: "scale(1.35)"}}/>
  </div>
  <T x={836} y={538} size={10} ls={1.5} color={K.dim}>pl. 1 · CDK20, predicted (AlphaFold DB)</T>
  <T x={96} y={96} size={15} ls={4} weight={700}>{TITLE}</T>
  <T x={96} y={122} size={13} ls={1} color={K.dim} w={520} style={{whiteSpace: "normal"}}>{SUB}</T>
  <T x={1824} y={96} size={13} ls={2.5} anchor="right" color={K.dim}>{COURSE}</T>
  {MEMBERS.map((m, i) => <T key={i} x={96} y={890 + i * 22} size={12} ls={2.5}>{m}</T>)}
  <RoadFaint y={1000} x0={760} x1={1760} color="rgba(237,235,228,0.14)" label={false}/>
  <T x={1824} y={1030} size={11} ls={2} anchor="right" color={K.dim}>HONG KONG · 2026</T>
  <Finish grain={0.12} vignette={0}/>
</AbsoluteFill>;

// 4. Klein blue field, red type (Blender pigment plate)
export const W1Klein = () => <AbsoluteFill style={{background: K.klein}}>
  <Plate src="w_pigment.png"/>
  <RoadFaint y={800} color="rgba(237,235,228,0.22)"/>
  <div style={{position: "absolute", left: 0, top: 290, width: W, textAlign: "center", fontFamily: GROT, fontWeight: 900, fontSize: 236, letterSpacing: -9, color: K.verm, lineHeight: 1}}>{TITLE}</div>
  <div style={{position: "absolute", left: 0, top: 560, width: W, textAlign: "center", fontFamily: SERIF, fontSize: 44, color: K.ink}}>{SUB}</div>
  <div style={{position: "absolute", left: 0, top: 960, width: W, textAlign: "center", fontFamily: MONO, fontSize: 13, letterSpacing: 3, color: K.ink}}>{COURSE}   ·   {MEMBERS.join("  ·  ")}</div>
  <Finish grain={0.18} vignette={0.25}/>
</AbsoluteFill>;

// 5. title through a glass protein (Blender: 3D type behind the glass CDK20 model)
export const W1Glass = () => <AbsoluteFill style={{background: K.bg}}>
  <Plate src="w_titleglass.png"/>
  <div style={{position: "absolute", left: 0, top: 930, width: W, textAlign: "center", fontFamily: GROT, fontSize: 28, color: K.ink}}>{SUB}</div>
  <T x={96} y={1030} size={12} ls={2.5} color={K.dim}>{COURSE}</T>
  <Members x={1824} y={1030} size={12} anchor="right"/>
  <Finish grain={0.15} vignette={0.35}/>
</AbsoluteFill>;

// 6. ink splash -> rain (Blender metaballs): a = the splash frame, b = drips running into rain
export const W1Ink = ({part = "a"}) => <AbsoluteFill style={{background: K.bg}}>
  <Plate src={part === "a" ? "w_splash.png" : "w_rain.png"}/>
  <RoadFaint y={960} color="rgba(237,235,228,0.14)" label={false}/>
  <T x={96} y={860} size={30} font={GROT} color={K.ink}>{SUB}</T>
  <T x={96} y={1030} size={12} ls={2.5} color={K.dim}>{COURSE}</T>
  <Members x={1824} y={1030} size={12} anchor="right"/>
  <Finish grain={0.18} vignette={0.3}/>
</AbsoluteFill>;

export const OPTIONS_W1 = [
  {id: "SW1o1", C: W1Fog}, {id: "SW1o2", C: W1Swiss}, {id: "SW1o3", C: W1Catalogue}, {id: "SW1o4", C: W1Klein}, {id: "SW1o5", C: W1Glass},
  {id: "SW1o6a", C: W1Ink, p: {part: "a"}}, {id: "SW1o6b", C: W1Ink, p: {part: "b"}},
];
