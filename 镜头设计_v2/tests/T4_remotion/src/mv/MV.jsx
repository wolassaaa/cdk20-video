import {AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile, useCurrentFrame, interpolate, Easing} from "remotion";
import plan from "./mv_plan.json";

// 5-minute music test: Blender clips + 2D scenes, every cut and text reveal placed on the songs' bars and beats
// (plan built by mv_test/build_plan.py). No narration.
const FPS = plan.fps;
const CYAN = "#7FE3FA", ORANGE = "#FF8A4C", INK = "#EEF4F8", QUIET = "#93A6B5", BG = "#03070C";
const SANS = '"Segoe UI", "Microsoft YaHei", sans-serif';
const MONO = 'Consolas, "Cascadia Mono", monospace';
const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"};

// last value <= t in a sorted list (binary search), or null
const lastBefore = (arr, t) => {
  let lo = 0, hi = arr.length - 1, ans = null;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    if (arr[mid] <= t) { ans = arr[mid]; lo = mid + 1; } else hi = mid - 1;
  }
  return ans;
};
// the n-th downbeat at or after time t0 (n = 0 is the first)
const nthDownbeat = (t0, n) => {
  const after = plan.downbeats.filter(d => d >= t0 - 0.02);
  return after[Math.min(n, after.length - 1)] ?? t0;
};
// 1 on a beat, decaying to 0 before the next
const pulse = (arr, t, decay) => {
  const b = lastBefore(arr, t);
  return b === null ? 0 : Math.exp(-(t - b) * decay);
};

// word lines that land one per bar, starting on the scene's first downbeat
const Lines = ({lines, t, start, size = 64, x = 120, y = 760, align = "left", color = INK}) => (
  <div style={{position: "absolute", left: align === "left" ? x : 0, right: align === "left" ? "auto" : 0, top: y, textAlign: align, fontFamily: SANS}}>
    {lines.map((line, i) => {
      const at = nthDownbeat(start, i);
      const p = interpolate(t, [at, at + 0.35], [0, 1], {...clamp, easing: Easing.out(Easing.cubic)});
      return <div key={i} style={{fontSize: i === 0 ? size : size * 0.82, fontWeight: i === 0 ? 700 : 500, color: i === 0 ? color : INK,
        opacity: p, transform: `translateY(${(1 - p) * 24}px)`, textShadow: "0 4px 24px rgba(0,0,0,0.8)", lineHeight: 1.2}}>{line}</div>;
    })}
  </div>
);

const Grid = ({t}) => {
  const b = pulse(plan.downbeats, t, 3);
  return <AbsoluteFill style={{background: `radial-gradient(circle at 50% 45%, rgba(40,90,130,${0.18 + 0.12 * b}), ${BG} 70%)`}}>
    <svg width="1920" height="1080" style={{opacity: 0.18 + 0.15 * b}}>
      {Array.from({length: 13}, (_, i) => <line key={"v" + i} x1={i * 160} y1="0" x2={i * 160} y2="1080" stroke={CYAN} strokeWidth="0.6"/>)}
      {Array.from({length: 8}, (_, i) => <line key={"h" + i} x1="0" y1={i * 160} x2="1920" y2={i * 160} stroke={CYAN} strokeWidth="0.6"/>)}
    </svg>
  </AbsoluteFill>;
};

const Clip = ({s, t, local}) => {
  const {src, rate = 1, lines = [], counter} = s.props;
  const b = pulse(plan.downbeats, t, 5);
  const zoom = interpolate(local, [0, s.dur], [1, 1.07]);
  return <AbsoluteFill style={{background: BG}}>
    <AbsoluteFill style={{transform: `scale(${zoom})`, filter: `brightness(${1 + 0.18 * b})`}}>
      <OffthreadVideo src={staticFile(src)} playbackRate={rate} muted style={{width: "100%", height: "100%", objectFit: "cover"}}/>
    </AbsoluteFill>
    <AbsoluteFill style={{background: "linear-gradient(90deg, rgba(3,7,12,0.75), rgba(3,7,12,0) 55%)"}}/>
    <Lines lines={lines} t={t} start={s.at}/>
    {counter ? <Counter from={counter[0]} to={counter[1]} t={t} s={s}/> : null}
  </AbsoluteFill>;
};

