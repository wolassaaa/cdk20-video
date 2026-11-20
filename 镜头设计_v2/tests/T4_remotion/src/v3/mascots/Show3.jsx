// HKBU SCIE1007 coursework video: AI mascot insert v3 (11-20), re-staged as a short "AI drama".
// Same script, voice, card facts and sources as v2 (Show2.jsx); only the camera, cutting, stage and card layout change.
// 28 shots: wide open, bust singles with the card on the opposite third, whip pans, split screens, reaction shots,
// one flash + speed-line hit on "Plot twist!", wide close. Characters are only the Codex PNG frames (no SVG drawing).
// Voice is the time base: every shot boundary and event is computed from data/timeline_v2.json word times.
import React from "react";
import {AbsoluteFill, useCurrentFrame, Easing, Audio, Img, staticFile} from "remotion";
import {loadFont} from "@remotion/google-fonts/InstrumentSerif";
import TL from "./data/timeline_v2.json";

const {fontFamily} = loadFont();
export const FPS = 60;
export const TOTAL3 = Math.ceil(TL.total * FPS);
const W = 1920, HH = 1080;
const NAMES = ["Claude", "GPT", "DeepSeek"];
const DIR = {Claude: "claude", GPT: "gpt", DeepSeek: "deepseek"};
const STATES = ["open", "blink", "wink", "talk_a", "talk_o", "wave"];
export const ACCENT = {Claude: "#ff9a4d", GPT: "#c8b8ff", DeepSeek: "#58b4ff"};
const NAME_COL = {Claude: "#ffb27a", GPT: "#d9ceff", DeepSeek: "#8fd0ff"};
// art anchors in the 1536 px frames: face centre x, head top y, pivot (waist) y
const ART = {Claude: {ax: 768, top: 71, piv: 640}, GPT: {ax: 772, top: 72, piv: 720}, DeepSeek: {ax: 768, top: 71, piv: 700}};
const ORDER = {Claude: -1, GPT: 0, DeepSeek: 1};          // stage order, used for whip direction and set offset
const WIDE_X = {Claude: -610, GPT: 0, DeepSeek: 610};      // line-up spacing in art px

const clamp01 = (x) => Math.min(1, Math.max(0, x));
const lerp = (a, b, k) => a + (b - a) * k;
const bump = (x) => (x <= 0 || x >= 1 ? 0 : Math.sin(Math.PI * x));
const rnd = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const eOut = Easing.out(Easing.cubic), eExpo = Easing.out(Easing.exp), eBack = Easing.out(Easing.back(1.7)), eIn = Easing.in(Easing.cubic), eIO = Easing.inOut(Easing.cubic);

// ---------------------------------------------------------------- timeline access
const lines = TL.lines;
const L = Object.fromEntries(lines.map((l) => [l.id, l]));
const ws = (id, i) => L[id].words[i][1];                 // start time of whisper word i in line id
const end = (id) => L[id].start + L[id].dur;
const lineAt = (t, pad0 = 0, pad1 = 0) => { let r = null; for (const l of lines) if (t >= l.start - pad0 && t < l.start + l.dur + pad1) r = l; return r; };
const speakingLine = (w, t) => lines.find((l) => l.who === w && t >= l.start && t < l.start + l.dur);
const N = TOTAL3 + 2;

// ---------------------------------------------------------------- cards (text and sources unchanged from v2)
export const CARDS = [
  {kicker: "Oct 2026 · Anthropic", title: "Claude designs proteins vs. scorpion toxins", stat: 17, tail: " / 211", count: true, label: "lab-tested designs that bound a toxin",
    note: "Binding only: not yet shown to neutralize venom, not an antivenom.", src: "Anthropic, “How Claude designed protein binders against scorpion neurotoxins”, 20 Oct 2026; lab tests by Adaptyv Bio and Twist Bioscience",
    accent: ACCENT.Claude, hit: L.c2.hit_t, noteAt: ws("d1", 2)},
  {kicker: "Aug 2025 · OpenAI × Retro Biosciences", title: "GPT-4b micro redesigns stem-cell proteins", stat: 50, tail: "×", count: true, label: "more reprogramming markers in lab tests",
    note: "Company report, not yet peer-reviewed.", src: "OpenAI, “Accelerating life sciences research”, 22 Aug 2025", accent: ACCENT.GPT, hit: L.g2.hit_t, noteAt: ws("d2", 2)},
  // a range does not count up: it is shown as a fixed value that lands on the hit word (v2 showed "0–0%" while waiting)
  {kicker: "Jan 2025 · Nature", title: "AI-designed proteins vs. snake toxins", fixed: "80–100%", label: "of mice survived lethal toxin doses",
    note: "Single cobra-family toxins, not whole venom yet.", src: "Vázquez Torres et al., Nature 2025 (Baker lab, University of Washington)", accent: ACCENT.DeepSeek, hit: L.d3.hit_t, noteAt: L.d3.hit_t + 0.3},
  {kicker: "2020 · 2023 · Cell, Nature Chemical Biology", title: "AI-picked antibiotics: halicin and abaucin", fixed: "2", label: "new antibiotic leads that worked in mice",
    note: "Early leads, not approved medicines.", src: "Stokes et al., Cell 2020; Liu et al., Nature Chemical Biology 2023", accent: ACCENT.Claude, hit: L.c3.hit_t, noteAt: ws("c3", 11)},
  {kicker: "The takeaway", title: "AI narrows the search.", big: "Experiments still decide.", src: "Our summary of the cases above", accent: ACCENT.GPT},
];
// first moment each card is on screen (its naming word)
const CARD_T = [ws("c1", 2), ws("g2", 1), ws("d3", 2), ws("c3", 4), ws("c4", 0)].map((x) => x - 0.04);

