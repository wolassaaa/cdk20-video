// 1-04 v2 (drugs104) · 00:31-00:52 · D VO · 630 f @ 30 fps.
//  A 0-9.6 s   two plinths: a blister pack of tablets in a spotlight ("Nexavar"); on "from Nexavar ..." its light
//              dies and two IV bags whose lines join into one come up ("atezolizumab + bevacizumab"); an arrow
//              draws from the old label to the new one.
//  B 9.6-21 s  ten glass globes lit blood red; a 0 -> 5 years ruler runs and seven go out; three stay lit.
//              "~3 in 10" + "5-year relative survival" + "(HK, 2010-2021)"; then "a huge unmet need."
// Plates: Blender (scene.py in _code/reel2/drugs104), JPEG sequences in public/drugs104/{a,b}.
// On-screen words from script_v3.3 1-04 ("Nexavar → atezolizumab + bevacizumab (first-line, advanced HCC)",
// "5-year relative survival ~3 in 10 (HK, 2010-2021)", "huge unmet need"); "sorafenib", "tablets", "IV infusion"
// and "compared with people of the same age and sex" (script Part 6 note on F22) are added descriptors.
import React from "react";
import {AbsoluteFill, Img, staticFile, useCurrentFrame} from "remotion";
import {ramp, inOut, outExpo, outCubic} from "../../../core";
import {Grain} from "../../../texture";
import {GROT, SERIF, MONO, K, W, H} from "../../s110/lib";
import PA from "./projA.json";
import PB from "./projB.json";

export const DUR_104 = 630;
const NA = 288, NB = 342, CUT = 288;          // A plays 0..287, B plays 288..629
const pad = n => String(n).padStart(4, "0");

const Seq = ({dir, idx, opacity = 1}) => <Img src={staticFile(`drugs104/${dir}/${pad(idx)}.jpg`)}
  style={{position: "absolute", left: 0, top: 0, width: W, height: H, opacity}}/>;

const Txt = ({x, y, size, font = GROT, weight = 300, color = K.ink, ls = 0, align = "left", opacity = 1, italic, children, style}) =>
  <div style={{position: "absolute", top: y, fontFamily: font, fontSize: size, fontWeight: weight, color, letterSpacing: ls,
    lineHeight: 1.05, whiteSpace: "pre", opacity, fontStyle: italic ? "italic" : "normal",
    ...(align === "center" ? {left: x - 800, width: 1600, textAlign: "center"} : align === "right" ? {right: W - x, textAlign: "right"} : {left: x}),
    ...style}}>{children}</div>;

const Mono = p => <Txt font={MONO} weight={400} ls={2} {...p}/>;
const SRC = "SOURCE  ";

// ------------------------------------------------------------------ A: the switch
const SwitchA = ({f}) => {
  const p = PA[Math.min(NA, Math.max(1, f + 1))];
  const xl = p.objL[0], xr = p.objR[0];
  const old = 1 - 0.62 * inOut(ramp(f, 166, 204));                 // "Nexavar" steps back with its light
  const newIn = outCubic(ramp(f, 196, 232));
  const arrow = inOut(ramp(f, 172, 214));
  const head = ramp(f, 4, 26), lab = ramp(f, 14, 40);
  const ax0 = xl + 175, ax1 = xr - 250, ay = 958;
  return <>
    <Mono x={110} y={92} size={15} ls={3} opacity={0.72 * head}>(first-line, advanced HCC)</Mono>
    {/* left label */}
    <div style={{opacity: lab * old}}>
      <Mono x={xl} y={902} size={13} ls={4} align="center" opacity={0.55}>BEFORE</Mono>
      <Txt x={xl} y={924} size={64} align="center" ls={-1}>Nexavar</Txt>
      <Mono x={xl} y={1002} size={13} align="center" opacity={0.55}>sorafenib · tablets</Mono>
    </div>
    {/* arrow */}
    <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
      <line x1={ax0} y1={ay} x2={ax0 + (ax1 - ax0) * arrow} y2={ay} stroke={K.ink} strokeWidth={2} opacity={0.85}/>
      {arrow > 0.97 ? <path d={`M${ax1 - 16},${ay - 9} L${ax1},${ay} L${ax1 - 16},${ay + 9}`} fill="none" stroke={K.ink} strokeWidth={2} opacity={0.85}/> : null}
    </svg>
    {/* right label */}
    <div style={{opacity: newIn, transform: `translateY(${(1 - newIn) * 14}px)`}}>
      <Mono x={xr} y={902} size={13} ls={4} align="center" opacity={0.6}>NOW</Mono>
      <Txt x={xr} y={924} size={50} align="center" ls={-0.5} weight={400}>atezolizumab</Txt>
      <Txt x={xr} y={978} size={50} align="center" ls={-0.5} weight={400}><span style={{color: K.verm}}>+</span> bevacizumab</Txt>
      <Mono x={xr} y={1044} size={13} align="center" opacity={0.6}>IV infusion</Mono>
    </div>
    <Mono x={1810} y={92} size={11} ls={1.2} align="right" opacity={0.45 * head}>{SRC}Ren et al., Chem. Sci. 2023</Mono>
  </>;
};

