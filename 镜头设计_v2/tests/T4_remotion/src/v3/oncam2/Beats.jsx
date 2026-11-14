// HKBU SCIE1007 coursework video: every on-camera beat exported at its full recorded length for the rough cut
// (镜头设计_v3/粗剪/oncam2_beats/<beat>.mp4). No head/tail trim: length = the beat's _wide.mp4 length.
// Ink at the ends from 镜头设计_v3/粗剪/cut_v2.json: previous beat not ON-CAM -> 0.5 s ink recedes toward the motion side;
// next beat not ON-CAM -> 0.7 s ink floods from the motion side over the person. Generated table below (frames at 30 fps).
import React from "react";
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame} from "remotion";
import {ramp, inOut} from "../core";
import {W, InkSheet, INK_OUT, edgeVol} from "./kit";
import {S12_SEGS} from "./S12";
import {S34_SEGS} from "./S34";
import {S58_SEGS} from "./S58";

export const BEATS = {"1-01": {frames: 166, inkIn: true, inkOut: true}, "1-03": {frames: 152, inkIn: true, inkOut: true}, "1-05": {frames: 110, inkIn: true, inkOut: false}, "1-06": {frames: 84, inkIn: false, inkOut: false}, "1-07": {frames: 110, inkIn: false, inkOut: true}, "2-02": {frames: 320, inkIn: true, inkOut: true}, "2-04": {frames: 104, inkIn: true, inkOut: true}, "3-01": {frames: 187, inkIn: true, inkOut: true}, "3-06": {frames: 338, inkIn: true, inkOut: true}, "3-09": {frames: 169, inkIn: true, inkOut: true}, "4-04": {frames: 64, inkIn: true, inkOut: false}, "4-05": {frames: 157, inkIn: false, inkOut: true}, "4-08": {frames: 250, inkIn: true, inkOut: true}, "4-11": {frames: 125, inkIn: true, inkOut: false}, "4-12": {frames: 218, inkIn: false, inkOut: true}, "5-02": {frames: 193, inkIn: true, inkOut: true}, "5-05": {frames: 134, inkIn: true, inkOut: false}, "5-06": {frames: 125, inkIn: false, inkOut: true}, "5-09": {frames: 96, inkIn: true, inkOut: true}, "6-04": {frames: 183, inkIn: true, inkOut: false}, "6-05": {frames: 103, inkIn: false, inkOut: true}, "6-12": {frames: 210, inkIn: true, inkOut: false}, "7-01": {frames: 147, inkIn: false, inkOut: true}, "8-01": {frames: 87, inkIn: true, inkOut: true}, "8-04": {frames: 293, inkIn: true, inkOut: false}, "8-05": {frames: 153, inkIn: false, inkOut: false}, "8-06": {frames: 310, inkIn: false, inkOut: false}, "8-07": {frames: 233, inkIn: false, inkOut: true}};
const INK_IN = 15; // 0.5 s

const BeatComp = ({seg, frames, inkIn, inkOut}) => {
  const f = useCurrentFrame(), G = seg.G, left = seg.side !== "right";
  // ink in: starts covering everything, edge travels toward the motion side and off frame
  const pIn = inOut(ramp(f, 0, INK_IN));
  const inEdge = left ? -250 + pIn * 2400 : W + 250 - pIn * 2400;   // left: ink at x > edge; right: ink at x < edge
  // ink out: from the motion side toward the person, fully covered on the last frame
  const T0 = frames - INK_OUT, pOut = inOut(ramp(f, T0, frames - 1));
  const outEdge = left ? 2080 - pOut * 2350 : -160 + pOut * 2350;
  const ownInk = seg.id === "1-07"; // 1-07's graphic already ends with the sample-v2 ink flood and cyan timeline
  return <AbsoluteFill style={{background: "#EAEAE1"}}>
    <OffthreadVideo src={staticFile(seg.src)} volume={edgeVol(frames, 2)}/>
    <G f={f} out={seg.id === "1-07" ? frames : seg.out}/>
    {inkIn && f < INK_IN && <InkSheet edgeX={inEdge} fromRight={left} t={f} id="bt-in" seed={4}/>}
    {inkOut && !ownInk && f >= T0 && <InkSheet edgeX={outEdge} fromRight={left} t={f - T0} id="bt-out" seed={9}/>}
  </AbsoluteFill>;
};

export const BEAT_COMPS = [...S12_SEGS, ...S34_SEGS, ...S58_SEGS].map(seg => {
  const b = BEATS[seg.id];
  return {id: "V3-OnCam2-Beat-" + seg.id, frames: b.frames, component: () => <BeatComp seg={seg} {...b}/>};
});
