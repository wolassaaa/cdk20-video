// HKBU SCIE1007 coursework video: AI mascot insert v2 (11-21). "AI drama" banter: Claude, GPT and DeepSeek trade
// true, checked stories (scorpion-toxin binders, GPT-4b micro, snake-toxin proteins, AI-found antibiotics).
// Voice is the time base: everything below is computed from data/timeline_v2.json (build_timeline2.py).
import React from "react";
import {AbsoluteFill, useCurrentFrame, interpolate, Easing, Audio, staticFile} from "remotion";
import {loadFont} from "@remotion/google-fonts/InstrumentSerif";
import {Stage2, ACCENT} from "./Stage2";
import TL from "./data/timeline_v2.json";

const {fontFamily} = loadFont();
export const FPS = 60;
export const TOTAL2 = Math.ceil(TL.total * FPS);
const NAMES = ["Claude", "GPT", "DeepSeek"];
const BX = {Claude: -3.15, GPT: 0, DeepSeek: 3.15};
const BZ = {Claude: 0, GPT: -0.25, DeepSeek: 0};
const H = 5.0, BASE_Y = -1.11;
const NAME_COL = {Claude: "#ffb27a", GPT: "#d9ceff", DeepSeek: "#8fd0ff"};

export const CARDS = [
  {kicker: "Oct 2026 · Anthropic", title: "Claude designs proteins vs. scorpion toxins", stat: 17, statFmt: (v) => `${Math.round(v)} / 211`, label: "lab-tested designs that bound a toxin",
    note: "Binding only: not yet shown to neutralize venom, not an antivenom.", src: "Anthropic, “How Claude designed protein binders against scorpion neurotoxins”, 20 Oct 2026; lab tests by Adaptyv Bio and Twist Bioscience", accent: ACCENT.Claude, word: "Scorpion"},
  {kicker: "Aug 2025 · OpenAI × Retro Biosciences", title: "GPT-4b micro redesigns stem-cell proteins", stat: 50, statFmt: (v) => `${Math.round(v)}×`, label: "more reprogramming markers in lab tests",
    note: "Company report, not yet peer-reviewed.", src: "OpenAI, “Accelerating life sciences research”, 22 Aug 2025", accent: ACCENT.GPT},
  {kicker: "Jan 2025 · Nature", title: "AI-designed proteins vs. snake toxins", stat: 100, statFmt: (v) => `${Math.round(v * 0.8)}–${Math.round(v)}%`, label: "of mice survived lethal toxin doses",
    note: "Single cobra-family toxins, not whole venom yet.", src: "Vázquez Torres et al., Nature 2025 (Baker lab, University of Washington)", accent: ACCENT.DeepSeek},
  {kicker: "2020 · 2023 · Cell, Nature Chemical Biology", title: "AI-picked antibiotics: halicin and abaucin", stat: 2, statFmt: (v) => `${Math.round(v)}`, label: "new antibiotic leads that worked in mice",
    note: "Early leads, not approved medicines.", src: "Stokes et al., Cell 2020; Liu et al., Nature Chemical Biology 2023", accent: ACCENT.Claude},
  {kicker: "The takeaway", title: "AI narrows the search.", big: "Experiments still decide.", src: "Our summary of the cases above", accent: ACCENT.GPT},
];

// ---------------------------------------------------------------- precompute (pure functions of the timeline)
const N = TOTAL2 + 2;
const lines = TL.lines;
const lineAt = (t, pad0 = 0, pad1 = 0) => { let r = null; for (const l of lines) if (t >= l.start - pad0 && t < l.start + l.dur + pad1) r = l; return r; };
const lastStarted = (t) => { let r = null; for (const l of lines) if (t >= l.start) r = l; return r; };
const firstStart = lines[0].start;
const lastEnd = lines[lines.length - 1].start + lines[lines.length - 1].dur;
const LAND = {Claude: 0.55, GPT: 0.8, DeepSeek: 1.05};