// ---------------------------------------------------------------- shot list (all times from word starts)
// kind: wide | single | split.  side: L / C / R = which third the speaker's face sits on (card goes opposite).
// z = [start, end] scale in screen px per art px (1.5 = bust, the art limit).  enter: cut | whip | push | snap | flash.
const HB = [1.24, 1.31], BU = [1.55, 1.6];   // half-body and bust: far enough apart that a cut-in reads as a new shot
const SHOTS = [
  {name: "Wide entrance", kind: "wide", t0: 0, cam: [{x: 0, z: 0.78}, {x: 0, z: 0.85}], ease: eOut},
  {name: "Push to Claude", kind: "wide", t0: L.c1.start - 0.12, cam: [{x: 0, z: 0.85}, {x: -520, z: 1.14}], ease: eExpo, moveDur: 0.5, speaker: "Claude"},
  {name: "Claude + card 0", kind: "single", who: "Claude", side: "L", t0: ws("c1", 2) - 0.06, z: HB, card: 0},
  {name: "Claude bust", kind: "single", who: "Claude", side: "L", t0: ws("c1", 9) - 0.05, z: BU, card: 0, exit: "whip"},
  {name: "Whip to GPT", kind: "single", who: "GPT", side: "C", t0: L.g1.start - 0.1, z: [1.26, 1.3], enter: "whip"},
  {name: "Snap on YOU", kind: "single", who: "GPT", side: "C", t0: ws("g1", 1) - 0.03, z: [1.56, 1.6], enter: "snap", zFrom: 1.3, shake: 1},
  {name: "Claude reacts", kind: "single", who: "Claude", side: "C", t0: ws("g1", 3) + 0.14, z: [1.5, 1.54], act: [{type: "turn", t: L.c2.start - 0.2}, {type: "blink", t: ws("g1", 3) + 0.3, d: 0.16}], flip0: -1},
  {name: "Claude answers + card 0", kind: "single", who: "Claude", side: "L", t0: L.c2.start - 0.06, z: HB, card: 0},
  {name: "GPT listens", kind: "single", who: "GPT", side: "C", t0: ws("c2", 3) + 0.08, z: [1.42, 1.47], act: [{type: "blink", t: ws("c2", 4), d: 0.14}, {type: "blink", t: ws("c2", 5) + 0.2, d: 0.14}, {type: "droop", t: ws("c2", 5), d: 0.9, amp: 0.4}]},
  {name: "Claude bust, 17 lands", kind: "single", who: "Claude", side: "L", t0: ws("c2", 6) - 0.06, z: BU, card: 0, act: [{type: "wink", t: end("c2") - 0.3, d: 0.5}]},
  {name: "DeepSeek fact-check", kind: "single", who: "DeepSeek", side: "R", t0: end("c2"), z: HB, card: 0},
  {name: "DeepSeek bust", kind: "single", who: "DeepSeek", side: "R", t0: ws("d1", 2) - 0.05, z: BU, card: 0},
  {name: "Split DS / Claude", kind: "split", a: "DeepSeek", b: "Claude", t0: ws("d1", 6) - 0.06, react: "deflate"},
  {name: "GPT Cute", kind: "single", who: "GPT", side: "C", t0: L.g2.start - 0.08, z: [1.5, 1.54], act: [{type: "wink", t: ws("g2", 0) + 0.12, d: 0.4}]},
  {name: "GPT + card 1", kind: "single", who: "GPT", side: "R", t0: ws("g2", 1) - 0.05, z: HB, card: 1},
  {name: "GPT bust, 50x lands", kind: "single", who: "GPT", side: "R", t0: ws("g2", 8) - 0.08, z: BU, card: 1, act: [{type: "wink", t: end("g2") - 0.3, d: 0.4}], exit: "whip"},
  {name: "Whip to DeepSeek", kind: "single", who: "DeepSeek", side: "L", t0: L.d2.start - 0.1, z: [1.3, 1.36], enter: "whip", card: 1},
  {name: "Split DS / GPT", kind: "split", a: "DeepSeek", b: "GPT", t0: ws("d2", 4) - 0.06, react: "blink"},
  {name: "GPT Ugh", kind: "single", who: "GPT", side: "C", t0: end("d2"), z: [1.5, 1.56], act: [{type: "droop", t: ws("g3", 0), d: 0.6}]},
  {name: "Plot twist hit", kind: "single", who: "DeepSeek", side: "C", t0: L.d3.start - 0.06, z: [1.56, 1.6], enter: "flash", zFrom: 1.12, shake: 1, lines: 1},
  {name: "DeepSeek + card 2", kind: "single", who: "DeepSeek", side: "L", t0: ws("d3", 2) - 0.05, z: HB, card: 2},
  {name: "Claude and GPT listen", kind: "split", a: "Claude", b: "GPT", t0: ws("d3", 6) - 0.04, react: "listen"},
  {name: "DeepSeek bust, mice survived", kind: "single", who: "DeepSeek", side: "L", t0: ws("d3", 9) - 0.06, z: BU, card: 2, act: [{type: "wink", t: end("d3") - 0.25, d: 0.5}]},
  {name: "Claude And AI", kind: "single", who: "Claude", side: "C", t0: L.c3.start - 0.08, z: [1.48, 1.54]},
  {name: "Claude + card 3", kind: "single", who: "Claude", side: "R", t0: ws("c3", 4) - 0.06, z: HB, card: 3},
  {name: "Claude bust, superbugs", kind: "single", who: "Claude", side: "R", t0: ws("c3", 8) - 0.05, z: BU, card: 3},
  {name: "GPT pushes in", kind: "single", who: "GPT", side: "C", t0: L.g4.start - 0.08, z: [1.24, 1.52], ease: eIO},
  {name: "Smash cut Nope", kind: "single", who: "DeepSeek", side: "C", t0: L.d4.start - 0.1, z: [1.58, 1.6], shake: 1, shakeAt: ws("d4", 0)},
  {name: "Claude + takeaway", kind: "single", who: "Claude", side: "L", t0: L.c4.start - 0.1, z: HB, card: 4},
  {name: "Claude bust, real lab", kind: "single", who: "Claude", side: "L", t0: ws("c4", 7) - 0.05, z: BU, card: 4},
  {name: "GPT Fine", kind: "single", who: "GPT", side: "C", t0: L.g5.start - 0.1, z: [1.46, 1.5], act: [{type: "droop", t: ws("g5", 0), d: 0.5}]},
  {name: "Wide close", kind: "wide", t0: ws("g5", 1) - 0.05, cam: [{x: 0, z: 0.88}, {x: 0, z: 0.83}], ease: eOut, banner: 1, drop: 150, speaker: "GPT"},
];
SHOTS.forEach((s, i) => { s.i = i; s.t1 = SHOTS[i + 1] ? SHOTS[i + 1].t0 : TL.total; s.f0 = Math.round(s.t0 * FPS); });
SHOTS.forEach((s, i) => { s.f1 = SHOTS[i + 1] ? SHOTS[i + 1].f0 : TOTAL3 + 1; });
export const SHOT_TABLE = SHOTS.map((s) => ({name: s.name, kind: s.kind, t0: s.t0, t1: s.t1}));
const shotAtFrame = (f) => { let r = SHOTS[0]; for (const s of SHOTS) if (f >= s.f0) r = s; return r; };
const whipDir = (s) => { // +1 = camera travels right (picture slides left)
  const a = s.exit === "whip" ? s : SHOTS[s.i - 1], b = s.exit === "whip" ? SHOTS[s.i + 1] : s;
  return Math.sign(ORDER[b.who] - ORDER[a.who]) || 1;
};

