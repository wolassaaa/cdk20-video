// Type laid over the Blender plates (neon metro, typographic road, recorder, stair, fog, counter).
import React from "react";
import {Print, Plate, Tag, Svg, GText, MText, P, ST, COUNT, W, H, NB} from "./common";
import ANCH from "./anch.json";

const Head = ({children, y = 96, color = P.ink}) => <MText x={70} y={y} size={15} opacity={0.65} ls={4} color={color}>{children}</MText>;
const Fail = ({x = 1850, y = 1000, color = P.red, anchor = "end"}) => <GText x={x} y={y} size={30} weight={600} anchor={anchor} color={color}>Any step can fail.</GText>;

/* 1-09 · neon metro on a black wall */
export const RoadNeon = ({lit = 6}) => {
  const A = ANCH.neon;
  return <Print grain={0.17} band={0.05}>
    <Plate src={lit >= 6 ? "plates/neon_full.png" : "plates/neon_lit4.png"}/>
    <Svg>
      {A.map(([x, y], i) => {
        const top = i < 3, on = i < lit, sz = i === 5 ? 44 : 36;
        const ty = top ? y - 70 : y + 92;
        return <g key={i} opacity={on ? 1 : 0.28}>
          <MText x={x} y={top ? ty - sz - 6 : ty - sz - 8} size={15} anchor="middle" color={on ? P.red : P.ink}>{ST[i].n}</MText>
          <GText x={x} y={ty} size={sz} anchor="middle" lh={1.0}>{top ? ST[i].name : ST[i].short}</GText>
          {ST[i].sub ? <MText x={x} y={ty + (top ? 30 : sz * 2 + 2)} size={13} anchor="middle" weight={400} ls={1} opacity={0.6}>{ST[i].sub}</MText> : null}
        </g>;
      })}
      <Head>EVERY MEDICINE WALKS THE SAME ROAD</Head>
      {lit >= 6 ? <Fail/> : null}
      <Tag/>
    </Svg>
  </Print>;
};

/* 1-09 · station names are 3D words on the road; overlay only adds numbers */
export const RoadType3D = ({lit = 6}) => {
  const A = ANCH.typeroad;
  return <Print grain={0.2} band={0.05}>
    <Plate src={lit >= 6 ? "plates/typeroad_full.png" : "plates/typeroad_lit4.png"}/>
    <Svg>
      {A.map(([x, y], i) => <MText key={i} x={x - 8} y={y + 6} size={Math.max(12, 22 - i * 2)} anchor="end" color={i < lit ? P.red : P.ink} opacity={i < lit ? 1 : 0.3}>{ST[i].n}</MText>)}
      <Head>EVERY MEDICINE WALKS THE SAME ROAD</Head>
      {lit >= 6 ? <Fail y={96} x={1850}/> : null}
      <Tag/>
    </Svg>
  </Print>;
};

/* 1-09 · chart-recorder strip, paper rolls out as the journey goes */
export const RoadRecorder3D = ({lit = 6}) => <Print grain={0.2} band={0.05}>
  <Plate src={lit >= 6 ? "plates/recorder_full.png" : "plates/recorder_lit4.png"}/>
  <Svg>
    <Head>EVERY MEDICINE WALKS THE SAME ROAD</Head>
    {lit < 6 ? <g opacity={0.35}>
      <MText x={1850} y={170} size={14} anchor="end">NOT YET PRINTED</MText>
      <GText x={1850} y={214} size={30} anchor="end">05 HUMAN TRIALS</GText>
      <GText x={1850} y={252} size={30} anchor="end">06 APPROVAL</GText>
    </g> : <Fail y={96}/>}
    <Tag/>
  </Svg>
</Print>;

/* 1-08 · cumulative cost as blue glass cubes, one column a year */
export const Stair = () => {
  const A = ANCH.stair;
  return <Print grain={0.2} band={0.05}>
    <Plate src="plates/stair_full.png"/>
    <Svg>
      {[5, 10, 15].map(k => <MText key={k} x={A[k][0] - 6} y={A[k][1] + 34} size={15} anchor="middle" opacity={0.8} ls={1}>{2006 + k}</MText>)}
      <MText x={70} y={1010} size={15} ls={3}>← 2006 · THE YEAR WE WERE BORN</MText>
      <MText x={A[19][0] + 60} y={A[19][1] - 40} size={15} ls={3} anchor="end" color={P.red}>2026 · ONLY READY NOW</MText>
      <GText x={70} y={200} size={110} weight={900} ls={-4}>US$2.8<tspan fill={P.blue} dx={30}>billion</tspan></GText>
      <MText x={74} y={250} size={15} ls={3} opacity={0.7}>IT CAN COST ALMOST · 1 CUBE = US$10 MILLION, RUNNING TOTAL</MText>
      <Tag/>
    </Svg>
  </Print>;
};

/* 1-08 · fogged glass, two frames */
export const FogTime = () => <Print grain={0.16} band={0.04} blotch={0}>
  <Plate src="plates/fog_time.png"/>
  <Svg>
    <MText x={70} y={1010} size={15} ls={4} opacity={0.75}>START THE SEARCH THE YEAR WE WERE BORN</MText>
    <MText x={1850} y={1010} size={15} ls={4} opacity={0.75} anchor="end">IT CAN COST ALMOST 2.8 BILLION US DOLLARS</MText>
  </Svg>
</Print>;
export const FogTally = () => <Print grain={0.16} band={0.04} blotch={0}>
  <Plate src="plates/fog_tally.png"/>
  <Svg>
    <MText x={70} y={1010} size={15} ls={4} opacity={0.75}>OF DRUGS TESTED IN PEOPLE,</MText>
    <MText x={1850} y={1010} size={15} ls={4} anchor="end" color={P.red}>ONLY ABOUT ONE IN TEN REACHES THE MARKET</MText>
  </Svg>
</Print>;

/* 1-08 · LED counter wall */
export const Counter = () => <Print grain={0.2} band={0.05} blotch={0}>
  <Plate src="plates/counter_full.png"/>
  <Svg>
    <MText x={70} y={96} size={15} ls={4} opacity={0.7}>US$ · IT CAN COST ALMOST 2.8 BILLION US DOLLARS</MText>
    <MText x={70} y={1010} size={15} ls={4} opacity={0.7}>THE YEAR WE WERE BORN → ONLY READY NOW</MText>
    <Tag/>
  </Svg>
</Print>;
