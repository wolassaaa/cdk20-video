import React from "react";
import {AbsoluteFill, OffthreadVideo, staticFile} from "remotion";
import {plan, SI, C, MONO, SERIF, HAND, ANTON, CBack, CLines, Boil, clamp01, outCubic, outBack, inOut, lerp, hash, countBefore, hits, env, nthDown, nthBeat} from "./common";
import {MixBack} from "./Silicon";

// Carbon shots: the body, cells, the lab. Warm fluorescence on dark, serif and hand-written type, boiling hand-drawn lines.
// Mix shots (dish, ladder, verdict, radio) are where the computer's answer meets living cells.

const Glow = ({id, sd = 10}) => (
  <filter id={id} x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation={sd} result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
);

// a Blender clip regraded into the warm world
export const CClip = ({s, t, f, local}) => {
  const {src, rate = 1, lines = []} = s.props, k = env("kick", f);
  return <CBack f={f} local={local}>
    <AbsoluteFill style={{transform: `translateX(300px) scale(${1.04 + local * 0.01})`,
      filter: `grayscale(1) sepia(1) saturate(2.4) hue-rotate(-12deg) contrast(1.15) brightness(${1.05 + 0.25 * k})`}}>
      <OffthreadVideo src={staticFile(src)} playbackRate={rate} muted style={{width: "100%", height: "100%", objectFit: "cover"}}/>
    </AbsoluteFill>
    <AbsoluteFill style={{background: "linear-gradient(90deg, rgba(19,10,7,0.85), rgba(19,10,7,0) 60%)"}}/>
    <CLines lines={lines} t={t} at={s.at}/>
  </CBack>;
};

const Cell = ({x, y, r, lit, boil}) => (
  <g>
    <circle cx={x} cy={y} r={r} fill={C.magenta} opacity={0.16} filter="url(#cglow)"/>
    <circle cx={x} cy={y} r={r} fill="none" stroke={C.amber} strokeWidth={3} opacity={0.55} filter={boil}/>
    <circle cx={x} cy={y} r={r * 0.42} fill={C.amber} opacity={0.55 + 0.45 * lit} filter="url(#cglow)"/>
  </g>
);

// fluorescent cells dividing on the beat (4 -> 8 -> 16 -> 32); zoom: one cell with CDK20 lighting up inside
export const Cells = ({s, t, f, local}) => {
  const k = env("kick", f), HATS = hits("hat"), hatN = countBefore(HATS, t);
  const bid = "boil" + f;
  if (s.props.zoom) {
    const arrow = clamp01((t - nthBeat(s.at, 4)) / 0.6);
    return <CBack f={f} local={local}>
      <svg width="1920" height="1080" style={{position: "absolute", transform: `scale(${1 + local * 0.02})`, transformOrigin: "1150px 580px"}}>
        <defs><Glow id="cglow" sd={14}/><Boil id={bid} f={f} scale={5}/></defs>
        <circle cx={1150} cy={580} r={400} fill={C.magenta} opacity={0.12} filter="url(#cglow)"/>
        <circle cx={1150} cy={580} r={400} fill="none" stroke={C.amber} strokeWidth={4} opacity={0.6} filter={`url(#${bid})`}/>
        <circle cx={1170} cy={600} r={150} fill={C.amber} opacity={0.35 + 0.3 * k} filter="url(#cglow)"/>
        {Array.from({length: 44}, (_, i) => {
          const a = hash(i, 1) * Math.PI * 2, rr = 200 + hash(i, 2) * 170, on = (hatN + i * 7) % 44 < 3 ? env("hat", f) : 0;
          return <circle key={i} cx={1150 + Math.cos(a) * rr} cy={580 + Math.sin(a) * rr} r={9 + 4 * on} fill={C.magenta} opacity={0.6 + 0.4 * on} filter="url(#cglow)"/>;
        })}
        <path d="M 760 880 C 820 820, 860 780, 905 742" fill="none" stroke={C.ink} strokeWidth={4} strokeLinecap="round" strokeDasharray="260" strokeDashoffset={260 * (1 - arrow)} filter={`url(#${bid})`}/>
        <text x={600} y={940} fill={C.ink} fontFamily={HAND} fontSize={72} opacity={arrow}>CDK20</text>
      </svg>
      <CLines lines={s.props.lines} t={t} at={s.at}/>
    </CBack>;
  }
  const splits = [2, 4, 6].map(b => nthBeat(s.at, b));
  const level = countBefore(splits, t);
  const roots = [[-300, -120], [260, -170], [-180, 190], [330, 160]];
  const cells = [];
  for (let j = 0; j < 4 << level; j++) {
    let x = 1120 + roots[j >> level][0], y = 590 + roots[j >> level][1];
    for (let l = 1; l <= level; l++) {
      const prefix = j >> (level - l), a = hash(prefix, l) * Math.PI * 2, d = 120 * Math.pow(0.78, l - 1) * 0.95;
      const p = outBack((t - splits[l - 1]) / 0.45), sgn = prefix & 1 ? 1 : -1;
      x += Math.cos(a) * d * p * sgn; y += Math.sin(a) * d * p * sgn;
    }
    cells.push(<Cell key={j} x={x} y={y} r={120 * Math.pow(0.78, level)} lit={k * (0.5 + hash(j, 9) * 0.5)} boil={`url(#${bid})`}/>);
  }
  return <CBack f={f} local={local}>
    <svg width="1920" height="1080" style={{position: "absolute"}}>
      <defs><Glow id="cglow"/><Boil id={bid} f={f}/></defs>
      {cells}
    </svg>
    <CLines lines={s.props.lines} t={t} at={s.at}/>
    <div style={{position: "absolute", right: 120, top: 120, fontFamily: HAND, fontSize: 64, color: C.amber}}>× {4 << level}</div>
  </CBack>;
};