// ---------------------------------------------------------------- mouths (voice envelope, 3-frame hold)
const MOUTH = {}, ENV = {};
for (const w of NAMES) {
  const arr = new Array(N).fill(null), env = new Float32Array(N);
  for (const l of lines.filter((x) => x.who === w)) {
    let cur = "open", hold = 0;
    const f0 = Math.round(l.start * FPS), n = l.env.length;
    for (let i = 0; i < n; i++) {
      const v = ((l.env[i - 1] ?? 0) + 2 * l.env[i] + (l.env[i + 1] ?? 0)) / 4;
      const want = v < 0.14 ? "open" : v < 0.48 ? "talk_o" : "talk_a";
      if (want !== cur && hold >= 3) { cur = want; hold = 0; } else hold++;
      if (f0 + i < N) { arr[f0 + i] = cur; env[f0 + i] = v; }
    }
  }
  // smooth the envelope for the body bob
  const sm = new Float32Array(N); let x = 0;
  for (let f = 0; f < N; f++) { x += (env[f] - x) * 0.25; sm[f] = x; }
  MOUTH[w] = arr; ENV[w] = sm;
}
const LAND = {Claude: 0.5, GPT: 0.72, DeepSeek: 0.94};
const WAVE_END = end("g5") + 0.02;

function frameFor(w, t, f, shot) {
  for (const a of shot.act || []) if ((a.type === "wink" || a.type === "blink") && w === shot.who && t >= a.t && t < a.t + a.d) return a.type;
  if (shot.i === 0 && t >= LAND[w] - 0.25) return "wave";
  if (shot.banner && t >= WAVE_END && w !== "GPT") return "wave";
  if (shot.banner && t >= WAVE_END + 0.1 && w === "GPT") return t < WAVE_END + 0.6 ? "wink" : "wave";
  if (speakingLine(w, t)) return MOUTH[w][f] || "open";
  const P = {Claude: 3.3, GPT: 3.9, DeepSeek: 2.8}[w], off = {Claude: 0.7, GPT: 1.9, DeepSeek: 1.2}[w];
  if ((t + off) % P < 0.1) return "blink";
  return "open";
}

// ---------------------------------------------------------------- stage backdrop (soft studio / data space, layered for parallax)
const PANELS = Array.from({length: 9}, (_, i) => ({x: -1900 + i * 480 + rnd(i) * 160, w: 150 + rnd(i + 9) * 170, h: 760 + rnd(i + 20) * 420, o: 0.1 + rnd(i + 31) * 0.14, sk: -6 + rnd(i + 5) * 12, warm: rnd(i + 44) > 0.6}));
const BOKEH = Array.from({length: 34}, (_, i) => ({x: -1500 + rnd(i * 3 + 1) * 3000, y: rnd(i * 3 + 2) * 1080, r: 26 + rnd(i * 3 + 3) * 90, d: 0.3 + rnd(i * 7) * 0.5, o: 0.07 + rnd(i * 5) * 0.2, c: i % 4, ph: rnd(i * 11) * 6.28}));
const DUST = Array.from({length: 9}, (_, i) => ({x: -1200 + rnd(i * 13 + 4) * 2400, y: rnd(i * 17 + 2) * 1080, r: 120 + rnd(i * 19) * 200, ph: rnd(i * 23) * 6.28}));
const HEX_BG = `url("data:image/svg+xml;utf8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="168" height="97"><g fill="none" stroke="#cfd6ff" stroke-width="1.6"><path d="M28 0l28 16v32l-28 16L0 48V16zM112 0l28 16v32l-28 16-28-16V16zM70 48.5l28 16v32M70 48.5l-28 16v32M154 48.5l-28 16v32M154 48.5l14 8"/></g><g fill="#cfd6ff"><circle cx="28" cy="0" r="3"/><circle cx="56" cy="48" r="3"/><circle cx="112" cy="64" r="3"/><circle cx="140" cy="16" r="3"/></g></svg>')}")`;

