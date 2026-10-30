// 1-08 · Swiss ledger, animated. Same three panels as s108/cost.jsx (LedgerTime / LedgerMoney / LedgerTen), now the numbers build.
// C's line (script v3.3, 01:00–01:16):
//   "Start the search the year we were born, and it might only be ready now."   0.0–5.8 s  -> 2006, bar runs, counter rolls to 2026
//   "It can cost almost 2.8 billion US dollars."                                 6.0–10.3 s -> US$ counts to 2.8 BILLION, 2,800 cells fill
//   "And of drugs tested in people, only about one in ten reaches the market."  10.5–16 s  -> ten circles, nine fade, one stays blood red
import React from "react";
import {AbsoluteFill} from "remotion";
import {ramp, inOut, outExpo, outCubic, outBack, hash, clamp01} from "../../../core";
import {useFrame30, Seq30} from "../../../time30";
import {Print, Tag, Svg, GText, MText, P, W, H} from "../../s108/common";

export const DUR_108 = 480;
const sec = s => Math.round(s * 30);
const Y0 = 2006, Y1 = 2026;

// a word/line that lands: fades in and rises a few px
const land = (f, a, n = 10) => ({o: outCubic(ramp(f, a, a + n)), dy: 14 * (1 - outExpo(ramp(f, a, a + n + 4)))});

/* ------------------------------------------------------------------ A. time: 2006 -> 2026 */
const Time = () => {
  const f = useFrame30();
  const x0 = 180, x1 = 1740, y = 610;
  const B0 = sec(2.3), B1 = sec(4.7);                      // the bar runs on "and it might only be ready now"
  const p = inOut(ramp(f, B0, B1));
  const xh = x0 + (x1 - x0) * p;
  const yr = Math.round(Y0 + (Y1 - Y0) * p);
  const done = f >= B1;
  const pop = 1 + 0.06 * (1 - outExpo(ramp(f, B1, B1 + 12)));
  const a = land(f, 2, 8), b = land(f, 10), c = land(f, B1 + 2), mid = land(f, B1 + 14);
  return <Svg>
    <g opacity={a.o} transform={`translate(0 ${a.dy})`}><GText x={x0 - 12} y={500} size={300} weight={900} ls={-14}>2006</GText></g>
    {/* the year counter rides to the right edge; it turns red when it lands */}
    <g opacity={ramp(f, B0 - 6, B0 + 2)} transform={`translate(${x1 + 12} 500) scale(${done ? pop : 1}) translate(${-(x1 + 12)} -500)`}>
      <GText x={x1 + 12} y={500} size={300} weight={900} ls={-14} anchor="end" color={done ? P.red : P.ink}>{String(yr)}</GText>
    </g>
    <line x1={x0} y1={y} x2={x1} y2={y} stroke={P.ink} strokeWidth={2} opacity={0.5 * ramp(f, 4, 14)}/>
    <line x1={x0} y1={y} x2={xh} y2={y} stroke={P.red} strokeWidth={10}/>
    {Array.from({length: 21}, (_, i) => {
      const x = x0 + (x1 - x0) * i / 20, maj = i % 5 === 0, on = ramp(xh, x - 30, x + 2);
      const o = i === 0 ? ramp(f, 4, 14) : on;
      return <g key={i} opacity={o}><line x1={x} y1={y + 12} x2={x} y2={y + (maj ? 44 : 26) * (0.4 + 0.6 * o)} stroke={P.ink} strokeWidth={maj ? 2.4 : 1.4} opacity={maj ? 0.9 : 0.5}/>
        {maj ? <MText x={x} y={y + 76} size={15} anchor="middle" opacity={0.7} ls={1}>{Y0 + i}</MText> : null}</g>;
    })}
    <circle cx={x0} cy={y} r={14} fill={P.bg} stroke={P.ink} strokeWidth={4} opacity={ramp(f, 4, 10)}/>
    {p > 0 ? <circle cx={xh} cy={y} r={done ? 14 * pop : 10} fill={P.red}/> : null}
    <g opacity={b.o} transform={`translate(0 ${b.dy})`}><MText x={x0} y={y + 160} size={20} ls={3}>THE YEAR WE WERE BORN</MText></g>
    <g opacity={c.o} transform={`translate(0 ${c.dy})`}><MText x={x1} y={y + 160} size={20} ls={3} anchor="end" color={P.red}>ONLY READY NOW</MText></g>
    <g opacity={mid.o}><MText x={W / 2} y={y + 160} size={20} ls={3} anchor="middle" opacity={0.55}>20 YEARS</MText></g>
    <MText x={70} y={110} size={15} opacity={0.6 * ramp(f, 0, 12)} ls={4}>START THE SEARCH THE YEAR WE WERE BORN</MText>
    <Tag/>
  </Svg>;
};

