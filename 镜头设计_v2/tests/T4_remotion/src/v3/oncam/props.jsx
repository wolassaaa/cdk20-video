// Post-production ink props for ON-CAM lines (script v3.3). Drawn as if by hand around the speaker.
// Every prop: x, y = where its origin sits in card-local pixels; s = scale; start = local frame it begins drawing.
// Ink props boil on 2s (INK layer); the cyan light trail is the computer's (SIGNAL): clean, every frame.
import React from "react";
import {useCurrentFrame} from "remotion";
import {C, ramp, clamp01, outBack, outCubic, outExpo, handLine, loopPts, quad, hash} from "../core";
import {InkPath, InkLine} from "../ink";
import {HandText, Mono} from "../type";
import {HandUnderline, HandCircle, Highlight, ScribbleBurst} from "../marks";

const COLOR = {ink: C.ink, verm: C.verm, cyan: C.cyan, acid: C.acid};
const useLocal = start => useCurrentFrame() - start;
const At = ({x, y, s = 1, rot = 0, ink = true, children}) =>
  <g transform={`translate(${x} ${y}) rotate(${rot}) scale(${s})`}>{ink ? <g filter="url(#oc-ink)">{children}</g> : children}</g>;
const pop = (f, t0, k = 2.2) => outBack(ramp(f, t0, t0 + 6), k);

const roundRect = (x0, y0, x1, y1, r, n = 6) => {
  const arc = (cx, cy, a0) => Array.from({length: n + 1}, (_, i) => { const a = a0 + (i / n) * Math.PI / 2; return [cx + Math.cos(a) * r, cy + Math.sin(a) * r]; });
  return [...arc(x1 - r, y0 + r, -Math.PI / 2), ...arc(x1 - r, y1 - r, 0), ...arc(x0 + r, y1 - r, Math.PI / 2), ...arc(x0 + r, y0 + r, Math.PI), [x1 - r, y0]];
};

/** 2-04 "1 2", 7-01 "1 2 3", 5-02 "001": hand numerals pop on one by one, then an underline. */
export const PropNumerals = ({x, y, s = 1, start = 0, text = "1 2", color = "ink"}) => {
  const f = useLocal(start);
  if (f < 0) return null;
  const col = COLOR[color] || C.ink, chars = [...text], size = 300, adv = size * 0.62, per = 5;
  const w = chars.length * adv, n = chars.filter(ch => ch !== " ").length;
  let order = -1;
  return <At x={x} y={y} s={s}>
    {chars.map((ch, i) => {
      if (ch === " ") return null;
      order++;
      const t0 = order * per;
      if (f < t0) return null;
      const gx = -w / 2 + adv * (i + 0.5), k = pop(f, t0);
      return <g key={i} transform={`translate(${gx} -100) scale(${k}) translate(${-gx} 100)`}>
        <HandText x={gx} y={0} size={size} anchor="middle" color={col} seed={i + 3}>{ch}</HandText>
      </g>;
    })}
    <HandUnderline x={-w / 2} y={60} w={w} size={9} color={col} seed={13} progress={ramp(f, n * per, n * per + 8)}/>
  </At>;
};

// key shape with its tip at the origin, pointing -x (shaft runs +x to the bow)
const Key = ({progress, color = C.cyan, seed = 40}) => <g>
  <InkPath points={handLine([0, 0], [170, 0], {bow: 2})} seed={seed} size={8} color={color} progress={progress} pressure="nib"/>
  <InkPath points={[[18, 0], [18, 24], [42, 24], [42, 10], [62, 10], [62, 0]]} seed={seed + 1} size={6} color={color} progress={progress} pressure="marker"/>
  <InkPath points={loopPts(212, 0, 42, 42, {seed: seed + 2, turns: 1.1})} seed={seed + 2} size={8} color={color} progress={progress}/>
</g>;

/**
 * 3-01 state "sketch": a lock and a key draw themselves.
 * 5-05 state "half": the key turns about 40 degrees and sticks, trembling.
 * 5-09 state "turn": the key turns all the way, the shackle pops and the lock lights vermilion.
 */
