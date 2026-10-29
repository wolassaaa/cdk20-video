// 1-02 (00:08–00:25, A VO) style frames. "That's 1,412 people in 2022 alone. ... one of the three deadliest cancers,
// alongside lung and colorectal. ... Worldwide, it's the sixth most common cancer, and the third deadliest."
// On-screen strings follow script_v3.3 1-02 Visual: "1,412 deaths in Hong Kong, 2022" /
// "Top 3 deadliest in HK: lung · colorectal · liver" / "World: 6th most common · 3rd deadliest".
import React, {useMemo} from "react";
import {AbsoluteFill, Img, staticFile} from "remotion";
import {C, W, H, hash, BoilProvider} from "../../core";
import {InkPath} from "../../ink";
import {InkDefs} from "../../texture";
import {SANS, GM, BLUE, IKB, BONE, RED, BG, SRC_HK, SRC_WORLD, T, Src, Tag, PrintGrain, Vignette, Svg} from "./lib";
import LAND from "./land.json";

const Frame = ({bg = BG, children}) => <BoilProvider frozen><AbsoluteFill style={{background: bg, overflow: "hidden"}}>{children}</AbsoluteFill></BoilProvider>;

// ------------------------------------------------------------------ opt1 tally: 1,412 hand-counted marks
const N = 1412;
export const Opt1Tally = ({count = N}) => {
  // 283 groups = 9 full rows of 31 + 4 on the last row; the type takes the rest of that row
  const COLS = 31, PX = 57, PY = 80, X0 = 78, Y0 = 44, GW = 36, GH = 50;
  const groups = Math.ceil(count / 5);
  const strokes = [];
  for (let g = 0; g < groups; g++) {
    const r = Math.floor(g / COLS), c = g % COLS;
    const x = X0 + c * PX, y = Y0 + r * PY;
    const n = Math.min(5, count - g * 5);
    const last = g === groups - 1;
    for (let k = 0; k < n; k++) {
      const j = i => (hash(g * 7 + k, i, 5) - 0.5);
      const pts = k < 4
        ? [[x + k * (GW / 3.2) + j(1) * 4, y + j(2) * 6], [x + k * (GW / 3.2) + j(3) * 6, y + GH + j(4) * 6]]
        : [[x - 6 + j(1) * 4, y + GH * 0.78 + j(2) * 8], [x + GW + 4 + j(3) * 4, y + GH * 0.18 + j(4) * 8]];
      strokes.push(<InkPath key={`${g}-${k}`} points={pts} seed={g * 5 + k + 1} size={k < 4 ? 3.6 : 3.2} jitter={0.8} pressure="nib"
        color={last ? RED : BONE} opacity={last ? 1 : 0.86} boil={false}/>);
    }
  }
    return <Frame>
    <Svg>
      <InkDefs/>
      <g filter="url(#v3-ink)">{strokes}</g>
      <T x={X0 - 8} y={990} size={190} weight={200} ls={-7}>1,412</T>
      <T x={X0 + 478} y={990} size={36} weight={300} opacity={0.9}>deaths in Hong Kong, 2022</T>
      <Src x={1840} y={1050} anchor="end">{SRC_HK}</Src>
    </Svg>
    <PrintGrain amount={0.3}/>
  </Frame>;
};

// ------------------------------------------------------------------ opt2 liver: BodyParts3D glass liver, red vs blue
export const Opt2Liver = ({line = "hk", img = "liver_rb_full.png", xf = "translate(400px, 0px) scale(0.9)", fade = 48}) => <Frame bg="#000">
  <Img src={staticFile(img)} style={{position: "absolute", left: 0, top: 0, width: W, height: H,
    transform: xf, transformOrigin: "50% 50%"}}/>
  <AbsoluteFill style={{background: `linear-gradient(90deg, rgba(6,6,6,0.92) 0%, rgba(6,6,6,0.6) ${fade * 0.62}%, rgba(6,6,6,0) ${fade}%)`}}/>
  <Svg>
    {line === "hk" ? <>
      <T x={92} y={560} size={250} weight={100} ls={-10}>1,412</T>
      <T x={104} y={630} size={42} weight={300}>deaths in Hong Kong, 2022</T>
      <rect x={106} y={662} width={64} height={3} fill={RED}/>
      <Src>{SRC_HK}</Src>
    </> : <>
      <T x={104} y={400} size={30} weight={400} font={GM} ls={4} opacity={0.75}>World:</T>
      <T x={92} y={560} size={170} weight={100} ls={-6}>6<tspan fontSize={72} dy={-74}>th</tspan></T>
      <T x={268} y={560} size={44} weight={300}>most common</T>
      <T x={92} y={760} size={170} weight={100} ls={-6} color={RED}>3<tspan fontSize={72} dy={-74}>rd</tspan></T>
      <T x={268} y={760} size={44} weight={300}>deadliest</T>
      <Src>{SRC_WORLD}</Src>
    </>}
    <T x={1840} y={1036} size={13} weight={400} font={GM} anchor="end" opacity={0.5} ls={1}>LIVER + VESSELS: BODYPARTS3D © DBCLS, CC BY 4.0 · RED PORTAL VEIN + HEPATIC ARTERY · BLUE HEPATIC VEINS</T>
  </Svg>
  <PrintGrain amount={0.26}/>
