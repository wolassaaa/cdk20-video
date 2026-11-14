// HKBU SCIE1007 coursework video: on-camera layout v1 test (1-04 tail -> 1-05 D -> 1-06 B -> 1-07 C -> 1-08 head).
// Rules: 镜头设计_v3/script/出镜新版式_v1.md. 1080p30 preview. Media are 1080p30 copies in public/oncam2/.
import React from "react";
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile, useCurrentFrame, delayRender, continueRender} from "remotion";
import {vnoise, clamp01, ramp, outCubic, inOut, handLine} from "../core";
import {InkPath, InkLine} from "../ink";

const W = 1920, H = 1080;
const INK = "#111113", RED = "#E8190F", CYAN = "#0E8C9A"; // fusion animation colours (s5c.jsx / s6.jsx)
const SERIF = "Instrument Serif";
const faces = [new FontFace(SERIF, `url(${staticFile("oncam2/fonts/InstrumentSerif-Regular.ttf")})`)];
const fontHandle = delayRender("oncam2 fonts");
Promise.all(faces.map(f => f.load())).then(l => { l.forEach(f => document.fonts.add(f)); continueRender(fontHandle); });

// ---- edit (global frames) ----
const A_LEN = 90;                          // 1-04 last 3 s
const D_IN = 0, D_OUT = 100;               // "one?" ends 3.238 s = 97.1 f -> cut +3 f
const B_IN = 9, B_OUT = 74;                // "sounds." ends 2.337 s = 70.1 f
const C_IN = 9, C_OUT = 110;               // full tail, ink leaves during "hard."
const T_D = A_LEN, T_B = T_D + (D_OUT - D_IN), T_C = T_B + (B_OUT - B_IN), T_E = T_C + (C_OUT - C_IN);
const IN_LEN = 15, OUT_LEN = 21;           // 0.5 s in, 0.7 s out
const T_OUT = T_E - OUT_LEN;
export const ONCAM2_V1_FRAMES = T_E + 90;

// short volume ramps at every cut so the hard cuts do not click
const edgeVol = (len, k = 2) => f => Math.min(1, (f + 1) / k, (len - f) / k);

// ---- wet ink edge ----
// side "right": ink occupies x > edge (comes from the right). progress 0..1 = how far the edge has travelled across.
const inkPoly = (edgeX, fromRight, t) => {
  const pts = [];
  for (let y = -40; y <= H + 40; y += 12) {
    const n = 70 * vnoise(y / 160, 11) + 28 * vnoise(y / 45 + t * 0.15, 23) + 10 * vnoise(y / 14, 37);
    pts.push([edgeX + (fromRight ? -n : n), y]);
  }
  const far = fromRight ? W + 400 : -400;
  return [[far, -40], ...pts, [far, H + 40]];
};
const toD = pts => "M" + pts.map(p => p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" L") + " Z";

const InkDefs = ({id, seed}) => <defs>
  <filter id={id} x="-10%" y="-10%" width="120%" height="120%">
    <feTurbulence type="fractalNoise" baseFrequency="0.035 0.05" numOctaves="3" seed={seed} result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="38" xChannelSelector="R" yChannelSelector="G"/>
  </filter>
  <filter id={id + "-bleed"} x="-10%" y="-10%" width="120%" height="120%">
    <feTurbulence type="fractalNoise" baseFrequency="0.09" numOctaves="2" seed={seed + 5} result="n"/>
    <feDisplacementMap in="SourceGraphic" in2="n" scale="70" xChannelSelector="R" yChannelSelector="G" result="d"/>
    <feGaussianBlur in="d" stdDeviation="10"/>
  </filter>
</defs>;

/** Ink sheet. Renders the ink body, a softer bleed fringe running ahead of it, and a darker wet rim. */
const InkSheet = ({edgeX, fromRight, t, id, seed}) => {
  const lead = fromRight ? -1 : 1;
  const body = toD(inkPoly(edgeX, fromRight, t));
  const bleed = toD(inkPoly(edgeX + lead * 52, fromRight, t + 7));
  const wash = toD(inkPoly(edgeX + lead * 22, fromRight, t + 3));
  return <svg width={W} height={H} style={{position: "absolute", inset: 0}}>
    <InkDefs id={id} seed={seed}/>
    <path d={bleed} fill={INK} opacity={0.22} filter={`url(#${id}-bleed)`}/>
    <path d={wash} fill={INK} opacity={0.42} filter={`url(#${id}-bleed)`}/>
    <path d={body} fill={INK} filter={`url(#${id})`}/>
    <path d={toD(inkPoly(edgeX, fromRight, t))} fill="none" stroke="#000" strokeWidth={9} opacity={0.55} filter={`url(#${id})`}/>
  </svg>;
};

