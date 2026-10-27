// V3-Ladder: the evidence ladder. Four solid rungs climbed, two dashed "not yet" rungs scribbled over.
import React from "react";
import {C, W, H, hash, clamp01, handLine, rotPt} from "../core";
import {InkPath, InkLine, Scribble} from "../ink";
import {HandArrow, Tick, Highlight, HandUnderline} from "../marks";
import {HandText, Mono} from "../type";
import {Stage, InkDefs, Dust, Halftone, radial} from "../texture";
import {Chrome} from "../chrome";

export const RUNGS = [
  {label: "PREDICTED", ev: "computer prediction", ok: true, ai: true},
  {label: "BINDS", ev: "Kd 566.7 nM", ok: true},
  {label: "BLOCKS THE ENZYME", ev: "IC50 33.4 nM", ok: true},
  {label: "WORKS IN CELLS", ev: "tested in cells", ok: true},
  {label: "ANIMALS", ev: "", ok: false},
  {label: "PATIENTS", ev: "", ok: false},
];
export const LAD = {x0: 330, x1: 560, yBottom: 1000, y0: 905, step: 140, tilt: -0.035};

/** Dashed hand line (each dash its own stroke). */
export const DashLine = ({from, to, dash = 22, gap = 16, seed = 1, size = 5, color = C.ink, opacity = 1, progress = 1}) => {
  const L = Math.hypot(to[0] - from[0], to[1] - from[1]), n = Math.floor(L / (dash + gap));
  const P = t => [from[0] + (to[0] - from[0]) * t, from[1] + (to[1] - from[1]) * t];
  return <g opacity={opacity}>{Array.from({length: n}, (_, i) => {
    const t0 = (i * (dash + gap)) / L, t1 = (i * (dash + gap) + dash) / L;
    if (t0 > progress) return null;
    return <InkLine key={i} from={P(t0)} to={P(Math.min(t1, progress))} seed={seed * 100 + i} size={size} color={color} pressure="marker" thinning={0.3} taperStart={1} taperEnd={3}/>;
  })}</g>;
};

/** The ladder itself. climbed = how many rungs are solid; progress draws it on. */
export const Ladder = ({climbed = 4, progress = 1, seed = 900}) => {
  const {x0, x1, yBottom, y0, step, tilt} = LAD;
  const c = [(x0 + x1) / 2, yBottom];
  const R = p => rotPt(p, c, tilt);
  const ySolid = y0 - step * (climbed - 1) - step * 0.45;
  const yTop = y0 - step * 5 - 60;
  return <g>
    {[x0, x1].map((x, i) => <g key={i}>
      <InkPath points={handLine(R([x, yBottom + 10]), R([x + (i ? 4 : -4), ySolid]), {bow: i ? -6 : 6})} seed={seed + i} size={13} pressure="brush" thinning={0.35} jitter={2} ghost={0.3} progress={progress}/>
      <DashLine from={R([x + (i ? 4 : -4), ySolid - 16])} to={R([x + (i ? 6 : -6), yTop])} seed={seed + 10 + i} size={6} opacity={0.55} progress={clamp01(progress * 2 - 1)}/>
    </g>)}
    {RUNGS.map((r, k) => {
      const y = y0 - k * step;
      const a = R([x0 - 6, y + (hash(k, seed) - 0.5) * 8]), b = R([x1 + 6, y + (hash(k, seed + 1) - 0.5) * 8]);
      const pk = clamp01(progress * 7 - k);
      if (k < climbed) return <InkPath key={k} points={handLine(a, b, {bow: 5, over: 10})} seed={seed + 20 + k} size={11} pressure="nib" thinning={0.4} progress={pk}/>;
      return <g key={k}>
        <DashLine from={a} to={b} seed={seed + 40 + k} size={5} dash={16} gap={12} opacity={0.6} progress={pk}/>
      </g>;
    })}
    {/* ground */}
    <InkPath points={handLine([200, yBottom + 14], [720, yBottom + 8], {bow: -3})} seed={seed + 70} size={6} pressure="flick" progress={progress}/>
  </g>;
};

export const V3Ladder = () => {
  const {y0, step} = LAD;
  const lx = 690;
  return <Stage>
    <svg width={W} height={H} style={{position: "absolute"}}>
      <InkDefs/>
      <Halftone bounds={[160, 380, 620, 660]} field={radial(445, 760, 420, 1.4)} cell={14} angle={0.5} color={C.ink} opacity={0.13}/>
      <g filter="url(#v3-ink)"><Ladder/></g>
      {RUNGS.map((r, k) => {
        const y = y0 - k * step;
        return <g key={k}>
          <Mono x={lx} y={y - 34} size={15} weight={700} color={r.ok ? (r.ai ? C.cyan : C.dim) : C.verm} letterSpacing={3}>{`${String(k + 1).padStart(2, "0")} · ${r.ok ? "DONE" : "NOT YET"}`}</Mono>
          {!r.ok ? <g filter="url(#v3-ink)"><Scribble poly={[[lx - 14, y - 26], [lx + (k === 4 ? 330 : 350), y - 30], [lx + (k === 4 ? 336 : 356), y + 36], [lx - 10, y + 38]]} angle={0.9} gap={26} size={4} color={C.verm} seed={80 + k} opacity={0.55} id={`nyscr${k}`}/></g> : null}
          <HandText x={lx} y={y + 26} size={66} seed={30 + k} color={C.ink} opacity={r.ok ? 1 : 0.62}>{r.label}</HandText>
          {r.ev ? <Mono x={lx + 4} y={y + 62} size={19} color={r.ai ? C.cyan : C.ink} opacity={0.85}>{r.ev}</Mono> : null}
          <g filter="url(#v3-ink)">
            {r.ok
              ? <Tick x={620} y={y + 4} s={58} size={10} color={r.ai ? C.cyan : C.ink} seed={60 + k}/>
              : null}
          </g>
          {!r.ok ? <HandText x={lx + (k === 4 ? 380 : 400)} y={y + 24} size={58} seed={40 + k} color={C.verm} rotate={-4}>NOT YET</HandText> : null}
        </g>;
      })}

      {/* headline + we-are-here */}
      <Mono x={1330} y={180} size={20} weight={700} color={C.cyan} letterSpacing={5}>EVIDENCE LADDER</Mono>
      <HandText x={1322} y={300} size={112} seed={2} split={4}>HOW HIGH</HandText>
      <HandText x={1322} y={410} size={112} seed={3} split={4}>HAVE WE</HandText>
      <HandText x={1322} y={520} size={112} seed={4} split={4}>CLIMBED?</HandText>
      <g filter="url(#v3-ink)">
        <Highlight x={52} y={372} w={262} h={62} seed={7}/>
        <HandArrow from={[150, 448]} to={[300, y0 - 3 * step + 12]} bend={0.35} size={7} head={24} seed={17}/>
      </g>
      <Mono x={70} y={414} size={26} weight={800} color={C.bg} letterSpacing={1}>WE ARE HERE</Mono>
      <Mono x={1332} y={640} size={22} color={C.ink}>4 of 6 rungs climbed.</Mono>
      <Mono x={1332} y={676} size={22} color={C.ink}>A promising hit —</Mono>
      <Mono x={1332} y={712} size={22} color={C.ink}>not yet a medicine.</Mono>
      <g filter="url(#v3-ink)"><HandUnderline x={1332} y={728} w={290} size={5} color={C.verm} seed={19}/></g>
      <Dust/>
      <Chrome fig="03"/>
    </svg>
  </Stage>;
};
