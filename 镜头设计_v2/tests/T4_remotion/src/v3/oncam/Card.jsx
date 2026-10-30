// M3 on-camera card: the speaker's phone footage as a warm photo print on the black stage.
// Grows from the speaker's corner (A TL, B TR, C BL, D BR) to half screen, optionally to full, then back and out.
// Children are drawn in card-local pixels (0..CW, 0..CH, overflow visible), so ink props scale and move with the card.
import React from "react";
import {OffthreadVideo, useVideoConfig} from "remotion";
import {useBoil, ramp, clamp01, inOut, vnoise} from "../core";
import {useFrame30, toFps} from "../time30";
import {InkDefs} from "../texture";
import {ThermalFilter} from "../thermal";

export const PIC_W = 860, PIC_H = 920, EDGE = 24;
export const CW = PIC_W + EDGE * 2, CH = PIC_H + EDGE * 2;
const CORNER = {A: 1, B: 2, C: 3, D: 4};
const PAPER = "#EFE7D6", LIFT = "#1C130C";

const backOut = x => x <= 0 ? 0 : 1 + 2.7 * Math.pow(x - 1, 3) + 1.7 * Math.pow(x - 1, 2);

/** Card animation state at local frame f. dur = frames on screen; full = [from, to] local frames for the full-screen push. */
export const cardState = (f, dur, full) => {
  const show = f < dur - 5 ? backOut(ramp(f, 0, 6)) : 1 - ramp(f, dur - 5, dur);
  const grow = inOut(ramp(f, 3, 13)) * (1 - inOut(ramp(f, dur - 12, dur - 3)));
  const fu = full ? inOut(ramp(f, full[0], full[0] + 10)) * (1 - inOut(ramp(f, full[1] - 10, full[1]))) : 0;
  return {show, grow, fu};
};

/** Card-local filters: rough paper edge (re-rolled on the boil clock) and an ink filter whose region follows the prop, not the frame. */
const CardDefs = ({id}) => {
  const s = (useBoil() % 997) + 1;
  return <svg width={0} height={0} style={{position: "absolute"}}>
    <defs>
      <filter id={`oc-rough-${id}`} x="-4%" y="-4%" width="108%" height="108%">
        <feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="2" seed={s} result="n"/>
        <feDisplacementMap in="SourceGraphic" in2="n" scale="9" xChannelSelector="R" yChannelSelector="G"/>
      </filter>
      <ThermalFilter id={`oc-thermal-${id}`} seed={s} noise={0.18}/>
    </defs>
  </svg>;
};

export const OcInkDefs = () => {
  const s = (useBoil() % 997) + 1;
  return <defs>
    <filter id="oc-ink" x="-30%" y="-30%" width="160%" height="160%">
      <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="1" seed={s + 11} result="n"/>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="2.6" xChannelSelector="R" yChannelSelector="G" result="d"/>
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="1" seed={s + 17} result="g"/>
      <feColorMatrix in="g" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  -3.6 0 0 0 3.05" result="m"/>
      <feComposite in="d" in2="m" operator="in"/>
    </filter>
  </defs>;
};

/**
 * Place inside a <Sequence> that spans the card's time on screen (dur frames).
 * src: footage URL (staticFile). videoStart: first frame of the take to use, counted at 30 fps like dur, full and thermal.
 * thermal: [from, to] local frames: the take shows as a heat image first and develops into the warm print over that span.
 */
export const OnCamCard = ({who, src, videoStart = 0, dur, full, thermal, children}) => {
  const f = useFrame30(), b = useBoil(), start = toFps(videoStart, useVideoConfig().fps);
  if (f >= dur) return null;
  const {show, grow, fu} = cardState(f, dur, full);
  const c = CORNER[who], left = c === 1 || c === 3, top = c <= 2;
  const chip = [left ? 182 : 1738, top ? 186 : 894], half = [left ? 490 : 1430, 540], mid = [960, 540];
  const p = [0, 1].map(k => { const v = chip[k] + (half[k] - chip[k]) * grow; return v + (mid[k] - v) * fu; });
  let s = 0.24 + (0.96 - 0.24) * grow; s = (s + (1.08 - s) * fu) * show;
  // a hand put the print down: a slight tilt that settles a little on 2s
  const rot = (left ? -1.1 : 0.9) * (1 - 0.5 * fu) + 0.15 * vnoise(b * 0.4, c * 10);
  return <div style={{position: "absolute", left: p[0] - CW / 2, top: p[1] - CH / 2, width: CW, height: CH,
    transform: `rotate(${rot}deg) scale(${s})`, transformOrigin: "50% 50%", opacity: clamp01(show * 5)}}>
    <CardDefs id={who}/>
    <div style={{position: "absolute", inset: 0, background: PAPER, filter: `url(#oc-rough-${who})`, boxShadow: "0 0 70px rgba(58,36,18,0.55)"}}/>
    <div style={{position: "absolute", left: EDGE, top: EDGE, width: PIC_W, height: PIC_H, overflow: "hidden", background: LIFT}}>
      <OffthreadVideo src={src} startFrom={start} muted
        style={{width: "100%", height: "100%", objectFit: "cover", filter: "sepia(0.22) saturate(1.12) contrast(0.94) brightness(1.03)"}}/>
      {/* warm: orange soft-light wash, blacks lifted to warm brown (a print, not dead black), soft vignette */}
      <div style={{position: "absolute", inset: 0, background: "#FF9A4A", mixBlendMode: "soft-light", opacity: 0.35}}/>
      <div style={{position: "absolute", inset: 0, background: LIFT, mixBlendMode: "lighten"}}/>
      <div style={{position: "absolute", inset: 0, background: "radial-gradient(ellipse at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)"}}/>
      {thermal && f < thermal[1] && <OffthreadVideo src={src} startFrom={start} muted
        style={{position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", filter: `url(#oc-thermal-${who})`,
          opacity: 1 - inOut(ramp(f, thermal[0], thermal[1]))}}/>}
    </div>
    <svg width={CW} height={CH} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
      <InkDefs/>
      <OcInkDefs/>
      {children}
    </svg>
  </div>;
};