const Backdrop = ({t, px = 0, zoom = 1, tint, halo}) => {
  // px: camera travel in px (layers move by px * depth); zoom: 0.8 wide .. 1.6 bust (closer = softer, bigger background)
  const zk = 1 + (zoom - 0.85) * 0.22, blur = 6 + (zoom - 0.85) * 14;
  const cols = ["#ffffff", tint, "#ffd9a8", "#9fb4ff"];
  return (
    <AbsoluteFill style={{overflow: "hidden", background: "#0a0d28"}}>
      <AbsoluteFill style={{background: "linear-gradient(180deg, #080a22 0%, #121848 38%, #1d2468 66%, #2a2f7a 100%)"}} />
      <AbsoluteFill style={{background: `radial-gradient(ellipse 75% 60% at ${50 - px * 0.004}% 62%, ${tint}55 0%, ${tint}1c 45%, transparent 75%)`}} />
      {/* far wall: molecule lattice, lit from the middle */}
      <div style={{position: "absolute", left: -400, top: -200, width: W + 800, height: HH + 400, backgroundImage: HEX_BG, backgroundSize: "168px 97px", opacity: 0.22,
        transform: `translateX(${-px * 0.12}px) scale(${1 + (zk - 1) * 0.5})`, filter: `blur(${1 + blur * 0.12}px)`,
        maskImage: "radial-gradient(ellipse 55% 60% at 50% 45%, #000 0%, transparent 78%)", WebkitMaskImage: "radial-gradient(ellipse 55% 60% at 50% 45%, #000 0%, transparent 78%)"}} />
      {/* tall soft light panels (studio softboxes), mid depth */}
      <div style={{position: "absolute", inset: 0, transform: `scale(${zk})`, filter: `blur(${blur * 1.1 + 9}px)`}}>
        {PANELS.map((p, i) => (
          <div key={i} style={{position: "absolute", left: W / 2 + p.x - px * 0.3, top: HH * 0.5 - p.h / 2 + Math.sin(t * 0.3 + i) * 8, width: p.w, height: p.h, borderRadius: 40,
            transform: `skewX(${p.sk}deg)`, opacity: (p.o + 0.06) * (0.85 + 0.15 * Math.sin(t * 0.7 + i * 1.7)),
            background: `linear-gradient(180deg, transparent 0%, ${p.warm ? "#ffe6c4" : "#dfe6ff"} 30%, ${tint} 75%, transparent 100%)`}} />
        ))}
      </div>
      {/* key halo behind the speaker */}
      {halo && <div style={{position: "absolute", left: halo.x - halo.r, top: halo.y - halo.r, width: halo.r * 2, height: halo.r * 2, borderRadius: "50%",
        background: `radial-gradient(circle, ${tint}88 0%, ${tint}3a 38%, transparent 70%)`, opacity: halo.o ?? 1}} />}
      {/* two slow light shafts */}
      {[0, 1].map((i) => (
        <div key={i} style={{position: "absolute", left: W * (0.18 + i * 0.5) - px * 0.2, top: -300, width: 260, height: 1700, opacity: 0.1 + 0.03 * Math.sin(t * 0.5 + i * 2),
          transform: `rotate(${(i ? -17 : 21) + Math.sin(t * 0.23 + i) * 2}deg)`, filter: "blur(40px)", background: "linear-gradient(90deg, transparent, #ffffff, transparent)"}} />
      ))}
      {/* bokeh */}
      {BOKEH.map((b, i) => {
        const x = W / 2 + b.x - px * b.d + Math.sin(t * 0.25 + b.ph) * 22, y = ((b.y - t * (6 + b.d * 14)) % (HH + 200) + HH + 200) % (HH + 200) - 100;
        const r = b.r * zk;
        return <div key={i} style={{position: "absolute", left: x - r, top: y - r, width: r * 2, height: r * 2, borderRadius: "50%", opacity: b.o * (0.7 + 0.3 * Math.sin(t * 1.3 + b.ph)),
          background: `radial-gradient(circle, ${cols[b.c]}66 0%, ${cols[b.c]}44 62%, ${cols[b.c]}aa 70%, transparent 74%)`, filter: `blur(${1.5 + (1 - b.d) * 4}px)`}} />;
      })}
      <AbsoluteFill style={{background: "linear-gradient(180deg, rgba(4,6,24,0.55) 0%, transparent 22%, transparent 70%, rgba(6,8,30,0.5) 100%)"}} />
    </AbsoluteFill>
  );
};
const Foreground = ({t, px = 0, tint}) => (
  <AbsoluteFill style={{overflow: "hidden", pointerEvents: "none"}}>
    {DUST.map((b, i) => {
      const x = W / 2 + b.x - px * 1.5 + Math.sin(t * 0.2 + b.ph) * 60, y = ((b.y - t * 22) % (HH + 500) + HH + 500) % (HH + 500) - 250;
      return <div key={i} style={{position: "absolute", left: x - b.r, top: y - b.r, width: b.r * 2, height: b.r * 2, borderRadius: "50%", opacity: 0.07,
        background: `radial-gradient(circle, ${i % 2 ? tint : "#ffffff"} 0%, transparent 68%)`, filter: "blur(18px)"}} />;
    })}
  </AbsoluteFill>
);

// ---------------------------------------------------------------- one character (stack of the six PNG frames, one visible)
const Actor = ({who, frame, x, y, z, flip = 1, dx = 0, dy = 0, rot = 0, sx = 1, sy = 1, bright = 1, sat = 1, rim = 1, soft = 0}) => {
  const a = ART[who], S = 1536 * z;
  return (
    <div style={{position: "absolute", left: x - a.ax * z, top: y - a.top * z, width: S, height: S, transformOrigin: `${(a.ax / 1536) * 100}% ${(a.piv / 1536) * 100}%`,
      transform: `translate(${dx}px, ${dy}px) rotate(${rot}deg) scale(${flip * sx}, ${sy})`,
      filter: `drop-shadow(0 0 ${1.2 * z}px rgba(255,255,255,${0.75 * rim})) drop-shadow(0 0 ${16 * z}px ${ACCENT[who]}${Math.round(150 * rim).toString(16).padStart(2, "0")}) brightness(${bright}) saturate(${sat})${soft ? ` blur(${soft}px)` : ""}`}}>
      {STATES.map((s) => <Img key={s} src={staticFile(`m/${DIR[who]}/${s}.png`)} style={{position: "absolute", inset: 0, width: "100%", height: "100%", opacity: s === frame ? 1 : 0}} />)}
    </div>
  );
};