export const PropLock = ({x, y, s = 1, start = 0, state = "sketch"}) => {
  const f = useLocal(start);
  if (f < 0) return null;
  const d = ramp(f, 0, 14);
  let ang = 0;
  if (state === "half") ang = 40 * outCubic(ramp(f, 14, 24)) + (f > 24 ? 4 * Math.sin(f * 1.7) * Math.exp(-(f - 24) / 30) : 0);
  if (state === "turn") ang = 90 * outBack(ramp(f, 14, 26), 1.6);
  const lit = state === "turn" ? ramp(f, 22, 32) : 0;
  const up = state === "turn" ? 34 * outBack(ramp(f, 24, 34), 2) : 0;
  const lockCol = lit > 0.5 ? C.verm : C.ink;
  const kh = [0, 90];
  return <At x={x} y={y} s={s}>
    {lit > 0 ? <circle cx={0} cy={80} r={260} fill={C.verm} opacity={0.18 * lit}/> : null}
    <InkPath points={[[-150, -40], [150, -40], [150, 210], [-150, 210], [-150, -40]]} seed={3} size={9} color={lockCol} progress={d} pressure="brush"/>
    <InkPath points={loopPts(0, -40 - up, 100, 130, {a0: Math.PI, turns: 0.5, seed: 5, spiral: 0, wob: 0.02})} seed={4} size={9} color={lockCol} progress={d}/>
    <InkPath points={loopPts(kh[0], kh[1] - 10, 16, 16, {seed: 6})} seed={6} size={6} color={lockCol} progress={ramp(f, 8, 16)}/>
    {state === "sketch"
      ? <g transform="translate(210 90)"><Key progress={ramp(f, 6, 20)}/></g>
      : <g transform={`translate(${kh[0]} ${kh[1]}) rotate(${ang})`}><Key progress={ramp(f, 4, 14)}/></g>}
    {state === "half" && f > 24 ? <g opacity={clamp01((f - 24) / 4)}>
      <InkPath points={quad([250, 170], [278, 210], [250, 250], 10)} seed={70} size={5} color={C.ink} pressure="marker"/>
      <InkPath points={quad([290, 150], [332, 210], [290, 270], 10)} seed={71} size={5} color={C.ink} pressure="marker"/>
    </g> : null}
    {state === "turn" ? <HandCircle cx={40} cy={80} rx={330} ry={270} size={8} color={C.acid} seed={21} progress={ramp(f, 26, 38)}/> : null}
  </At>;
};

/** 4-05: ink scissors snip twice; the low-confidence tail hanging below drops away. Origin = pivot. */
export const PropScissors = ({x, y, s = 1, start = 0}) => {
  const f = useLocal(start);
  if (f < 0) return null;
  const d = ramp(f, 0, 10);
  const open = f < 12 ? 1 : f < 16 ? 1 - outCubic(ramp(f, 12, 16)) : f < 20 ? outCubic(ramp(f, 16, 20)) : 1 - outCubic(ramp(f, 20, 24));
  const a = (6 + 20 * open) * Math.PI / 180;
  const blade = sgn => {
    const tip = [-Math.cos(sgn * a) * 300, -Math.sin(sgn * a) * 300];
    const ra = sgn * (a + 0.35), ring = [Math.cos(ra) * 160, Math.sin(ra) * 160];
    return <g key={sgn}>
      <InkPath points={handLine([0, 0], tip, {bow: sgn * 16})} seed={30 + sgn} size={8} progress={d} pressure="nib"/>
      <InkPath points={handLine([0, 0], tip, {bow: sgn * 3})} seed={32 + sgn} size={5} progress={d} pressure="nib"/>
      <InkPath points={handLine([0, 0], [ring[0] * 0.6, ring[1] * 0.6])} seed={34 + sgn} size={8} progress={d}/>
      <InkPath points={loopPts(ring[0], ring[1], 48, 40, {seed: 36 + sgn, turns: 1.1, rot: ra})} seed={36 + sgn} size={8} progress={d}/>
    </g>;
  };
  const cut = 24, fall = Math.max(0, f - cut), dy = 0.9 * fall * fall, fade = 1 - ramp(f, cut + 8, cut + 22);
  const tail = Array.from({length: 28}, (_, i) => [-200 + 26 * Math.sin(i * 0.9) + 10 * Math.sin(i * 2.3), 14 + i * 9]);
  return <At x={x} y={y} s={s}>
    {fade > 0 ? <g transform={`translate(${-fall * 3} ${dy}) rotate(${fall * 2} -200 14)`} opacity={fade}>
      <InkPath points={tail} seed={50} size={7} color={C.verm} progress={ramp(f, 0, 10)} pressure="marker"/>
    </g> : null}
    {blade(1)}{blade(-1)}
    <circle cx={0} cy={0} r={7} fill={C.ink}/>
    <ScribbleBurst cx={-200} cy={10} r0={30} r1={90} n={9} size={5} color={C.acid} phase={(f - cut) / 10} seed={8}/>
  </At>;
};