/* ------------------------------------------------------------------ B. money: US$ 2.8 BILLION, 2,800 cells (one per US$1 million) */
const COLS = 70, ROWS = 40, CELL = 15.4, GX = 840, GY = 228;
const cellD = (n0, n1) => {           // cells n0..n1-1, filled column by column (left to right, top to bottom)
  let d = ""; const s = CELL - 3.4;
  for (let n = n0; n < n1; n++) { const c = Math.floor(n / ROWS), r = n % ROWS; d += `M${GX + c * CELL},${GY + r * CELL}h${s}v${s}h${-s}z`; }
  return d;
};
const EMPTY = cellD(0, COLS * ROWS);
const Money = () => {
  const f = useFrame30();
  const C0 = 24, C1 = 78;                     // local frames: count runs 6.8–8.6 s, lands on "2.8 billion"
  const p = clamp01(outCubic(ramp(f, C0, C1)) * 1.0);
  const n = Math.round(2800 * p);
  const v = (2.8 * p).toFixed(1);
  const done = f >= C1;
  const pop = 1 + 0.05 * (1 - outExpo(ramp(f, C1, C1 + 12)));
  const lab = land(f, 4), usd = land(f, 10), bil = land(f, C1 - 6), key = land(f, 14);
  // the column being filled glows for a moment
  const col = Math.floor(n / ROWS);
  return <Svg>
    <path d={EMPTY} fill={P.blue} opacity={0.1 * ramp(f, 0, 14)}/>
    <path d={cellD(0, n)} fill={P.blue}/>
    {p > 0 && p < 1 ? <rect x={GX + col * CELL - 2} y={GY - 4} width={CELL + 1} height={ROWS * CELL + 4} fill={P.ink} opacity={0.18}/> : null}
    <g opacity={key.o}><MText x={GX} y={GY - 26} size={14} opacity={0.7} ls={2}>■ = US$1 MILLION · 2,800 OF THEM</MText></g>
    <g opacity={usd.o} transform={`translate(0 ${usd.dy})`}><GText x={120} y={470} size={120} weight={900} ls={-5}>US$</GText></g>
    <g opacity={ramp(f, C0 - 4, C0 + 2)} transform={`translate(110 720) scale(${done ? pop : 1}) translate(-110 -720)`}>
      <GText x={110} y={720} size={300} weight={900} ls={-16} color={P.red}>{v}</GText>
    </g>
    <g opacity={bil.o} transform={`translate(0 ${bil.dy})`}><GText x={120} y={830} size={110} weight={900} ls={-4}>BILLION</GText></g>
    <g opacity={lab.o}><MText x={124} y={900} size={20} ls={3} opacity={0.7}>IT CAN COST ALMOST</MText></g>
    <MText x={70} y={110} size={15} opacity={0.6} ls={4}>ONE DRUG, START TO MARKET</MText>
    <Tag/>
  </Svg>;
};

