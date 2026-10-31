// M06 · W3, second pass. The number is made of itself: exactly 8,918 bone dots, one per generated design (Ren 2023 Fig. 5, E11), filling the digits.
// Positions mean nothing, so it stays ILLUSTRATIVE. Dots come from code/make_dots_m.py, which asserts the count; `python make_dots.py count <png>` recounts them on the render.
// M06mask is the digit shape make_dots_m.py samples. No fast full-screen flicker in the moving version: the script rules that out for W3.
import React, {useLayoutEffect, useRef} from "react";
import {Stage, Plate, PlateText, K, W, H} from "../kit";
import {Disp, Micro, Reg} from "../kit_m";
import DOTS from "../data/dots_m06.json";

const N = 8918, SIZE = 1040, TOP = 32;
export const Mask = () => <div style={{position: "absolute", inset: 0, background: "#fff"}}>
  <Disp x={W / 2} y={TOP} size={SIZE} wide={50} weight={740} color="#000" track="0.035em" style={{transform: "translateX(-50%)"}}>8,918</Disp>
</div>;

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

export default () => {
  if (DOTS.n !== N || DOTS.xy.length !== 2 * N) throw new Error(`M06 needs ${N} dots, data has ${DOTS.xy.length / 2}`);
  return <Stage bg={K.blue}>
    <div style={{position: "absolute", left: 0, top: 946, width: W, height: 134, background: K.bg}}/>
    <Dots/>
    <div style={{position: "absolute", left: 96, top: 990}}><PlateText on={K.bg}>Tool: generative design</PlateText></div>
    <Micro x={560} y={984} size={14}>{"one dot = one generated design\n8,918 dots, counted on this render"}</Micro>
    <Plate kind="illustrative" x={1560} y={982}/>
    
  </Stage>;
};
