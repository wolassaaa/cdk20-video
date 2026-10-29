// 1-11 options: Hong Kong, one red line from Sha Tin to Pak Shek Kok.
import React from "react";
import {AbsoluteFill} from "remotion";
import {Plate, T, Tag, Credit, Finish, K, GROT, SERIF, MONO, OSM_CREDIT, W, H} from "./lib";
import LAND from "./hk_land.json";
import PK from "./m_klein.json";
import PT from "./m_thread.json";
import PB from "./m_bluesea.json";
import PBC from "./m_bluesea_close.json";

// a label with a hairline leader
const Pin = ({at, dx = 40, dy = -40, title, sub, color = K.ink, line = "rgba(237,235,228,0.6)", anchor = "left"}) => {
  const [x, y] = at, lx = x + dx, ly = y + dy;
  return <>
    <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
      <line x1={x} y1={y} x2={lx} y2={ly} stroke={line} strokeWidth={1}/>
      <circle cx={x} cy={y} r={3} fill={color}/>
    </svg>
    <T x={anchor === "left" ? lx + 8 : lx - 8} y={ly - 10} size={15} ls={3} color={color} anchor={anchor} weight={700}>{title}</T>
    {sub ? <T x={anchor === "left" ? lx + 8 : lx - 8} y={ly + 10} size={11} ls={1.5} color={K.dim} anchor={anchor}>{sub}</T> : null}
  </>;
};
const PINS = (P, o = {}) => <>
  <Pin at={P.pwh} dx={o.adx ?? -60} dy={o.ady ?? 40} anchor="right" title="SHA TIN" sub="Prince of Wales Hospital · CUHK"/>
  <Pin at={P.hkstp} dx={o.bdx ?? -60} dy={o.bdy ?? -40} anchor="right" title="PAK SHEK KOK" sub="Hong Kong Science Park"/>
</>;

// 1. Klein relief: Hong Kong in one blue pigment, a glossy red cord (Yves Klein, Relief planetaire RP 17, Nice)
export const M1Klein = () => <AbsoluteFill style={{background: K.bg}}>
  <Plate src="m_klein.png"/>
  {PINS(PK)}
  <T x={96} y={84} size={92} font={GROT} weight={800} ls={-3} color={K.ink}>Hong Kong</T>
  <T x={100} y={190} size={13} ls={3} color={K.ink}>22.38°N 114.20°E → 22.43°N 114.21°E</T>
  <Credit x={96} y={1032} color="rgba(237,235,228,0.75)">{OSM_CREDIT}</Credit>
  <Finish grain={0.14} vignette={0.35}/>
</AbsoluteFill>;

// 2. Red thread (Chiharu Shiota): coast as bone wire on black felt, one red thread pinned between two places
export const M2Thread = () => <AbsoluteFill style={{background: K.bg}}>
  <Plate src="m_thread.png"/>
  {PINS(PT, {adx: -80, ady: 60, bdx: -90, bdy: -70})}
  <T x={96} y={90} size={14} ls={4} color={K.dim}>PART OF IT STARTS HERE</T>
  <T x={96} y={114} size={44} font={SERIF} color={K.ink}>Sha Tin → Pak Shek Kok</T>
  <Credit x={96} y={1032}>{OSM_CREDIT}</Credit>
  <Tag/>
  <Finish grain={0.18} vignette={0.3}/>
</AbsoluteFill>;

// 3. Blue sea, black land, one red vessel line (two frames: whole territory, then the close-up)
export const M3Blue = ({part = "a"}) => {
  const P = part === "a" ? PB : PBC;
  return <AbsoluteFill style={{background: K.bg}}>
    <Plate src={part === "a" ? "m_bluesea.png" : "m_bluesea_close.png"}/>
    {part === "a" ? <>
      <T x={96} y={86} size={120} font={GROT} weight={900} ls={-5} color={K.ink}>HONG KONG</T>
      {PINS(P, {adx: -70, ady: 80, bdx: -80, bdy: -60})}
    </> : <>
      {PINS(P, {adx: -120, ady: 60, bdx: -140, bdy: 70})}
      <T x={1824} y={950} size={13} ls={3} anchor="right" color={K.ink}>≈ 5 KM</T>
    </>}
    <Credit x={96} y={1032} color="rgba(237,235,228,0.8)">{OSM_CREDIT}</Credit>
    <Finish grain={0.16} vignette={0.25}/>
  </AbsoluteFill>;
};

// 4. Coordinates (On Kawara / Richard Long): hairline coast, one red line, the place said as numbers
const proj = (x0, y0, x1, y1, box) => {
  const [bx, by, bw, bh] = box;
  const s = Math.min(bw / (x1 - x0), bh / (y1 - y0));
  return p => [bx + (p[0] - x0) * s, by + bh - (p[1] - y0) * s];
};
export const M4Coord = () => {
  const pr = proj(-14000, -9000, 20000, 13000, [520, 110, 1300, 860]);
  const d = LAND.rings.map(r => "M" + r.p.map(q => pr(q).map(v => v.toFixed(1)).join(",")).join("L") + "Z").join("");
  const rt = LAND.route.map(q => pr(q));
  const a = pr(LAND.poi.pwh), b = pr(LAND.poi.hkstp);
  return <AbsoluteFill style={{background: K.bg}}>
    <svg width={W} height={H} style={{position: "absolute"}}>
      <defs><clipPath id="c4"><rect x={470} y={80} width={1400} height={900}/></clipPath></defs>
      <path d={d} fill="none" stroke="rgba(237,235,228,0.62)" strokeWidth={1} clipPath="url(#c4)"/>
      <polyline points={rt.map(p => p.join(",")).join(" ")} fill="none" stroke={K.verm} strokeWidth={6} strokeLinecap="round"/>
      <circle cx={a[0]} cy={a[1]} r={5} fill={K.verm}/><circle cx={b[0]} cy={b[1]} r={5} fill={K.verm}/>
    </svg>
    <T x={96} y={150} size={13} ls={3} color={K.dim}>FROM</T>
    <T x={96} y={174} size={40} font={MONO} weight={700}>22.38°N</T>
    <T x={96} y={222} size={40} font={MONO} weight={700}>114.20°E</T>
    <T x={96} y={278} size={13} ls={2} color={K.ink}>SHA TIN</T>
    <T x={96} y={360} size={13} ls={3} color={K.dim}>TO</T>
    <T x={96} y={384} size={40} font={MONO} weight={700} color={K.verm}>22.43°N</T>
    <T x={96} y={432} size={40} font={MONO} weight={700} color={K.verm}>114.21°E</T>
    <T x={96} y={488} size={13} ls={2} color={K.ink}>PAK SHEK KOK</T>
    <T x={96} y={940} size={13} ls={3} color={K.dim}>HONG KONG</T>
    <Credit x={96} y={1032}>{OSM_CREDIT}</Credit>
    <Finish grain={0.2} vignette={0}/>
  </AbsoluteFill>;
};

export const OPTIONS_111 = [
  {id: "S111o1", C: M1Klein}, {id: "S111o2", C: M2Thread}, {id: "S111o3a", C: M3Blue, p: {part: "a"}}, {id: "S111o3b", C: M3Blue, p: {part: "b"}},
  {id: "S111o4", C: M4Coord},
];
