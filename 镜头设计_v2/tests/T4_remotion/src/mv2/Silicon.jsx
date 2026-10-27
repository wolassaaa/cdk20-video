import React from "react";
import {AbsoluteFill, OffthreadVideo, Sequence, staticFile} from "remotion";
import {plan, FPS, SI, C, MONO, ANTON, HAND, SiBack, SiLines, clamp01, outCubic, outBack, inOut, lerp, hash, countBefore, hits, env, nthDown, nthBeat} from "./common";

// Silicon shots: screens, terminals, the AI's view. Cool palette, mono type, hard digital cuts.

// big type, split into colour channels that jump on the drums
export const Glitch = ({s, t, f, local}) => {
  const k = env("kick", f), sn = env("snare", f), off = 4 + 18 * Math.max(k, sn);
  return <SiBack f={f} local={local}>
    <AbsoluteFill style={{justifyContent: "center", alignItems: "center"}}>
      {s.props.lines.map((line, i) => {
        const a = nthBeat(s.at, i * 2); if (t < a) return <div key={i} style={{height: 200}}/>;
        const p = outBack((t - a) / 0.2);
        const base = {fontFamily: ANTON, fontSize: 200, lineHeight: 1, letterSpacing: 8, whiteSpace: "pre"};
        return <div key={i} style={{position: "relative", transform: `scale(${0.6 + 0.4 * p})`}}>
          <div style={{...base, position: "absolute", left: -off, color: "rgba(255,40,110,0.8)", mixBlendMode: "screen"}}>{line}</div>
          <div style={{...base, position: "absolute", left: off, color: "rgba(60,220,255,0.8)", mixBlendMode: "screen"}}>{line}</div>
          <div style={{...base, color: SI.ink, position: "relative"}}>{line}</div>
        </div>;
      })}
    </AbsoluteFill>
  </SiBack>;
};

// a terminal window: each line starts on a beat, the hi-hats type it
export const Term = ({s, t, f, local}) => {
  const k = env("kick", f), HATS = hits("hat");
  const {title, lines} = s.props;
  return <SiBack f={f} local={local}>
    <AbsoluteFill style={{perspective: 1600}}>
      <div style={{position: "absolute", left: 230, top: 150, width: 1460, height: 760, borderRadius: 18, background: "rgba(4,10,16,0.92)", border: `1px solid ${SI.line}`,
        boxShadow: `0 30px 120px rgba(0,0,0,0.8), 0 0 ${20 + 40 * k}px rgba(127,227,250,0.12)`,
        transform: `rotateY(${-7 + local * 0.6}deg) rotateX(3deg) scale(${1 + local * 0.012}) translateY(${k * 4}px)`}}>
        <div style={{height: 54, borderBottom: `1px solid ${SI.line}`, display: "flex", alignItems: "center", gap: 10, padding: "0 22px"}}>
          {["#FF5F57", "#FEBC2E", "#28C840"].map(c => <div key={c} style={{width: 14, height: 14, borderRadius: 7, background: c, opacity: 0.7}}/>)}
          <div style={{flex: 1, textAlign: "center", fontFamily: MONO, fontSize: 18, color: SI.quiet}}>~/cdk20 — {title}</div>
        </div>
        <div style={{padding: "34px 44px", fontFamily: MONO, fontSize: 38, lineHeight: 1.6}}>
          {lines.map((line, i) => {
            const a = nthBeat(s.at, i * 2); if (t < a) return null;
            const typed = Math.max((t - a) * 45, (countBefore(HATS, t) - countBefore(HATS, a)) * 6);
            const n = Math.min(line.length, Math.floor(typed));
            const color = line.startsWith("#") ? SI.quiet : line.startsWith(">") ? SI.accent : SI.ink;
            return <div key={i} style={{color, whiteSpace: "pre"}}>{line.slice(0, n)}{n < line.length ? "▋" : ""}</div>;
          })}
        </div>
      </div>
    </AbsoluteFill>
  </SiBack>;
};