// protein-as-lock drawing; the pocket is a dip at the top
const blob = (cx, cy, R) => {
  const pts = Array.from({length: 96}, (_, i) => {
    const th = i / 96 * Math.PI * 2 - Math.PI;
    const dip = Math.exp(-Math.pow((th + Math.PI / 2) / 0.26, 2));
    const r = R + 26 * Math.sin(3 * th + 1) + 16 * Math.sin(5 * th) - 150 * dip;
    return [cx + Math.cos(th) * r, cy + Math.sin(th) * r];
  });
  return "M " + pts.map(p => p.map(v => v.toFixed(1)).join(" ")).join(" L ") + " Z";
};
const KeyGlyph = ({x, y, rot, color, scale = 1}) => (
  <g transform={`translate(${x} ${y}) rotate(${rot}) scale(${scale})`}>
    <polygon points={Array.from({length: 6}, (_, i) => `${Math.cos(i * Math.PI / 3) * 40},${Math.sin(i * Math.PI / 3) * 40 - 30}`).join(" ")} fill="none" stroke={color} strokeWidth={7}/>
    <polygon points={Array.from({length: 5}, (_, i) => `${Math.cos(i * 2 * Math.PI / 5 - Math.PI / 2) * 30 + 62},${Math.sin(i * 2 * Math.PI / 5 - Math.PI / 2) * 30 - 70}`).join(" ")} fill="none" stroke={color} strokeWidth={7}/>
    <path d="M 0 10 L 0 60 L 22 80" fill="none" stroke={color} strokeWidth={7} strokeLinecap="round"/>
  </g>
);
export const LockKey = ({s, t, f, local}) => {
  const {mode, lines} = s.props, k = env("kick", f), bid = "boil" + f;
  const cx = 1180, cy = 600, seat = cy - 300 + 150 + 10;
  let ky = seat, rot = 0, lockGlow = 0.15, keyColor = C.ink, dash, extra = null;
  if (mode === "fit") {
    const land = nthBeat(s.at, 2), p = outBack((t - land) / 0.4);
    ky = lerp(120, seat, p); lockGlow = 0.15 + 0.5 * Math.exp(-(t - land - 0.4) * 3) * (t > land + 0.35 ? 1 : 0);
  } else if (mode === "unknown") {
    ky = 170 + Math.sin(local * 2.4) * 18; dash = "18 16"; lockGlow = 0.05;
    extra = [[960, 420], [1450, 470], [1300, 860], [990, 820], [1180, 330]].map(([x, y], i) => {
      const a = nthBeat(s.at, 1 + i), p = outBack((t - a) / 0.3);
      return t < a ? null : <text key={i} x={x} y={y} fill={C.amber} fontFamily={HAND} fontSize={110} opacity={0.85} transform={`rotate(${(hash(i) - 0.5) * 30} ${x} ${y}) scale(1)`}
        style={{transformBox: "fill-box", transformOrigin: "center", transform: `scale(${p})`}}>?</text>;
    });
  } else if (mode === "noturn") {
    const sn = hits("snare", 0.5), last = sn[countBefore(sn, t) - 1] ?? -9, age = t - last;
    rot = age < 0.5 ? Math.sin(age * 40) * 12 * Math.exp(-age * 6) : 0;
    extra = <text x={1460} y={300} fill={C.amber} fontFamily={HAND} fontSize={70} transform="rotate(-6 1460 300)">won't turn</text>;
  } else if (mode === "turn") {
    const go = nthDown(s.at, 1), p = outBack((t - go) / 0.5);
    rot = 90 * p; lockGlow = 0.15 + 0.55 * clamp01((t - go) / 0.4) + 0.2 * k; keyColor = p > 0.5 ? SI.accent : C.ink;
    extra = p > 0.5 ? Array.from({length: 16}, (_, i) => {
      const a = hash(i, 4) * Math.PI * 2, d = 330 + (t - go) * 160 * hash(i, 5);
      return <circle key={i} cx={cx + Math.cos(a) * d} cy={cy + Math.sin(a) * d} r={5} fill={SI.accent} opacity={Math.max(0, 1 - (t - go) / 2)}/>;
    }) : null;
  }
  return <CBack f={f} local={local}>
    <svg width="1920" height="1080" style={{position: "absolute"}}>
      <defs><Glow id="cglow" sd={16}/><Boil id={bid} f={f} scale={5}/></defs>
      <path d={blob(cx, cy, 300)} fill={C.amber} opacity={lockGlow} filter="url(#cglow)"/>
      <path d={blob(cx, cy, 300)} fill="none" stroke={C.amber} strokeWidth={6} strokeDasharray={dash} opacity={mode === "unknown" ? 0.35 : 0.9} filter={`url(#${bid})`}/>
      <g filter={`url(#${bid})`}><KeyGlyph x={cx} y={ky} rot={rot} color={keyColor}/></g>
      {extra}
    </svg>
    <CLines lines={lines} t={t} at={s.at}/>
  </CBack>;
};

