// V3-Demo: 8 s / 30 fps / fake 120 BPM. The system in motion: draw-on, boil, impact frames on every beat, 001 -> 048 morph.
import React from "react";
import {AbsoluteFill, useCurrentFrame} from "remotion";
import {C, W, H, hash, clamp01, ramp, lerp, outCubic, outExpo, outBack, inOut, loopPts, BoilProvider} from "./core";
import {InkPath, RoughCircle} from "./ink";
import {HandArrow, HandCircle, HandUnderline, StrikeOut, ScribbleBurst, Highlight} from "./marks";
import {HandText, Mono, DataTag, monoW} from "./type";
import {Stage, InkDefs, Dust, Halftone, radial} from "./texture";
import {Chrome} from "./chrome";
import {InkMolecule, MolGhost, M001, M048, NEW_048, bbox, molPoints} from "./molecule";
import {FunnelBody, PixelCloud, HexMark, FUN, funnelSpan} from "./frames/Funnel";
import {BEAT, beatOf, sinceBeat, isDownbeat, kick, SplitDefs, BeatBar} from "./beat";

export const V3_DEMO_FRAMES = 240;
const B = n => n * BEAT; // frame of beat n

// slam-in transform for something that lands on a beat
const slam = (f, t0, cx, cy, from = 1.6) => {
  const t = clamp01((f - t0) / 5);
  const s = lerp(from, 1, outExpo(t));
  return `translate(${cx} ${cy}) scale(${s}) translate(${-cx} ${-cy})`;
};

// ---------------- act 1: the funnel (beats 0-4) ----------------
const NUMS = [
  {x: 110, v: "8,918", label: "AI-DESIGNED", t: B(0)},
  {x: 760, v: "54", label: "SELECTED", t: B(2)},
  {x: 1180, v: "7", label: "SYNTHESISED", t: B(3)},
  {x: 1540, v: "1", label: "FIRST HIT", t: B(4)},
];
const scatter = (n, x0, x1, pad, seed, minD) => {
  const out = [];
  for (let k = 0; out.length < n && k < 5000; k++) {
    const x = x0 + hash(k, seed) * (x1 - x0), [a, b] = funnelSpan(x);
    const y = a + pad + hash(k, seed + 1) * (b - a - 2 * pad);
    if (out.every(p => Math.hypot(p[0] - x, p[1] - y) > minD)) out.push([x, y]);
  }
  return out;
};
const S2 = scatter(54, 745, 1160, 22, 3, 21), S3 = scatter(7, 1200, 1415, 14, 8, 34);

const ActFunnel = ({f}) => {
  const big = 150, ny = 228;
  return <g>
    <PixelCloud reveal={outCubic(f / 10)} squeeze={outCubic((f - B(2)) / 12)} opacity={1 - 0.85 * ramp(f, B(2) + 6, B(2) + 16)}/>
    <g filter="url(#v3-ink)">
      <FunnelBody progress={outCubic(f / 16)}/>
      {f >= B(2) && S2.map((p, i) => <RoughCircle key={i} cx={p[0]} cy={p[1]} d={17} seed={600 + i} size={3} options={{roughness: 1.4, bowing: 1}} progress={clamp01((f - B(2) - i * 0.12) / 4)}/>)}
      {f >= B(3) && S3.map((p, i) => <HexMark key={i} x={p[0]} y={p[1]} r={20} seed={700 + i} progress={clamp01((f - B(3) - i * 0.9) / 5)}/>)}
      {f >= B(4) + 4 && <HandArrow from={[1575, 676]} to={[1660, 790]} bend={0.25} size={6} head={20} seed={81} progress={ramp(f, B(4) + 4, B(4) + 12)}/>}
    </g>
    {NUMS.map((n, i) => f >= n.t && <g key={i}>
      <g transform={slam(f, n.t, n.x + monoW(n.v, big) / 2, ny - 55)}>
        <Mono x={n.x} y={ny} size={big} weight={800} color={C.ink}>{n.v}</Mono>
      </g>
      <Mono x={n.x + 4} y={ny + 58} size={20} weight={700} color={i === 0 ? C.cyan : C.dim} letterSpacing={3} reveal={ramp(f, n.t + 3, n.t + 11)} cursor>{n.label}</Mono>
    </g>)}
    <g filter="url(#v3-ink)">
      {NUMS.slice(0, 3).map((n, i) => f >= NUMS[i + 1].t && <StrikeOut key={i} x={n.x} y={ny - 110} w={monoW(n.v, big)} h={110} size={16 - i} seed={3 + i * 2}
        kind={i === 2 ? "x" : "double"} progress={ramp(f, NUMS[i + 1].t, NUMS[i + 1].t + 6)}/>)}
      {f >= B(4) && <HandCircle cx={1540 + monoW("1", big) / 2} cy={ny - 56} rx={86} ry={88} size={9} color={C.acid} seed={31} turns={1.25} progress={ramp(f, B(4) + 1, B(4) + 11)}/>}
      {NUMS.map((n, i) => <ScribbleBurst key={i} cx={n.x + monoW(n.v, big) / 2} cy={ny - 55} r0={100} r1={240} n={16} size={9} color={i === 3 ? C.acid : C.ink} phase={(f - n.t) / 9} seed={40 + i}/>)}
      <HandArrow from={[120, 965]} to={[1400, 958]} bend={0.012} size={7} head={26} seed={95} progress={ramp(f, B(1), B(4))}/>
    </g>
    {f >= B(1) && <g transform={slam(f, B(1), 790, 960, 1.4)}>
      <rect x={640} y={925} width={300} height={70} fill={C.bg}/>
      <HandText x={790} y={985} size={72} seed={21} anchor="middle" color={C.verm}>30 DAYS</HandText>
    </g>}
  </g>;
};