const Hud = ({label, t}) => (
  <>
    {[[40, 40, "0 0"], [1880, 40, "90deg"], [1880, 1040, "180deg"], [40, 1040, "270deg"]].map(([x, y, r], i) => (
      <div key={i} style={{position: "absolute", left: x - 20, top: y - 20, width: 40, height: 40, borderLeft: `3px solid ${SI.accent}`, borderTop: `3px solid ${SI.accent}`,
        transform: `rotate(${r === "0 0" ? "0deg" : r})`, opacity: 0.7}}/>
    ))}
    <div style={{position: "absolute", left: 70, top: 66, fontFamily: MONO, fontSize: 18, color: SI.quiet, letterSpacing: 3}}>
      <span style={{color: SI.hot}}>●</span> CDK20 / {label} · {t.toFixed(2)}
    </div>
  </>
);

const Kd = ({from, to, t, at}) => {
  const v = Math.exp(lerp(Math.log(from), Math.log(to), inOut((t - nthDown(at, 1)) / (nthDown(at, 3) - nthDown(at, 1)))));
  return <div style={{position: "absolute", right: 90, top: 110, textAlign: "right", fontFamily: MONO}}>
    <div style={{fontSize: 22, color: SI.quiet, letterSpacing: 3}}>BINDING · Kd (lower = tighter)</div>
    <div style={{fontSize: 96, fontWeight: 700, color: v < 1000 ? SI.hot : SI.ink}}>{v.toLocaleString("en-US", {maximumFractionDigits: v < 1000 ? 1 : 0})} nM</div>
  </div>;
};

// a Blender clip in the computer's frame
export const SiClip = ({s, t, f, local}) => {
  const {src, rate = 1, lines = [], flash, counter} = s.props;
  const k = env("kick", f), blind = flash ? Math.exp(-local * 2.2) : 0;
  return <SiBack f={f} local={local} grid={false}>
    <AbsoluteFill style={{transform: `scale(${1.02 + local * 0.012})`, filter: `brightness(${1 + 0.25 * k + 2.5 * blind}) contrast(${1 + 0.1 * k})`}}>
      <OffthreadVideo src={staticFile(src)} playbackRate={rate} muted style={{width: "100%", height: "100%", objectFit: "cover"}}/>
    </AbsoluteFill>
    <AbsoluteFill style={{background: "linear-gradient(90deg, rgba(2,6,11,0.8), rgba(2,6,11,0) 55%)"}}/>
    {blind > 0.01 ? <AbsoluteFill style={{background: "#fff", opacity: blind * 0.9}}/> : null}
    <Hud label={src.split("/").pop().replace(".mp4", "")} t={local}/>
    <SiLines lines={lines} t={t} at={s.at} y={160}/>
    {counter ? <Kd from={counter[0]} to={counter[1]} t={t} at={s.at}/> : null}
  </SiBack>;
};

// fast cut-ins every two beats, then the picture powers off like a CRT while the music tape-stops
export const Montage = ({s, t, f, local}) => {
  const {srcs, term} = s.props;
  const actEnd = plan.acts[0].at + plan.acts[0].length, off = actEnd - 1.2;
  const cuts = plan.beats.filter(b => b >= s.at - 0.03 && b < off).filter((_, i) => i % 2 === 0);
  const crt = clamp01((t - off) / 1.1);
  const sy = crt < 0.5 ? lerp(1, 0.004, outCubic(crt / 0.5)) : 0.004, sx = crt < 0.5 ? 1 : lerp(1, 0, outCubic((crt - 0.5) / 0.5));
  return <SiBack f={f} local={local} grid={false}>
    <AbsoluteFill style={{transform: `scale(${sx}, ${sy})`, filter: `brightness(${1 + crt * 3})`}}>
      {cuts.map((c, i) => {
        const from = Math.round((c - s.at) * FPS), to = Math.round(((cuts[i + 1] ?? off + 1.2) - s.at) * FPS);
        return <Sequence key={i} from={from} durationInFrames={Math.max(1, to - from)} layout="none">
          <AbsoluteFill style={{transform: `scale(${1.15 + 0.1 * hash(i, 2)}) rotate(${(hash(i, 3) - 0.5) * 4}deg)`}}>
            <OffthreadVideo src={staticFile(srcs[i % srcs.length])} trimBefore={Math.round(hash(i, 1) * 150)} muted
              style={{width: "100%", height: "100%", objectFit: "cover", filter: i % 3 === 2 ? "hue-rotate(160deg) saturate(1.6)" : "none"}}/>
          </AbsoluteFill>
        </Sequence>;
      })}
      <div style={{position: "absolute", left: 96, bottom: 120, fontFamily: MONO, fontSize: 44, color: SI.accent, textShadow: "0 0 20px rgba(0,0,0,0.9)"}}>
        {term.slice(0, Math.floor(clamp01(local / 2.5) * term.length))}<span style={{opacity: Math.floor(local * 3) % 2}}>▋</span>
      </div>
    </AbsoluteFill>
  </SiBack>;
};