// ------------------------------------------------------------------ B: ten lights, seven go out
const LIT = [1, 4, 8];
const OUTS = [[6, 30], [0, 44], [9, 58], [3, 74], [7, 92], [2, 114], [5, 140]];   // = scene.py OUT (Blender frame)
const SurvivalB = ({b}) => {               // b = local frame inside B (0..341); Blender frame = b + 1
  const p = PB[Math.min(NB, Math.max(1, b + 1))];
  const rIn = ramp(b, 6, 24), run = ramp(b, 24, 156);                // ruler: year 0 -> 5 over the seven outs
  const num = outExpo(ramp(b, 150, 176)), sub = ramp(b, 166, 192);
  const unmet = outCubic(ramp(b, 196, 236));
  const dimStat = 1 - 0.25 * ramp(b, 196, 236);
  const rx0 = 760, rx1 = 1160, ry = 704;
  // three survivors get a fine red tick under them once the count is done
  const gy = p.g0[1];
  return <>
    {/* ruler */}
    <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0, opacity: rIn * (1 - 0.6 * unmet)}}>
      <line x1={rx0} y1={ry} x2={rx1} y2={ry} stroke={K.ink} strokeOpacity={0.25} strokeWidth={1.5}/>
      <line x1={rx0} y1={ry} x2={rx0 + (rx1 - rx0) * run} y2={ry} stroke={K.ink} strokeOpacity={0.85} strokeWidth={1.5}/>
      {[0, 1, 2, 3, 4, 5].map(i => <line key={i} x1={rx0 + (rx1 - rx0) * i / 5} y1={ry - 5} x2={rx0 + (rx1 - rx0) * i / 5} y2={ry + 5}
        stroke={K.ink} strokeOpacity={run >= i / 5 ? 0.8 : 0.3} strokeWidth={1.5}/>)}
      <circle cx={rx0 + (rx1 - rx0) * run} cy={ry} r={5} fill={K.ink}/>
    </svg>
    <Mono x={rx0} y={ry + 16} size={12} align="center" opacity={0.55 * rIn * (1 - 0.6 * unmet)}>0</Mono>
    <Mono x={rx1} y={ry + 16} size={12} align="center" opacity={0.55 * rIn * (1 - 0.6 * unmet)}>5 years</Mono>
    <Mono x={rx0 + (rx1 - rx0) * run} y={ry - 30} size={12} align="center" opacity={0.8 * rIn * (1 - ramp(b, 156, 170))}>
      {`year ${(5 * run).toFixed(1)}`}</Mono>

    {/* a light that has gone out: drain the red the glass still picks up from its neighbours */}
    {OUTS.map(([i, f0]) => { const k = inOut(ramp(b, f0 - 1, f0 + 20)); if (k <= 0) return null;
      const [x, y] = p[`g${i}`], r = (p.g1[0] - p.g0[0]) * 0.105 / 0.29 * 1.04;
      return <React.Fragment key={i}>
        <div style={{position: "absolute", left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: "50%",
          background: "#7d7d7d", mixBlendMode: "saturation", opacity: 0.8 * k}}/>
        <div style={{position: "absolute", left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: "50%",
          background: "radial-gradient(circle, rgba(6,6,6,0.6) 0%, rgba(6,6,6,0.45) 70%, rgba(6,6,6,0) 100%)", opacity: k}}/>
      </React.Fragment>; })}
    {/* survivor ticks */}
    <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0, opacity: sub}}>
      {LIT.map(i => { const [x, y] = p[`g${i}`]; return <line key={i} x1={x - 22} y1={gy + 118} x2={x + 22} y2={gy + 118} stroke={K.verm} strokeWidth={3}/>; })}
    </svg>

    {/* the number */}
    <div style={{opacity: num * dimStat}}>
      <Txt x={W / 2} y={790} size={150} weight={800} ls={-6} align="center"
        style={{transform: `translateY(${(1 - num) * 20}px)`}}><span style={{color: K.verm}}>~3</span> in 10</Txt>
    </div>
    <div style={{opacity: sub * dimStat}}>
      <Mono x={W / 2} y={960} size={17} ls={3} align="center" opacity={0.9}>5-year relative survival</Mono>
      <Mono x={W / 2} y={990} size={12} ls={1.5} align="center" opacity={0.55}>(HK, 2010-2021)  ·  compared with people of the same age and sex</Mono>
    </div>
    <Mono x={110} y={1036} size={11} ls={1.2} opacity={0.45 * rIn}>
      {SRC}Hong Kong Cancer Registry, Hospital Authority{unmet > 0.5 ? "  ·  Ren et al., Chem. Sci. 2023" : ""}</Mono>
    <Mono x={1810} y={1036} size={11} ls={2.5} align="right" opacity={0.45 * rIn}>ILLUSTRATIVE</Mono>

    {/* unmet need */}
    <Txt x={W / 2} y={190} size={104} font={SERIF} weight={400} italic align="center" opacity={unmet}
      style={{transform: `translateY(${(1 - unmet) * 16}px)`}}>a huge unmet need.</Txt>
  </>;
};

export const Beat104 = () => {
  const f = useCurrentFrame();
  const b = f - CUT;
  const aOp = 1 - ramp(f, CUT - 14, CUT), bOp = ramp(f, CUT, CUT + 16);    // short dip through black
  return <AbsoluteFill style={{background: K.bg, overflow: "hidden"}}>
    {f < CUT ? <div style={{opacity: aOp}}>
      <Seq dir="a" idx={Math.min(NA, f + 1)}/>
      <SwitchA f={f}/>
    </div> : <div style={{opacity: bOp}}>
      <Seq dir="b" idx={Math.min(NB, b + 1)}/>
      <SurvivalB b={b}/>
    </div>}
    <AbsoluteFill style={{pointerEvents: "none", background: "radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)"}}/>
    <Grain opacity={0.12}/>
  </AbsoluteFill>;
};
