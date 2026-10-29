// 1-10 options: the real AlphaFold CDK20 model (Blender plates) + type.
import React from "react";
import {AbsoluteFill} from "remotion";
import {Plate, T, Tag, Credit, Finish, K, GROT, SERIF, MONO, AF_CREDIT, W, H} from "./lib";

const Nobel = ({x, y, size = 30, color = K.ink, anchor = "left"}) => <>
  <T x={x} y={y} size={size} font={SERIF} color={color} ls={size * 0.18} anchor={anchor}>NOBEL PRIZE IN CHEMISTRY 2024</T>
</>;
const Names = ({x, y, size = 22, color = K.dim, anchor = "left"}) =>
  <T x={x} y={y} size={size} font={SERIF} color={color} anchor={anchor} style={{fontStyle: "italic"}}>Demis Hassabis &amp; John Jumper, for AlphaFold</T>;

// 1. glass on a light slit (Turrell / Eliasson)
export const O1Glass = () => <AbsoluteFill style={{background: K.bg}}>
  <Plate src="p_glass.png"/>
  <Nobel x={96} y={880} size={30}/>
  <div style={{position: "absolute", left: 96, top: 930, width: 520, height: 1, background: "rgba(237,235,228,0.35)"}}/>
  <Names x={96} y={948} size={24}/>
  <Credit x={1824} y={1032}><span style={{position: "absolute", right: 0, whiteSpace: "pre"}}>{AF_CREDIT}</span></Credit>
  <Finish grain={0.14} vignette={0.35}/>
</AbsoluteFill>;

// 2. confidence lacquer: pLDDT bins in red / bone / blue (Red Knot Chain gloss)
const BINS = [["#002FA7", "VERY HIGH", "> 90"], ["#1F3BFF", "CONFIDENT", "70–90"], [K.ink, "LOW", "50–70"], [K.verm, "VERY LOW", "< 50"]];
export const O2Plddt = () => <AbsoluteFill style={{background: K.bg}}>
  <Plate src="p_plddt.png"/>
  <T x={1440} y={96} size={12} ls={3} color={K.dim}>MODEL CONFIDENCE (pLDDT)</T>
  {BINS.map(([c, n, v], i) => <React.Fragment key={i}>
    <div style={{position: "absolute", left: 1440, top: 130 + i * 34, width: 44, height: 14, background: c, boxShadow: "0 0 0 1px rgba(237,235,228,0.25)"}}/>
    <T x={1500} y={127 + i * 34} size={13} ls={2}>{n}</T>
    <T x={1700} y={127 + i * 34} size={13} ls={1} color={K.dim}>{v}</T>
  </React.Fragment>)}
  <T x={96} y={86} size={68} font={GROT} weight={800} ls={-2}>AlphaFold</T>
  <T x={100} y={168} size={14} ls={3} color={K.dim}>AN AI THAT PREDICTS THE SHAPE OF PROTEINS</T>
  <T x={96} y={952} size={14} ls={3}>NOBEL PRIZE IN CHEMISTRY 2024</T>
  <T x={96} y={976} size={14} ls={3} color={K.dim}>DEMIS HASSABIS · JOHN JUMPER</T>
  <Credit x={1824} y={1032}><span style={{position: "absolute", right: 0, whiteSpace: "pre"}}>{AF_CREDIT}</span></Credit>
  <Finish grain={0.2} vignette={0.2}/>
</AbsoluteFill>;

// 3. the gallery: a cast of the model on a plinth, with a wall label (Voss-Andreae)
export const O3Plinth = () => <AbsoluteFill style={{background: K.bg}}>
  <Plate src="p_plaster.png"/>
  <div style={{position: "absolute", left: 1412, top: 640, width: 400, padding: "26px 28px", background: "rgba(237,235,228,0.92)", color: "#111"}}>
    <div style={{fontFamily: GROT, fontWeight: 800, fontSize: 21}}>CDK20, predicted</div>
    <div style={{fontFamily: GROT, fontSize: 15, marginTop: 6, color: "#333"}}>AlphaFold DB model AF-Q8IZL9-F1 (v6)</div>
    <div style={{fontFamily: GROT, fontSize: 15, color: "#333"}}>346 amino acids, shown as a cartoon cast</div>
    <div style={{height: 1, background: "#999", margin: "14px 0"}}/>
    <div style={{fontFamily: SERIF, fontSize: 19, lineHeight: 1.3}}>Nobel Prize in Chemistry 2024, in part to Demis Hassabis and John Jumper, for AlphaFold.</div>
    <div style={{fontFamily: MONO, fontSize: 10, letterSpacing: 1, marginTop: 14, color: "#555"}}>CC BY 4.0 · PREDICTED</div>
  </div>
  <Tag/>
  <Finish grain={0.16} vignette={0.3}/>
</AbsoluteFill>;

// 4. radiograph + monumental serif (X-ray; type as the star)
export const O4Xray = () => <AbsoluteFill style={{background: K.bg}}>
  <Plate src="p_xray.png" style={{opacity: 0.92}}/>
  <T x={960} y={748} size={15} ls={6} color={K.dim} anchor="center" style={{left: 0, width: W}}>AN AI THAT PREDICTS THE SHAPE OF PROTEINS</T>
  <div style={{position: "absolute", left: 0, top: 790, width: W, textAlign: "center", fontFamily: SERIF, fontSize: 112, color: K.ink, lineHeight: 1, letterSpacing: 1,
    mixBlendMode: "difference"}}>Nobel Prize in Chemistry 2024</div>
  <div style={{position: "absolute", left: 0, top: 924, width: W, textAlign: "center", fontFamily: MONO, fontSize: 16, letterSpacing: 5, color: K.verm}}>DEMIS HASSABIS · JOHN JUMPER · ALPHAFOLD</div>
  <Credit x={80} y={1032}>{AF_CREDIT}</Credit>
  <Finish grain={0.22} vignette={0.45}/>
</AbsoluteFill>;

// 5. assembly out of flow lines (three frames)
export const O5Assemble = ({part = "b"}) => <AbsoluteFill style={{background: K.bg}}>
  <Plate src={`p_as_${part}.png`}/>
  {part === "c" ? <>
    <T x={96} y={900} size={14} ls={3}>ALPHAFOLD · NOBEL PRIZE IN CHEMISTRY 2024</T>
    <T x={96} y={926} size={14} ls={3} color={K.dim}>DEMIS HASSABIS · JOHN JUMPER</T>
  </> : null}
  <Credit x={1840} y={1032}><span style={{position: "absolute", right: 0, whiteSpace: "pre"}}>{AF_CREDIT}</span></Credit>
  <Finish grain={0.18} vignette={0.4}/>
</AbsoluteFill>;

export const OPTIONS_110 = [
  {id: "S110o1", C: O1Glass}, {id: "S110o2", C: O2Plddt}, {id: "S110o3", C: O3Plinth}, {id: "S110o4", C: O4Xray},
  {id: "S110o5a", C: O5Assemble, p: {part: "a"}}, {id: "S110o5b", C: O5Assemble, p: {part: "b"}}, {id: "S110o5c", C: O5Assemble, p: {part: "c"}},
];
