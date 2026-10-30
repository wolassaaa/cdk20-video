// Still 11 · 6-08: the correction. The "millions → 13" row of 6-03 is pulled apart at the arrow and the note lands in the gap, so it interrupts the claim instead of footnoting it.
// Section 3 S6: BEFORE and NOW are two ledgers, each with its own source; only their heading rule and claim line stay collinear, which is what shows they were pulled apart.
// The note is the largest type on screen, on purpose bigger than the claim it corrects. Set in the 120 px Voice, against the script's "small" note, per the section 3 guard (at least 36 px).
// PLACEHOLDER: the note is Instrument Serif standing in for a group member's real handwriting (section 4). Swap the one Voice block, keep its size and place; the tag goes with it.
// The quote stays type when the note becomes handwriting, so the paper's words and the group's words stay visibly different.
import React from "react";
import {Stage, Big, Voice, Foot, K, DIM, H, M, colX, colW} from "../kit";

const WALL = colX(2) + colW(1);                  // the bone field: "millions", so many they merge. Bleeds off, ends at column 2
const NOW = colX(9), NOW_W = colW(3);            // mirror of the wall about x = 960
const GAP = NOW - WALL;                          // 900 px, 47% of the frame: half the screen at 6-03 has become this
const AXIS = 470;                                // claim and note share this centre line
const [BEFORE_WORD, NOW_WORDS] = "millions → 13".split(/ (?=→)/);  // same string, torn at the arrow
const ROUNDS = [7, 6];                           // 13 made = 7 (E11) + 6 (E17). One dot, one real molecule; the two rows are the two rounds
const R = 22, PITCH = (NOW_W - 2 * R) / 6;       // row of 7 fills the column exactly

const SHAFT_X = 412, SHAFT_Y = 469, SHAFT_H = 7;  // the arrow's own line, torn at the wall's edge: same y and weight as the arrow in "→ 13"

const Rule = ({x, w, color}) => <div style={{position: "absolute", left: x, top: 136, width: w, height: 4, background: color}}/>;
const Centred = {textAlign: "center"};

export default () => <Stage>
  <div style={{position: "absolute", left: 0, top: 0, width: WALL, height: H, background: K.bone}}/>

  <Foot x={M} y={96} on={K.bone}>BEFORE</Foot>
  <Rule x={M} w={WALL - M} color={K.bg}/>
  <Big x={M} y={AXIS - 50} size={96} on={K.bone}>{BEFORE_WORD}</Big>
  <div style={{position: "absolute", left: SHAFT_X, top: SHAFT_Y, width: WALL - SHAFT_X, height: SHAFT_H, background: K.bg}}/>
  <Foot x={M} y={953} on={K.bone}>Wang 2023 pp.4-5</Foot>

  <Foot x={NOW} y={96}>NOW</Foot>
  <Rule x={NOW} w={NOW_W} color={K.bone}/>
  <Big x={NOW} y={AXIS - 50} size={96} color={K.red}>{NOW_WORDS}</Big>
  <svg width={NOW_W} height={R * 2 + PITCH} style={{position: "absolute", left: NOW, top: AXIS + 90, overflow: "visible"}}>
    {ROUNDS.flatMap((n, row) => Array.from({length: n}, (_, i) => <circle key={`${row}-${i}`} cx={R + i * PITCH} cy={R + row * PITCH} r={R} fill={K.red}/>))}
  </svg>
  <Foot x={NOW} y={953}>Ren 2023</Foot>

  {/* the · is the script's, verbatim: on a line of its own it separates the two phrases and no longer hangs off the first */}
  <Voice x={WALL} y={AXIS - 157} w={GAP} size={120} style={Centred}>different sources<div style={{lineHeight: 0.5}}>·</div>scale and speed</Voice>
  <Voice x={WALL} y={840} w={GAP} size={64} style={Centred}>“cost- and time-efficient”</Voice>
  <Foot x={WALL} y={953} w={GAP} style={Centred}>Ren et al. 2023</Foot>
  <Foot x={WALL} y={1004} w={GAP} color={DIM} style={Centred}>PLACEHOLDER · handwriting</Foot>
</Stage>;
