// 1-09 ROAD MAP options. Each takes {lit}: number of stations reached (6 = full map, 4 = re-use state).
import React from "react";
import {AbsoluteFill} from "remotion";
import {hash} from "../../core";
import {Print, Plate, Tag, Svg, GText, MText, GROT, MONO, P, ST, COUNT, W, H} from "./common";

const dimOr = (i, lit, a = 1, b = 0.2) => (i < lit ? a : b);

/* ------------------------------------------------------------------ 1. METRO (Vignelli) */
export const RoadMetro = ({lit = 6}) => {
  // 45/90 geometry: top run, one 45 deg drop, bottom run
  const y0 = 400, y1 = 640, xa = 820, xb = xa + (y1 - y0);
  const S = [[190, y0], [440, y0], [690, y0], [1090, y1], [1400, y1], [1730, y1]];
  const path = `M70,${y0} H${xa} L${xb},${y1} H1800`;
  const cut = lit >= 6 ? null : S[lit - 1][0] + 60;
  const LW = 30;
  return <Print>
    <Svg>
      <defs>
        <clipPath id="m-live"><rect x={0} y={0} width={cut ?? W} height={H}/></clipPath>
        <clipPath id="m-dead"><rect x={cut ?? W} y={0} width={W} height={H}/></clipPath>
      </defs>
      {/* failures hang under each station as grey dot columns */}
      {S.map(([x, y], i) => {
        if (i === 0 || i >= lit) return null;
        const k = COUNT[i - 1] - COUNT[i];
        return <g key={"f" + i}>{Array.from({length: k}, (_, j) => <circle key={j} cx={x - 70 + (j % 2) * 16} cy={y + 52 + Math.floor(j / 2) * 16} r={5.5} fill="#5a5955"/>)}
          <MText x={x - 62} y={y + 52 + Math.ceil(k / 2) * 16 + 18} size={13} color="#8a8984" ls={1}>−{k}</MText></g>;
      })}
      {/* misregistered blue plate under the line (screen-print) */}
      <path d={path} stroke={P.blue} strokeWidth={LW} fill="none" opacity={0.55} transform="translate(7,6)" clipPath="url(#m-live)"/>
      <path d={path} stroke={P.red} strokeWidth={LW} fill="none" clipPath="url(#m-live)"/>
      {cut ? <path d={path} stroke="rgba(237,235,228,0.28)" strokeWidth={3} strokeDasharray="2 12" strokeLinecap="round" fill="none" clipPath="url(#m-dead)"/> : null}
      {/* candidates queued at the start */}
      {Array.from({length: COUNT[0]}, (_, j) => <circle key={"q" + j} cx={86 + (j % 6) * 15} cy={y0 - 120 + Math.floor(j / 6) * 15} r={5.5} fill={P.red}/>)}
      <MText x={86} y={y0 - 142} size={13} color={P.ink} opacity={0.7}>{COUNT[0]} CANDIDATES</MText>
      {S.map(([x, y], i) => {
        const on = i < lit, top = i < 3;
        const r = i === 5 ? 30 : 23;
        return <g key={i}>
          <circle cx={x} cy={y} r={r} fill={on ? P.ink : P.bg} stroke={on ? P.bg : "rgba(237,235,228,0.35)"} strokeWidth={on ? 9 : 3}/>
          {i === lit - 1 && lit < 6 ? <circle cx={x} cy={y} r={44} fill="none" stroke={P.red} strokeWidth={3}/> : null}
          <g opacity={dimOr(i, lit)}>
            <MText x={x} y={top ? y - 92 : y + 78} size={16} anchor="middle" color={on ? P.red : P.ink}>{ST[i].n}</MText>
            <GText x={x} y={top ? y - 52 : y + 120} size={i === 5 ? 46 : 38} anchor="middle">{ST[i].name}</GText>
            {ST[i].sub ? <MText x={x} y={top ? y - 128 : y + 150} size={13} anchor="middle" weight={400} ls={1} opacity={0.6}>{ST[i].sub}</MText> : null}
            {on && i > 0 ? <MText x={x + r + 14} y={y + (top ? -14 : -14)} size={14} color={P.ink} opacity={0.75}>{COUNT[i]}</MText> : null}
          </g>
        </g>;
      })}
      <MText x={70} y={110} size={15} opacity={0.6} ls={4}>EVERY MEDICINE WALKS THE SAME ROAD</MText>
      {lit >= 6 ? <GText x={1800} y={940} size={30} weight={600} anchor="end" color={P.red}>Any step can fail.</GText> : null}
      <Tag/>
    </Svg>
  </Print>;
};

