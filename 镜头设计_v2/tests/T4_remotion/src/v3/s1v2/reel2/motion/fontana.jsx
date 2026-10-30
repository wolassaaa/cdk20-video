// W0 + 1-01 background: the Fontana canvas is cut for real. Frames come from
// 镜头设计_v3/styleframes/S1/v2/_code/reel2/motion/fontana_anim.py (+ post_seq.py), public/motion/fontana/*.jpg.
// Only the frames where something changes were rendered; every timeline frame maps to one of them.
import React from "react";
import {AbsoluteFill, Img, staticFile} from "remotion";
import {W, H, ramp, outExpo, hash} from "../../../core";
import {Grain} from "../../../texture";
import {useFrame30} from "../../../time30";

const OPEN = 8;               // rendered frames per opening (fontana_anim.py W_CURVE length)
const HITS = [0, 20, 40];     // W0 drum hits (0, 0.67, 1.33 s)
export const DUR_W0 = 60;
export const DUR_101 = 180;
const TRUCK = 40;             // 1-01: camera move from the W0 framing to the 1-01 framing, frames 0..40
export const CUT4 = 72;       // 1-01: fourth cut opens on "four" (~4.4 s into the film)

const src = n => staticFile(`motion/fontana/${n}.jpg`);
const pad = (n, k) => String(n).padStart(k, "0");

// camera kick on a hit: a quick push and a small damped shake (2D, on top of the render)
const kick = (k, amt = 1) => {
  if (k < 0 || k > 14) return {s: 1, x: 0, y: 0};
  const e = 1 - outExpo(ramp(k, 0, 10));
  const sh = Math.exp(-k / 3.2) * 7 * amt;
  return {s: 1 + 0.03 * amt * e, x: (hash(k, 11) - 0.5) * 2 * sh, y: (hash(k, 12) - 0.5) * 2 * sh};
};

const Frame = ({name, s = 1, x = 0, y = 0, origin = "50% 50%"}) =>
  <Img src={src(name)} style={{position: "absolute", left: 0, top: 0, width: W, height: H,
    transform: `translate(${x}px, ${y}px) scale(${s})`, transformOrigin: origin}}/>;

export const BeatW0 = () => {
  const f = useFrame30();
  const h = [...HITS].reverse().find(v => v <= f) ?? 0, k = f - h;
  const name = `w0_${pad(Math.floor(k < OPEN ? f : h + OPEN - 1), 2)}`;
  const kk = kick(k);
  return <AbsoluteFill style={{background: "#000", overflow: "hidden"}}>
    <Frame name={name} s={kk.s * 1.01} x={kk.x} y={kk.y}/>
  </AbsoluteFill>;
};

// background only: A's on-camera card is laid on top by the reel (top-left stays plain canvas)
export const Beat101Bg = () => {
  const f = useFrame30();
  const t = f <= TRUCK ? f : f < CUT4 ? TRUCK : f < CUT4 + OPEN ? f : CUT4 + OPEN - 1;
  const kk = kick(f - CUT4, 0.6);
  // the reel's v1 used a slow 1.00 -> 1.04 push; it starts once the camera has settled, centred on the cuts
  const push = 1.01 + 0.03 * ramp(f, TRUCK, DUR_101);
  return <AbsoluteFill style={{background: "#000", overflow: "hidden"}}>
    <Frame name={`c101_${pad(Math.floor(t), 3)}`} s={kk.s * push} x={kk.x} y={kk.y} origin="74% 50%"/>
    <Grain opacity={0.08}/>
  </AbsoluteFill>;
};
