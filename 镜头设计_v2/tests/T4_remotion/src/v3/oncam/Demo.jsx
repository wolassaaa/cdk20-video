// V3-OnCamCards: the M3 card with its ink props, one ON-CAM beat each (script v3.3). Footage = placeholder phone clip.
// Render with --public-dir pointing at 镜头设计_v3/remotion_public (holds placeholder_hand.mp4, later the real takes).
import React from "react";
import {AbsoluteFill, Sequence, staticFile} from "remotion";
import {C, BoilProvider} from "../core";
import {Stage} from "../texture";
import {Mono} from "../type";
import {OnCamCard, CW, CH} from "./Card";
import {PropNumerals, PropLock, PropScissors, PropTrail, PropPhone, PropDots, PropTimeline, PropPulse} from "./props";

const FOOT = "placeholder_hand.mp4";
// side the diagram / props live on: beside the card, away from its own corner
const RIGHT = CW + 330, LEFT = -330;

const BEATS = [
  {beat: "1-01", who: "A", dur: 90, prop: <PropPulse x={CW / 2 - 450} y={CH + 34} start={14}/>},
  {beat: "1-07", who: "C", dur: 90, prop: <PropTimeline x={CW + 70} y={CH * 0.5} s={0.72} start={14}/>},
  {beat: "2-04", who: "C", dur: 75, prop: <PropNumerals x={RIGHT} y={CH * 0.45} start={14} text="1 2"/>},
  {beat: "3-01", who: "D", dur: 90, prop: <PropLock x={LEFT - 200} y={CH * 0.35} s={0.9} start={14} state="sketch"/>},
  {beat: "4-05", who: "B", dur: 75, prop: <PropScissors x={CW * 0.5} y={CH * 0.42} s={0.9} start={12}/>},
  {beat: "4-08", who: "A", dur: 60, prop: <PropTrail x={CW - 40} y={CH * 0.45} start={16}/>},
  {beat: "5-05", who: "C", dur: 90, prop: <PropLock x={RIGHT + 40} y={CH * 0.3} s={0.9} start={12} state="half"/>},
  {beat: "5-09", who: "C", dur: 75, prop: <PropLock x={RIGHT + 40} y={CH * 0.3} s={0.9} start={8} state="turn"/>},
  {beat: "6-04", who: "D", dur: 90, prop: <PropDots x={CW * 0.5} y={CH * 0.62} start={12}/>},
  {beat: "7-01", who: "A", dur: 75, prop: <PropNumerals x={RIGHT + 80} y={CH * 0.45} s={0.85} start={14} text="1 2 3"/>},
  {beat: "8-05", who: "B", dur: 90, prop: <PropPhone x={LEFT} y={CH * 0.5} s={1.1} start={14}/>},
];

let t = 0;
const TIMED = BEATS.map(b => { const o = {...b, from: t}; t += b.dur; return o; });
export const ONCAM_CARDS_FRAMES = t;

export const V3OnCamCards = () => <BoilProvider rate={2.5}>
  <Stage grain={0.16}>
    {TIMED.map(b => <Sequence key={b.beat} from={b.from} durationInFrames={b.dur}>
      <AbsoluteFill>
        <OnCamCard who={b.who} src={staticFile(FOOT)} videoStart={b.from % 200} dur={b.dur}>{b.prop}</OnCamCard>
        <svg width={1920} height={1080} style={{position: "absolute"}}>
          <Mono x={960} y={1050} size={16} color={C.dim} anchor="middle" letterSpacing={3}>{`${b.beat} · ${b.who} ON-CAM · PLACEHOLDER FOOTAGE`}</Mono>
        </svg>
      </AbsoluteFill>
    </Sequence>)}
  </Stage>
</BoilProvider>;