// docking scores scroll past; rows are illustrative, the count is real
export const Scores = ({s, t, f, local}) => {
  const HATS = hits("hat"), flashRow = countBefore(HATS, t) % 13, hat = env("hat", f);
  const rowH = 58, speed = 16, first = Math.floor(local * speed);
  return <SiBack f={f} local={local}>
    <div style={{position: "absolute", left: 160, top: 110, width: 1600, fontFamily: MONO}}>
      <div style={{display: "flex", justifyContent: "space-between", color: SI.quiet, fontSize: 22, letterSpacing: 2}}>
        <span>~/cdk20 — score every design in the pocket</span><span>8,918 to score</span>
      </div>
      <div style={{display: "grid", gridTemplateColumns: "300px 1fr 1fr 160px", color: SI.quiet, fontSize: 20, marginTop: 26, paddingBottom: 10, borderBottom: `1px solid ${SI.line}`}}>
        <span>design</span><span>fit in pocket</span><span>drug-like</span><span>keep?</span>
      </div>
      <div style={{position: "relative", height: 13 * rowH, overflow: "hidden"}}>
        {Array.from({length: 14}, (_, r) => {
          const id = first + r, y = r * rowH - (local * speed - first) * rowH, a = hash(id, 1), b = hash(id, 2), keep = a * b > 0.62;
          const lit = r === flashRow ? hat : 0;
          return <div key={id} style={{position: "absolute", left: 0, right: 0, top: y, height: rowH, display: "grid", gridTemplateColumns: "300px 1fr 1fr 160px",
            alignItems: "center", fontSize: 24, color: keep ? SI.hot : SI.ink, background: `rgba(127,227,250,${0.12 * lit})`}}>
            <span>gen-{String((id * 7919) % 8918 + 1).padStart(4, "0")}</span>
            <span><div style={{width: `${a * 90}%`, height: 10, borderRadius: 5, background: SI.accent, opacity: 0.8}}/></span>
            <span><div style={{width: `${b * 90}%`, height: 10, borderRadius: 5, background: SI.accent, opacity: 0.5}}/></span>
            <span>{keep ? "keep" : "·"}</span>
          </div>;
        })}
      </div>
      <div style={{color: SI.quiet, fontSize: 16, marginTop: 14}}>rows illustrative</div>
    </div>
  </SiBack>;
};

// numbers that slam in one per bar (silicon: mono; mix: mono number, hand-written label)
export const Numbers = ({s, t, f, local}) => {
  const {steps, title} = s.props, mix = s.world !== "si";
  const bars = plan.downbeats.filter(d => d >= s.at - 0.03 && d < s.at + s.dur - 0.05);
  const per = Math.max(1, Math.floor(bars.length / steps.length));
  const i = Math.min(steps.length - 1, Math.floor(Math.max(0, countBefore(bars, t) - 1) / per));
  const since = t - (bars[i * per] ?? s.at), punch = 1 + 0.14 * Math.exp(-since * 7);
  const last = i === steps.length - 1;
  const body = <AbsoluteFill style={{justifyContent: "center", alignItems: "center", textAlign: "center"}}>
    <div style={{fontFamily: MONO, fontSize: 24, color: mix ? C.quiet : SI.quiet, letterSpacing: 6, marginBottom: 30}}>{title}</div>
    <div style={{fontFamily: MONO, fontSize: 210, fontWeight: 700, color: last ? (mix ? C.amber : SI.hot) : SI.ink, transform: `scale(${punch})`, lineHeight: 1}}>{steps[i][0]}</div>
    <div style={{fontFamily: mix ? HAND : MONO, fontSize: mix ? 64 : 40, color: mix ? C.amber : SI.quiet, marginTop: 24}}>{steps[i][1]}</div>
  </AbsoluteFill>;
  return mix ? <MixBack f={f} local={local}>{body}</MixBack> : <SiBack f={f} local={local}>{body}</SiBack>;
};

