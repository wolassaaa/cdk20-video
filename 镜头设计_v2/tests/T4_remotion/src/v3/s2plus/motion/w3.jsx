// W3 motion test: the field counts itself up to 8,918, then the numeral cuts in. Ends on still 06, frame for frame.
// One dot, one design, in reading order, so what you watch is a count and not a texture. A dot turns on once and stays: nothing here can flicker.
// The ILLUSTRATIVE plate is up from the first frame, since the positions mean nothing from the first dot on.
import React, {useLayoutEffect, useRef} from "react";
import {useCurrentFrame, useVideoConfig} from "remotion";
import {Stage, Giant, Plate, PlateText, K, W, H} from "../kit";
import DOTS from "../data/dots_8918.json";

const N = 8918;
const FILL = 5.4;    // seconds to reach 8,918
const CUT = 5.6;     // the numeral cuts in here, with no fade. The short gap lets the last row land first

const Dots = ({n}) => {
  const ref = useRef(null);
  useLayoutEffect(() => {
    const c = ref.current, ss = Math.max(window.devicePixelRatio || 1, 2), g = c.getContext("2d"), {xy, r} = DOTS;
    c.width = W * ss; c.height = H * ss;
    g.scale(ss, ss);
    g.fillStyle = K.bone; g.beginPath();
    for (let i = 0; i < n; i++) { g.moveTo(xy[2 * i] + r, xy[2 * i + 1]); g.arc(xy[2 * i], xy[2 * i + 1], r, 0, 2 * Math.PI); }
    g.fill();
  }, [n]);
  return <canvas ref={ref} style={{position: "absolute", left: 0, top: 0, width: W, height: H}}/>;
};

export default () => {
  const f = useCurrentFrame(), {fps} = useVideoConfig(), t = f / fps;
  const x = Math.min(1, t / FILL), n = Math.round(N * x * x * (3 - 2 * x));   // starts one at a time, ends in a rush
  return <Stage bg={K.blue}>
    <Dots n={n}/>
    <PlateText x={DOTS.tag.x} y={DOTS.tag.y} on={K.blue}>Tool: generative design</PlateText>
    {t < CUT
      ? <PlateText x={96} y={DOTS.tag.y} on={K.blue}>{n.toLocaleString("en-US")}</PlateText>
      : <Giant x={DOTS.giant.x} y={DOTS.giant.y} size={480} on={K.blue} style={{whiteSpace: "nowrap"}}>8,918</Giant>}
    <Plate kind="illustrative" x={DOTS.plate.x} y={DOTS.plate.y} on={K.blue}/>
  </Stage>;
};