// ---- motion side ----
const enter = (f, t0, len = 10) => outCubic(ramp(f, t0, t0 + len));
const Word = ({x, y, size, f, t0, children, anchor = "start"}) => {
  const k = enter(f, t0);
  if (k <= 0) return null;
  return <text x={x} y={y + (1 - k) * 26} fontFamily={SERIF} fontSize={size} fill={INK} opacity={k} textAnchor={anchor}>{children}</text>;
};

// 1-05: D on the right, motion on the left. Net zone x 0.07-0.47 W, y 0.275-0.725 H.
const G105 = ({f}) => <svg width={W} height={H} style={{position: "absolute", inset: 0}}>
  <Word x={150} y={560} size={132} f={f} t0={74}>a better</Word>
  <Word x={150} y={700} size={132} f={f} t0={86}>one?</Word>
</svg>;

// 1-06: B on the left, motion on the right. Net zone x 0.53-0.93 W.
const G106 = ({f}) => {
  const out = 1 - ramp(f, 64, 72);
  return <svg width={W} height={H} style={{position: "absolute", inset: 0, opacity: out}}>
    <Word x={1110} y={560} size={150} f={f} t0={27}>way harder</Word>
    <InkPath points={handLine([1105, 600], [1700, 590], {bow: 5, over: 6})} seed={61} size={11} color={RED}
      progress={outCubic(ramp(f, 37, 48))} pressure="marker"/>
  </svg>;
};

// 1-07: C on the left. Ink timeline 10-17 years drawn on "ten-to-seventeen".
const TL = {x0: 1060, x1: 1740, y: 600};
const Timeline = ({f, thin}) => {
  const L = TL.x1 - TL.x0, d = thin ? 1 : outCubic(ramp(f, 0, 11));
  const col = thin ? CYAN : INK, sz = thin ? 3 : 7;
  return <g>
    <InkPath points={handLine([TL.x0, TL.y], [TL.x1, TL.y - 6], {bow: -4, over: 3})} seed={100} size={sz} progress={d} color={col} pressure="nib"/>
    {Array.from({length: 17}, (_, i) => {
      const tx = TL.x0 + L * (i + 1) / 17.4, late = i >= 9;
      if (tx > TL.x0 + L * d) return null;
      const h = late ? 22 : 13;
      return <InkLine key={i} from={[tx, TL.y - h]} to={[tx, TL.y + h]} seed={110 + i} size={thin ? 2 : (late ? 5 : 3.5)} color={thin ? CYAN : (late ? RED : INK)} pressure="marker"/>;
    })}
    {!thin && <InkPath points={[[TL.x0 + L * 10 / 17.4, TL.y - 44], [TL.x0 + L * 10 / 17.4, TL.y - 58], [TL.x0 + L * 17 / 17.4, TL.y - 60], [TL.x0 + L * 17 / 17.4, TL.y - 46]]}
      seed={130} size={5} color={RED} progress={outCubic(ramp(f, 24, 34))} pressure="marker"/>}
  </g>;
};
const G107 = ({f, coverPoly}) => {
  const lf = f - 35;                 // clip frame: draw starts 5 f before "ten" (40.4 f)
  if (lf < 0) return null;
  const k = enter(lf, 12);
  const label = <text x={(TL.x0 + TL.x1) / 2 + 40} y={TL.y - 90} fontFamily={SERIF} fontSize={120} fill={INK} textAnchor="middle"
    opacity={k} transform={`translate(0 ${(1 - k) * 26})`}>10–17 years</text>;
  return <svg width={W} height={H} style={{position: "absolute", inset: 0}}>
    <defs>
      <clipPath id="tl-dry"><path d={coverPoly ? coverPoly.dry : `M0 0 H${W} V${H} H0 Z`}/></clipPath>
      <clipPath id="tl-wet"><path d={coverPoly ? coverPoly.wet : "M0 0 Z"}/></clipPath>
    </defs>
    <g clipPath="url(#tl-dry)"><Timeline f={lf}/>{label}</g>
  </svg>;
};
// the cyan thin line drawn on top of the ink where the ink has passed over the timeline
const CyanLine = ({wetD, opacity = 1}) => <svg width={W} height={H} style={{position: "absolute", inset: 0, opacity}}>
  <defs><clipPath id="tl-wet2"><path d={wetD}/></clipPath></defs>
  <g clipPath="url(#tl-wet2)"><Timeline f={99} thin/></g>