</Frame>;

// ------------------------------------------------------------------ opt3 year: 2022 as a calendar, about four marks a day
const DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
const MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
export const Opt3Year = () => {
  // 1,412 = 365 x 3 + 317: 317 days carry four marks, 48 carry three (spread evenly). Schematic, not daily data.
  const order = useMemo(() => Array.from({length: 365}, (_, i) => [hash(i, 2022), i]).sort((a, b) => a[0] - b[0]).map(e => e[1]), []);
  const three = new Set(order.slice(0, 365 - 317));
  const X0 = 600, Y0 = 250, PX = 39.5, PY = 50, d = 13.5, r = 5.2;
  const dots = [];
  let doy = 0, total = 0;
  DAYS.forEach((n, m) => {
    for (let day = 0; day < n; day++, doy++) {
      const cx = X0 + day * PX, cy = Y0 + m * PY;
      const lit = three.has(doy) ? 3 : 4;
      for (let k = 0; k < 4; k++) {
        const x = cx + (k % 2) * d, y = cy + Math.floor(k / 2) * d;
        if (k < lit) { dots.push(<circle key={`${doy}-${k}`} cx={x} cy={y} r={r} fill={RED}/>); total++; }
        else dots.push(<circle key={`${doy}-${k}`} cx={x} cy={y} r={r} fill="none" stroke={BONE} strokeWidth={1} opacity={0.4}/>);
      }
    }
  });
  if (total !== N) throw new Error("dot count " + total);
  return <Frame>
    <Svg>
      {MON.map((m, i) => <T key={m} x={X0 - 34} y={Y0 + i * PY + 12} size={14} font={GM} weight={400} anchor="end" opacity={0.55} ls={2}>{m}</T>)}
      {Array.from({length: 31}, (_, i) => (i + 1) % 5 === 0 || i === 0 ? <T key={i} x={X0 + i * PX + d / 2} y={Y0 - 30} size={12} font={GM} anchor="middle" opacity={0.4}>{i + 1}</T> : null)}
      {dots}
      <T x={92} y={560} size={170} weight={100} ls={-7}>1,412</T>
      <T x={98} y={622} size={34} weight={300}>deaths in Hong Kong, 2022</T>
      <T x={X0 - 34} y={Y0 + 12 * PY + 30} size={14} font={GM} opacity={0.55} ls={1.5}>ONE DOT = ONE DEATH · 1,412 ÷ 365 ≈ 3.9 A DAY · PLACED EVENLY, NOT DAILY DATA</T>
      <Src>{SRC_HK}</Src>
      <Tag>SCHEMATIC</Tag>
    </Svg>
    <PrintGrain amount={0.24}/>
  </Frame>;
};

// ------------------------------------------------------------------ opt4 ikeda: 1,412 hairlines, one per person; data as a test pattern
export const Opt4Ikeda = ({focus = 0}) => {
  const X0 = 0, X1 = W, Y0 = 0, Y1 = 640, step = (X1 - X0) / N;
  let d = "", dr = "";
  for (let i = 0; i < N; i++) {
    const x = X0 + i * step, w = hash(i, 11) < 0.5 ? 0.5 : (hash(i, 12) < 0.8 ? 1 : 2);
    const seg = `M${x.toFixed(2)},${Y0}h${w}v${Y1 - Y0}h${-w}z`;
    if (i >= N - 4) dr += seg; else d += seg;
  }
  const ticks = [];
  for (let i = 0; i <= N; i += 10) {
    const major = i % 100 === 0, x = X0 + i * step;
    ticks.push(<rect key={i} x={x} y={Y1 + 6} width={1} height={major ? 16 : 5} fill={BONE}/>);
    if (major) ticks.push(<T key={"t" + i} x={x + 4} y={Y1 + 36} size={11} font={GM} opacity={0.75}>{String(i).padStart(4, "0")}</T>);
  }
  const L = ["1,412 deaths in Hong Kong, 2022", "Top 3 deadliest in HK: lung · colorectal · liver", "World: 6th most common · 3rd deadliest"];
  return <Frame bg="#000">
    <Svg>
      <path d={d} fill="#fff"/>
      <path d={dr} fill={RED}/>
      <rect x={W - 4 * step - 1} y={Y1} width={4 * step + 2} height={110} fill={RED}/>
      {ticks}
      <T x={80} y={790} size={14} font={GM} ls={3} opacity={0.8}>{`0${focus + 1} / 03`}</T>
      <T x={76} y={870} size={64} font={GM} weight={300} ls={-1}>{L[focus]}</T>
      {L.map((l, i) => i === focus ? null : <T key={i} x={80} y={930 + (i > focus ? i - 1 : i) * 24} size={14} font={GM} opacity={0.4} ls={1}>{`0${i + 1}  ${l}`}</T>)}
      <T x={1840} y={790} size={14} font={GM} ls={3} anchor="end" color={RED}>N = 1412 · 1 LINE = 1 PERSON · RED = ~1 DAY</T>
      <Src y={1036} x={1840} anchor="end">{focus === 2 ? SRC_WORLD : SRC_HK}</Src>
    </Svg>
  </Frame>;
};