const Counter = ({from, to, t, s}) => {
  const a = nthDownbeat(s.at, 1), z = nthDownbeat(s.at, 5);
  const v = interpolate(t, [a, z], [from, to], {...clamp, easing: Easing.inOut(Easing.cubic)});
  return <div style={{position: "absolute", right: 120, top: 110, textAlign: "right", fontFamily: MONO}}>
    <div style={{fontSize: 22, color: QUIET, letterSpacing: 3}}>BINDING · Kd</div>
    <div style={{fontSize: 84, color: v < 1000 ? ORANGE : INK, fontWeight: 600}}>{v.toLocaleString("en-US", {maximumFractionDigits: v < 1000 ? 1 : 0})} nM</div>
  </div>;
};

const Title = ({s, t}) => <AbsoluteFill><Grid t={t}/><Lines lines={s.props.lines} t={t} start={s.at} size={110} y={380} align="center"/></AbsoluteFill>;

const Numbers = ({s, t}) => {
  const steps = s.props.steps;
  const bars = plan.downbeats.filter(d => d >= s.at - 0.02 && d < s.at + s.dur);
  const per = Math.max(1, Math.floor(bars.length / steps.length));
  // bars already started (the scene's first bar counts as 1); each step holds `per` bars
  const started = bars.filter(d => d <= t).length;
  const i = Math.min(steps.length - 1, Math.max(0, Math.floor((started - 1) / per)));
  const since = Math.max(0, t - (bars[i * per] ?? s.at));
  const punch = 1 + 0.12 * Math.exp(-since * 6);
  return <AbsoluteFill><Grid t={t}/>
    <div style={{position: "absolute", left: 0, right: 0, top: 300, textAlign: "center", fontFamily: SANS}}>
      <div style={{fontSize: 260, fontWeight: 800, color: i === steps.length - 1 ? ORANGE : INK, transform: `scale(${punch})`}}>{steps[i][0]}</div>
      <div style={{fontSize: 48, color: QUIET, marginTop: 10}}>{steps[i][1]}</div>
    </div>
  </AbsoluteFill>;
};

const Phone = ({s, t}) => {
  const {headline, verdict} = s.props;
  const drop = nthDownbeat(s.at, 1);
  const p = interpolate(t, [drop, drop + 0.4], [0, 1], {...clamp, easing: Easing.out(Easing.back(1.4))});
  const v = verdict ? interpolate(t, [nthDownbeat(s.at, 4), nthDownbeat(s.at, 4) + 0.3], [0, 1], clamp) : 0;
  return <AbsoluteFill><Grid t={t}/>
    <div style={{position: "absolute", left: 760, top: 120, width: 400, height: 820, borderRadius: 56, border: `3px solid ${QUIET}`, background: "#0B1118"}}>
      <div style={{position: "absolute", left: 24, right: 24, top: 120, padding: 22, borderRadius: 24, background: "rgba(127,227,250,0.12)",
        border: `1px solid ${CYAN}`, fontFamily: SANS, opacity: p, transform: `translateY(${(1 - p) * -40}px)`}}>
        <div style={{fontSize: 18, color: QUIET}}>NEWS · now</div>
        <div style={{fontSize: 30, color: INK, fontWeight: 700, marginTop: 8, lineHeight: 1.25}}>{headline}</div>
        <div style={{fontSize: 15, color: QUIET, marginTop: 10}}>illustrative headline</div>
      </div>
    </div>
    {verdict ? <div style={{position: "absolute", left: 1220, top: 420, fontFamily: SANS, fontSize: 56, fontWeight: 700, color: ORANGE, opacity: v,
      transform: `rotate(-4deg) scale(${1 + 0.2 * (1 - v)})`}}>{verdict}</div> : null}
  </AbsoluteFill>;
};