function spring1(target, k = 70, z = 0.85) {
  const c = 2 * Math.sqrt(k) * z, dt = 1 / FPS, out = new Float32Array(N);
  let x = target(0), v = 0;
  for (let f = 0; f < N; f++) { const a = k * (target(f / FPS) - x) - c * v; v += a * dt; x += v * dt; out[f] = x; }
  return out;
}
// camera
const camTarget = (t) => {
  if (t < firstStart - 0.2) return {x: 0, z: 12.2, y: 0};
  if (t > lastEnd + 0.25) return {x: 0, z: 12.3, y: 0};
  const l = lineAt(t, 0.12, 0.3) || lastStarted(t);
  if (!l) return {x: 0, z: 12, y: 0};
  const z = l.punch ? 10.25 : 11.1;
  return {x: BX[l.who] * 0.1, z, y: (12 - z) * 0.16};
};
const CX = spring1((t) => camTarget(t).x, 55, 0.9), CZ = spring1((t) => camTarget(t).z, 55, 0.9), CY = spring1((t) => camTarget(t).y, 55, 0.9);
// intro dolly: start far and high, settle by firstStart
const introK = (t) => Easing.bezier(0.2, 0.7, 0.2, 1)(Math.min(1, Math.max(0, t / (firstStart + 0.1))));
// per-character focus (1 while speaking)
const FOCUS = {};
for (const w of NAMES) FOCUS[w] = spring1((t) => { const l = lineAt(t, 0.1, 0.2); return l && l.who === w ? 1 : (t < firstStart || t > lastEnd + 0.2 ? 0.6 : 0); }, 80, 0.95);

// mouth frames with hysteresis (min hold 3 frames)
const MOUTH = {};
for (const w of NAMES) {
  const arr = new Array(N).fill(null);
  for (const l of lines.filter((x) => x.who === w)) {
    let cur = "open", hold = 0;
    const f0 = Math.round(l.start * FPS), n = l.env.length;
    for (let i = 0; i < n; i++) {
      const v = ((l.env[i - 1] ?? 0) + 2 * l.env[i] + (l.env[i + 1] ?? 0)) / 4;
      const want = v < 0.14 ? "open" : v < 0.48 ? "talk_o" : "talk_a";
      if (want !== cur && hold >= 3) { cur = want; hold = 0; } else hold++;
      if (f0 + i < N) arr[f0 + i] = cur;
    }
  }
  MOUTH[w] = arr;
}
// reactions after lines: wink 0.7 s, wave 1.3 s
const REACT = {Claude: [], GPT: [], DeepSeek: []};
for (const l of lines) for (const [w, kind] of Object.entries(l.react || {})) {
  const s = l.start + l.dur + 0.04;
  REACT[w].push({kind, s, e: s + (kind === "wave" ? (l === lines[lines.length - 1] ? 9 : 1.3) : 0.7)});
}
const reactAt = (w, t) => REACT[w].find((r) => t >= r.s && t < r.e);
const speakingLine = (w, t) => lines.find((l) => l.who === w && t >= l.start && t < l.start + l.dur);

function frameFor(w, t, f) {
  if (t < firstStart + 0.3 && t >= LAND[w] - 0.3) return "wave";        // entrance wave
  const sp = speakingLine(w, t);
  if (sp) return MOUTH[w][f] || "open";
  const r = reactAt(w, t);
  if (r) return r.kind;
  // idle cycle: blink every P s (6 frames), a playful wink every ~9 s when nobody near is reacting
  const P = {Claude: 3.3, GPT: 3.9, DeepSeek: 2.8}[w], off = {Claude: 0.7, GPT: 1.9, DeepSeek: 1.2}[w];
  const ph = (t + off) % P;
  const wk = (t + off * 3) % 9.0;
  if (wk < 0.55 && !lineAt(t, 0, 0.1)?.punch) return "wink";
  if (ph < 0.1) return "blink";
  return "open";
}

// hops: speaker line start, reaction wink, landing
const bump = (x) => (x <= 0 || x >= 1 ? 0 : Math.sin(Math.PI * x));
function hopFor(w, t) {
  let y = 0, sq = 0;
  for (const l of lines) if (l.who === w) { const k = (t - l.start + 0.05) / 0.32; y += (l.punch ? 0.26 : 0.13) * bump(k); }
  for (const r of REACT[w]) if (r.kind === "wink") y += 0.09 * bump((t - r.s) / 0.3);
  // landing from above with a squash
  // entrance: pop up from below the frame with an overshoot (the knee crop never shows)
  const k = (t - (LAND[w] - 0.45)) / 0.45;
  if (k < 0) y -= 7; else if (k < 1) y -= 7 * (1 - Easing.out(Easing.back(1.7))(k));
  const kl = (t - LAND[w]) / 0.3; sq = -0.05 * bump(kl);
  return {y, sq};
}

