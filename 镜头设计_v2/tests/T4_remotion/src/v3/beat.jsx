// Fake 120 BPM clock (30 fps -> a beat every 15 frames) + impact-frame helpers.
import React from "react";
import {C, W, H, hash} from "./core";

export const BPM = 120;
export const BEAT = 15; // frames per beat at 30 fps
export const beatOf = f => Math.floor(f / BEAT);
export const sinceBeat = f => f % BEAT;
export const beatEnv = (f, decay = 3.2) => Math.exp(-sinceBeat(f) / decay);
export const isDownbeat = f => beatOf(f) % 4 === 0;

/** Camera kick on each beat: [dx, dy, scale]. */
export const kick = (f, amp = 14) => {
  const s = sinceBeat(f), b = beatOf(f), e = Math.exp(-s / 2.2);
  if (s > 6) return [0, 0, 1];
  return [(hash(b, 1) - 0.5) * amp * e * 2, (hash(b, 2) - 0.5) * amp * e, 1 + 0.018 * e];
};

/** RGB misregistration filter: cyan copy left, vermilion copy right, original on top. k = offset in px. */
export const SplitDefs = ({k = 0}) => <defs>
  <filter id="v3-split" x="0" y="0" width={W} height={H} filterUnits="userSpaceOnUse">
    <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 0.16  0 0 0 0 0.94  0 0 0 0 1  0.35 0.55 0.1 0 0" result="c"/>
    <feOffset in="c" dx={-k} dy={-k * 0.25} result="c2"/>
    <feColorMatrix in="SourceGraphic" type="matrix" values="0 0 0 0 1  0 0 0 0 0.23  0 0 0 0 0.12  0.35 0.55 0.1 0 0" result="v"/>
    <feOffset in="v" dx={k} dy={k * 0.35} result="v2"/>
    <feBlend in="c2" in2="v2" mode="screen" result="cv"/>
    <feMerge><feMergeNode in="cv"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>;

/** 16-step beat bar for the frame furniture (the computer keeping time). */
export const BeatBar = ({f, x = 812, y = 1004, n = 16}) => {
  const b = beatOf(f);
  return <g>
    {Array.from({length: n}, (_, i) => <rect key={i} x={x + i * 19} y={y} width={13} height={13}
      fill={i === b ? C.cyan : i < b ? "rgba(237,235,228,0.45)" : "none"} stroke={i === b ? C.cyan : "rgba(237,235,228,0.35)"} strokeWidth={1.2}/>)}
  </g>;
};
