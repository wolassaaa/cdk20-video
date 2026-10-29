// Wipe masks for the Blender fog-glass pane (opt4): white = wiped clear glass, black = fogged. 1920x1080, UV-aligned.
import React from "react";
import {AbsoluteFill} from "remotion";
import {W, H, rng} from "../../core";
import {GROT} from "./common";

export const FX = i => 420 + i * 120;
const LIT = [1, 4, 8];
const finger = (i, seed) => {
  const r = rng(seed * 31 + i * 7), x = FX(i) + (r() - 0.5) * 14, y0 = 230 + r() * 40, y1 = 780 + r() * 50, lean = (r() - 0.5) * 26;
  return `M${x},${y0} C${x + lean * 0.3},${y0 + 160} ${x + lean},${y1 - 200} ${x + lean * 0.8},${y1}`;
};
const drip = (i, seed) => {
  const r = rng(seed * 13 + i * 5), x = FX(i) + (r() - 0.5) * 10 + 4, y = 810 + r() * 30, L = 60 + r() * 180;
  return `M${x},${y} L${x + (r() - 0.5) * 6},${y + L}`;
};
const Edge = () => <defs>
  <filter id="me" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.08" numOctaves="3" seed="4" result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="12" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
</defs>;

export const Mask = ({part}) => <AbsoluteFill style={{background: "#000"}}>
  <svg width={W} height={H}>
    <Edge/>
    <g filter="url(#me)" stroke="#fff" fill="#fff" strokeLinecap="round" strokeLinejoin="round">
      {part === "a" ? <g>
        {/* v2: the old name is simply fogging back over (no strike) */}
        <g opacity={0.42}>
          <text x={210} y={420} fontFamily={GROT} fontWeight={500} fontSize={160} strokeWidth={10}>Nexavar</text>
        </g>
        <text x={210} y={660} fontFamily={GROT} fontWeight={500} fontSize={124} strokeWidth={10} letterSpacing={2}>atezolizumab + bevacizumab</text>
        <path d="M214,732 C640,724 1100,730 1520,722" strokeWidth={9} fill="none"/>
      </g> : <g fill="none">
        {Array.from({length: 10}, (_, i) => {
          const op = part === "c" && !LIT.includes(i) ? 0.22 : 1;
          return <g key={i} opacity={op}>
            <path d={finger(i, 3)} strokeWidth={58}/>
            <path d={drip(i, 3)} strokeWidth={10}/>
          </g>;
        })}
      </g>}
    </g>
  </svg>
</AbsoluteFill>;