const statVal = (card, t, cardIdx) => {
  const hl = lines.find((l) => l.card === cardIdx && l.hit_t);
  const ht = hl ? hl.hit_t : (lines.find((l) => l.card === cardIdx)?.start ?? 0) + 0.6;
  const k = Math.min(1, Math.max(0, (t - (ht - 0.45)) / 0.45));
  return {v: card.stat * Easing.out(Easing.cubic)(k), landed: t >= ht, pulse: bump((t - ht) / 0.35), ht};
};
// card start time: first word that names it (card.word), else the first line on that card
const CARD_T = CARDS.map((c, i) => {
  const l = lines.find((x) => x.card === i);
  if (!l) return 1e9;
  if (c.word) { const w = l.words.find((x) => x[0].toLowerCase().startsWith(c.word.toLowerCase())); if (w) return w[1] - 0.1; }
  return l.start - 0.1;
});
const cardAt = (t) => { let k = -1; CARD_T.forEach((s, i) => { if (t >= s) k = i; }); return k; };

// ---------------------------------------------------------------- overlay components
const Card = ({t}) => {
  const k = cardAt(t);
  if (k < 0) return null;
  const c = CARDS[k], age = t - CARD_T[k];
  const next = CARD_T[k + 1] ?? 1e9, out = Math.max(0, Math.min(1, (t - (next - 0.16)) / 0.16));
  const ein = Easing.out(Easing.back(1.6))(Math.min(1, age / 0.42));
  const rx = (1 - ein) * -70 + out * 80, op = Math.min(1, age / 0.15) * (1 - out);
  const sweep = interpolate(age, [0.15, 0.75], [-30, 130], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const st = c.stat != null ? statVal(c, t, k) : null;
  return (
    <div style={{position: "absolute", top: 34, left: 0, right: 0, display: "flex", justifyContent: "center", perspective: 1400}}>
      <div style={{width: 1320, transform: `rotateX(${rx}deg) scale(${0.94 + 0.06 * ein})`, transformOrigin: "50% 0%", opacity: op, borderRadius: 26, overflow: "hidden", position: "relative",
        background: "linear-gradient(135deg, rgba(22,26,62,0.86), rgba(12,14,38,0.9))", border: `2px solid ${c.accent}88`,
        boxShadow: `0 18px 50px rgba(0,0,0,0.45), 0 0 34px ${c.accent}40, inset 0 1px 0 rgba(255,255,255,0.18)`, fontFamily, color: "#f4f1ff"}}>
        <div style={{position: "absolute", inset: 0, background: `linear-gradient(105deg, transparent ${sweep - 18}%, rgba(255,255,255,0.22) ${sweep}%, transparent ${sweep + 18}%)`}} />
        <div style={{position: "absolute", left: 0, top: 0, bottom: 0, width: 10, background: c.accent}} />
        <div style={{display: "flex", alignItems: "center", padding: "20px 36px 16px 46px", gap: 34}}>
          <div style={{flex: 1, minWidth: 0, textAlign: c.big ? "center" : "left"}}>
            <div style={{fontSize: 27, letterSpacing: 3, textTransform: "uppercase", color: c.accent}}>{c.kicker}</div>
            <div style={{fontSize: 52, lineHeight: 1.04, marginTop: 4, whiteSpace: "nowrap"}}>{c.title}</div>
            {c.big ? <div style={{fontSize: 58, lineHeight: 1.05, marginTop: 6, color: c.accent, fontStyle: "italic"}}>{c.big}</div>
              : <div style={{fontSize: 29, marginTop: 8, color: "#d8d2f0"}}>{c.note}</div>}
          </div>
          {st && (
            <div style={{textAlign: "center", minWidth: 330, transform: `scale(${1 + 0.16 * st.pulse})`}}>
              <div style={{fontSize: 96, lineHeight: 0.95, color: st.landed ? c.accent : "#ffffff", textShadow: `0 0 ${10 + 30 * st.pulse}px ${c.accent}`}}>{c.statFmt(st.v)}</div>
              <div style={{fontSize: 24, color: "#cfc8ea", maxWidth: 380, lineHeight: 1.1, marginTop: 4}}>{c.label}</div>
            </div>
          )}
        </div>
        <div style={{fontSize: 20, fontStyle: "italic", color: "#9d97bd", padding: "0 36px 14px 46px"}}>Source: {c.src}</div>
      </div>
    </div>
  );
};

const Subtitle = ({t}) => {
  const l = lineAt(t, 0, 0.18);
  if (!l) return null;
  const age = t - l.start, k = Math.min(1, age / 0.12);
  return (
    <div style={{position: "absolute", left: 0, right: 0, bottom: 58, display: "flex", justifyContent: "center"}}>
      <div style={{maxWidth: 1560, padding: "10px 32px 14px", borderRadius: 16, background: "rgba(8,10,30,0.78)", border: `1px solid ${ACCENT[l.who]}55`, color: "#fff",
        fontFamily, fontSize: 50, lineHeight: 1.12, textAlign: "center", textShadow: "0 2px 6px rgba(0,0,0,.5)", opacity: k, transform: `translateY(${(1 - k) * 8}px)`}}>
        <span style={{color: NAME_COL[l.who]}}>{l.who}: </span>{l.text}
      </div>
    </div>
  );
};

const Sweep = ({t, total}) => { // T6 light sweep in and out
  const a = interpolate(t, [0, 0.45], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const b = interpolate(t, [total - 0.45, total], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const one = (p, key, cover) => {
    if (p <= 0 || p >= 1) return null;
    const x = -40 + p * 180;
    return <div key={key} style={{position: "absolute", inset: 0, background: `linear-gradient(110deg, ${cover ? "rgba(255,248,235,0)" : "rgba(255,248,235,0)"} ${x - 35}%, rgba(255,246,228,0.95) ${x}%, rgba(255,248,235,0) ${x + 35}%)`}} />;
  };
  return <>{one(a, "a")}{one(b, "b")}{t < 0.2 && <div style={{position: "absolute", inset: 0, background: "#fff6e8", opacity: 1 - t / 0.2}} />}</>;
};

// ---------------------------------------------------------------- main
export const MascotShow2 = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const ik = introK(t);
  const pl = lineAt(t, 0, 0.4);
  const punchAge = pl && pl.punch ? t - pl.start : 9;
  const shake = punchAge >= 0 && punchAge < 0.35 ? (1 - punchAge / 0.35) : 0;
  const cam = {
    x: CX[f], y: CY[f] + (1 - ik) * 0.7, z: CZ[f] + (1 - ik) * 1.1, ly: CY[f] * 0.9, fov: 30,
    shx: Math.sin(t * 71) * 0.045 * shake, shy: Math.cos(t * 53) * 0.035 * shake, roll: Math.sin(t * 37) * 0.006 * shake + Math.sin(t * 0.5) * 0.002,
  };
  const sparks = [];
  const chars = NAMES.map((w, i) => {
    const fo = FOCUS[w][f];
    const {y, sq} = hopFor(w, t);
    const fr = frameFor(w, t, f);
    for (const r of REACT[w]) if (r.kind === "wink" && t >= r.s && t < r.s + 0.7) sparks.push({x: BX[w] + 0.55, y: BASE_Y + H * 0.38, z: BZ[w] + fo * 0.6, age: t - r.s, color: ACCENT[w]});
    const land = t - LAND[w];
    if (land >= 0 && land < 0.7) sparks.push({x: BX[w] - 0.5, y: BASE_Y + H * 0.42, z: BZ[w], age: land, color: ACCENT[w]});
    const breath = Math.sin(t * 2 * Math.PI / (3.2 + i * 0.4) + i);
    return {
      who: w, frame: fr, h: H,
      x: BX[w] + (fo - 0.3) * (w === "GPT" ? 0 : BX[w] > 0 ? -0.15 : 0.15), y: BASE_Y + y, z: BZ[w] + fo * 0.6,
      s: 0.93 + 0.07 * fo, sx: 1 + sq * 0.6, sy: 1 - sq + breath * 0.004, rotZ: Math.sin(t * 0.9 + i * 2) * 0.008 + (fr === "wave" ? 0.01 : 0),
      bright: 0.7 + 0.3 * Math.min(1, fo + (t < firstStart ? 0.4 : 0)), glow: 0.12 + 0.5 * fo, beam: 0.06 + 0.3 * fo,
    };
  });
  return (
    <AbsoluteFill style={{background: "#070a1f"}}>
      <Audio src={staticFile("m/mix.wav")} />
      <Stage2 width={1920} height={1080} t={t} cam={cam} chars={chars} sparks={sparks} />
      <AbsoluteFill style={{background: "radial-gradient(ellipse at 50% 55%, rgba(0,0,0,0) 55%, rgba(0,0,10,0.55) 100%)"}} />
      <Card t={t} />
      <Subtitle t={t} />
      <div style={{position: "absolute", right: 22, bottom: 10, fontFamily, fontSize: 19, fontStyle: "italic", color: "rgba(240,236,255,0.92)", background: "rgba(8,10,30,0.78)", padding: "3px 12px 5px", borderRadius: 8}}>
        Illustration. Characters adapted from fan designs by ZipZipPipe (Bilibili) and Shangshan Wuxing (CC BY-NC-SA 4.0).
      </div>
      <Sweep t={t} total={TL.total} />
    </AbsoluteFill>
  );
};
