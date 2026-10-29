// 1-08 options: time (the year we were born -> now), money (US$2.8 billion), one in ten.
import React from "react";
import {hash} from "../../core";
import {Print, Plate, Tag, Svg, GText, MText, GROT, MONO, P, W, H, NB} from "./common";

const Y0 = 2006, Y1 = 2026;

/* ------------------------------------------------------------------ A. SWISS LEDGER: three frames */
export const LedgerTime = () => {
  const x0 = 180, x1 = 1740, y = 610;
  return <Print>
    <Svg>
      <GText x={x0 - 12} y={500} size={300} weight={900} ls={-14}>2006</GText>
      <GText x={x1 + 12} y={500} size={300} weight={900} ls={-14} anchor="end" color={P.red}>2026</GText>
      <line x1={x0} y1={y} x2={x1} y2={y} stroke={P.ink} strokeWidth={2} opacity={0.5}/>
      <line x1={x0} y1={y} x2={x1} y2={y} stroke={P.red} strokeWidth={10}/>
      {Array.from({length: 21}, (_, i) => {
        const x = x0 + (x1 - x0) * i / 20, maj = i % 5 === 0;
        return <g key={i}><line x1={x} y1={y + 12} x2={x} y2={y + (maj ? 44 : 26)} stroke={P.ink} strokeWidth={maj ? 2.4 : 1.4} opacity={maj ? 0.9 : 0.5}/>
          {maj ? <MText x={x} y={y + 76} size={15} anchor="middle" opacity={0.7} ls={1}>{Y0 + i}</MText> : null}</g>;
      })}
      <circle cx={x0} cy={y} r={14} fill={P.bg} stroke={P.ink} strokeWidth={4}/>
      <circle cx={x1} cy={y} r={14} fill={P.red}/>
      <MText x={x0} y={y + 160} size={20} ls={3}>THE YEAR WE WERE BORN</MText>
      <MText x={x1} y={y + 160} size={20} ls={3} anchor="end" color={P.red}>ONLY READY NOW</MText>
      <MText x={W / 2} y={y + 160} size={20} ls={3} anchor="middle" opacity={0.55}>20 YEARS</MText>
      <MText x={70} y={110} size={15} opacity={0.6} ls={4}>START THE SEARCH THE YEAR WE WERE BORN</MText>
      <Tag/>
    </Svg>
  </Print>;
};

export const LedgerMoney = () => {
  // 2,800 cells, one per US$1 million (70 x 40)
  const cols = 70, rows = 40, cell = 15.4, gx = 840, gy = 228;
  let d = "";
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const x = gx + c * cell, y = gy + r * cell; d += `M${x},${y}h${cell - 3.4}v${cell - 3.4}h${-(cell - 3.4)}z`;
  }
  return <Print>
    <Svg>
      <path d={d} fill={P.blue}/>
      <MText x={gx} y={gy - 26} size={14} opacity={0.7} ls={2}>■ = US$1 MILLION · 2,800 OF THEM</MText>
      <GText x={120} y={470} size={120} weight={900} ls={-5}>US$</GText>
      <GText x={110} y={720} size={300} weight={900} ls={-16} color={P.red}>2.8</GText>
      <GText x={120} y={830} size={110} weight={900} ls={-4}>BILLION</GText>
      <MText x={124} y={900} size={20} ls={3} opacity={0.7}>IT CAN COST ALMOST</MText>
      <MText x={70} y={110} size={15} opacity={0.6} ls={4}>ONE DRUG, START TO MARKET</MText>
      <Tag/>
    </Svg>
  </Print>;
};

export const LedgerTen = () => {
  const cx = i => 200 + i * 169, cy = 520, R = 62, win = 6;
  return <Print>
    <Svg>
      {Array.from({length: 10}, (_, i) => i === win
        ? <g key={i}><circle cx={cx(i)} cy={cy} r={R} fill={P.red}/><circle cx={cx(i)} cy={cy} r={R + 22} fill="none" stroke={P.red} strokeWidth={2}/></g>
        : <circle key={i} cx={cx(i)} cy={cy} r={R - 2} fill="none" stroke="#4d4c48" strokeWidth={4}/>)}
      {Array.from({length: 10}, (_, i) => <MText key={"n" + i} x={cx(i)} y={cy + 128} size={16} anchor="middle" color={i === win ? P.red : P.ink} opacity={i === win ? 1 : 0.35}>{String(i + 1).padStart(2, "0")}</MText>)}
      <GText x={120} y={300} size={110} weight={900} ls={-4}>1<tspan fill={P.red} dx={26}>in</tspan><tspan dx={26}>10</tspan></GText>
      <MText x={124} y={820} size={20} ls={3}>OF DRUGS TESTED IN PEOPLE,</MText>
      <MText x={124} y={856} size={20} ls={3} color={P.red}>ONLY ABOUT ONE IN TEN REACHES THE MARKET</MText>
      <Tag/>
    </Svg>
  </Print>;
};

