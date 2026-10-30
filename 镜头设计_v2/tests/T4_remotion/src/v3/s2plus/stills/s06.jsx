// Still 06 · W3: 8,918 real dots on the blue field, one per generated design (Ren 2023 Fig. 5, E11). Positions mean nothing, so ILLUSTRATIVE stays on.
// Dots and the Giant's place come from code/make_dots.py, which also keeps them off the type and asserts the count. `make_dots.py count S06.png` checks the render.
// Bone here is not measured: 2.1 allows it on blue only with this label. Canvas at device scale, so 4K stays sharp.
import React, {useLayoutEffect, useRef} from "react";
import {Stage, Giant, Plate, PlateText, K, W, H} from "../kit";
import DOTS from "../data/dots_8918.json";

const N = 8918;
if (DOTS.n !== N || DOTS.xy.length !== 2 * N) throw new Error(`still 6 needs ${N} dots, data has ${DOTS.xy.length / 2}`);

const Dots = () => {
  const ref = useRef(null);
  useLayoutEffect(() => {
    const c = ref.current, ss = Math.max(window.devicePixelRatio || 1, 2), g = c.getContext("2d"), {xy, r} = DOTS;
    c.width = W * ss; c.height = H * ss;
    g.scale(ss, ss);
    g.fillStyle = K.bone; g.beginPath();
    for (let i = 0; i < N; i++) { g.moveTo(xy[2 * i] + r, xy[2 * i + 1]); g.arc(xy[2 * i], xy[2 * i + 1], r, 0, 2 * Math.PI); }
    g.fill();
  }, []);
  return <canvas ref={ref} style={{position: "absolute", left: 0, top: 0, width: W, height: H}}/>;
};

export default () => <Stage bg={K.blue}>
  <Dots/>
  <PlateText x={DOTS.tag.x} y={DOTS.tag.y} on={K.blue}>Tool: generative design</PlateText>
  <Giant x={DOTS.giant.x} y={DOTS.giant.y} size={480} on={K.blue} style={{whiteSpace: "nowrap"}}>8,918</Giant>
  <Plate kind="illustrative" x={DOTS.plate.x} y={DOTS.plate.y} on={K.blue}/>
</Stage>;
