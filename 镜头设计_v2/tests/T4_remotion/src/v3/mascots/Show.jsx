// HKBU SCIE1007 coursework video: AI mascot insert (Claude / GPT / DeepSeek). Timeline from data/timeline.json (gen_voice.py).
import React from "react";
import {AbsoluteFill, useCurrentFrame, spring} from "remotion";
import {loadFont} from "@remotion/google-fonts/InstrumentSerif";
import {Stage} from "./Stage";
import {NAMES, NAME_COLOR} from "./Character";
import TL from "./data/timeline.json";

loadFont();
export const FPS = 60;
export const TOTAL_FRAMES = Math.ceil(TL.total * FPS);

export const CARDS = [
  {title: "AI in drug discovery", sub: "What is new, 2024 to 2026: public, checkable milestones.", src: null, accent: "#e9691c"},
  {title: "2024 · AlphaFold 3", sub: "Predicts how proteins fit with small molecules, DNA and RNA.", src: "Abramson et al., Nature 2024", accent: "#6d5fc0"},
  {title: "2024 · Chemistry Nobel Prize", sub: "Awarded for protein structure prediction and computational protein design.", src: "Nobel Prize announcement, 9 Oct 2024", accent: "#2c55b8"},
  {title: "2025 · Rentosertib, phase 2a", sub: "AI-designed TNIK inhibitor, lung fibrosis, 71 patients. Small, early trial.", src: "Nature Medicine, 3 Jun 2025", accent: "#e9691c"},
  {title: "Sep 2026 · Lirafugratinib", sub: "FDA-approved for FGFR2-driven bile duct cancer. AI-assisted platform.", src: "U.S. FDA, 23 Sep 2026", accent: "#2c55b8"},
  {title: "AI narrows the search.", sub: "Experiments still decide.", src: "Our summary of the cases above", accent: "#6d5fc0"},
];
const WINKS = [["Claude", "c1"], ["DeepSeek", "d1"], ["GPT", "g2"], ["Claude", "c3"], ["GPT", "g3"]];
const X = {Claude: -3.5, GPT: 0, DeepSeek: 3.5};
const Z = {Claude: 0, GPT: 0.25, DeepSeek: 0};
const ROT = {Claude: 0.14, GPT: 0, DeepSeek: -0.14};

const bump = (x) => (x <= 0 || x >= 1 ? 0 : Math.sin(Math.PI * x) ** 0.6);

export function charState(who, t, extra = {}) {
  const lines = TL.lines;
  let open = 0, nod = 0;
  const L = lines.find((l) => l.who === who && t >= l.start && t < l.start + l.dur);
  if (L) {
    const i = Math.floor((t - L.start) * FPS), e = L.env;
    const v = ((e[i - 1] ?? 0) + (e[i] ?? 0) * 2 + (e[i + 1] ?? 0)) / 4;
    open = Math.min(1, Math.pow(v, 0.8) * 1.0);
    nod = Math.sin(t * 9) * 2 * v;
  }
  const per = 3.3 + NAMES.indexOf(who) * 0.55, ph = (t + NAMES.indexOf(who) * 1.3) % per;
  const blink = ph < 0.2 ? Math.sin((ph / 0.2) * Math.PI) : 0;
  let wink = null;
  for (const [w, id] of WINKS) {
    if (w !== who) continue;
    const ln = lines.find((l) => l.id === id), c = ln.start + ln.dur + 0.05, a = bump((t - (c - 0.3)) / 0.7);
    if (a > 0) wink = {side: who === "Claude" ? "R" : who === "GPT" ? "L" : "R", amt: Math.min(1, a * 1.4)};
  }
  return {t, open, blink: wink ? 0 : blink, wink, nod, ...extra};
}

export const MascotShow = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const lines = TL.lines;
  const active = lines.find((l) => t >= l.start && t < l.start + l.dur + 0.15);
  const lastStarted = [...lines].reverse().find((l) => t >= l.start);
  const cardIdx = lastStarted ? lastStarted.card : 0;
  const cardStart = cardIdx === 0 ? 0 : lines.find((l) => l.card === cardIdx).start;
  const appear = spring({frame: frame - 12, fps: FPS, config: {damping: 14, stiffness: 120}});
  const chars = NAMES.map((who, i) => {
    const p = spring({frame: frame - (8 + i * 16), fps: FPS, config: {damping: 8, stiffness: 140}});
    const speaking = active && active.who === who;
    const sc = (0.96 + (speaking ? 0.07 : 0)) * (0.3 + 0.7 * Math.min(1.12, p));
    const bob = speaking ? Math.abs(Math.sin(t * 6)) * 0.05 : 0;
    return {who, state: charState(who, t), x: X[who], z: Z[who], rotY: ROT[who], scale: sc, y: -0.45 - (1 - p) * 3.4 + bob};
  });
  return (
    <AbsoluteFill style={{background: "#e8dcff"}}>
      <Stage width={1920} height={1080} t={t} frame={frame} chars={chars} card={CARDS[cardIdx]} cardKey={cardIdx} cardAge={t - cardStart} boardAppear={Math.max(0.001, appear)} P={60} total={TL.total} />
      {active && (
        <div style={{position: "absolute", left: 0, right: 0, bottom: 44, display: "flex", justifyContent: "center"}}>
          <div style={{maxWidth: 1500, padding: "10px 30px 14px", borderRadius: 18, background: "rgba(30,22,46,0.82)", color: "#fff", fontFamily: "'Instrument Serif', serif", fontSize: 52, lineHeight: 1.12, textAlign: "center", textShadow: "0 2px 6px rgba(0,0,0,.4)"}}>
            <span style={{color: "#ffc58f"}}>{active.who}: </span>{active.text}
          </div>
        </div>
      )}
    </AbsoluteFill>
  );
};

// 2-second seamless wink loop for one character (no board, no subtitle)
export const WINK_FRAMES = 120;
export const WinkLoop = ({who}) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const a = bump((t - 0.55) / 0.8);
  const state = {t, open: 0, blink: 0, nod: 0, loopP: 2, wink: a > 0 ? {side: who === "GPT" ? "L" : "R", amt: Math.min(1, a * 1.5)} : null};
  const chars = [{who, state, x: 0, z: 0, rotY: 0, scale: 1.18, y: -0.05}];
  return (
    <AbsoluteFill style={{background: "#e8dcff"}}>
      <Stage width={1920} height={1080} t={t} frame={frame} chars={chars} card={null} P={2} total={2} loop charHeight={4.6} />
      <div style={{position: "absolute", bottom: 40, width: "100%", textAlign: "center", fontFamily: "'Instrument Serif', serif", fontSize: 64, color: NAME_COLOR[who]}}>{who}</div>
    </AbsoluteFill>
  );
};