// how long a drug usually takes, drawn by hand; the 30 days is a hair-thin cyan mark at the very start
export const Timeline = ({s, t, f, local}) => {
  const b = i => nthDown(s.at, i), grow = inOut((t - b(0)) / (b(2) - b(0))), bid = "boil" + f;
  const x0 = 160, x1 = 1760, y = 560;
  const fade = i => outCubic((t - b(i)) / 0.5);
  return <CBack f={f} local={local}>
    <div style={{position: "absolute", left: 160, top: 120, fontFamily: SERIF, fontSize: 76, fontWeight: 600, color: C.amber}}>A new drug: 10–17 years</div>
    <div style={{position: "absolute", left: 160, top: 230, fontFamily: SERIF, fontSize: 44, fontStyle: "italic", color: C.ink, opacity: fade(1)}}>about US$2.8 billion each</div>
    <div style={{position: "absolute", left: 160, top: 296, fontFamily: SERIF, fontSize: 44, fontStyle: "italic", color: C.ink, opacity: fade(2)}}>roughly 1 in 10 drugs tested in people reaches patients</div>
    <svg width="1920" height="1080" style={{position: "absolute"}}>
      <defs><Boil id={bid} f={f} scale={4}/></defs>
      <path d={`M ${x0} ${y} L ${lerp(x0, x1, grow)} ${y}`} stroke={C.amber} strokeWidth={14} strokeLinecap="round" filter={`url(#${bid})`}/>
      {Array.from({length: 18}, (_, i) => {
        const x = lerp(x0, x1, i / 17); if (x > lerp(x0, x1, grow) + 1) return null;
        return <g key={i}><path d={`M ${x} ${y + 16} L ${x} ${y + (i % 5 ? 34 : 50)}`} stroke={C.ink} strokeWidth={3} filter={`url(#${bid})`}/>
          {i % 5 === 0 || i === 17 ? <text x={x - 10} y={y + 100} fill={C.ink} fontFamily={HAND} fontSize={44}>{i}</text> : null}</g>;
      })}
      <text x={x1 - 40} y={y + 160} fill={C.quiet} fontFamily={HAND} fontSize={40}>years</text>
      <g opacity={fade(3)}>
        <line x1={x0} y1={y - 40} x2={x0} y2={y + 30} stroke={SI.accent} strokeWidth={4}/>
        <text x={x0 - 6} y={y - 60} fill={SI.accent} fontFamily={MONO} fontSize={30}>30 days ↓ only the very first step</text>
      </g>
    </svg>
    <div style={{position: "absolute", right: 110, top: 70, fontFamily: MONO, fontSize: 18, color: C.quiet}}>Wang et al., Pharmaceuticals 2023</div>
  </CBack>;
};