/* ------------------------------------------------------------------ 2. GLASS TUBE (Blender plate) */
const GLASS_A = [[200, 504], [496, 501], [784, 497], [1066, 494], [1343, 491], [1613, 488]];
export const RoadGlass = ({lit = 6}) => <Print grain={0.16} band={0.04}>
  <Plate src={lit >= 6 ? "plates/glass_full.png" : "plates/glass_lit4.png"}/>
  <Svg>
    {GLASS_A.map(([x, y], i) => {
      const yy = 300 - (i % 2) * 0;
      return <g key={i} opacity={dimOr(i, lit, 1, 0.25)}>
        <line x1={x} y1={yy + 18} x2={x} y2={y - 14} stroke={P.ink} strokeWidth={1.2} opacity={0.5}/>
        <MText x={x} y={yy - 70} size={15} anchor="middle" color={i < lit ? P.red : P.ink}>{ST[i].n}</MText>
        <GText x={x} y={yy - 30} size={30} anchor="middle" lh={1.0}>{ST[i].short.replace("\n", " ")}</GText>
        {i < lit ? <MText x={x} y={yy + 2} size={13} anchor="middle" opacity={0.6} weight={400}>{COUNT[i]} in · {i ? COUNT[i - 1] - COUNT[i] : 0} out</MText> : null}
      </g>;
    })}
    <MText x={70} y={110} size={15} opacity={0.6} ls={4}>EVERY MEDICINE WALKS THE SAME ROAD</MText>
    {lit >= 6 ? <GText x={W / 2} y={960} size={30} weight={600} anchor="middle" color={P.red}>Any step can fail.</GText> : null}
    <Tag/>
  </Svg>
</Print>;