// where the worlds meet: cool on one side, warm on the other
export const MixBack = ({f, local, children}) => {
  const k = env("kick", f);
  return <AbsoluteFill style={{background: `linear-gradient(100deg, #04101A 0%, #0B0B10 50%, #1A0C07 100%)`, overflow: "hidden"}}>
    <AbsoluteFill style={{background: `radial-gradient(circle at 20% 30%, rgba(127,227,250,${0.10 + 0.06 * k}), transparent 50%), radial-gradient(circle at 80% 70%, rgba(255,160,70,${0.12 + 0.06 * k}), transparent 50%)`}}/>
    {children}
    <AbsoluteFill style={{background: "radial-gradient(ellipse at center, transparent 55%, rgba(0,0,0,0.6))"}}/>
  </AbsoluteFill>;
};

// the headline as giant type. open: typed out over the beatless intro, then it starts to glitch.
// return: back on screen. fix: hand-written corrections strike the overclaims one bar at a time.
const WORDS = ["AI designs", "liver cancer", "drug", "in 30 days"];
const FIXES = [[0, "AI + chemists designed it"], [2, "a drug candidate, not yet tested in people"], [3, "the first hit took 30 days"]];
export const Headline = ({s, t, f, local}) => {
  const {mode} = s.props, fix = mode === "fix", k = env("kick", f);
  const total = WORDS.join(" ").length;
  const typed = mode === "open" ? Math.floor(clamp01((local - 0.8) / 6) * total) : total;
  const shake = mode === "open" ? clamp01((local - 9) / 4) : 0;
  const off = 3 + 14 * Math.max(shake * (0.5 + 0.5 * Math.sin(local * 37)), k, env("snare", f));
  let used = 0;
  const rows = WORDS.map((w, i) => {
    const n = Math.max(0, Math.min(w.length, typed - used)); used += w.length + 1;
    const fx = FIXES.findIndex(([wi]) => wi === i), at = fx >= 0 ? nthDown(s.at, fx + 1) : 1e9;
    const on = fix && t >= at, p = on ? outCubic((t - at) / 0.3) : 0, write = on ? clamp01((t - at - 0.2) / 0.7) : 0;
    const base = {fontFamily: ANTON, fontSize: 150, lineHeight: 1.02, letterSpacing: 2, whiteSpace: "pre"};
    return <div key={i} style={{position: "relative", marginBottom: fix ? 6 : 0}}>
      <div style={{position: "relative", display: "inline-block"}}>
        {!fix ? <>
          <div style={{...base, position: "absolute", left: -off, color: "rgba(255,40,110,0.75)", mixBlendMode: "screen"}}>{w.slice(0, n)}</div>
          <div style={{...base, position: "absolute", left: off, color: "rgba(60,220,255,0.75)", mixBlendMode: "screen"}}>{w.slice(0, n)}</div>
        </> : null}
        <div style={{...base, position: "relative", color: on ? SI.quiet : SI.ink}}>{w.slice(0, n)}{mode === "open" && n > 0 && n < w.length ? "▋" : ""}</div>
        {on ? <div style={{position: "absolute", left: -10, top: "52%", height: 12, width: `calc(${p * 100}% + 20px)`, background: C.amber, borderRadius: 6, transform: "rotate(-1.5deg)"}}/> : null}
      </div>
      {on ? <div style={{fontFamily: HAND, fontSize: 64, color: C.amber, marginTop: -14, marginLeft: 8, clipPath: `inset(0 ${100 - write * 100}% 0 0)`}}>↳ {FIXES[fx][1]}</div> : null}
    </div>;
  });
  const body = <>
    <div style={{position: "absolute", left: 150, top: fix ? 70 : 150, transform: `scale(${1 + local * (mode === "open" ? 0.012 : 0.006)})`, transformOrigin: "0 0"}}>
      <div style={{fontFamily: MONO, fontSize: 24, color: SI.hot, letterSpacing: 6, marginBottom: 18, opacity: typed > 0 ? 1 : 0}}>● HEADLINE <span style={{color: SI.quiet, letterSpacing: 2, fontSize: 18}}>· illustrative</span></div>
      {rows}
    </div>
  </>;
  return fix ? <MixBack f={f} local={local}>{body}</MixBack> : <SiBack f={f} local={local}>{body}</SiBack>;
};
