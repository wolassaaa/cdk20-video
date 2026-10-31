// M09 · W4, second pass. Same evidence border, harder: lab result on pure red, our re-docking on black, pure blue lines against pure red.
// The error stays the same size as the value (048's error is 68% of it), so nobody reads 33.4 as firmer than it is.
// Pocket is engraved like the protein in M04 (render_048.py --lines), so the two read as one world. Ligand layer is unchanged.
import React from "react";
import {Img, staticFile} from "remotion";
import {Stage, Plate, PlateText, Body, K, W, H} from "../kit";
import {Disp, Micro, Reg, CrossField} from "../kit_m";

const LINE = 1040, PAD = 64;

export default () => <Stage>
  <div style={{position: "absolute", left: 0, top: 0, width: LINE, height: H, background: K.red}}/>
  <CrossField x0={LINE + 60} y0={60} x1={W - 40} y1={1020} step={120} color={K.bone} s={6} weight={1.25}/>
  <Disp x={PAD - 4} y={98} size={118} wide={150} color={K.bone}>048</Disp>
  <Disp x={PAD - 8} y={206} size={312} wide={112} color={K.bg}>33.4</Disp>
  <Disp x={PAD - 8} y={490} size={312} wide={84} color={K.bg}><span style={{marginRight: "0.07em"}}>±</span>22.6</Disp>
  <Disp x={PAD - 2} y={778} size={118} wide={150} color={K.bg}>nM</Disp>
  {/* plain-language line, script/数字大白话_brief_20261031.md. W4 has no narration and 001 is off frame, so it reads on its own: script 5-04's IC50 definition, 5-08's "just" */}
  <Body x={PAD} y={868} on={K.red} color={K.bg} style={{whiteSpace: "nowrap"}}>Just this much cuts the enzyme's activity in half.</Body>

  <div style={{position: "absolute", left: PAD, top: 36, background: K.bg, padding: "6px 14px"}}><PlateText>Enzyme IC50</PlateText></div>
  <Plate kind="measured" fig="9A" x={PAD} y={930} on={K.red}/>

  {["pose_048_lines.png", "pose_048_lig.png"].map(f => <Img key={f} src={staticFile(f)} style={{position: "absolute", left: W / 2, top: 0, width: W / 2, height: H}}/>)}
  <PlateText x={1296} y={108}>Lys33</PlateText>
  <Plate kind="ours" x={LINE + 56} y={930}/>
  <Reg x={W - 76} y={40} flip/>
</Stage>;