// ------------------------------------------------------------------ opt5 globe: dot-matrix Earth turned to Hong Kong, world ranks
const LAT0 = 22.3 * Math.PI / 180, LON0 = 114.17 * Math.PI / 180;
const ortho = (lat, lon, R, cx, cy) => {
  const p = lat * Math.PI / 180, l = lon * Math.PI / 180 - LON0;
  const cosc = Math.sin(LAT0) * Math.sin(p) + Math.cos(LAT0) * Math.cos(p) * Math.cos(l);
  return [cx + R * Math.cos(p) * Math.sin(l), cy - R * (Math.cos(LAT0) * Math.sin(p) - Math.sin(LAT0) * Math.cos(p) * Math.cos(l)), cosc];
};
export const Opt5Globe = ({R = 600, cx = 1360, cy = 560}) => {
  let d = "";
  for (const [la, lo] of LAND) {
    const [x, y, c] = ortho(la, lo, R, cx, cy);
    if (c <= 0) continue;
    const r = 1.2 + 2.9 * Math.pow(c, 0.8);
    d += `M${(x - r).toFixed(1)},${y.toFixed(1)}a${r.toFixed(1)},${r.toFixed(1)} 0 1,0 ${(2 * r).toFixed(1)},0a${r.toFixed(1)},${r.toFixed(1)} 0 1,0 ${(-2 * r).toFixed(1)},0`;
  }
  const grat = [];
  for (let la = -80; la <= 80; la += 20) {
    const pts = []; for (let lo = -180; lo <= 180; lo += 2) { const q = ortho(la, lo, R, cx, cy); if (q[2] > 0) pts.push(q); else if (pts.length) { grat.push(pts.splice(0)); } }
    if (pts.length) grat.push(pts);
  }
  for (let lo = -180; lo < 180; lo += 20) {
    const pts = []; for (let la = -90; la <= 90; la += 2) { const q = ortho(la, lo, R, cx, cy); if (q[2] > 0) pts.push(q); else if (pts.length) { grat.push(pts.splice(0)); } }
    if (pts.length) grat.push(pts);
  }
  const [hx, hy] = ortho(22.3, 114.17, R, cx, cy);
  return <Frame>
    <Svg>
      <defs><radialGradient id="g5" cx="45%" cy="40%" r="60%"><stop offset="0" stopColor={BLUE} stopOpacity="0.16"/><stop offset="1" stopColor={BLUE} stopOpacity="0"/></radialGradient></defs>
      <circle cx={cx} cy={cy} r={R} fill="none" stroke={BLUE} strokeWidth={1.2} opacity={0.7}/>
      {grat.map((g, i) => <path key={i} d={g.map((p, k) => `${k ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("")} stroke={BLUE} strokeWidth={0.8} fill="none" opacity={0.35}/>)}
      <path d={d} fill={BLUE}/>
      <circle cx={hx} cy={hy} r={34} fill="none" stroke={RED} strokeWidth={1.5}/>
      <circle cx={hx} cy={hy} r={9} fill={RED}/>
      <line x1={hx + 34} y1={hy} x2={hx + 120} y2={hy} stroke={RED} strokeWidth={1.5}/>
      <T x={hx + 130} y={hy + 5} size={15} font={GM} color={RED} ls={2.5}>HONG KONG</T>
      <T x={98} y={300} size={30} weight={400} font={GM} ls={4} opacity={0.75}>World:</T>
      <T x={86} y={500} size={200} weight={100} ls={-8}>6<tspan fontSize={90} dy={-86}>th</tspan></T>
      <T x={98} y={556} size={40} weight={300}>most common</T>
      <T x={86} y={820} size={200} weight={100} ls={-8} color={RED}>3<tspan fontSize={90} dy={-86}>rd</tspan></T>
      <T x={98} y={876} size={40} weight={300}>deadliest</T>
      <Src y={1032}>{SRC_WORLD}</Src>
      <T x={80} y={1060} size={12} weight={400} font={GM} opacity={0.45} ls={1}>LAND: NATURAL EARTH 1:110M (PUBLIC DOMAIN)</T>
    </Svg>
    <PrintGrain amount={0.24}/>
  </Frame>;
};

// ------------------------------------------------------------------ opt6 chain: three lacquer links on Klein blue
export const Opt6Chain = () => <Frame bg={IKB}>
  <Svg style={{position: "absolute"}}>
    <filter id="post6" colorInterpolationFilters="sRGB">
      <feComponentTransfer>
        <feFuncR type="discrete" tableValues="0 .1 .2 .3 .4 .5 .6 .7 .8 .9 1"/>
        <feFuncG type="discrete" tableValues="0 .1 .2 .3 .4 .5 .6 .7 .8 .9 1"/>
        <feFuncB type="discrete" tableValues="0 .1 .2 .3 .4 .5 .6 .7 .8 .9 1"/>
      </feComponentTransfer>
    </filter>
    <image href={staticFile("chain_full.png")} x={0} y={0} width={W} height={H} filter="url(#post6)"/>
  </Svg>
  <Svg>
    <T x={96} y={360} size={30} weight={400} font={GM} ls={4} opacity={0.85}>Top 3 deadliest in HK:</T>
    <T x={90} y={500} size={110} weight={200} ls={-3} opacity={0.6}>lung ·</T>
    <T x={90} y={630} size={110} weight={200} ls={-3} opacity={0.6}>colorectal ·</T>
    <T x={90} y={760} size={110} weight={300} ls={-3}>liver</T>
    <Src>{SRC_HK.replace("Liver Cancer in 2022 (Oct 2024)", "Liver Cancer in 2022 (Oct 2024) and 2023 overview")}</Src>
    <Tag>ILLUSTRATIVE · EQUAL LINKS, NO VALUES</Tag>
  </Svg>
  <PrintGrain amount={0.42} freq={1.1}/>
  <Vignette k={0.35}/>
</Frame>;

// ------------------------------------------------------------------ opt1 fog (Blender): 1,412 marks and the number wiped into a fogged pane
export const Opt1Fog = ({img = "fog_full.png"}) => <Frame bg="#000">
  <Img src={staticFile(img)} style={{position: "absolute", left: 0, top: 0, width: W, height: H}}/>
  <Svg>
    <T x={1000} y={968} size={40} weight={300} opacity={0.92}>deaths in Hong Kong, 2022</T>
    <Src x={1840} y={1050} anchor="end">{SRC_HK}</Src>
  </Svg>
  <PrintGrain amount={0.3}/>
</Frame>;

// ------------------------------------------------------------------ opt3 year (Blender): the calendar as a field of red glass beads
export const Opt3Beads = () => <Frame bg="#000">
  <Img src={staticFile("beads_full.png")} style={{position: "absolute", left: 0, top: 0, width: W, height: H}}/>
  <Svg>
    <T x={92} y={250} size={190} weight={100} ls={-8}>1,412</T>
    <T x={100} y={316} size={38} weight={300}>deaths in Hong Kong, 2022</T>
    <T x={100} y={360} size={14} font={GM} opacity={0.55} ls={1.5}>ONE BEAD = ONE DEATH · 2022 BY DAY · ≈ 3.9 A DAY, PLACED EVENLY (NOT DAILY DATA)</T>
    <Src x={80} y={1050}>{SRC_HK}</Src>
    <Tag x={1840} y={1050}>SCHEMATIC</Tag>
  </Svg>
  <PrintGrain amount={0.22}/>
</Frame>;

// ------------------------------------------------------------------ opt5 globe 3D (Blender): land as cobalt beads on a black glass globe, HK one red bead
export const Opt5Globe3D = () => <Frame bg="#000">
  <Img src={staticFile("globe_full.png")} style={{position: "absolute", left: 0, top: 0, width: W, height: H}}/>
  <Svg>
    <T x={98} y={300} size={30} weight={400} font={GM} ls={4} opacity={0.75}>World:</T>
    <T x={86} y={500} size={200} weight={100} ls={-8}>6<tspan fontSize={90} dy={-86}>th</tspan></T>
    <T x={98} y={556} size={40} weight={300}>most common</T>
    <T x={86} y={820} size={200} weight={100} ls={-8} color={RED}>3<tspan fontSize={90} dy={-86}>rd</tspan></T>
    <T x={98} y={876} size={40} weight={300}>deadliest</T>
    <Src y={1032}>{SRC_WORLD}</Src>
    <T x={80} y={1060} size={12} weight={400} font={GM} opacity={0.45} ls={1}>LAND: NATURAL EARTH 1:110M (PUBLIC DOMAIN) · RED BEAD: HONG KONG</T>
  </Svg>
  <PrintGrain amount={0.22}/>
</Frame>;
