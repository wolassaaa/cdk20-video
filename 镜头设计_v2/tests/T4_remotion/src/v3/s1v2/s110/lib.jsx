// s110 shared pieces: fonts, plate image, labels, title block, faint road map, grain.
import React from "react";
import {AbsoluteFill, Img, staticFile} from "remotion";
import {loadFont as loadGrot} from "@remotion/google-fonts/InterTight";
import {loadFont as loadSerif} from "@remotion/google-fonts/InstrumentSerif";
import {MONO} from "../../core";
import {Grain} from "../../texture";

export const GROT = loadGrot("normal", {weights: ["300", "400", "600", "800", "900"], subsets: ["latin"]}).fontFamily;
export const SERIF = loadSerif("normal", {weights: ["400"], subsets: ["latin"]}).fontFamily;
loadSerif("italic", {weights: ["400"], subsets: ["latin"]});
export {MONO};
export const K = {bg: "#060606", ink: "#EDEBE4", verm: "#FF3B1F", blue: "#1F3BFF", klein: "#002FA7", dim: "rgba(237,235,228,0.55)", faint: "rgba(237,235,228,0.22)"};
export const W = 1920, H = 1080;

// exact script text (W1)
export const TITLE = "WORTH TESTING?";
export const SUB = "How computers help find cancer drug candidates: the CDK20 story";
export const COURSE = "SCIE1007 · SECTION S— · GROUP —";
export const MEMBERS = ["MEMBER A", "MEMBER B", "MEMBER C", "MEMBER D"];
export const STATIONS = ["Target", "Hit", "Improve", "Cells & animals", "Clinical trials 1-2-3", "Approval"];

export const Plate = ({src, style}) => <Img src={staticFile(src)} style={{position: "absolute", left: 0, top: 0, width: W, height: H, objectFit: "cover", ...style}}/>;

export const T = ({x, y, size = 16, font = MONO, color = K.ink, weight = 400, ls = 0, children, style, anchor = "left", w}) =>
  <div style={{position: "absolute", left: anchor === "right" ? undefined : x, right: anchor === "right" ? W - x : undefined, top: y, fontFamily: font, fontSize: size,
    color, fontWeight: weight, letterSpacing: ls, lineHeight: 1.15, whiteSpace: w ? "normal" : "pre", width: w, textAlign: anchor, ...style}}>{children}</div>;

export const Tag = ({x = 1840, y = 1030, children = "ILLUSTRATIVE", anchor = "right", color = K.dim}) =>
  <T x={x} y={y} size={12} ls={2.5} color={color} anchor={anchor}>{children}</T>;

export const Credit = ({children, x = 80, y = 1032, color = "rgba(237,235,228,0.45)"}) => <T x={x} y={y} size={11} ls={1.2} color={color}>{children}</T>;

export const AF_CREDIT = "CDK20 · AlphaFold DB AF-Q8IZL9-F1 v6 · predicted · CC BY 4.0";
export const OSM_CREDIT = "© OpenStreetMap contributors";

// faint road map: six stations on one hairline (layout only; the real map comes from 1-09)
export const RoadFaint = ({y = 900, x0 = 160, x1 = 1760, color = "rgba(237,235,228,0.18)", lit = 0, label = true}) => {
  const n = STATIONS.length;
  return <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
    <line x1={x0 - 60} y1={y} x2={x1 + 60} y2={y} stroke={color} strokeWidth={1.2}/>
    {lit > 0 ? <line x1={x0 - 60} y1={y} x2={x0 + (x1 - x0) * lit / (n - 1)} y2={y} stroke={K.verm} strokeOpacity={0.5} strokeWidth={1.6}/> : null}
    {STATIONS.map((s, i) => {
      const x = x0 + (x1 - x0) * i / (n - 1);
      return <g key={i}>
        <circle cx={x} cy={y} r={5} fill={K.bg} stroke={color} strokeWidth={1.2}/>
        {label ? <text x={x} y={y + 30} fill={color} fontFamily={MONO} fontSize={12} letterSpacing={1.5} textAnchor="middle">{s.toUpperCase()}</text> : null}
      </g>;
    })}
  </svg>;
};

export const Members = ({x, y, size = 13, color = K.dim, gap = "   ·   ", anchor}) => <T x={x} y={y} size={size} ls={2} color={color} anchor={anchor}>{MEMBERS.join(gap)}</T>;

export const Finish = ({grain = 0.16, vignette = 0.5}) => <>
  {vignette ? <AbsoluteFill style={{background: `radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,${vignette}) 100%)`}}/> : null}
  <Grain opacity={grain}/>
</>;