/* ------------------------------------------------------------------ B. COST CALENDAR: 20 year-columns of blue money dots, one red line of search */
export const DotYears = () => {
  const n = 20, per = 140, gx0 = 150, gx1 = 1770, top = 380, pitch = 13, cw = (gx1 - gx0) / n;
  let d = "";
  for (let k = 0; k < n; k++) for (let j = 0; j < per; j++) {
    const c = j % 6, r = Math.floor(j / 6);
    const x = gx0 + k * cw + 6 + c * pitch, y = top + 380 - r * pitch;
    d += `M${x + 5},${y}a5,5 0 1,0 0.01,0`;
  }
  return <Print>
    <Svg>
      <path d={d} stroke={P.blue} strokeWidth={10} strokeLinecap="round" fill="none"/>
      {/* the search: one red line across the 20 years */}
      <line x1={gx0} y1={top + 430} x2={gx1} y2={top + 430} stroke={P.red} strokeWidth={8}/>
      <circle cx={gx1} cy={top + 430} r={13} fill={P.red}/>
      {Array.from({length: n + 1}, (_, k) => k % 5 === 0 || k === n ? <MText key={k} x={gx0 + k * cw} y={top + 476} size={15} anchor={k === n ? "end" : "start"} opacity={0.7} ls={1}>{Y0 + k}</MText> : null)}
      <MText x={gx0} y={top + 520} size={18} ls={3}>THE YEAR WE WERE BORN</MText>
      <MText x={gx1} y={top + 520} size={18} ls={3} anchor="end" color={P.red}>ONLY READY NOW</MText>
      <GText x={gx0 - 6} y={250} size={150} weight={900} ls={-7}>US$2.8<tspan fill={P.blue} dx={30}>billion</tspan></GText>
      <MText x={gx0} y={312} size={16} ls={2} opacity={0.7}>IT CAN COST ALMOST · ● = US$1 MILLION · 2,800 DOTS</MText>
      <Tag/>
    </Svg>
  </Print>;
};

/* ------------------------------------------------------------------ C. TEN VIALS (Blender plate) */
export const Vials = () => <Print grain={0.18}>
  <Plate src="plates/vials_full.png"/>
  <Svg>
    <GText x={W / 2} y={190} size={120} weight={900} ls={-4} anchor="middle">1<tspan fill={P.red} dx={26}>in</tspan><tspan dx={26}>10</tspan></GText>
    <MText x={W / 2} y={250} size={18} ls={3} anchor="middle" opacity={0.75}>OF DRUGS TESTED IN PEOPLE · REACHES THE MARKET</MText>
    <MText x={70} y={1030} size={15} ls={3} opacity={0.6}>2006 → 2026 · THE YEAR WE WERE BORN → NOW</MText>
    <MText x={1850} y={1030} size={15} ls={3} opacity={0.6} anchor="end">ALMOST US$2.8 BILLION</MText>
    <Tag y={60}/>
  </Svg>
</Print>;

/* ------------------------------------------------------------------ D. GROWTH MARKS: door-frame height chart vs. the search */
export const Growth = () => {
  const base = 960, topY = 150, x = 760;
  // height in cm by age (rough growth curve), scaled
  const hcm = a => 50 + 120 * (1 - Math.exp(-a / 5.5)) + (a > 10 ? 6 * Math.min(1, (a - 10) / 6) : 0);
  const yOf = cm => base - (cm - 40) * ((base - topY) / 140);
  const marks = [];
  for (let a = 0; a <= 20; a++) {
    const y = yOf(hcm(a)), len = 120 + hash(a, 3) * 70;
    marks.push(<g key={a}>
      <line x1={x - len / 2 + hash(a, 1) * 20} y1={y} x2={x + len / 2 - hash(a, 2) * 20} y2={y + (hash(a, 4) - 0.5) * 6} stroke={P.ink} strokeWidth={3} strokeLinecap="round" filter="url(#v3-ink)" opacity={0.92}/>
      <MText x={x + len / 2 + 14} y={y + 6} size={a % 5 === 0 ? 18 : 13} opacity={a % 5 === 0 ? 0.95 : 0.5} ls={1}>{Y0 + a}</MText>
    </g>);
  }
  const sx = 1180, sy0 = yOf(hcm(0)), sy1 = yOf(hcm(20));
  return <Print>
    <Svg>
      <defs>
        <filter id="v3-ink" x="0" y="0" width={W} height={H} filterUnits="userSpaceOnUse">
          <feTurbulence type="fractalNoise" baseFrequency="0.55" numOctaves="1" seed="12" result="n"/>
          <feDisplacementMap in="SourceGraphic" in2="n" scale="3" xChannelSelector="R" yChannelSelector="G"/>
        </filter>
      </defs>
      {/* the door frame edge */}
      <rect x={x - 230} y={0} width={14} height={H} fill={P.ink} opacity={0.12}/>
      {/* ruler */}
      {Array.from({length: 141}, (_, i) => { const y = yOf(40 + i); return <line key={i} x1={x - 216} y1={y} x2={x - 216 + (i % 10 === 0 ? 30 : i % 5 === 0 ? 18 : 9)} y2={y} stroke={P.ink} strokeWidth={1} opacity={0.35}/>; })}
      {marks}
      <MText x={x - 120} y={sy0 + 46} size={16} ls={3} opacity={0.75}>US, GROWING UP</MText>
      {/* the search: a red bar rising at the same pace */}
      <rect x={sx} y={sy1} width={46} height={sy0 - sy1} fill={P.red}/>
      <rect x={sx + 8} y={sy1 + 8} width={46} height={sy0 - sy1} fill={P.blue} opacity={0.45} style={{mixBlendMode: "screen"}}/>
      <MText x={sx + 23} y={sy0 + 46} size={16} ls={3} anchor="middle" color={P.red}>ONE DRUG SEARCH</MText>
      <GText x={sx + 90} y={sy1 + 40} size={60} weight={900} ls={-2} color={P.red}>only ready now</GText>
      <MText x={sx + 94} y={sy1 + 82} size={16} ls={3} opacity={0.75}>STARTED THE YEAR WE WERE BORN</MText>
      <GText x={sx + 90} y={sy0 - 120} size={80} weight={900} ls={-3}>US$2.8B</GText>
      <MText x={sx + 94} y={sy0 - 80} size={16} ls={3} opacity={0.75}>IT CAN COST ALMOST 2.8 BILLION US DOLLARS</MText>
      <Tag/>
    </Svg>
  </Print>;
};