/* ------------------------------------------------------------------ C. one in ten */
const Ten = () => {
  const f = useFrame30();
  const cx = i => 200 + i * 169, cy = 520, R = 62, win = 6;
  const IN = i => 6 + i * 3;                        // ten circles land (drugs tested in people)
  const FADE0 = sec(2.3);                            // "only about one in ten" (~12.8 s)
  const order = Array.from({length: 10}, (_, i) => i).filter(i => i !== win).sort((a, b) => hash(a, 5) - hash(b, 5));
  const fadeAt = i => FADE0 + order.indexOf(i) * 3;
  const RED = FADE0 + 26, RING = sec(4.0);           // the one stays and turns red; ring on "reaches the market"
  const tested = land(f, 4), title = land(f, RED - 4), red = land(f, RING - 6);
  return <Svg>
    {Array.from({length: 10}, (_, i) => {
      const a = outBack(ramp(f, IN(i), IN(i) + 10), 1.4), o = ramp(f, IN(i), IN(i) + 6);
      if (i === win) {
        const r = ramp(f, RED, RED + 8), ring = outExpo(ramp(f, RING, RING + 18));
        return <g key={i} opacity={o}>
          <circle cx={cx(i)} cy={cy} r={(R - 2) * a} fill={P.ink} opacity={0.88 * (1 - r)}/>
          <circle cx={cx(i)} cy={cy} r={R * a * (1 + 0.08 * (1 - outExpo(ramp(f, RED, RED + 12))) * r)} fill={P.red} opacity={r}/>
          {ring > 0 ? <circle cx={cx(i)} cy={cy} r={R + 22 * ring} fill="none" stroke={P.red} strokeWidth={2} opacity={ring}/> : null}
        </g>;
      }
      const g = inOut(ramp(f, fadeAt(i), fadeAt(i) + 12));
      return <g key={i} opacity={o}>
        <circle cx={cx(i)} cy={cy} r={(R - 2) * a * (1 - 0.04 * g)} fill={P.ink} opacity={0.88 * (1 - g)}/>
        <circle cx={cx(i)} cy={cy} r={(R - 2) * a * (1 - 0.04 * g)} fill="none" stroke="#4d4c48" strokeWidth={4} opacity={g}/>
      </g>;
    })}
    {Array.from({length: 10}, (_, i) => {
      const r = i === win ? ramp(f, RED, RED + 8) : 0, g = i === win ? 0 : ramp(f, fadeAt(i), fadeAt(i) + 12);
      return <MText key={"n" + i} x={cx(i)} y={cy + 128} size={16} anchor="middle" color={r > 0.5 ? P.red : P.ink}
        opacity={ramp(f, IN(i) + 4, IN(i) + 10) * (0.6 - 0.25 * g + 0.4 * r)}>{String(i + 1).padStart(2, "0")}</MText>;
    })}
    <g opacity={title.o} transform={`translate(0 ${title.dy})`}>
      <GText x={120} y={300} size={110} weight={900} ls={-4}>1<tspan fill={P.red} dx={26}>in</tspan><tspan dx={26}>10</tspan></GText>
    </g>
    <g opacity={tested.o} transform={`translate(0 ${tested.dy})`}><MText x={124} y={820} size={20} ls={3}>OF DRUGS TESTED IN PEOPLE,</MText></g>
    <g opacity={red.o} transform={`translate(0 ${red.dy})`}><MText x={124} y={856} size={20} ls={3} color={P.red}>ONLY ABOUT ONE IN TEN REACHES THE MARKET</MText></g>
    <Tag/>
  </Svg>;
};

// panels dissolve into each other over 8 frames (as the v1 reel did)
const PANELS = [[0, sec(6.0), Time], [sec(6.0), sec(10.5), Money], [sec(10.5), DUR_108, Ten]];
const XF = 8;
const Panel = ({C, fade}) => { const f = useFrame30(); return <AbsoluteFill style={{opacity: fade ? inOut(ramp(f, 0, XF)) : 1}}><Print><C/></Print></AbsoluteFill>; };
export const Beat108 = () => <AbsoluteFill style={{background: P.bg}}>
  {PANELS.map(([a, b, C], i) => <Seq30 key={i} from={a} durationInFrames={b - a + (i < PANELS.length - 1 ? XF : 0)}><Panel C={C} fade={i > 0}/></Seq30>)}
</AbsoluteFill>;