// ---------------- acts 2+3: 001 draws, round 2 adds the pyrazole -> 048 ----------------
const MX = 960, MY = 600, MS = 84;
const C001 = (({cx, cy}) => [cx, cy])(bbox(M001)), C048 = (({cx, cy}) => [cx, cy])(bbox(M048));
// order the pyrazole bonds outward from the attachment atom (14)
const NEW_BONDS = (() => {
  const bonds = M048.bonds.map((b, i) => ({...b, i})).filter(b => NEW_048.has(b.a) || NEW_048.has(b.b));
  const out = [], seen = new Set([14]);
  while (out.length < bonds.length) {
    const nx = bonds.find(b => !out.includes(b.i) && (seen.has(b.a) || seen.has(b.b)));
    if (!nx) break;
    out.push(nx.i); seen.add(nx.a); seen.add(nx.b);
  }
  return out;
})();

const ActMolecule = ({f}) => {
  const tMove = inOut((f - B(9)) / 30);
  const center = [lerp(C001[0], C048[0], tMove), lerp(C001[1], C048[1], tMove)];
  const P = molPoints(M048, MX, MY, MS, center);
  const pyr = M048.newAtoms.map(i => P[i]);
  const pc = pyr.reduce((s, p) => [s[0] + p[0] / pyr.length, s[1] + p[1] / pyr.length], [0, 0]);
  const tPyr = (f - B(10)) / 22;
  const morphing = f >= B(10);
  const ny = 300;
  return <g>
    {/* halftone body glow behind the molecule, pumps on each beat */}
    <Halftone bounds={[260, 260, 1400, 700]} field={radial(MX, MY, 520 + 40 * Math.exp(-sinceBeat(f) / 3), 1.5)} cell={16} angle={0.4} color={C.verm} opacity={0.22 + 0.12 * Math.exp(-sinceBeat(f) / 3)}/>
    {f >= B(9) && <MolGhost mol={M048} x={MX} y={MY} scale={MS} center={center} atoms={M048.newAtoms} progress={ramp(f, B(9), B(9) + 10)} opacity={1 - 0.8 * ramp(f, B(11), B(12))}/>}
    <g filter="url(#v3-ink)">
      {!morphing
        ? <InkMolecule mol={M001} x={MX} y={MY} scale={MS} center={center} seed={11} size={9} progress={outCubic((f - B(5)) / 42)}/>
        : <InkMolecule mol={M048} x={MX} y={MY} scale={MS} center={center} seed={48} size={9} tint={i => NEW_048.has(i) ? C.cyan : C.ink}
          bondProgress={bi => { const r = NEW_BONDS.indexOf(bi); return r < 0 ? 1 : clamp01((tPyr * (NEW_BONDS.length + 2) - r) / 2.2); }}/>}
      {f >= B(11) && <HandCircle cx={pc[0] + 10} cy={pc[1] + 4} rx={128} ry={110} size={7} color={C.cyan} seed={9} rot={0.2} progress={ramp(f, B(11), B(11) + 10)}/>}
      {f >= B(10) && <ScribbleBurst cx={pc[0]} cy={pc[1]} r0={130} r1={260} n={18} size={8} color={C.cyan} phase={(f - B(10)) / 10} seed={77}/>}
      {f >= B(15) && <ScribbleBurst cx={640 + monoW("33.4", 60) / 2} cy={906} r0={160} r1={260} n={16} size={8} color={C.acid} phase={(f - B(15)) / 10} seed={78}/>}
    </g>
    {f >= B(11) + 3 && <g>
      <line x1={pc[0] + 80} y1={pc[1] - 90} x2={pc[0] + 150} y2={pc[1] - 170} stroke={C.cyan} strokeWidth={2}/>
      <rect x={pc[0] + 146} y={pc[1] - 214} width={290} height={58} fill={C.bg}/>
      <Mono x={pc[0] + 158} y={pc[1] - 189} size={19} weight={700} color={C.cyan} reveal={ramp(f, B(11) + 3, B(11) + 10)}>+ PYRAZOLE</Mono>
      <Mono x={pc[0] + 158} y={pc[1] - 165} size={15} color={C.cyan} reveal={ramp(f, B(11) + 6, B(11) + 14)}>added in round 2</Mono>
    </g>}

    {/* 001 label, struck when 048 lands */}
    <g transform={slam(f, B(5), 260, ny - 70)}>
      <HandText x={110} y={ny} size={190} seed={5}>001</HandText>
    </g>
    <Mono x={122} y={ny + 46} size={20} weight={700} color={C.dim} letterSpacing={3} reveal={ramp(f, B(6), B(6) + 10)} cursor>FIRST HIT · DAY 30</Mono>
    <g filter="url(#v3-ink)">
      {f >= B(7) && <HandUnderline x={118} y={ny + 66} w={330} size={6} color={C.verm} seed={33} kind="wave" progress={ramp(f, B(7), B(7) + 8)}/>}
      {f >= B(12) && <StrikeOut x={110} y={ny - 140} w={330} h={140} size={18} seed={7} kind="double" progress={ramp(f, B(12), B(12) + 6)}/>}
      {f >= B(12) && <ScribbleBurst cx={680} cy={ny - 70} r0={120} r1={250} n={16} size={9} color={C.ink} phase={(f - B(12)) / 9} seed={79}/>}
    </g>
    {f >= B(12) && <g transform={slam(f, B(12), 680, ny - 70, 1.9)}>
      <HandText x={500} y={ny} size={210} seed={6}>048</HandText>
    </g>}

    {/* round 2 counter */}
    {f >= B(8) && <g transform={slam(f, B(8), 1500, 190, 1.3)}>
      <rect x={1300} y={160} width={160} height={40} fill={C.cyan}/>
      <Mono x={1316} y={188} size={20} weight={800} color={C.bg} letterSpacing={2}>ROUND 2</Mono>
      <Mono x={1480} y={192} size={32} weight={800} color={C.ink} reveal={ramp(f, B(8) + 2, B(9))}>16 → 6 → 048</Mono>
    </g>}
    {f >= B(8) + 8 && <g filter="url(#v3-ink)">
      <StrikeOut x={1480} y={160} w={monoW("16", 32)} h={36} size={7} seed={13} kind="slash" progress={ramp(f, B(8) + 8, B(8) + 12)}/>
      <StrikeOut x={1480 + monoW("16 → ", 32)} y={160} w={monoW("6", 32)} h={36} size={7} seed={14} kind="slash" progress={ramp(f, B(9) + 2, B(9) + 6)}/>
    </g>}

    {/* data lands on the last beats */}
    {f >= B(13) && <DataTag x={124} y={930} label="BINDS · Kd" value="566.7" unit="nM" size={60} reveal={ramp(f, B(13), B(13) + 8)}/>}
    {f >= B(14) && <DataTag x={640} y={930} label="BLOCKS THE ENZYME · IC50" value="33.4" unit="nM" size={60} hl={ramp(f, B(14), B(14) + 6)} reveal={ramp(f, B(14), B(14) + 6)} seed={12}/>}
  </g>;
};

