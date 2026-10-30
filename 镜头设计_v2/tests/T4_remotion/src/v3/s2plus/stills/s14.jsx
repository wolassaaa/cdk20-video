// Still 14 · 8-03 to 8-04: the last sweep. The film's interface above the line, one person below it (section 3 S8: everything is taken away until only a person is speaking).
// Klein is this frame's one colour (the objective tags of 2-05 coming back), so the barcode goes all bone; its heights are still the real pLDDT, and it stands on the line to be erased first.
// PLACEHOLDER: the three Voice lines and both ticks stand in for the ink strokes of 8-02 and 8-03.
// C sits 180 px below the kit default so the eye line clears y = 540; the line crops C at the brow. Real footage needs the same framing.
import React from "react";
import {Stage, Voice, PlateText, Foot, Barcode, Tag, PersonPlaceholder, K, DIM, W, H, M, colX} from "../kit";

const LINE = H / 2, BAR_H = 64, LEFT = colX(0), RIGHT = colX(6);

// The tick runs over the tag's edge, as a hand-drawn tick would, instead of sitting beside it like an icon.
const Done = ({x, children}) => <div style={{position: "absolute", left: x, top: M, display: "flex", alignItems: "flex-start"}}>
  <Tag>{children}</Tag>
  <svg viewBox="0 0 100 100" width="72" height="72" style={{marginLeft: -14, marginTop: -9, overflow: "visible"}}><path d="M10 54L38 84L92 16" fill="none" stroke={K.bone} strokeWidth="11"/></svg>
</div>;

export default () => <Stage>
  <PersonPlaceholder who="C" side="full" y={180} eye/>

  <div style={{position: "absolute", left: 0, top: 0, width: W, height: LINE, background: K.bg, overflow: "hidden"}}>
    <Done x={LEFT}>Objective 1</Done>
    <Done x={RIGHT}>Objective 2</Done>
    <PlateText x={RIGHT + 340} y={M + 10}>(for this case)</PlateText>{/* the two strongest claims carry the same limit as Objective 1 (F19, F21) */}
    <Voice x={LEFT} y={216} size={72}>(for this case)</Voice>{/* 72, so "millions → 13" leads alone; y puts it on that line's baseline */}
    <Foot x={LEFT} y={340} color={DIM}>PLACEHOLDER · handwriting</Foot>
    <Voice x={RIGHT} y={176} size={120}>millions → 13</Voice>
    <Voice x={RIGHT} y={316} size={72}>10-17 years · first hit in 30 days</Voice>
    <Foot x={RIGHT} y={404} color={DIM}>Wang 2023 pp.1, 4-5 · Ren 2023</Foot>
    <Barcode x={M} y={LINE - BAR_H} height={BAR_H} mode={() => K.bone} cutAt={302} tail={false}/>{/* ends where still 5 cut it */}
  </div>

  <div style={{position: "absolute", left: 0, top: LINE - 1, width: W, height: 2, background: K.bone}}/>
  <Foot x={24} y={LINE + 20} on={null}>PLACEHOLDER · C</Foot>
</Stage>;