</svg>;

export const V3OnCam2TestV1 = () => {
  const f = useCurrentFrame();
  // ink in (animation -> on-cam): starts full, recedes from the person side (right, D) toward the motion side (left)
  const inP = inOut(ramp(f, T_D, T_D + IN_LEN));
  const inEdge = 2050 - inP * 2300;          // ink occupies x < edge
  const preDark = ramp(f, A_LEN - 5, A_LEN);  // 1-04 dissolves into the ink just before the cut
  // ink out (on-cam -> animation): from the motion side (right) toward C on the left
  const outP = inOut(ramp(f, T_OUT, T_E));
  const outEdge = 2080 - outP * 2350;        // ink occupies x > edge
  const outT = f - T_OUT;
  const wetD = toD(inkPoly(outEdge, true, outT));
  const dryD = toD(inkPoly(outEdge, true, outT).map(([x, y], i, a) => i === 0 || i === a.length - 1 ? [-400, y] : [x, y]));
  const postDark = 1 - ramp(f, T_E + 2, T_E + 8); // ink lifts off 1-08 placeholder (rough cut is pale paper)

  return <AbsoluteFill style={{background: "#EAEAE1"}}>
    <Sequence from={0} durationInFrames={A_LEN}>
      <OffthreadVideo src={staticFile("oncam2/a104.mp4")} volume={edgeVol(A_LEN, 4)}/>
    </Sequence>
    <Sequence from={T_D} durationInFrames={D_OUT - D_IN}>
      <OffthreadVideo src={staticFile("oncam2/D_cam_1-05.mp4")} startFrom={D_IN} volume={edgeVol(D_OUT - D_IN)}/>
      <Inner render={lf => <G105 f={lf}/>}/>
    </Sequence>
    <Sequence from={T_B} durationInFrames={B_OUT - B_IN}>
      <OffthreadVideo src={staticFile("oncam2/B_cam_1-06.mp4")} startFrom={B_IN} volume={edgeVol(B_OUT - B_IN)}/>
      <Inner render={lf => <G106 f={lf + B_IN}/>}/>
    </Sequence>
    <Sequence from={T_C} durationInFrames={C_OUT - C_IN}>
      <OffthreadVideo src={staticFile("oncam2/C_cam_1-07.mp4")} startFrom={C_IN} volume={edgeVol(C_OUT - C_IN, 3)}/>
      <Inner render={lf => <G107 f={lf + C_IN} coverPoly={f >= T_OUT ? {dry: dryD, wet: wetD} : null}/>}/>
    </Sequence>
    <Sequence from={T_E} durationInFrames={90}>
      <OffthreadVideo src={staticFile("oncam2/a108.mp4")} volume={edgeVol(90, 4)}/>
    </Sequence>

    {preDark > 0 && f < T_D && <AbsoluteFill style={{background: INK, opacity: preDark}}/>}
    {f >= T_D && f < T_D + IN_LEN && <InkSheet edgeX={inEdge} fromRight={false} t={f - T_D} id="ink-in" seed={4}/>}
    {f >= T_OUT && f < T_E && <InkSheet edgeX={outEdge} fromRight t={outT} id="ink-out" seed={9}/>}
    {f >= T_E && postDark > 0 && <AbsoluteFill style={{background: INK, opacity: postDark}}/>}
    {/* prop hand-off: under the ink the timeline becomes a thin cyan line, which carries into 1-08 */}
    {f >= T_OUT && f < T_E && <CyanLine wetD={wetD}/>}
    {f >= T_E && f < T_E + 60 && <CyanLine wetD={`M-10 -10 H${W + 10} V${H + 10} H-10 Z`} opacity={1 - ramp(f, T_E + 52, T_E + 60)}/>}
  </AbsoluteFill>;
};

const Inner = ({render}) => render(useCurrentFrame());