// a hand-drawn flask: seven glowing designs drop in on the beats, bubbles on the hats
export const Flask = ({s, t, f, local}) => {
  const HATS = hits("hat"), bid = "boil" + f, cx = 1180, cy = 650, R = 230;
  const bubbles = HATS.filter(h => h > s.at - 1.2 && h <= t).slice(-14);
  return <CBack f={f} local={local}>
    <svg width="1920" height="1080" style={{position: "absolute"}}>
      <defs><Glow id="cglow" sd={12}/><Boil id={bid} f={f} scale={4}/>
        <clipPath id="liquid"><circle cx={cx} cy={cy} r={R - 8}/></clipPath></defs>
      <rect x={cx - R} y={cy - 20 + Math.sin(local * 3) * 6} width={2 * R} height={R + 40} fill={C.amber} opacity={0.28} clipPath="url(#liquid)" filter="url(#cglow)"/>
      {bubbles.map((h, i) => { const a = (t - h) / 1.2; return <circle key={h} cx={cx + (hash(Math.round(h * 100)) - 0.5) * 260} cy={cy + 180 - a * 200} r={6 + 6 * hash(i)} fill="none" stroke={C.ink} strokeWidth={2} opacity={1 - a} clipPath="url(#liquid)"/>; })}
      {Array.from({length: 7}, (_, i) => {
        const a = nthBeat(s.at, i), p = clamp01((t - a) / 0.45);
        if (t < a) return null;
        const x = cx + (i - 3) * 46, y = lerp(130, cy + 40 + (i % 3) * 40, outCubic(p));
        return <circle key={i} cx={x} cy={y} r={14} fill={p < 1 ? SI.accent : C.amber} filter="url(#cglow)"/>;
      })}
      <path d={`M ${cx - 55} 200 L ${cx - 55} ${cy - R + 18} A ${R} ${R} 0 1 0 ${cx + 55} ${cy - R + 18} L ${cx + 55} 200`} fill="none" stroke={C.ink} strokeWidth={6} filter={`url(#${bid})`}/>
      <path d={`M ${cx - 75} 200 L ${cx + 75} 200`} stroke={C.ink} strokeWidth={6} filter={`url(#${bid})`}/>
    </svg>
    <CLines lines={s.props.lines} t={t} at={s.at}/>
  </CBack>;
};