/** 4-08: a cyan light trail flicks out of the warm card into the dark (SIGNAL: clean, no boil). Origin = where it leaves the card. */
export const PropTrail = ({x, y, s = 1, start = 0, dir = 1}) => {
  const f = useLocal(start);
  if (f < 0 || f > 40) return null;
  const path = quad([0, 0], [dir * 420, -300], [dir * 880, -120], 80);
  const head = outExpo(ramp(f, 0, 14)) * (path.length - 1), len = 34 * (1 - 0.6 * ramp(f, 10, 24));
  const fade = 1 - ramp(f, 16, 34);
  const segs = [];
  for (let i = Math.max(1, Math.floor(head - len)); i <= Math.floor(head); i++) {
    const k = 1 - (head - i) / len;
    segs.push(<line key={i} x1={path[i - 1][0]} y1={path[i - 1][1]} x2={path[i][0]} y2={path[i][1]} stroke={C.cyan} strokeWidth={2 + 14 * k} strokeLinecap="round" opacity={k}/>);
  }
  const h = path[Math.floor(head)];
  return <At x={x} y={y} s={s} ink={false}>
    <defs><filter id="oc-glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="9"/></filter></defs>
    <g opacity={fade}>
      <g filter="url(#oc-glow)">{segs}</g>
      {segs}
      <circle cx={h[0]} cy={h[1]} r={10} fill="#FFFFFF"/>
      {Array.from({length: 10}, (_, i) => {
        const j = Math.max(0, Math.floor(head - hash(i, 3) * len * 1.4)), q = path[j];
        return <circle key={i} cx={q[0] + (hash(i, 4) - 0.5) * 40} cy={q[1] + (hash(i, 5) - 0.5) * 40} r={1.5 + hash(i, 6) * 3} fill={C.cyan}/>;
      })}
    </g>
  </At>;
};

/** 8-05: an ink phone with a headline bar. Generic news layout only: no real outlet's name or branding. */
export const PropPhone = ({x, y, s = 1, start = 0}) => {
  const f = useLocal(start);
  if (f < 0) return null;
  const d = ramp(f, 0, 12);
  return <At x={x} y={y} s={s} rot={-6}>
    <InkPath points={roundRect(-165, -320, 165, 320, 44)} seed={80} size={9} progress={d}/>
    <InkPath points={handLine([-40, -292], [40, -292])} seed={81} size={7} progress={ramp(f, 6, 12)}/>
    <Highlight x={-128} y={-235} w={256} h={50} seed={82} progress={ramp(f, 10, 16)}/>
    <Mono x={-112} y={-200} size={22} weight={800} color={C.bg} reveal={ramp(f, 14, 20)}>HEADLINE</Mono>
    {[0, 1, 2, 3, 4].map(i => <InkLine key={i} from={[-125, -140 + i * 34]} to={[-125 + [240, 210, 250, 170, 220][i], -140 + i * 34]}
      seed={90 + i} size={5} color={C.dim} progress={ramp(f, 14 + i * 2, 20 + i * 2)} pressure="marker"/>)}
    <InkPath points={[[-125, 60], [125, 60], [125, 220], [-125, 220], [-125, 60]]} seed={96} size={6} color={C.cyan} progress={ramp(f, 22, 30)}/>
    <InkPath points={[...Array.from({length: 7}, (_, i) => { const t = i / 6 * Math.PI * 2 + 0.5; return [Math.cos(t) * 42, 140 + Math.sin(t) * 42]; })]}
      seed={97} size={6} color={C.cyan} progress={ramp(f, 28, 36)}/>
  </At>;
};

