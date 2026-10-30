// Still 09 · W4: the centre line is the evidence border. Measured on red, our re-docking on black, and only the frame edge between them.
// Big, not Giant: section 4 asks for 大字, ± keeps the value's size (048's error is 68%, section 3 S5), and Giant beside a mono plate would be a third of methods 9-14 (rule 7).
// Right half is pose_048.png, 1920x2160 from code/render_048.py, so it lands 1:1 at --scale=2. Until that has run, a vector stand-in from the same camera holds the place and says so on screen.
// A blue mass beside the red half breaks one colour per screen (section 3's exception covers only the hollow plate), so the pocket is a mid grey, render_048.py --pocket 6B6965 --name grey. A darker grey went to mud. --props '{"pocket":"blue"}' keeps the blue version for comparison.
import React from "react";
import {Img, staticFile, getStaticFiles, getInputProps} from "remotion";
import {Stage, Big, Body, Foot, Plate, PlateText, K, W, H, M} from "../kit";
import POSE from "../data/pose048_2d.json";

const FILE = "pose_048_lig.png", POCKET = `pose_048_${getInputProps().pocket || "grey"}.png`;
const LINE = W / 2, RIGHT = LINE + M;  // the black half keeps its own 96 off the evidence line; column 6 would put blue 12 px from red
const PLATE_Y = 930;                   // plate bottom on the 96 margin

const StandIn = () => <>
  <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
    {POSE.hbonds.map(([a, b, c, d], i) => <line key={i} x1={a} y1={b} x2={c} y2={d} stroke={K.bone} strokeWidth={3} strokeDasharray="10 12"/>)}
    {POSE.bonds.map(([a, b, c, d], i) => <line key={i} x1={a} y1={b} x2={c} y2={d} stroke={K.bone} strokeWidth={8}/>)}
    {POSE.atoms.map(([x, y, r], i) => <circle key={i} cx={x} cy={y} r={r} fill={K.bone}/>)}
  </svg>
  <Foot x={RIGHT} y={M}>FALLBACK · {FILE} not rendered yet</Foot>
</>;

export default () => {
  const rendered = getStaticFiles().some(f => f.name === FILE);
  return <Stage>
    <div style={{position: "absolute", left: 0, top: 0, width: LINE, height: H, background: K.red}}/>
    <Body x={M} y={778} on={K.red}>Enzyme IC50</Body>{/* W4 has no narration, so the frame says what the number is: not this pose's score */}
    <Big x={M - 3} y={826} size={84} on={K.red} style={{whiteSpace: "nowrap"}}>048 = 33.4 ± 22.6 nM</Big>
    <Plate kind="measured" fig="9A" x={M} y={PLATE_Y} on={K.red}/>
    {rendered ? [POCKET, FILE].map(f => <Img key={f} src={staticFile(f)} style={{position: "absolute", left: LINE, top: 0, width: LINE, height: H}}/>) : <StandIn/>}
    {rendered && <PlateText x={1296} y={108}>Lys33</PlateText>}
    <Plate kind="ours" x={RIGHT} y={PLATE_Y}/>
  </Stage>;
};