// two dishes: dose of 048 climbs; liver cancer cells (Huh7) fade first, kidney cells (HEK293) hold on much longer
const Dish = ({cx, cy, r, ic50, dose, label, f, n = 70, rain}) => {
  const k = env("kick", f);
  return <g>
    <circle cx={cx} cy={cy} r={r} fill="rgba(255,255,255,0.025)" stroke={C.ink} strokeWidth={3} opacity={0.8}/>
    {Array.from({length: n}, (_, i) => {
      const a = hash(i, 1) * Math.PI * 2, d = Math.sqrt(hash(i, 2)) * (r - 40), x = cx + Math.cos(a) * d, y = cy + Math.sin(a) * d;
      const v = ic50 ? 1 / (1 + Math.pow(dose / ic50, 1.4)) : 1, alive = hash(i, 3) < v ? 1 : 0.12;
      return <g key={i} opacity={alive}>
        <circle cx={x} cy={y} r={22} fill={C.magenta} opacity={0.22} filter="url(#cglow)"/>
        <circle cx={x} cy={y} r={9} fill={C.amber} opacity={0.6 + 0.4 * k * alive} filter="url(#cglow)"/>
      </g>;
    })}
    {rain}
    <text x={cx} y={cy + r + 70} fill={C.amber} fontFamily={HAND} fontSize={54} textAnchor="middle">{label}</text>
  </g>;
};
export const DishScene = ({s, t, f, local}) => {
  const HATS = hits("hat"), drops = HATS.filter(h => h <= t && h > t - 0.8);
  const rain = (cx, cy, r) => drops.map(h => {
    const p = (t - h) / 0.8, a = hash(Math.round(h * 1000), 1) * Math.PI * 2, d = Math.sqrt(hash(Math.round(h * 1000), 2)) * (r - 30);
    return <circle key={h} cx={cx + Math.cos(a) * d} cy={lerp(cy - r - 300, cy + Math.sin(a) * d, outCubic(p))} r={7} fill={SI.accent} opacity={1 - p * 0.6} filter="url(#cglow)"/>;
  });
  if (s.props.single) return <MixBack f={f} local={local}>
    <svg width="1920" height="1080" style={{position: "absolute"}}><defs><Glow id="cglow" sd={8}/></defs>
      <Dish cx={1200} cy={560} r={340} f={f} label="Huh7 · liver cancer cells" rain={rain(1200, 560, 340)}/></svg>
    <CLines lines={s.props.lines} t={t} at={s.at}/>
  </MixBack>;
  const a = nthDown(s.at, 1), z = s.at + s.dur - 1.2;
  const logd = lerp(0, 4, inOut((t - a) / (z - a))), dose = Math.pow(10, logd); // 1 nM -> 10 µM
  const fmt = dose < 1000 ? `${dose.toFixed(dose < 10 ? 1 : 0)} nM` : `${(dose / 1000).toFixed(2)} µM`;
  return <MixBack f={f} local={local}>
    <svg width="1920" height="1080" style={{position: "absolute"}}><defs><Glow id="cglow" sd={8}/></defs>
      <Dish cx={600} cy={600} r={290} ic50={208.7} dose={dose} f={f} label="Huh7 · liver cancer" rain={rain(600, 600, 290)}/>
      <Dish cx={1320} cy={600} r={290} ic50={1706.7} dose={dose} f={f} label="HEK293 · kidney (control)" rain={rain(1320, 600, 290)}/>
    </svg>
    <div style={{position: "absolute", left: 0, right: 0, top: 120, textAlign: "center", fontFamily: MONO}}>
      <div style={{fontSize: 22, color: SI.quiet, letterSpacing: 4}}>048 DOSE</div>
      <div style={{fontSize: 84, fontWeight: 700, color: SI.accent}}>{fmt}</div>
    </div>
    <div style={{position: "absolute", right: 90, bottom: 60, fontFamily: MONO, fontSize: 16, color: C.quiet}}>fading = growth held back · drawn from the paper's IC50s, not a real image</div>
  </MixBack>;
};

const RUNGS = [["Predicted", "AlphaFold + generative AI", SI.accent], ["Binds", "001, then 048", SI.accent], ["Blocks the enzyme", "048", C.amber],
  ["Works in cells", "liver cancer cells", C.amber], ["Animals", "not yet", C.quiet], ["Patients", "not yet", C.quiet]];
export const Ladder = ({s, t, f, local}) => (
  <MixBack f={f} local={local}>
    <div style={{position: "absolute", left: 140, top: 90, fontFamily: SERIF, fontSize: 64, fontWeight: 600, color: C.ink}}>How far did the evidence get?</div>
    {RUNGS.map(([name, note, color], i) => {
      const at = nthDown(s.at, Math.min(i, 4)), on = t >= at, p = outBack((t - at) / 0.3), y = 880 - i * 118, x = 220 + i * 120;
      const later = i >= 4;
      return <div key={name} style={{position: "absolute", left: x, top: y, width: 760, height: 96, borderRadius: 14, padding: "12px 26px",
        border: `3px ${later ? "dashed" : "solid"} ${on ? color : "#3A4A58"}`, background: on && !later ? `${color}1F` : "transparent",
        transform: `scale(${on ? 0.9 + 0.1 * p : 0.9})`, transformOrigin: "left center", opacity: on ? 1 : 0.35}}>
        <div style={{fontFamily: SERIF, fontSize: 36, fontWeight: 600, color: on ? C.ink : C.quiet}}>{i + 1} · {name}</div>
        <div style={{fontFamily: later ? HAND : MONO, fontSize: later ? 40 : 22, color: later ? C.amber : SI.quiet, marginTop: later ? -4 : 2}}>{note}</div>
      </div>;
    })}
  </MixBack>
);