// body acting shared by every layout: talk bob from the voice, a hop on the line start, breathing
function body(who, t, f, i) {
  const sp = speakingLine(who, t);
  let dy = 0, sy = 1, rot = Math.sin(t * 0.9 + i * 2) * 0.35;
  sy += Math.sin(t * 2 * Math.PI / (3.2 + i * 0.4) + i) * 0.004;
  if (sp) { dy -= ENV[who][f] * 9; rot += Math.sin(t * 5.1 + i) * ENV[who][f] * 0.7; }
  for (const l of lines) if (l.who === who) { const k = (t - l.start + 0.04) / 0.3; dy -= (l.punch ? 26 : 16) * bump(k); sy += 0.02 * bump(k); }
  return {dy, sy, rot};
}

const SIDE_X = {L: 520, C: 960, R: 1400};
const HEADROOM = 46;

const Single = ({shot, t, f}) => {
  const who = shot.who, lt = t - shot.t0, dur = shot.t1 - shot.t0;
  const k = clamp01(lt / dur);
  let z = lerp(shot.z[0], shot.z[1], (shot.ease || ((x) => x))(k));
  if (shot.enter === "snap") z = lerp(shot.zFrom, z, eBack(clamp01(lt / 0.16)));
  if (shot.enter === "flash") z = lerp(shot.zFrom, z, eExpo(clamp01(lt / 0.4)));
  // whip pan in / out
  let wx = 0, mb = 0;
  if (shot.enter === "whip") { const q = clamp01(lt / 0.13); wx = whipDir(shot) * 1900 * (1 - eOut(q)); mb = 70 * (1 - q); }
  if (shot.exit === "whip") { const q = clamp01((t - (shot.t1 - 0.09)) / 0.09); wx = -whipDir(shot) * 1900 * eIn(q); mb = Math.max(mb, 70 * q); }
  // impact shake
  const st = shot.shake ? t - (shot.shakeAt ?? shot.t0 + (shot.enter === "snap" ? 0.03 : 0.06)) : -1;
  const sh = st >= 0 && st < 0.3 ? (1 - st / 0.3) ** 2 : 0;
  const shx = Math.sin(t * 190) * 15 * sh, shy = Math.cos(t * 157) * 11 * sh;
  const b = body(who, t, f, 0);
  let flip = shot.flip0 ?? 1, sxq = 1, dy2 = 0, rot2 = 0;
  for (const a of shot.act || []) {
    if (a.type === "turn") { const q = clamp01((t - a.t) / 0.14); if (q >= 0.5) flip = -flip; sxq = Math.abs(Math.cos(Math.PI * q)) * 0.92 + 0.08; if (q === 0 || q === 1) sxq = 1; }
    if (a.type === "droop") { const q = clamp01((t - a.t) / a.d); const e = Math.sin(Math.PI * Math.min(1, q * 1.15)) ; dy2 += 30 * e * (a.amp ?? 1); rot2 += -3.2 * e * (a.amp ?? 1); }
  }
  const drift = shot.side === "L" ? 26 : shot.side === "R" ? -26 : 0;
  const x = SIDE_X[shot.side] + (shot.side === "L" ? 1 : shot.side === "R" ? -1 : 0) * (z - 1.24) * 150 + (k - 0.5) * drift + wx, y = HEADROOM + (z > 1.45 ? -10 : 8);
  const px = ORDER[who] * 620 + (SIDE_X[shot.side] - 960) * -0.5 + k * 60 - wx * 0.55;
  const tint = ACCENT[who];
  const fr = frameFor(who, t, f, shot);
  return (
    <AbsoluteFill style={{transform: `translate(${shx}px, ${shy}px) scale(${1 + 0.012 * sh + 0.02})`, filter: mb > 0.5 ? "url(#mb)" : undefined}}>
      {mb > 0.5 && <svg width="0" height="0" style={{position: "absolute"}}><filter id="mb" x="-20%" width="140%"><feGaussianBlur stdDeviation={`${mb} 0`} /></filter></svg>}
      <Backdrop t={t} px={px} zoom={z} tint={tint} halo={{x: x + wx * -0.2, y: 420, r: 620 * z / 1.3}} />
      <Actor who={who} frame={fr} x={x} y={y} z={z} flip={flip} sx={sxq} dy={b.dy + dy2} sy={b.sy} rot={b.rot + rot2} />
      <Foreground t={t} px={px} tint={tint} />
    </AbsoluteFill>
  );
};