// small scribble bursts for beats that have no bigger event of their own (every beat gets a hit)
const EXTRA_HITS = {1: [790, 955, C.verm], 6: [470, 335, C.ink], 7: [470, 366, C.verm], 9: [1420, 640, C.cyan], 11: [1640, 420, C.cyan], 13: [230, 905, C.ink], 14: [724, 906, C.acid, 150]};
const ExtraHit = ({f}) => {
  const b = beatOf(f), h = EXTRA_HITS[b];
  if (!h) return null;
  return <g filter="url(#v3-ink)"><ScribbleBurst cx={h[0]} cy={h[1]} r0={h[3] || 70} r1={(h[3] || 70) + 80} n={12} size={7} color={h[2]} phase={sinceBeat(f) / 8} seed={200 + b}/></g>;
};

export const V3Demo = ({grain = 0.24}) => {
  const f = useCurrentFrame();
  const s = sinceBeat(f), b = beatOf(f);
  const invert = isDownbeat(f) && s < 2;      // impact frame: whole image flips for 2 frames on each bar
  const split = s < 3 ? (3 - s) * 5 : 0;        // misregistration on every beat
  const [dx, dy, sc] = kick(f);
  return <BoilProvider rate={2.5}>
    <AbsoluteFill style={{filter: invert ? "invert(1)" : undefined}}>
      <Stage grain={grain}>
        <svg width={W} height={H} style={{position: "absolute"}}>
          <InkDefs/>
          <SplitDefs k={split}/>
          <g transform={`translate(${960 + dx} ${540 + dy}) scale(${sc}) translate(-960 -540)`} filter={split ? "url(#v3-split)" : undefined}>
            {f < B(5) ? <ActFunnel f={f}/> : <ActMolecule f={f}/>}
            <ExtraHit f={f}/>
          </g>
          <Dust/>
          <Chrome fig={f < B(5) ? "01" : "02"} smiles={false}/>
          <BeatBar f={f}/>
        </svg>
      </Stage>
    </AbsoluteFill>
  </BoilProvider>;
};