// the answer, landing on the song's words: yes on the bar, 'not yet' on the key word
export const Verdict = ({s, t, f, local}) => {
  const actC = plan.acts.find(a => a.name === "C"), song = x => actC.at + x - 0.67;
  const yes = song(62.6), q2 = song(64.0), no = song(65.3);
  const pop = a => outBack((t - a) / 0.3);
  return <MixBack f={f} local={local}>
    <div style={{position: "absolute", left: 200, top: 250, fontFamily: SERIF, fontSize: 96, color: C.ink}}>Worth testing?
      <span style={{fontFamily: MONO, fontWeight: 700, color: SI.accent, marginLeft: 40, display: "inline-block", opacity: t >= yes ? 1 : 0, transform: `scale(${t >= yes ? pop(yes) : 0})`}}>Yes.</span></div>
    <div style={{position: "absolute", left: 200, top: 480, fontFamily: SERIF, fontSize: 96, color: C.ink, opacity: outCubic((t - q2) / 0.4)}}>A medicine?
      <span style={{fontFamily: HAND, fontWeight: 700, fontSize: 150, color: C.amber, marginLeft: 40, display: "inline-block", opacity: t >= no ? 1 : 0, transform: `rotate(-4deg) scale(${t >= no ? pop(no) : 0})`}}>Not yet.</span></div>
  </MixBack>;
};

// act B -> C: an old radio dial sweeps from the silicon end to the carbon end through static
export const Radio = ({s, t, f, local}) => {
  const p = clamp01(local / s.dur), synth = env("synth", f);
  const x0 = 260, x1 = 1660, nx = lerp(x0, x1, inOut(p)) + (hash(f, 2) - 0.5) * 30 * synth;
  return <AbsoluteFill style={{background: `linear-gradient(90deg, ${SI.bg}, ${C.bg})`}}>
    <AbsoluteFill style={{background: C.bg, opacity: inOut(p)}}/>
    <div style={{position: "absolute", left: 0, right: 0, top: 260, textAlign: "center", fontFamily: SERIF, fontSize: 64, fontStyle: "italic", color: C.ink, opacity: outCubic(p * 2)}}>from the screen to the lab</div>
    <svg width="1920" height="1080" style={{position: "absolute"}}>
      <rect x={x0 - 60} y={480} width={x1 - x0 + 120} height={180} rx={20} fill="rgba(0,0,0,0.35)" stroke={C.quiet} strokeWidth={2}/>
      {Array.from({length: 57}, (_, i) => { const x = lerp(x0, x1, i / 56); return <line key={i} x1={x} y1={520} x2={x} y2={i % 4 ? 545 : 565} stroke={C.quiet} strokeWidth={2}/>; })}
      <text x={x0} y={630} fill={SI.accent} fontFamily={MONO} fontSize={34}>Si · silicon</text>
      <text x={x1} y={630} fill={C.amber} fontFamily={MONO} fontSize={34} textAnchor="end">C · carbon</text>
      <line x1={nx} y1={495} x2={nx} y2={645} stroke={p < 0.5 ? SI.accent : C.amber} strokeWidth={6}/>
    </svg>
    <svg width="1920" height="1080" style={{position: "absolute", inset: 0, opacity: 0.05 + 0.2 * Math.sin(p * Math.PI), mixBlendMode: "screen"}}>
      <filter id={"st" + f}><feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="1" seed={f % 89}/><feColorMatrix type="saturate" values="0"/></filter>
      <rect width="1920" height="1080" filter={`url(#st${f})`}/>
    </svg>
  </AbsoluteFill>;
};

export const Credits = ({s, t, f, local}) => {
  const items = ["Test cut · no narration · not the final video",
    "Music: The Weeknd — Blinding Lights · Sacrifice · Out of Time (course test use only)",
    "Science: Ren et al., Chem. Sci. 2023 · Feng et al., J. Clin. Invest. 2011 · Wang et al., Pharmaceuticals 2023",
    "3D: Blender · BodyParts3D (CC BY-SA 2.1 JP) · AlphaFold DB AF-Q8IZL9 (CC BY 4.0) · our own re-docking (AutoDock Vina)"];
  return <CBack f={f} local={local}>
    <div style={{position: "absolute", left: 160, top: 260, fontFamily: SERIF, fontSize: 96, fontWeight: 600, color: C.amber}}>Worth Testing?</div>
    <div style={{position: "absolute", left: 164, top: 390, fontFamily: HAND, fontSize: 48, color: C.ink}}>carbon vs silicon · test 2</div>
    {items.map((it, i) => {
      const at = nthDown(s.at, i + 1);
      return <div key={i} style={{position: "absolute", left: 164, top: 500 + i * 60, fontFamily: MONO, fontSize: 24, color: C.quiet, opacity: outCubic((t - at) / 0.5)}}>{it}</div>;
    })}
  </CBack>;
};
