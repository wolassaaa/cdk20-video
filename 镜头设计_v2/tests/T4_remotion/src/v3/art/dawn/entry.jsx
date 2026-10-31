// HKBU SCIE1007 coursework science video, dawn art direction. Words over the painted plates. Plates come from 镜头设计_v3/styleframes/art/dawn/code, this file only sets type.
// Newsreader for everything that is read, IBM Plex Sans for provenance tags. Both SIL OFL on Google Fonts.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, Img, staticFile} from "remotion";
import {loadFont as loadSerif} from "@remotion/google-fonts/Newsreader";
import {loadFont as loadSans} from "@remotion/google-fonts/IBMPlexSans";

const SERIF = loadSerif("normal", {weights: ["400", "500"], subsets: ["latin"]}).fontFamily;
const SANS = loadSans("normal", {weights: ["500"], subsets: ["latin"]}).fontFamily;
const BONE = "#F1EADF";

// evidence is a phase of the moon, so it survives without colour: full = measured, half = AI predicted, ring = our own docking, dashed ring = schematic
const Moon = ({kind, size = 30, ink = BONE, style}) => {
  const r = size / 2 - 2, c = size / 2;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{flex: "none", ...style}}>
      {kind === "measured" && <circle cx={c} cy={c} r={r} fill={ink} />}
      {kind === "predicted" && <>
        <circle cx={c} cy={c} r={r} fill="none" stroke={ink} strokeWidth={2.5} />
        <path d={`M ${c} ${c - r} A ${r} ${r} 0 0 1 ${c} ${c + r} Z`} fill={ink} />
      </>}
      {kind === "docking" && <circle cx={c} cy={c} r={r} fill="none" stroke={ink} strokeWidth={3} />}
      {kind === "schematic" && <circle cx={c} cy={c} r={r} fill="none" stroke={ink} strokeWidth={2.5} strokeDasharray="5 4.5" />}
    </svg>
  );
};

const Tag = ({kind, children, x, y, ink = BONE, px = 36, right}) => (
  <div style={{position: "absolute", left: right === undefined ? x : undefined, right, top: y, display: "flex", alignItems: "center", gap: 16, fontFamily: SANS, fontWeight: 500, fontSize: px, lineHeight: 1.1, color: ink, whiteSpace: "nowrap"}}>
    <Moon kind={kind} size={px * .86} ink={ink} />
    <span>{children}</span>
  </div>
);

const T = ({x, y, w, px, lh = 1.28, ink = BONE, weight = 400, style, children}) => (
  <div style={{position: "absolute", left: x, top: y, width: w, fontFamily: SERIF, fontWeight: weight, fontSize: px, lineHeight: lh, color: ink, ...style}}>{children}</div>
);

const Plate = ({name, children}) => (
  <AbsoluteFill style={{background: "#000"}}>
    <Img src={staticFile(`${name}.png`)} style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080}} />
    {children}
  </AbsoluteFill>
);

const T1 = () => (
  <Plate name="T1">
    <T x={120} y={826} w={1700} px={60} lh={1.1} style={{display: "flex", alignItems: "baseline", gap: 26, whiteSpace: "nowrap"}}>
      <span style={{fontSize: 164, fontWeight: 500, letterSpacing: "-.01em"}}>1,412</span>
      <span>deaths in Hong Kong, 2022</span>
    </T>
  </Plate>
);

const T2 = () => (
  <Plate name="T2">
    <T x={1262} y={756} w={610} px={40} lh={1.28} ink="#F4ECEC">How can computer-aided methods help scientists find and assess potential cancer drug candidates?</T>
  </Plate>
);

const T3 = () => (
  <Plate name="T3">
    <T x={0} y={872} w={1920} px={46} ink="#D8DBE2" style={{textAlign: "center"}}>no one had measured CDK20's shape</T>
    <div style={{position: "absolute", left: 0, top: 952, width: 1920, display: "flex", justifyContent: "center"}}>
      <div style={{display: "flex", alignItems: "center", gap: 14, fontFamily: SANS, fontWeight: 500, fontSize: 36, color: "#AEB2BC"}}>
        <Moon kind="schematic" size={31} ink="#AEB2BC" /><span>schematic</span>
      </div>
    </div>
  </Plate>
);

const T4 = () => (
  <Plate name="T4">
    <Tag kind="predicted" x={110} y={986} px={38}>AlphaFold DB v6 · predicted</Tag>
  </Plate>
);