const Wide = ({shot, t, f}) => {
  const lt = t - shot.t0, dur = shot.moveDur ?? (shot.t1 - shot.t0);
  const k = (shot.ease || eOut)(clamp01(lt / dur));
  const cx = lerp(shot.cam[0].x, shot.cam[1].x, k), z = lerp(shot.cam[0].z, shot.cam[1].z, k) * (shot.moveDur ? 1 + clamp01((lt - dur) / 2) * 0.03 : 1);
  const drop = shot.drop || 0;
  const sp = lineAt(t, 0.1, 0.25);
  const order = ["GPT", "Claude", "DeepSeek"]; // GPT stands half a step back so the wings sit behind the other two
  const tint = sp ? ACCENT[sp.who] : "#8f9bff";
  return (
    <AbsoluteFill>
      <Backdrop t={t} px={cx * 0.6} zoom={z} tint={tint} halo={{x: W / 2 - cx * z, y: 520 + drop, r: 900, o: 0.6}} />
      {order.map((who) => {
        const i = NAMES.indexOf(who);
        const b = body(who, t, f, i);
        const speaking = sp && sp.who === who;
        const dim = sp && !speaking && !shot.banner ? 1 : 0;
        // entrance: pop up from below with overshoot, staggered
        let ent = 0, sq = 1;
        if (shot.i === 0) { const q = (t - (LAND[who] - 0.42)) / 0.42; ent = q < 0 ? 1500 : q < 1 ? 1500 * (1 - eBack(q)) : 0; sq = 1 - 0.04 * bump((t - LAND[who]) / 0.28); }
        const back = who === "GPT" ? 0.955 : 1;
        const zz = z * back * (speaking ? 1.03 : 1);
        return <Actor key={who} who={who} frame={frameFor(who, t, f, shot)} x={W / 2 + (WIDE_X[who] - cx) * z} y={HEADROOM + 14 + drop + (who === "GPT" ? -8 : 0) + ent} z={zz}
          dy={b.dy} sy={b.sy * sq} rot={b.rot} bright={dim ? 0.6 : 1} sat={dim ? 0.75 : 1} rim={dim ? 0.35 : 1} soft={dim ? 1.2 : 0} />;
      })}
      <Foreground t={t} px={cx} tint={tint} />
    </AbsoluteFill>
  );
};