/* ------------------------------------------------------------------ 3. TYPOGRAPHIC ROAD (words painted on the road, CSS 3D) */
export const RoadType = ({lit = 6}) => {
  const PW = 1100, PH = 5200;
  const rows = ST.map((s, i) => ({...s, y: PH - 420 - i * 820}));
  return <Print grain={0.22}>
    <AbsoluteFill style={{perspective: 1100, perspectiveOrigin: "50% 8%"}}>
      <div style={{position: "absolute", left: (W - PW) / 2, top: H - PH, width: PW, height: PH, transformOrigin: "50% 100%", transform: "rotateX(74deg)"}}>
        {/* road edges */}
        <div style={{position: "absolute", left: 0, top: 0, width: 6, height: PH, background: P.ink, opacity: 0.55}}/>
        <div style={{position: "absolute", right: 0, top: 0, width: 6, height: PH, background: P.ink, opacity: 0.55}}/>
        {/* red centre line: solid where travelled, dashed grey after */}
        {(() => {
          const yCut = lit >= 6 ? 0 : rows[lit - 1].y - 260;
          return <>
            <div style={{position: "absolute", left: PW / 2 - 9, top: yCut, width: 18, height: PH - yCut, background: P.red}}/>
            {lit < 6 ? <div style={{position: "absolute", left: PW / 2 - 4, top: 0, width: 8, height: yCut, background: "repeating-linear-gradient(0deg, rgba(237,235,228,0.25) 0 60px, transparent 60px 140px)"}}/> : null}
          </>;
        })()}
        {rows.map((r, i) => {
          const on = i < lit;
          const words = r.name.split(" & ");
          return <div key={i} style={{position: "absolute", left: 0, width: PW, top: r.y - 560, height: 600, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", opacity: on ? 1 : 0.16}}>
            <div style={{fontFamily: MONO, fontWeight: 700, fontSize: 64, color: on ? P.red : P.ink, letterSpacing: 8, marginBottom: 10}}>{r.n}</div>
            <div style={{fontFamily: GROT, fontWeight: 900, fontSize: r.name.length > 9 ? 150 : 210, lineHeight: 0.86, color: P.ink, letterSpacing: -4, textAlign: "center", transform: "scaleY(1.9)", transformOrigin: "50% 100%", background: P.bg, padding: "0 20px"}}>
              {r.name === "CELLS & ANIMALS" ? <>CELLS&nbsp;→<br/>ANIMALS</> : r.name === "HUMAN TRIALS" ? <>TRIALS<br/>I · II · III</> : r.name}
            </div>
          </div>;
        })}
        {/* candidates as red discs between the words, thinning; dropouts grey on the verge */}
        {COUNT.map((c, i) => i < lit ? Array.from({length: c}, (_, j) => {
          const y = rows[i].y + 120 + hash(j, i, 3) * 200, x = PW / 2 + (hash(j, i, 5) - 0.5) * 380;
          return <div key={i + "-" + j} style={{position: "absolute", left: x - 16, top: y - 16, width: 32, height: 32, borderRadius: 16, background: P.red}}/>;
        }) : null)}
        {COUNT.map((c, i) => (i > 0 && i < lit) ? Array.from({length: COUNT[i - 1] - c}, (_, j) => {
          const side = j % 2 ? 1 : -1, y = rows[i].y + 60 + hash(j, i, 8) * 260, x = PW / 2 + side * (PW / 2 + 40 + hash(j, i, 9) * 160);
          return <div key={"g" + i + "-" + j} style={{position: "absolute", left: x - 15, top: y - 15, width: 30, height: 30, borderRadius: 15, background: "#4a4945"}}/>;
        }) : null)}
      </div>
    </AbsoluteFill>
    <Svg>
      <MText x={70} y={110} size={15} opacity={0.6} ls={4}>EVERY MEDICINE WALKS THE SAME ROAD</MText>
      {lit >= 6 ? <GText x={1850} y={110} size={30} weight={600} anchor="end" color={P.red}>Any step can fail.</GText> : null}
      <Tag/>
    </Svg>
  </Print>;
};

/* ------------------------------------------------------------------ 4. VESSEL + VALVES (Blender plate on Klein-blue table) */
const VES_A = [[183, 724], [483, 537], [798, 444], [1098, 613], [1425, 568], [1714, 399]];
const VES_OFF = [[40, 150], [-40, -150], [0, -170], [30, 170], [0, -170], [-10, 170]];
export const RoadVessel = ({lit = 6}) => <Print grain={0.24} band={0.06} blotch={0.04} bg={P.deep}>
  <Plate src={lit >= 6 ? "plates/vessel_full.png" : "plates/vessel_lit4.png"}/>
  <Svg>
    {VES_A.map(([x, y], i) => {
      const [dx, dy] = VES_OFF[i], tx = x + dx, ty = y + dy, up = dy < 0;
      return <g key={i} opacity={dimOr(i, lit, 1, 0.35)}>
        <line x1={x} y1={y + (up ? -40 : 40)} x2={tx} y2={ty + (up ? 16 : -46)} stroke={P.ink} strokeWidth={1.5} opacity={0.75}/>
        <MText x={tx} y={up ? ty - 38 : ty - 20 + 30} size={15} anchor="middle" color={P.ink}>{ST[i].n}</MText>
        <GText x={tx} y={up ? ty - 4 : ty + 52} size={32} anchor="middle">{ST[i].name}</GText>
      </g>;
    })}
    <MText x={70} y={1010} size={15} opacity={0.8} ls={4}>EVERY MEDICINE WALKS THE SAME ROAD</MText>
    {lit >= 6 ? <GText x={1850} y={1010} size={30} weight={600} anchor="end" color={P.ink}>Any step can fail.</GText> : null}
    <Tag y={60}/>
  </Svg>
</Print>;

/* ------------------------------------------------------------------ 5. GATES (Blender plate, light-frame installation) */
const GATE_A = [[292, 396], [623, 391], [877, 387], [1078, 383], [1242, 381], [1378, 378]];
export const RoadGates = ({lit = 6}) => <Print grain={0.18} band={0.05}>
  <Plate src={lit >= 6 ? "plates/gates_full.png" : "plates/gates_lit4.png"}/>
  <Svg>
    {GATE_A.map(([x, y], i) => {
      const lift = [0, 0, 0, 90, 0, 90][i];
      const ty = y - 40 - lift;
      return <g key={i} opacity={dimOr(i, lit, 1, 0.3)}>
        {lift ? <line x1={x} y1={y - 12} x2={x} y2={ty + 30} stroke={P.ink} strokeWidth={1.2} opacity={0.5}/> : null}
        <MText x={x} y={ty - (ST[i].short.includes("\n") ? 62 : 34)} size={14} anchor="middle" color={i === 5 ? P.red : P.ink} opacity={0.85}>{ST[i].n}</MText>
        <GText x={x} y={ty - (ST[i].short.includes("\n") ? 30 : 2)} size={28} anchor="middle" lh={1.0}>{ST[i].short}</GText>
      </g>;
    })}
    <MText x={70} y={110} size={15} opacity={0.6} ls={4}>EVERY MEDICINE WALKS THE SAME ROAD</MText>
    {lit >= 6 ? <GText x={1850} y={980} size={30} weight={600} anchor="end" color={P.red}>Any step can fail.</GText> : null}
    <Tag/>
  </Svg>
</Print>;

/* ------------------------------------------------------------------ 6. CHART RECORDER STRIP */
export const RoadRecorder = ({lit = 6}) => {
  const X0 = 150, X1 = 1770, Y0 = 300, Y1 = 760; // paper
  const gx0 = X0 + 140, gx1 = X1 - 60, gy0 = Y0 + 70, gy1 = Y1 - 120; // plot area
  const sx = i => gx0 + (gx1 - gx0) * (i + 0.5) / 6;
  const yv = c => gy1 - (gy1 - gy0) * Math.log(c) / Math.log(40) - 6;
  // trace: flat jitter, sharp step at each station
  const pts = []; let xEnd = lit >= 6 ? gx1 - 10 : sx(lit - 1) + 90;
  for (let x = gx0; x <= xEnd; x += 3) {
    const k = Math.max(0, Math.min(5, ST.findIndex((_, i) => x < sx(i) + 30) === -1 ? 5 : ST.findIndex((_, i) => x < sx(i) + 30)));
    let c = COUNT[Math.max(0, k - (x < sx(k) ? 0 : 0))];
    const idx = ST.reduce((a, _, i) => (x >= sx(i) ? i : a), -1);
    c = idx < 0 ? COUNT[0] : COUNT[idx];
    let y = yv(c) + (hash(Math.floor(x / 3), 7) - 0.5) * 5;
    for (let i = 1; i < 6; i++) { const d = x - sx(i); if (d >= 0 && d < 24) y -= Math.sin(d / 24 * Math.PI) * 26; }
    pts.push([x, y]);
  }
  const d = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("");
  const pen = pts[pts.length - 1];
  const grid = [];
  for (let x = gx0; x <= gx1; x += 22) grid.push(<line key={"x" + x} x1={x} y1={gy0} x2={x} y2={gy1} stroke={P.blue} strokeWidth={(x - gx0) % 110 === 0 ? 1.4 : 0.6} opacity={0.55}/>);
  for (let y = gy0; y <= gy1; y += 22) grid.push(<line key={"y" + y} x1={gx0} y1={y} x2={gx1} y2={y} stroke={P.blue} strokeWidth={(y - gy0) % 110 === 0 ? 1.4 : 0.6} opacity={0.55}/>);
  return <Print grain={0.22}>
    <Svg>
      <defs>
        <filter id="paper"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="4"/><feColorMatrix values="0 0 0 0 0.86  0 0 0 0 0.85  0 0 0 0 0.8  0 0 0 -0.9 0.95"/></filter>
        <filter id="stamp"><feTurbulence type="fractalNoise" baseFrequency="0.45" numOctaves="2" seed="9" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="2.5"/></filter>
        <filter id="shadow"><feDropShadow dx="0" dy="24" stdDeviation="22" floodColor="#000" floodOpacity="0.9"/></filter>
      </defs>
      <g transform={`rotate(-3.2 ${W / 2} ${H / 2})`}>
        <rect x={X0 - 400} y={Y0} width={X1 - X0 + 800} height={Y1 - Y0} fill={P.ink} filter="url(#shadow)"/>
        <rect x={X0 - 400} y={Y0} width={X1 - X0 + 800} height={Y1 - Y0} filter="url(#paper)" opacity={0.6}/>
        {/* sprocket holes */}
        {Array.from({length: 46}, (_, i) => <g key={i}><rect x={X0 - 390 + i * 60} y={Y0 + 14} width={22} height={14} rx={4} fill={P.bg}/><rect x={X0 - 390 + i * 60} y={Y1 - 28} width={22} height={14} rx={4} fill={P.bg}/></g>)}
        {grid}
        {/* y axis */}
        {[1, 2, 5, 10, 20, 34].map(c => <MText key={c} x={gx0 - 14} y={yv(c) + 5} size={13} anchor="end" color={P.blue} weight={700} ls={0}>{c}</MText>)}
        <MText x={X0 - 10} y={gy0 - 22} size={12} color={P.blue} ls={2}>CANDIDATES STILL ALIVE (LOG)</MText>
        {/* stations: pre-printed on the form */}
        {ST.map((s, i) => <g key={i} filter="url(#stamp)">
          <line x1={sx(i)} y1={gy0} x2={sx(i)} y2={gy1 + 14} stroke={P.blue} strokeWidth={2.2} strokeDasharray="6 5" opacity={i < lit ? 1 : 0.45}/>
          <MText x={sx(i)} y={gy1 + 44} size={13} anchor="middle" color={P.blue} weight={800} opacity={i < lit ? 1 : 0.45}>{s.n}</MText>
          <text x={sx(i)} y={gy1 + 76} textAnchor="middle" fontFamily={GROT} fontWeight={800} fontSize={25} fill={i < lit ? "#111" : "rgba(17,17,17,0.35)"} letterSpacing={-0.3}>{s.name}</text>
        </g>)}
        {/* failures: tick marks where the pen dropped */}
        {ST.map((s, i) => i > 0 && i < lit ? <MText key={"k" + i} x={sx(i) + 30} y={yv(COUNT[i]) + 34} size={13} color={P.red} weight={800} ls={0}>−{COUNT[i - 1] - COUNT[i]}</MText> : null)}
        <path d={d} stroke={P.red} strokeWidth={4.2} fill="none" strokeLinejoin="round" style={{mixBlendMode: "multiply"}}/>
        {/* pen */}
        <g transform={`translate(${pen[0]},${pen[1]})`}>
          <circle r={7} fill={P.red}/>
          <rect x={-4} y={-150} width={8} height={140} fill="#111"/>
          <rect x={-16} y={-190} width={32} height={46} fill="#111"/>
        </g>
        <MText x={X1 - 20} y={Y0 + 56} size={12} color={P.blue} anchor="end" ls={2}>STRIP 01 · ONE DRUG'S JOURNEY</MText>
      </g>
      <MText x={70} y={110} size={15} opacity={0.6} ls={4}>EVERY MEDICINE WALKS THE SAME ROAD</MText>
      {lit >= 6 ? <GText x={1850} y={980} size={30} weight={600} anchor="end" color={P.red}>Any step can fail.</GText> : null}
      <Tag/>
    </Svg>
  </Print>;
};

/* flat paper texture for the 3D recorder strip (5200x600). Pen end is at the right; paper further left is older. */
export const StripFlat = ({lit = 6}) => {
  const Wt = 5200, Ht = 600, sp = 560, pen = 5080;
  const sx = i => pen - 150 - (lit - 1 - i) * sp;
  const gy0 = 110, gy1 = 420;
  const yv = c => gy1 - (gy1 - gy0) * Math.log(c) / Math.log(40) - 4;
  const pts = [];
  for (let x = 0; x <= pen; x += 3) {
    const idx = ST.reduce((a, _, i) => (i < lit && x >= sx(i) ? i : a), -1);
    let y = yv(idx < 0 ? COUNT[0] : COUNT[idx]) + (hash(Math.floor(x / 3), 7) - 0.5) * 6;
    for (let i = 1; i < lit; i++) { const d = x - sx(i); if (d >= 0 && d < 30) y -= Math.sin(d / 30 * Math.PI) * 30; }
    pts.push([x, y]);
  }
  const d = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("");
  const grid = [];
  for (let x = 0; x <= Wt; x += 26) grid.push(<line key={"x" + x} x1={x} y1={gy0} x2={x} y2={gy1} stroke={P.blue} strokeWidth={x % 130 === 0 ? 2 : 0.9} opacity={0.6}/>);
  for (let y = gy0; y <= gy1; y += 26) grid.push(<line key={"y" + y} x1={0} y1={y} x2={Wt} y2={y} stroke={P.blue} strokeWidth={(y - gy0) % 130 === 0 ? 2 : 0.9} opacity={0.6}/>);
  return <svg width={Wt} height={Ht} viewBox={`0 0 ${Wt} ${Ht}`} style={{background: "#E9E6DC"}}>
    <defs><filter id="pp"><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" seed="4"/><feColorMatrix values="0 0 0 0 0.5  0 0 0 0 0.48  0 0 0 0 0.44  0 0 0 0.25 0"/></filter></defs>
    <rect width={Wt} height={Ht} filter="url(#pp)"/>
    {Array.from({length: 87}, (_, i) => <g key={i}><rect x={10 + i * 60} y={22} width={24} height={16} rx={4} fill="#111"/><rect x={10 + i * 60} y={Ht - 38} width={24} height={16} rx={4} fill="#111"/></g>)}
    {grid}
    {[0, 1, 2, 3, 4].map(r => [1, 2, 5, 10, 20, 34].map(c => <text key={r + "-" + c} x={r * 1040 + 40} y={yv(c) + 6} fontFamily={MONO} fontSize={18} fontWeight={700} fill={P.blue}>{c}</text>))}
    {ST.map((s, i) => i < lit ? <g key={i}>
      <line x1={sx(i)} y1={gy0 - 20} x2={sx(i)} y2={gy1 + 16} stroke={P.blue} strokeWidth={3} strokeDasharray="8 6"/>
      <text x={sx(i) + 16} y={gy1 + 64} fontFamily={MONO} fontSize={26} fontWeight={800} fill={P.blue}>{s.n}</text>
      <text x={sx(i) + 70} y={gy1 + 66} fontFamily={GROT} fontSize={50} fontWeight={800} fill="#111" letterSpacing={-1}>{s.name}</text>
      {i > 0 ? <text x={sx(i) + 40} y={yv(COUNT[i]) + 44} fontFamily={MONO} fontSize={24} fontWeight={800} fill={P.red}>−{COUNT[i - 1] - COUNT[i]}</text> : null}
    </g> : null)}
    <text x={sx(0) - 520} y={gy0 - 34} fontFamily={MONO} fontSize={20} fontWeight={700} fill={P.blue} letterSpacing={3}>CANDIDATES STILL ALIVE (LOG) · ILLUSTRATIVE</text>
    <path d={d} stroke={P.red} strokeWidth={5.5} fill="none" strokeLinejoin="round"/>
  </svg>;
};