const T5 = () => (
  <Plate name="T5">
    <T x={110} y={762} w={900} px={42} ink="#E9DFD6">Enzyme IC<sub style={{fontSize: ".66em", lineHeight: 0}}>50</sub></T>
    <T x={108} y={812} w={1000} px={94} lh={1.08} weight={500} style={{whiteSpace: "nowrap", letterSpacing: "-.005em"}}>048 = 33.4 ± 22.6 nM</T>
    <T x={110} y={930} w={960} px={38} style={{whiteSpace: "nowrap"}}>Just this much cuts the enzyme's activity in half.</T>
    <Tag kind="measured" x={110} y={990} px={36}>MEASURED · Ren 2023, Fig. 9A</Tag>
    <Tag kind="docking" x={1452} y={846} px={36}>OUR RE-DOCKING</Tag>
  </Plate>
);

const LIT = "#FFEBCB", DIM = "#ECE7EE";
const Station = ({x, y, name, lit}) => <T x={x} y={y} w={520} px={46} lh={1.1} ink={LIT} weight={500} style={{whiteSpace: "nowrap"}}>{name}</T>;

// stations not reached: a dashed flagpole up from the dark lamp, the words to its left, so no pole ever crosses a label
const Pending = ({x, y, name, foot}) => (
  <>
    <svg style={{position: "absolute", left: 0, top: 0}} width={1920} height={1080}>
      <line x1={x} y1={y + 6} x2={x} y2={foot} stroke={DIM} strokeWidth={2} strokeDasharray="7 8" />
    </svg>
    <div style={{position: "absolute", right: 1920 - x + 16, top: y, textAlign: "right", whiteSpace: "nowrap", color: DIM}}>
      <div style={{fontFamily: SERIF, fontSize: 46, lineHeight: 1.1}}>{name}</div>
      <div style={{fontFamily: SANS, fontWeight: 500, fontSize: 36, lineHeight: 1.2, marginTop: 2}}>not reported</div>
    </div>
  </>
);

const T6 = () => (
  <Plate name="T6">
    <Station x={214} y={286} name="Target" lit />
    <Station x={650} y={434} name="Hit" lit />
    <Station x={954} y={508} name="Improve" lit />
    <Pending x={1231} y={392} foot={632} name="Cells & animals" />
    <Pending x={1412} y={252} foot={659} name="Clinical trials 1-2-3" />
    <Pending x={1555} y={112} foot={675} name="Approval" />
    <T x={1254} y={800} w={200} px={68} lh={1} weight={500} ink="#FFC37E">048</T>
  </Plate>
);

const SEG = [["S1", "2:21", "last ember"], ["S2", "2:22", "dusk"], ["S3", "2:09", "deep night"], ["S4", "3:33", "blue hour"], ["S5", "2:19", "before dawn"], ["S6", "2:31", "grey"], ["S7", "0:49", "rose"], ["S8", "1:39", "first light"]];
const EDGE = [0, 254.7, 511.2, 744.2, 1128.9, 1379.9, 1652.7, 1741.2, 1920];
const Script = () => (
  <AbsoluteFill style={{background: "#000"}}>
    <Img src={staticFile("colour_script_plate.png")} style={{width: 1920, height: 480}} />
    {SEG.map(([s, t, n], i) => (
      <div key={s} style={{position: "absolute", left: EDGE[i] + 12, top: 340, color: BONE, fontFamily: SERIF}}>
        <div style={{fontSize: 34, lineHeight: 1.1, fontWeight: 500}}>{s}</div>
        <div style={{fontSize: 22, lineHeight: 1.3}}>{t}</div>
        <div style={{fontSize: 22, lineHeight: 1.2, whiteSpace: "nowrap"}}>{n}</div>
      </div>
    ))}
    {EDGE.slice(1, -1).map((x) => <div key={x} style={{position: "absolute", left: x, top: 330, width: 1, height: 130, background: "rgba(241,234,223,.28)"}} />)}
  </AbsoluteFill>
);

const ALL = {T1, T2, T3, T4, T5, T6};
const Root = () => (
  <>
    {Object.entries(ALL).map(([id, C]) => <Composition key={id} id={id} component={C} width={1920} height={1080} fps={30} durationInFrames={1} />)}
    <Composition id="Script" component={Script} width={1920} height={480} fps={30} durationInFrames={1} />
  </>
);
registerRoot(Root);