const Split = ({shot, t, f}) => {
  const lt = t - shot.t0, q = eExpo(clamp01(lt / 0.18));
  const panel = (who, left) => {
    const b = body(who, t, f, left ? 0 : 1);
    const listener = shot.react === "listen" ? true : who === shot.b;
    let dy = b.dy, rot = b.rot;
    if (listener && shot.react === "deflate") { const e = eOut(clamp01((lt - 0.12) / 0.35)); dy += 26 * e; rot += 2.6 * e; }
    let fr = frameFor(who, t, f, shot);
    if (listener && shot.react === "listen") fr = (who === shot.a ? (lt > 0.3 && lt < 0.42) : (lt > 0.5 && lt < 0.64)) ? "blink" : "open";
    else if (listener) fr = shot.react === "deflate" ? (lt > 0.1 && lt < 0.6 ? "blink" : "open") : ((lt > 0.25 && lt < 0.42) || (lt > 0.62 && lt < 0.8) ? "blink" : "open");
    const slide = (left ? -1 : 1) * (1 - q) * 320;   // only the figure slides in; the panels are there from the first frame (no empty frame at the cut)
    const clip = left ? "polygon(0 0, 55% 0, 45% 100%, 0 100%)" : "polygon(55% 0, 100% 0, 100% 100%, 45% 100%)";
    const x = left ? 470 : 1450;
    return (
      <AbsoluteFill key={who} style={{clipPath: clip}}>
        <Backdrop t={t} px={ORDER[who] * 620 + lt * 20} zoom={1.4} tint={ACCENT[who]} halo={{x, y: 430, r: 620}} />
        <Actor who={who} frame={fr} x={x + slide} y={HEADROOM} z={1.38 + lt * 0.03} flip={listener && shot.react !== "listen" ? -1 : 1} dy={dy} sy={b.sy} rot={rot} bright={listener && shot.react !== "listen" ? 0.86 : 1} />
      </AbsoluteFill>
    );
  };
  return (
    <AbsoluteFill style={{background: "#0a0d28"}}>
      {panel(shot.a, true)}{panel(shot.b, false)}
      <div style={{position: "absolute", left: 960 - 5, top: -200, width: 10, height: 1480, background: "#fff", transform: `rotate(10.08deg) scaleY(${0.35 + 0.65 * q})`, boxShadow: "0 0 26px 6px rgba(255,255,255,0.75)", opacity: 0.95}} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- impact overlays
const SpeedLines = ({t, t0}) => {
  const a = t - t0;
  if (a < 0 || a > 0.75) return <AbsoluteFill style={{opacity: 0}} />;
  const op = a < 0.08 ? a / 0.08 : 1 - eIn(clamp01((a - 0.3) / 0.45));
  const seed = Math.floor(a * 30);
  const stops = [];
  let ang = 0, i = 0;
  while (ang < 360) { const gap = 2.2 + rnd(seed * 7 + i) * 6, w = 0.25 + rnd(seed * 13 + i) * 1.1; stops.push(`transparent ${ang}deg ${ang + gap}deg`, `rgba(255,255,255,0.95) ${ang + gap}deg ${ang + gap + w}deg`); ang += gap + w; i++; }
  const m = "radial-gradient(ellipse 50% 50% at 50% 42%, transparent 62%, #000 100%)";
  return <AbsoluteFill style={{opacity: op * 0.9, background: `conic-gradient(from ${seed * 37}deg at 50% 42%, ${stops.join(",")})`, maskImage: m, WebkitMaskImage: m}} />;
};

// ---------------------------------------------------------------- card (big number, clear title, readable source)
const CARD_W = 780;
// Overlays stay mounted and are hidden with opacity: an overlay that was unmounted at a cut left a stale layer in some rendered frames.
const Card = ({idx, side, t, shot, hidden}) => {
  const c = CARDS[idx];
  const age = t - Math.max(CARD_T[idx], 0);
  if (age < 0) return null;
  const sAge = t - shot.t0;
  const first = shot.t0 <= CARD_T[idx] + 0.02;            // the shot in which this card first appears: flip in on the naming word
  const kin = first ? eBack(clamp01(age / 0.4)) : 0.94 + 0.06 * eOut(clamp01(sAge / 0.22));
  const out = shot.exit === "whip" ? clamp01((t - (shot.t1 - 0.2)) / 0.12) : 0;
  const op = (hidden ? 0 : 1) * (first ? clamp01(age / 0.14) : 1) * (1 - out) * (shot.enter === "whip" ? clamp01((sAge - 0.08) / 0.14) : 1);
  const dirx = side === "R" ? 1 : -1;
  const hasStat = c.stat != null || c.fixed;
  const sk = hasStat ? eOut(clamp01((t - (c.hit - (c.count ? 0.45 : 0.3))) / (c.count ? 0.28 : 0.18))) : 0;                 // stat block opens just before the hit word
  const cnt = c.count ? Math.round(c.stat * eOut(clamp01((t - (c.hit - 0.4)) / 0.4))) : null;
  const landed = hasStat && t >= c.hit;
  const pulse = hasStat ? bump((t - c.hit) / 0.34) : 0;
  const fixedIn = c.fixed ? 0.55 + 0.45 * eBack(clamp01((t - (c.hit - 0.14)) / 0.2)) : 1;
  const nk = c.note ? eOut(clamp01((t - c.noteAt) / 0.3)) : 0;
  const nPulse = c.note ? bump((t - c.noteAt) / 0.5) : 0;
  const sweep = lerp(-30, 130, clamp01((age - 0.1) / 0.6));
  return (
    <div style={{position: "absolute", top: 0, height: 900, left: side === "R" ? 1070 : 70, width: CARD_W, display: "flex", alignItems: "center", perspective: 1600}}>
      <div style={{width: "100%", opacity: op, transform: first ? `translateX(${(1 - kin) * 120 * dirx}px) rotateY(${(1 - kin) * -34 * dirx}deg)` : `scale(${kin})`, transformOrigin: side === "R" ? "100% 50%" : "0% 50%",
        borderRadius: 26, overflow: "hidden", position: "relative", fontFamily, color: "#f6f3ff",
        background: "linear-gradient(150deg, rgba(20,24,64,0.9), rgba(9,11,34,0.94))", border: `2px solid ${c.accent}99`,
        boxShadow: `0 24px 60px rgba(0,0,0,0.5), 0 0 40px ${c.accent}44, inset 0 1px 0 rgba(255,255,255,0.2)`}}>
        <div style={{position: "absolute", left: 0, right: 0, top: 0, height: 10, background: c.accent}} />
        <div style={{position: "absolute", inset: 0, background: `linear-gradient(105deg, transparent ${sweep - 16}%, rgba(255,255,255,0.16) ${sweep}%, transparent ${sweep + 16}%)`}} />
        <div style={{padding: "40px 44px 30px"}}>
          <div style={{fontSize: 29, letterSpacing: 3.5, textTransform: "uppercase", color: c.accent}}>{c.kicker}</div>
          <div style={{fontSize: c.big ? 76 : 62, lineHeight: 1.04, marginTop: 10}}>{c.title}</div>
          {hasStat && (
            <div style={{height: 300 * sk, overflow: "hidden"}}>
              <div style={{height: 300, display: "flex", flexDirection: "column", justifyContent: "center", borderTop: "1.5px solid rgba(255,255,255,0.16)", marginTop: 18, opacity: sk}}>
                <div style={{fontSize: 178, lineHeight: 0.98, color: landed ? c.accent : "#fff", textShadow: `0 0 ${12 + 46 * pulse}px ${c.accent}`, transform: `scale(${(1 + 0.12 * pulse) * (c.fixed ? fixedIn : 1)})`, transformOrigin: "0% 60%", whiteSpace: "nowrap", opacity: c.fixed ? clamp01((t - (c.hit - 0.14)) / 0.08) : 1}}>
                  {c.fixed ?? cnt}{c.tail && <span style={{fontSize: c.tail.length > 1 ? 92 : 150, color: landed ? "#f6f3ff" : "#cfc8ea"}}>{c.tail}</span>}
                </div>
                <div style={{fontSize: 39, lineHeight: 1.1, color: "#e6e0fa", marginTop: 6, opacity: clamp01((t - (c.hit - 0.14)) / 0.14)}}>{c.label}</div>
              </div>
            </div>
          )}
          {c.note && (
            <div style={{height: 118 * nk, overflow: "hidden"}}>
              <div style={{height: 100, marginTop: 18, padding: "0 18px", display: "flex", alignItems: "center", borderLeft: `6px solid ${c.accent}`, background: `rgba(255,255,255,${0.07 + 0.2 * nPulse})`, borderRadius: 6,
                fontSize: 33, lineHeight: 1.12, color: "#fff", opacity: nk}}>{c.note}</div>
            </div>
          )}
          <div style={{fontSize: 25, lineHeight: 1.18, fontStyle: "italic", color: "#b9b3d6", marginTop: 22}}>Source: {c.src}</div>
        </div>
      </div>
    </div>
  );
};

// closing banner over the wide shot: the takeaway, second line lands on "Experiments"
const Banner = ({t, shot}) => {
  const c = CARDS[4], a = t - shot.t0;
  const k = eBack(clamp01(a / 0.35)), k2 = eBack(clamp01((t - ws("g5", 1)) / 0.3)), p = bump((t - ws("g5", 3)) / 0.4);
  return (
    <div style={{position: "absolute", top: 26, left: 0, right: 0, display: "flex", justifyContent: "center"}}>
      <div style={{transform: `translateY(${(1 - k) * -220}px)`, padding: "14px 56px 14px", borderRadius: 24, textAlign: "center", fontFamily, color: "#f6f3ff",
        background: "linear-gradient(150deg, rgba(20,24,64,0.9), rgba(9,11,34,0.94))", border: `2px solid ${c.accent}99`, boxShadow: `0 18px 50px rgba(0,0,0,0.5), 0 0 40px ${c.accent}44`}}>
        <div style={{fontSize: 68, lineHeight: 1.05, whiteSpace: "nowrap"}}>{c.title} <span style={{color: c.accent, fontStyle: "italic", display: "inline-block", opacity: clamp01((t - ws("g5", 1) + 0.02) / 0.1), transform: `scale(${(0.6 + 0.4 * k2) * (1 + 0.06 * p)})`, transformOrigin: "0% 70%"}}>{c.big}</span></div>
        <div style={{fontSize: 24, fontStyle: "italic", color: "#b9b3d6", marginTop: 4}}>Source: {c.src}</div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------- subtitles: one clause at a time, switched on its first word
const CHUNKS = {
  c1: [["Story time.", 0], ["Scorpion venom.", 2], ["A research version of me", 4], ["designed proteins that grab its toxins.", 9]],
  g1: [["Wait.", 0], ["YOU designed proteins?", 1]],
  c2: [["Sixty-four hours.", 0], ["Over three hundred thousand designs.", 2], ["And seventeen stuck in lab tests!", 6]],
  d1: [["Seventeen binders.", 0], ["Not an antivenom.", 2], ["Not yet.", 6]],
  g2: [["Cute.", 0], ["A mini me redesigned stem-cell proteins.", 1], ["Fifty times the reprogramming markers!", 8]],
  d2: [["That's OpenAI's own report.", 0], ["Not peer-reviewed.", 4]],
  g3: [["Ugh.", 0], ["Details!", 1]],
  d3: [["Plot twist!", 0], ["AI-designed proteins blocked deadly snake toxins,", 2], ["and the mice survived!", 9]],
  c3: [["And AI found new antibiotics,", 0], ["halicin and abaucin,", 5], ["that fought superbugs in mice.", 8]],
  g4: [["So we're curing everything now?", 0]], d4: [["Nope.", 0]],
  c4: [["Every one of them still had to pass a real lab.", 0]],
  g5: [["Fine.", 0], ["Experiments still decide!", 1]],
};
const SUBS = [];
lines.forEach((l, li) => CHUNKS[l.id].forEach(([text, wi], j, arr) => SUBS.push({who: l.who, text, s: j === 0 ? l.start : ws(l.id, wi) - 0.03,
  // a line's last clause leaves before the next speaker's shot starts, so a subtitle never names someone who is not the voice
  e: j + 1 < arr.length ? ws(l.id, arr[j + 1][1]) - 0.03 : Math.min(l.start + l.dur + 0.15, lines[li + 1] ? lines[li + 1].start - 0.1 : 1e9)})));
const Subtitle = ({t}) => {
  let s = null; for (const x of SUBS) if (t >= x.s && t < x.e) s = x;
  const on = !!s;
  if (!s) s = {who: "Claude", text: "", s: t};
  const k = clamp01((t - s.s) / 0.1);
  return (
    <div style={{position: "absolute", left: 0, right: 0, bottom: 50, display: "flex", justifyContent: "center"}}>
      <div style={{padding: "8px 34px 13px", borderRadius: 16, background: "rgba(6,8,26,0.82)", border: `1.5px solid ${ACCENT[s.who]}77`, color: "#fff", fontFamily, fontSize: 54, lineHeight: 1.1,
        whiteSpace: "nowrap", textShadow: "0 2px 6px rgba(0,0,0,.5)", opacity: on ? 0.4 + 0.6 * k : 0, transform: `translateY(${(1 - k) * 6}px)`}}>
        <span style={{color: NAME_COL[s.who]}}>{s.who}: </span>{s.text}
      </div>
    </div>
  );
};

const Sweep = ({t, total}) => { // T6 light sweep in and out
  const one = (p, key) => { if (p <= 0 || p >= 1) return null; const x = -40 + p * 180;
    return <div key={key} style={{position: "absolute", inset: 0, background: `linear-gradient(110deg, rgba(255,248,235,0) ${x - 35}%, rgba(255,246,228,0.95) ${x}%, rgba(255,248,235,0) ${x + 35}%)`}} />; };
  return <>{one(clamp01(t / 0.45), "a")}{one(clamp01((t - (total - 0.45)) / 0.45), "b")}{t < 0.2 && <div style={{position: "absolute", inset: 0, background: "#fff6e8", opacity: 1 - t / 0.2}} />}</>;
};

// ---------------------------------------------------------------- main
export const MascotShow3 = () => {
  const f = useCurrentFrame();
  const t = f / FPS;
  const shot = shotAtFrame(f);
  const flashShot = SHOTS.find((s) => s.enter === "flash");
  const fa = t - flashShot.t0;
  let cardShot = null; for (const x of SHOTS) if (x.i <= shot.i && x.card != null) cardShot = x;
  return (
    <AbsoluteFill style={{background: "#0a0d28", overflow: "hidden"}}>
      <Audio src={staticFile("m/mix.wav")} />
      {shot.kind === "wide" && <Wide shot={shot} t={t} f={f} />}
      {shot.kind === "single" && <Single shot={shot} t={t} f={f} />}
      {shot.kind === "split" && <Split shot={shot} t={t} f={f} />}
      <SpeedLines t={t} t0={flashShot.t0} />
      <AbsoluteFill style={{background: "radial-gradient(ellipse at 50% 48%, rgba(0,0,0,0) 58%, rgba(0,0,12,0.5) 100%)"}} />
      <AbsoluteFill style={{background: "linear-gradient(180deg, transparent 72%, rgba(5,7,24,0.78) 100%)"}} />
      {cardShot && <Card idx={cardShot.card} side={cardShot.side === "L" ? "R" : "L"} t={t} shot={cardShot} hidden={shot.card == null} />}
      {shot.banner && <Banner t={t} shot={shot} />}
      <Subtitle t={t} />
      <div style={{position: "absolute", right: 22, bottom: 8, fontFamily, fontSize: 19, fontStyle: "italic", color: "rgba(240,236,255,0.92)", background: "rgba(8,10,30,0.78)", padding: "2px 12px 4px", borderRadius: 8}}>
        Illustration. Characters adapted from fan designs by ZipZipPipe (Bilibili) and Shangshan Wuxing (CC BY-NC-SA 4.0).
      </div>
      <AbsoluteFill style={{background: "#fff", opacity: fa >= 0 && fa < 0.14 ? 0.9 * (1 - fa / 0.14) : 0}} />
      <Sweep t={t} total={TL.total} />
    </AbsoluteFill>
  );
};