const Timeline = ({s, t}) => {
  const grow = interpolate(t, [nthDownbeat(s.at, 0), nthDownbeat(s.at, 3)], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  const tiny = interpolate(t, [nthDownbeat(s.at, 4), nthDownbeat(s.at, 4) + 0.4], [0, 1], clamp);
  return <AbsoluteFill><Grid t={t}/>
    <div style={{position: "absolute", left: 160, top: 360, fontFamily: SANS, fontSize: 64, fontWeight: 700, color: INK}}>A new drug: 10–17 years</div>
    <div style={{position: "absolute", left: 160, top: 450, fontFamily: SANS, fontSize: 36, color: QUIET}}>about US$2.8 billion · roughly 1 in 10 clinical candidates reaches patients</div>
    <div style={{position: "absolute", left: 160, top: 560, width: 1600 * grow, height: 26, background: CYAN, opacity: 0.85, borderRadius: 13}}/>
    <div style={{position: "absolute", left: 160, top: 556, width: 8, height: 34, background: ORANGE, opacity: tiny}}/>
    <div style={{position: "absolute", left: 150, top: 610, fontFamily: SANS, fontSize: 40, color: ORANGE, opacity: tiny}}>30 days ↑ only the very first step</div>
    <div style={{position: "absolute", right: 160, bottom: 120, fontFamily: MONO, fontSize: 20, color: QUIET}}>Wang et al., Pharmaceuticals 2023</div>
  </AbsoluteFill>;
};

const RUNGS = [["Predicted", "AlphaFold + docking"], ["Binds", "001 and 048"], ["Blocks the enzyme", "048"], ["Works in cells", "liver cancer cells"], ["Animals", "not yet"], ["Patients", "not yet"]];
const Ladder = ({s, t}) => {
  const lit = RUNGS.map((_, i) => i < 4 && t >= nthDownbeat(s.at, i * 2));
  return <AbsoluteFill><Grid t={t}/>
    <div style={{position: "absolute", left: 160, top: 90, fontFamily: SANS, fontSize: 56, fontWeight: 700, color: INK}}>How far did the evidence get?</div>
    {RUNGS.map(([name, note], i) => {
      const y = 860 - i * 120, x = 300 + i * 110, on = lit.at(i);
      return <div key={name} style={{position: "absolute", left: x, top: y, width: 700, height: 92, borderRadius: 14, fontFamily: SANS,
        border: `2px ${i > 3 ? "dashed" : "solid"} ${on ? (i === 3 ? ORANGE : CYAN) : "#3A4A58"}`, background: on ? "rgba(127,227,250,0.10)" : "transparent",
        color: on ? INK : QUIET, padding: "14px 24px"}}>
        <div style={{fontSize: 34, fontWeight: 700}}>{i + 1} · {name}</div><div style={{fontSize: 22, color: QUIET}}>{note}</div>
      </div>;
    })}
  </AbsoluteFill>;
};

const Credits = ({s, t}) => {
  const items = ["Test cut · no narration · not the final video",
    "Music: The Weeknd — Blinding Lights · Sacrifice · Out of Time (course test use only)",
    "Science: Ren et al., Chem. Sci. 2023 · Feng et al., J. Clin. Invest. 2011 · Wang et al., Pharmaceuticals 2023",
    "3D: Blender · BodyParts3D (CC BY-SA 2.1 JP) · AlphaFold DB AF-Q8IZL9 (CC BY 4.0) · our own re-docking (AutoDock Vina)"];
  return <AbsoluteFill style={{background: BG}}>
    <div style={{position: "absolute", left: 160, top: 300, fontFamily: SANS, fontSize: 72, fontWeight: 800, color: INK}}>Worth Testing?</div>
    {items.map((it, i) => {
      const at = nthDownbeat(s.at, i + 1);
      return <div key={i} style={{position: "absolute", left: 160, top: 430 + i * 64, fontFamily: SANS, fontSize: 28, color: QUIET,
        opacity: interpolate(t, [at, at + 0.5], [0, 1], clamp)}}>{it}</div>;
    })}
  </AbsoluteFill>;
};

const KINDS = {clip: Clip, title: Title, numbers: Numbers, phone: Phone, timeline: Timeline, ladder: Ladder, credits: Credits};

const Scene = ({s}) => {
  const f = useCurrentFrame();           // frame inside this Sequence
  const local = f / FPS, t = s.at + local; // seconds in the scene / in the whole film
  const K = KINDS[s.kind];
  const fadeIn = interpolate(local, [0, 0.12], [0, 1], clamp);
  return <AbsoluteFill style={{opacity: fadeIn}}><K s={s} t={t} local={local}/></AbsoluteFill>;
};

export const MV = () => (
  <AbsoluteFill style={{background: BG}}>
    {plan.music.map((m, i) => (
      <Sequence key={"m" + i} from={Math.round(m.at * FPS)} durationInFrames={Math.round(m.length * FPS)}>
        <Audio src={staticFile(m.src)} trimBefore={Math.round(m.from * FPS)}
          volume={f => Math.min(m.fade_in ? f / (m.fade_in * FPS) : 1, m.fade_out ? (m.length * FPS - f) / (m.fade_out * FPS) : 1, 1)}/>
      </Sequence>
    ))}
    {plan.scenes.map((s, i) => (
      <Sequence key={"s" + i} from={Math.round(s.at * FPS)} durationInFrames={Math.max(1, Math.round(s.dur * FPS))}>
        <Scene s={s}/>
      </Sequence>
    ))}
  </AbsoluteFill>
);

export const MV_FRAMES = Math.round(plan.duration * FPS);