/** 6-04: 13 vermilion ink dots appear one by one in cupped hands, then a big "13". */
export const PropDots = ({x, y, s = 1, start = 0, count = 13, number = true}) => {
  const f = useLocal(start);
  if (f < 0) return null;
  return <At x={x} y={y} s={s}>
    {Array.from({length: count}, (_, i) => {
      const t0 = 2 + i * 2;
      if (f < t0) return null;
      const a = i * 2.399963, r = Math.sqrt((i + 0.5) / count);
      const dx = Math.cos(a) * r * 140, dy = Math.sin(a) * r * 80, k = pop(f, t0, 2.6);
      return <g key={i} transform={`translate(${dx} ${dy}) scale(${k})`}>
        <InkPath points={loopPts(0, 0, 11, 11, {turns: 1.7, spiral: 0.5, seed: i + 60})} seed={i + 60} size={16} color={C.verm} pressure="marker"/>
      </g>;
    })}
    {number && f >= 32 ? <g transform={`translate(250 -150) scale(${pop(f, 32)}) translate(-250 150)`}>
      <HandText x={250} y={-90} size={230} anchor="middle" color={C.verm} seed={13}>13</HandText>
    </g> : null}
  </At>;
};

/** 1-07: C pulls out an ink "10-17 years" timeline. Origin = left end. */
export const PropTimeline = ({x, y, s = 1, start = 0}) => {
  const f = useLocal(start);
  if (f < 0) return null;
  const L = 1150, d = outCubic(ramp(f, 0, 14));
  return <At x={x} y={y} s={s}>
    <InkPath points={handLine([0, 0], [L, -8], {bow: -6, over: 4})} seed={100} size={8} progress={d} pressure="nib"/>
    <circle cx={0} cy={0} r={9} fill={C.ink} opacity={clamp01(f / 3)}/>
    {Array.from({length: 17}, (_, i) => {
      const tx = L * (i + 1) / 17.4, late = i >= 9;
      if (tx > L * d) return null;
      return <InkLine key={i} from={[tx, late ? -30 : -18]} to={[tx, late ? 30 : 18]} seed={110 + i} size={late ? 6 : 4} color={late ? C.verm : C.ink} pressure="marker"/>;
    })}
    <InkPath points={[[L * 10 / 17.4, -60], [L * 10 / 17.4, -80], [L * 17 / 17.4, -82], [L * 17 / 17.4, -62]]} seed={130} size={6} color={C.verm} progress={ramp(f, 14, 22)} pressure="marker"/>
    <HandText x={L * 13.5 / 17.4} y={-110} size={96} anchor="middle" color={C.ink} seed={131} reveal={ramp(f, 14, 26)}>10-17 YEARS</HandText>
    <Mono x={-6} y={58} size={22} color={C.dim} reveal={ramp(f, 4, 10)}>0</Mono>
  </At>;
};

/** 1-01: a single vermilion ink line under the card with a heartbeat blip running along it (period 1 s). Origin = left end. */
export const PropPulse = ({x, y, s = 1, start = 0, width = 900}) => {
  const f = useLocal(start);
  if (f < 0) return null;
  const amp = ramp(f, 12, 20), head = ((f % 30) / 30) * (width + 300) - 150;
  const k = u => -70 * Math.exp(-((u / 9) ** 2)) + 22 * Math.exp(-(((u + 28) / 10) ** 2)) + 30 * Math.exp(-(((u - 26) / 12) ** 2));
  const pts = [];
  for (let px = 0; px <= width; px += 5) pts.push([px, amp * k(px - head)]);
  return <At x={x} y={y} s={s}>
    <InkPath points={pts} seed={140} size={6} color={C.verm} progress={ramp(f, 0, 12)} pressure="marker" spacing={5}/>
  </At>;
};
