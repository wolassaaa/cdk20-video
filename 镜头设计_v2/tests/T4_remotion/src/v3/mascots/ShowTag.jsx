// HKBU SCIE1007 coursework video: post-credits AI skit (four characters, 19 section 4). Composition "MascotTag".
// Voice is the time base: every frame number comes from data/shots_tag.json (build_shots_tag.py, words found by text in
// data/timeline_tag.json). All card and subtitle text is read from cards_tag.json / lines_tag.json through that file.
// Characters are only the Codex art in pub_tag/t/<who>/ (whole-image scale and move, small hops/sinks/tilts; never redrawn,
// never mirrored). All scaling, placement and cropping come from art_meta.json (prep_assets_tag.py): no per-character pixel
// constants live in this file. Overlays (cards, tags, subtitles) stay mounted and are hidden with opacity.
import React from "react";
import {AbsoluteFill, useCurrentFrame, Easing, Audio, Img, staticFile} from "remotion";
import {loadFont} from "@remotion/google-fonts/InstrumentSerif";
import SH from "./data/shots_tag.json";
import META from "./art_meta.json";

const {fontFamily} = loadFont();
export const FPS_TAG = 60;
// 11-23 director: all copyright and source text goes to one closing card after S79 (no per-card source lines, no disclosure line,
// no voice-prompt box, no decorative version tags). The card holds still for CREDITS_F frames; dialogue and bed are untouched.
export const CREDITS_F = 360;
export const TOTAL_TAG = SH.frames + CREDITS_F;
const W = 1920, HH = 1080;
const DIR = {Claude: "claude", ChatGPT: "gpt", DeepSeek: "deepseek", Gemini: "gemini"};
const ORDER = ["Claude", "ChatGPT", "DeepSeek", "Gemini"];
export const ACCENT = {Claude: "#ff9a4d", ChatGPT: "#c8b8ff", DeepSeek: "#58b4ff", Gemini: "#9b8cff"};
const NAME_COL = {Claude: "#ffb27a", ChatGPT: "#d9ceff", DeepSeek: "#8fd0ff", Gemini: "#bdb3ff"};
const BONE = "#F7F4EE";
// layout constants (frame geometry, not character sizes)
const U = 2150;            // screen px of a full figure (head top to sole) at zoom 1.0 in singles
const DUAL = 0.62;         // the Gemini + clones mid shot: zoom 1.0 = 0.62 U, so the six clones stay in frame
const HEAD_Y = 46;         // head top in singles
const WIDE_Y = 180;        // head top in wide shots (room for the small name tags and the closing banner)
const BANNER_Y = 226;      // head top in shots under the closing banner: the banner ends at ~206, figures start below it
const underBanner = (shot) => shot.f0 < SH.banner.f_out && shot.f1 > SH.banner.f_in;
const SIDE_X = {L: 520, C: 960, R: 1400};
const CLONE_REF = 1333;    // clone offsets (105 k right, 38 k up) are given for a 1333 px tall Gemini

const clamp01 = (x) => Math.min(1, Math.max(0, x));
const lerp = (a, b, k) => a + (b - a) * k;
const bump = (x) => (x <= 0 || x >= 1 ? 0 : Math.sin(Math.PI * x));
const rnd = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const eOut = Easing.out(Easing.cubic), eBack = Easing.out(Easing.back(1.7)), eIn = Easing.in(Easing.cubic), eIO = Easing.inOut(Easing.cubic);

const SHOTS = SH.shots;
SHOTS.forEach((s, i) => { s.i = i; });
const shotAt = (f) => { let r = SHOTS[0]; for (const s of SHOTS) if (f >= s.f0) r = s; return r; };
const NF = SH.frames;

// ---------------------------------------------------------------- art meta (all geometry from the measured table)
const meta = (who, name) => META[DIR[who]][name];
const src = (who, name) => staticFile(`t/${DIR[who]}/${name}${name.startsWith("tag_") ? ".png" : ".webp"}`);
const fullRef = (who, name) => { const n = meta(who, "full_neutral"), m = meta(who, name) || n; return m.w === n.w && m.h === n.h ? n : m; };
// full figure of height H: returns {s, left, top} so the head top sits at y and the anchor x (face or bbox centre) at x
function placeFull(who, name, H, x, y, anchor = "face") {
  const m = fullRef(who, name), s = H / (m.foot - m.top);
  const ax = anchor === "face" ? m.face_cx : (m.bbox[0] + m.bbox[2]) / 2;
  return {s, left: x - ax * s, top: y - m.top * s, w: (meta(who, name) || m).w * s, h: (meta(who, name) || m).h * s, waist: y + 0.42 * H, m};
}
// bust "equivalent to" a full figure of height H; never shorter than the frame (the cut edge must stay below the frame)
function placeBust(who, name, H, x, y) {
  const n = meta(who, "full_neutral"), b = meta(who, name);
  let s = H / (n.foot - n.top) / b.k;
  s = Math.max(s, (HH + 10 - y) / (b.bbox[3] - b.top));
  return {s, left: x - b.face_cx * s, top: y - b.top * s, w: b.w * s, h: b.h * s};
}
const widthRatio = (who) => { const n = meta(who, "full_neutral"); return (n.bbox[2] - n.bbox[0]) / (n.foot - n.top); };

// ---------------------------------------------------------------- voice: mouths, hops, envelopes
const VOICE = SH.voice;
const MOUTH = {}, ENV = {}, ONSET = {};
for (const w of ORDER) {
  const st = new Array(NF + 2).fill(null), env = new Float32Array(NF + 2), on = new Int32Array(NF + 2).fill(-999);
  for (const l of VOICE.filter((x) => x.who === w)) {
    let cur = "base", hold = 0;
    const n = l.env.length;
    for (let i = 0; i < n; i++) {
      const v = ((l.env[i - 1] ?? 0) + 2 * l.env[i] + (l.env[i + 1] ?? 0)) / 4;
      const want = v < 0.14 ? "base" : v < 0.48 ? "talk_o" : "talk_a";
      if (want !== cur && hold >= 3) { cur = want; hold = 0; } else hold++;
      const f = l.f0 + i; if (f <= NF) { st[f] = cur; env[f] = v; }
    }
    for (const o of l.onsets) for (let f = o; f < Math.min(NF + 2, o + 3); f++) on[f] = o;
  }
  MOUTH[w] = st; ENV[w] = env; ONSET[w] = on;
}
const speakingAt = (w, f) => VOICE.some((l) => l.who === w && f >= l.f0 && f < l.f1);
const speakersAt = (f) => VOICE.filter((l) => f >= l.f0 && f < l.f1).map((l) => l.who);

// the image a character shows at frame f in a shot, given the shot's art for her
function artFor(shot, who, base, f) {
  let art = base;
  for (const a of SH.art_at) if (a.shot === shot.id && a.who === who && f >= a.f) art = a.art;
  for (const a of SH.act) if (a.shot === shot.id && a.who === who && a.type === "blink2") {
    const q = f - a.f; if ((q >= 0 && q < 6) || (q >= 14 && q < 20)) art = art.split("_")[0] + "_blink";
  }
  const [kind, expr] = [art.split("_")[0], art.split("_").slice(1).join("_")];
  if (speakingAt(who, f) && (expr === "neutral" || expr === "think")) {
    const m = MOUTH[who][f];
    if (m === "talk_o" || m === "talk_a") return `${kind}_${m}`;
    return art;
  }
  if (!speakingAt(who, f) && expr === "neutral") {   // listeners in a neutral state blink now and then
    const P = {Claude: 199, ChatGPT: 233, DeepSeek: 171, Gemini: 187}[who], off = {Claude: 40, ChatGPT: 110, DeepSeek: 75, Gemini: 20}[who];
    if ((f + off) % P < 6) return `${kind}_blink`;
  }
  return art;
}

// body acting: breathing, the hop on each spoken word for static faces, the shot's small acts
function body(shot, who, art, f, idx = 0) {
  const t = f / 60;
  let dy = 0, dx = 0, rot = Math.sin(t * 0.9 + idx * 2) * 0.3, sc = 1 + Math.sin(t * 2 * Math.PI / (3.2 + idx * 0.4) + idx) * 0.003;
  const expr = art.split("_").slice(1).join("_");
  if (speakingAt(who, f)) {
    const on = ONSET[who][f];
    if (on > 0 && !(expr.startsWith("talk") || expr === "neutral" || expr === "think")) dy -= 5 * (1 - (f - on) / 3);
    sc *= 1 + 0.01 * ENV[who][f];
  }
  for (const a of SH.act) {
    if (a.shot !== shot.id || a.who !== who) continue;
    const q = (f - a.f) / a.d;
    if (a.type === "sink") { const e = eOut(clamp01(q)); dy += 26 * e; rot += 2.6 * e; }
    if (a.type === "nod") dy += 30 * bump(clamp01(q));
    if (a.type === "sigh") { const e = Math.sin(Math.PI * Math.min(1, clamp01(q) * 1.15)); dy += 30 * e; rot += -3 * e; }
    if (a.type === "tilt") rot += 3;
    if (a.type === "jump") dy -= 60 * bump(clamp01(q));
    if (a.type === "run_left") { const e = eIn(clamp01(q)); dx -= 1900 * e; dy -= 18 * Math.abs(Math.sin(q * 14)) * (q > 0 && q < 1 ? 1 : 0); }
    if (a.type === "run_right") { const e = eIn(clamp01(q)); dx += 1900 * e; dy -= 18 * Math.abs(Math.sin(q * 14)) * (q > 0 && q < 1 ? 1 : 0); }
  }
  return {dy, dx, rot, sc};
}

// ---------------------------------------------------------------- stage
const PANELS = Array.from({length: 9}, (_, i) => ({x: -1900 + i * 480 + rnd(i) * 160, w: 150 + rnd(i + 9) * 170, h: 760 + rnd(i + 20) * 420, o: 0.1 + rnd(i + 31) * 0.14, sk: -6 + rnd(i + 5) * 12, warm: rnd(i + 44) > 0.6}));
const BOKEH = Array.from({length: 34}, (_, i) => ({x: -1500 + rnd(i * 3 + 1) * 3000, y: rnd(i * 3 + 2) * 1080, r: 26 + rnd(i * 3 + 3) * 90, d: 0.3 + rnd(i * 7) * 0.5, o: 0.07 + rnd(i * 5) * 0.2, c: i % 4, ph: rnd(i * 11) * 6.28}));
const DUST = Array.from({length: 9}, (_, i) => ({x: -1200 + rnd(i * 13 + 4) * 2400, y: rnd(i * 17 + 2) * 1080, r: 120 + rnd(i * 19) * 200, ph: rnd(i * 23) * 6.28}));
const HEX_BG = `url("data:image/svg+xml;utf8,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="168" height="97"><g fill="none" stroke="#cfd6ff" stroke-width="1.6"><path d="M28 0l28 16v32l-28 16L0 48V16zM112 0l28 16v32l-28 16-28-16V16zM70 48.5l28 16v32M70 48.5l-28 16v32M154 48.5l-28 16v32M154 48.5l14 8"/></g><g fill="#cfd6ff"><circle cx="28" cy="0" r="3"/><circle cx="56" cy="48" r="3"/><circle cx="112" cy="64" r="3"/><circle cx="140" cy="16" r="3"/></g></svg>')}")`;

// softbox brightness 0..1 at frame f (S02 light-up from the middle, S52-S55 dimmed, S79 three steps off)
function boxLight(f, i) {
  const lu = SH.fx.light_up, dm = SH.fx.dim, e = SH.fx.s79;
  let k = 1;
  if (f >= lu.f && f < lu.f + lu.boxes) { const r = (f - lu.f) / lu.boxes * 2100; k = Math.abs(PANELS[i].x + PANELS[i].w / 2) < r ? 1 : 0.15; }
  if (f >= dm.f0 - 1 && f < dm.f1 + dm.ramp) { const a = clamp01((f - dm.f0) / dm.ramp), b = clamp01((f - dm.f1) / dm.ramp); k *= lerp(1, dm.to, a * (1 - b)); }
  if (f >= e.f0) { const grp = Math.min(2, Math.floor((PANELS[i].x + 1900) / 1450)); if (f >= e.f0 + e.off[grp]) k *= Math.max(0.0, 1 - (f - e.f0 - e.off[grp]) / 3); }
  return k;
}

const Backdrop = ({f, px = 0, zoom = 1, tint, halo, spot}) => {
  const t = f / 60;
  const zk = 1 + (zoom - 0.85) * 0.2, blur = 6 + clamp01((zoom - 0.7) / 1.0) * 14;
  const cols = ["#ffffff", tint, "#ffd9a8", "#9fb4ff"];
  const dimAll = (() => { const dm = SH.fx.dim; const a = clamp01((f - dm.f0) / dm.ramp), b = clamp01((f - dm.f1) / dm.ramp); return lerp(1, 0.6, a * (1 - b)); })();
  const s79 = f >= SH.fx.s79.f0 ? 1 - 0.75 * clamp01((f - SH.fx.s79.f0 - SH.fx.s79.off[0]) / 33) : 1;
  return (
    <AbsoluteFill style={{overflow: "hidden", background: "#0a0d28"}}>
      <AbsoluteFill style={{background: "linear-gradient(180deg, #080a22 0%, #121848 38%, #1d2468 66%, #2a2f7a 100%)", opacity: dimAll * s79}} />
      <AbsoluteFill style={{background: `radial-gradient(ellipse 75% 60% at ${50 - px * 0.004}% 62%, ${tint}55 0%, ${tint}1c 45%, transparent 75%)`, opacity: dimAll * s79}} />
      <div style={{position: "absolute", left: -400, top: -200, width: W + 800, height: HH + 400, backgroundImage: HEX_BG, backgroundSize: "168px 97px", opacity: 0.22 * dimAll * s79,
        transform: `translateX(${-px * 0.12}px) scale(${1 + (zk - 1) * 0.5})`, filter: `blur(${1 + blur * 0.12}px)`,
        maskImage: "radial-gradient(ellipse 55% 60% at 50% 45%, #000 0%, transparent 78%)", WebkitMaskImage: "radial-gradient(ellipse 55% 60% at 50% 45%, #000 0%, transparent 78%)"}} />
      <div style={{position: "absolute", inset: 0, transform: `scale(${zk})`, filter: `blur(${blur * 1.1 + 9}px)`}}>
        {PANELS.map((p, i) => (
          <div key={i} style={{position: "absolute", left: W / 2 + p.x - px * 0.3, top: HH * 0.5 - p.h / 2 + Math.sin(t * 0.3 + i) * 8, width: p.w, height: p.h, borderRadius: 40,
            transform: `skewX(${p.sk}deg)`, opacity: (p.o + 0.06) * (0.85 + 0.15 * Math.sin(t * 0.7 + i * 1.7)) * boxLight(f, i),
            background: `linear-gradient(180deg, transparent 0%, ${p.warm ? "#ffe6c4" : "#dfe6ff"} 30%, ${tint} 75%, transparent 100%)`}} />
        ))}
      </div>
      {halo && <div style={{position: "absolute", left: halo.x - halo.r, top: halo.y - halo.r, width: halo.r * 2, height: halo.r * 2, borderRadius: "50%",
        background: `radial-gradient(circle, ${tint}88 0%, ${tint}3a 38%, transparent 70%)`, opacity: (halo.o ?? 1) * s79}} />}
      {[0, 1].map((i) => (
        <div key={i} style={{position: "absolute", left: W * (0.18 + i * 0.5) - px * 0.2, top: -300, width: 260, height: 1700, opacity: (0.1 + 0.03 * Math.sin(t * 0.5 + i * 2)) * dimAll * s79,
          transform: `rotate(${(i ? -17 : 21) + Math.sin(t * 0.23 + i) * 2}deg)`, filter: "blur(40px)", background: "linear-gradient(90deg, transparent, #ffffff, transparent)"}} />
      ))}
      {spot && <div style={{position: "absolute", left: spot.x - 420, top: -120, width: 840, height: 1320, opacity: spot.o,
        background: "radial-gradient(ellipse 50% 60% at 50% 55%, rgba(255,246,228,0.30) 0%, rgba(255,246,228,0.12) 45%, transparent 72%)",
        clipPath: "polygon(38% 0, 62% 0, 100% 100%, 0 100%)", filter: "blur(10px)"}} />}
      {BOKEH.map((b, i) => {
        const x = W / 2 + b.x - px * b.d + Math.sin(t * 0.25 + b.ph) * 22, y = ((b.y - t * (6 + b.d * 14)) % (HH + 200) + HH + 200) % (HH + 200) - 100;
        const r = b.r * zk;
        return <div key={i} style={{position: "absolute", left: x - r, top: y - r, width: r * 2, height: r * 2, borderRadius: "50%", opacity: b.o * (0.7 + 0.3 * Math.sin(t * 1.3 + b.ph)) * dimAll * s79,
          background: `radial-gradient(circle, ${cols[b.c]}66 0%, ${cols[b.c]}44 62%, ${cols[b.c]}aa 70%, transparent 74%)`, filter: `blur(${1.5 + (1 - b.d) * 4}px)`}} />;
      })}
      <AbsoluteFill style={{background: "linear-gradient(180deg, rgba(4,6,24,0.55) 0%, transparent 22%, transparent 70%, rgba(6,8,30,0.5) 100%)"}} />
    </AbsoluteFill>
  );
};
const Foreground = ({f, px = 0, tint}) => {
  const t = f / 60;
  return (
    <AbsoluteFill style={{overflow: "hidden", pointerEvents: "none"}}>
      {DUST.map((b, i) => {
        const x = W / 2 + b.x - px * 1.5 + Math.sin(t * 0.2 + b.ph) * 60, y = ((b.y - t * 22) % (HH + 500) + HH + 500) % (HH + 500) - 250;
        return <div key={i} style={{position: "absolute", left: x - b.r, top: y - b.r, width: b.r * 2, height: b.r * 2, borderRadius: "50%", opacity: 0.07,
          background: `radial-gradient(circle, ${i % 2 ? tint : "#ffffff"} 0%, transparent 68%)`, filter: "blur(18px)"}} />;
      })}
    </AbsoluteFill>
  );
};

// one placed image (character art, clone or tag); the whole image only moves, scales and tilts
const Art = ({who, name, p, b = {dy: 0, dx: 0, rot: 0, sc: 1}, rim = 1, bright = 1, sat = 1, soft = 0, opacity = 1, pivotY = 0.7}) => (
  <div style={{position: "absolute", left: p.left + b.dx, top: p.top + b.dy, width: p.w, height: p.h, opacity,
    transformOrigin: `50% ${pivotY * 100}%`, transform: `rotate(${b.rot}deg) scale(${b.sc})`,
    filter: `drop-shadow(0 0 1.4px rgba(255,255,255,${0.7 * rim})) drop-shadow(0 0 18px ${ACCENT[who]}${Math.round(140 * rim).toString(16).padStart(2, "0")}) brightness(${bright}) saturate(${sat})${soft ? ` blur(${soft}px)` : ""}`}}>
    <Img src={src(who, name)} style={{width: "100%", height: "100%", display: "block"}} />
  </div>
);

// ---------------------------------------------------------------- Gemini's clones (behind her, waist-anchored diagonal)
function cloneState(c, f) {   // 0..1 presence (pop in / go back in)
  let v = 0;
  for (const [a, b] of c.on) {
    if (f < a) continue;
    const pin = eBack(clamp01((f - a) / 10));
    const pout = b != null && f >= b ? 1 - clamp01((f - b) / 10) : 1;
    v = Math.max(v, pin * pout);
  }
  return v;
}
const Clones = ({f, H, gx, gy, shot}) => {
  const k0 = H / CLONE_REF;
  const cm = META.gemini.clone;
  const run = f >= SH.clone_run ? eIn(clamp01((f - SH.clone_run) / 40)) * 1900 : 0;
  const sway = f >= SH.clone_sway[0] && f < SH.clone_sway[1] ? Math.sin((f - SH.clone_sway[0]) / 60 * 2 * Math.PI * 1.6) * 6 * bump(clamp01((f - SH.clone_sway[0]) / (SH.clone_sway[1] - SH.clone_sway[0]))) : 0;
  const waist = gy + 0.42 * H;
  const items = SH.clones.map((c) => ({c, v: cloneState(c, f)})).filter((x) => x.v > 0.001);
  return (
    <>
      {items.slice().reverse().map(({c, v}) => {
        const k = c.k, Hc = H * Math.pow(0.86, k), s = Hc / (cm.foot - cm.top);
        const cx = gx + 105 * k * k0 + run * (1 + k * 0.08), cw = waist - 38 * k * k0;
        const top = cw - 0.42 * Hc, left = cx - cm.face_cx * s;
        const sparkle = v < 1 && v > 0 ? 1 : 0;
        return (
          <div key={c.k} style={{position: "absolute", left, top, width: cm.w * s, height: cm.h * s, transformOrigin: "50% 92%",
            transform: `scale(${v}) rotate(${sway * (k % 2 ? 1 : -1)}deg)`, opacity: Math.min(1, v * 1.4),
            filter: `drop-shadow(0 0 ${10 + 18 * sparkle}px #9fe8ffaa) brightness(${1.05 + 0.4 * sparkle})`}}>
            <Img src={src("Gemini", "clone")} style={{width: "100%", height: "100%", display: "block"}} />
          </div>
        );
      })}
    </>
  );
};
const clonesVisible = (f) => SH.clones.some((c) => cloneState(c, f) > 0.001);

// ---------------------------------------------------------------- name tags
const BigTag = ({who, f, f_in, scale = 1, left, top, origin = "0% 100%"}) => {
  const n = SH.nametags[who], q = clamp01((f - f_in) / 10), k = eBack(q);
  return (
    <div style={{position: "absolute", left, top, width: 520, transform: `scale(${scale}) translateY(${(1 - k) * 60}px) rotateX(${(1 - k) * 70}deg)`, transformOrigin: origin,
      opacity: clamp01(q * 2), fontFamily, color: BONE, textShadow: "0 3px 14px rgba(0,0,20,.65)"}}>
      <div style={{fontSize: 34, fontStyle: "italic", letterSpacing: "0.12em", color: ACCENT[who], lineHeight: 1.1}}>{n.no}</div>
      <div style={{display: "inline-block", fontSize: 112, lineHeight: 1.0, borderBottom: `2px solid ${ACCENT[who]}`, paddingBottom: 4, whiteSpace: "nowrap"}}>{n.name}</div>
      <div style={{fontSize: 40, fontStyle: "italic", color: "rgba(255,255,255,0.8)", marginTop: 8, lineHeight: 1.1, whiteSpace: "nowrap"}}>{n.subtitle}</div>
    </div>
  );
};
// ---------------------------------------------------------------- cards
const CARD_W = 780;
const statSize = (txt) => Math.min(178, 700 / (0.42 * [...txt].length));
const CardView = ({c, f, side, op, mode, settle}) => {
  const first = f - c.first, kin = mode === "first" ? eBack(clamp01(first / 24)) : 1;
  const dirx = side === "R" ? 1 : -1;
  const r0 = c.rows[0].f, open = eOut(clamp01((f - (r0 - 27)) / 17));
  const nk = eOut(clamp01((f - c.note_f) / 18)), nPulse = bump(clamp01((f - c.note_f) / 30));
  const sweep = lerp(-30, 130, clamp01((first - 6) / 36));
  const small = mode === "small";
  const rowH = c.rows.map((r) => statSize(r.text) * 0.98);
  const stamp = c.stamp && f >= c.stamp.f ? clamp01((f - c.stamp.f) / 6) : 0;
  const side_k = c.side_note && f >= c.side_note.f ? eBack(clamp01((f - c.side_note.f) / 10)) : 0;
  const statOpen = small ? 0 : open;
  const wrapStyle = small
    ? {position: "absolute", left: 40, top: 36, width: CARD_W, transform: `scale(0.6) translateX(${(1 - kin) * -160}px)`, transformOrigin: "0 0"}
    : {position: "absolute", left: side === "R" ? 1070 : 70, top: 30, height: 880, width: CARD_W, display: "flex", alignItems: "center", perspective: 1600};
  return (
    <div style={wrapStyle}>
      <div style={{width: "100%", opacity: op, transform: mode === "first" ? `translateX(${(1 - kin) * 120 * dirx}px) rotateY(${(1 - kin) * -34 * dirx}deg)` : `scale(${settle})`,
        transformOrigin: side === "R" ? "100% 50%" : "0% 50%", borderRadius: 26, overflow: "hidden", position: "relative", fontFamily, color: "#f6f3ff",
        background: "linear-gradient(150deg, rgba(20,24,64,0.92), rgba(9,11,34,0.95))", border: `2px solid ${c.accent}99`,
        boxShadow: `0 24px 60px rgba(0,0,0,0.5), 0 0 40px ${c.accent}44, inset 0 1px 0 rgba(255,255,255,0.2)`}}>
        <div style={{position: "absolute", left: 0, right: 0, top: 0, height: 10, background: c.accent}} />
        <div style={{position: "absolute", inset: 0, background: `linear-gradient(105deg, transparent ${sweep - 16}%, rgba(255,255,255,0.14) ${sweep}%, transparent ${sweep + 16}%)`}} />
        <div style={{padding: "36px 42px 28px", position: "relative"}}>
          {c.side_note && <div style={{position: "absolute", right: 40, top: 30, fontSize: 44, fontStyle: "italic", padding: "2px 16px", borderRadius: 12, border: `2px solid ${c.accent}`,
                color: c.accent, background: "rgba(10,12,34,0.8)", opacity: side_k > 0 ? 1 : 0, transform: `scale(${0.6 + 0.4 * side_k}) rotate(4deg)`}}>{c.side_note.text}</div>}
          <div style={{fontSize: 29, letterSpacing: 3.5, textTransform: "uppercase", color: c.accent, lineHeight: 1.15}}>{c.kicker}</div>
          <div style={{fontSize: 62, lineHeight: 1.04, marginTop: 8}}>{c.title}</div>
          {c.funnel && (
            <div style={{fontSize: 40, marginTop: 12, whiteSpace: "nowrap", lineHeight: 1.1}}>
              {c.funnel.map((s, i) => {
                const hf = s.f ?? c.funnel[i + 1]?.f; const on = f >= hf; const p = bump(clamp01((f - hf) / 24));
                return <span key={i} style={{color: s.f != null ? (on ? c.accent : "#fff") : "#b9b3d6", opacity: on ? 1 : 0, textShadow: `0 0 ${18 * p}px ${c.accent}`}}>{s.text}</span>;
              })}
            </div>
          )}
          {c.desc_lines && (
            <div style={{fontSize: 39, lineHeight: 1.12, marginTop: 14, fontStyle: "italic"}}>
              {c.desc_lines.map((d, i) => <div key={i} style={{color: f >= d.f ? "#ffffff" : "rgba(230,224,250,0.38)", textShadow: f >= d.f ? `0 0 ${16 * bump(clamp01((f - d.f) / 24))}px ${c.accent}` : "none"}}>{d.text}</div>)}
            </div>
          )}
          <div style={{height: (rowH.reduce((a, b) => a + b, 0) + 28 + (c.desc_lines ? 0 : 92)) * statOpen, overflow: "hidden", position: "relative"}}>
            <div style={{borderTop: "1.5px solid rgba(255,255,255,0.16)", marginTop: 18, paddingTop: 8, opacity: statOpen, position: "relative"}}>
              {c.rows.map((r, i) => {
                const fs = statSize(r.text), landed = f >= r.f, pulse = bump(clamp01((f - r.f) / 20));
                let txt = r.text, o = 1, sc = 1;
                if (r.count) {
                  const q = clamp01((f - (r.f - 24)) / 24);
                  let v = Math.round(r.count.n * eOut(q)); if (!landed) v = Math.min(v, r.count.n - 1);
                  txt = `${r.count.pre}${v}${r.count.post}`; o = f >= r.f - 24 ? 1 : 0;
                } else { o = landed ? 1 : 0; sc = landed ? 0.7 + 0.3 * eBack(clamp01((f - r.f) / 12)) : 0.7; }
                return <div key={i} style={{fontSize: fs, lineHeight: 0.98, height: fs * 0.98, whiteSpace: "nowrap", color: landed ? c.accent : "#fff", opacity: o,
                  textShadow: `0 0 ${12 + 46 * pulse}px ${c.accent}`, transform: `scale(${sc * (1 + 0.1 * pulse)})`, transformOrigin: "0% 60%"}}>{txt}</div>;
              })}
              {!c.desc_lines && <div style={{fontSize: 39, lineHeight: 1.1, color: "#e6e0fa", marginTop: 8}}>{c.desc}</div>}
              
              {c.stamp && <div style={{position: "absolute", right: 10, top: 40, fontSize: 92, letterSpacing: 4, color: "#ff3b4e", border: "6px solid #ff3b4e", borderRadius: 14, padding: "0 18px",
                lineHeight: 1.1, transform: `rotate(-8deg) scale(${stamp > 0 ? lerp(1.7, 1, eOut(stamp)) : 1.7})`, opacity: stamp > 0 ? 0.92 : 0, background: "rgba(40,0,8,0.35)",
                boxShadow: "0 0 30px rgba(255,59,78,.45)"}}>{c.stamp.text}</div>}
            </div>
          </div>
          {c.note && (
            <div style={{height: 112 * nk, overflow: "hidden"}}>
              <div style={{minHeight: 92, marginTop: 16, padding: "6px 18px", display: "flex", alignItems: "center", borderLeft: `6px solid ${c.accent}`,
                background: `rgba(255,255,255,${0.07 + 0.2 * nPulse})`, borderRadius: 6, fontSize: 33, lineHeight: 1.12, color: "#fff", opacity: nk}}>{c.note}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
const CARD_ACCENT = {"0": ACCENT.Claude, "1": ACCENT.ChatGPT, "2": ACCENT.Gemini, "3": ACCENT.Gemini, "4": ACCENT.Gemini, "5": ACCENT.ChatGPT, "6": ACCENT.Claude, "7": ACCENT.ChatGPT, "8": ACCENT.Claude, "9": ACCENT.Claude};
Object.entries(SH.cards).forEach(([k, c]) => { c.accent = CARD_ACCENT[k]; });
// which shot first shows each card (it flips in there on its naming word)
const FIRST_SHOT = {};
for (const s of SHOTS) if (s.card != null && s.card !== "banner" && FIRST_SHOT[s.card] == null) FIRST_SHOT[s.card] = s.id;

function cardNow(shot, f) {
  if (shot.card == null || shot.card === "banner") return null;
  const c = SH.cards[String(shot.card)];
  const side = shot.kind === "dual" ? "L" : shot.side === "L" ? "R" : "L";
  const mode = shot.id === "S53" ? "small" : FIRST_SHOT[shot.card] === shot.id ? "first" : "cont";
  let op = 1;
  if (mode === "first" || mode === "small") op = f >= c.first ? clamp01((f - c.first) / 8) : 0;
  if (shot.whip_out) op *= 1 - clamp01((f - (shot.f1 - shot.whip_out.n - 3)) / 4);
  const settle = mode === "cont" ? 0.965 + 0.035 * eOut(clamp01((f - shot.f0) / 10)) : 1;
  return {c, side, mode, op, settle};
}

// ---------------------------------------------------------------- shot renderers
const halfZ = (shot, f) => { const k = clamp01((f - shot.f0) / Math.max(1, shot.f1 - shot.f0)); return lerp(shot.z[0], shot.z[1], eIO(k)); };

function cameraFX(shot, f) {   // whip pan offset + blur, snap push scale
  let wx = 0, mb = 0, push = 1;
  if (shot.whip_in) { const q = clamp01((f - shot.f0 + 1) / shot.whip_in.n); const d = shot.whip_in.dir === "R" ? 1 : -1; wx = d * 1900 * (1 - eOut(q)); mb = q < 1 ? 70 * (1 - q) : 0; }
  if (shot.whip_out) { const q = clamp01((f - (shot.f1 - shot.whip_out.n)) / shot.whip_out.n); const d = shot.whip_out.dir === "R" ? 1 : -1; if (q > 0) { wx = -d * 1900 * eIn(q); mb = Math.max(mb, 70 * q); } }
  if (shot.push) push = 1 + shot.push.amt * eOut(clamp01((f - shot.push.f) / 10));
  const hit = SH.fx.hit; if (shot.id === "S22") push *= 1 + 0.1 * eOut(clamp01((f - hit.f) / hit.push));
  return {wx, mb, push};
}

const Single = ({shot, f}) => {
  const who = shot.who, z = halfZ(shot, f);
  const {wx, mb, push} = cameraFX(shot, f);
  const k = clamp01((f - shot.f0) / Math.max(1, shot.f1 - shot.f0));
  const isDual = shot.kind === "dual";
  const H = (isDual ? DUAL : 1) * z * U;
  const X = isDual ? 760 : SIDE_X[shot.side] + (shot.side === "L" ? 1 : shot.side === "R" ? -1 : 0) * 0 + (k - 0.5) * (shot.side === "L" ? 22 : shot.side === "R" ? -22 : 0);
  const art = artFor(shot, who, shot.art, f);
  const isBust = art.startsWith("bust");
  const topY = underBanner(shot) ? BANNER_Y : HEAD_Y;
  const p = isBust ? placeBust(who, art, H, X, topY) : placeFull(who, art, H, X, topY);
  const b = body(shot, who, art, f);
  const tint = ACCENT[who];
  const pxCam = ORDER.indexOf(who) * 620 + (X - 960) * -0.5 + k * 60 - wx * 0.55;
  const bigTag = SH.tags.find((tg) => tg.kind === "big" && tg.who === who && f >= tg.f_in && f < tg.f_out);
  const gem = who === "Gemini" && !isBust && clonesVisible(f);
  const spot = (shot.id === "S52" || shot.id === "S53" || shot.id === "S55") ? {x: X, o: 1} : null;
  const pivot = {transformOrigin: `${X}px 300px`, transform: `scale(${push})`};
  return (
    <AbsoluteFill style={{filter: mb > 0.5 ? `url(#mb${shot.id})` : undefined}}>
      {mb > 0.5 && <svg width="0" height="0" style={{position: "absolute"}}><filter id={`mb${shot.id}`} x="-20%" width="140%"><feGaussianBlur stdDeviation={`${mb} 0`} /></filter></svg>}
      {/* whip pans move the figure layer; the stage only slides through its own parallax (px), so no frame is ever empty */}
      <Backdrop f={f} px={pxCam} zoom={isBust ? 1.6 : z * (isDual ? DUAL : 1) + 0.1} tint={tint} halo={{x: X + wx * 0.35, y: 420, r: 640}} spot={spot} />
      <AbsoluteFill style={{transform: `translateX(${wx}px)`}}>
        <AbsoluteFill style={pivot}>
          {gem && <Clones f={f} H={H} gx={X} gy={HEAD_Y} shot={shot} />}
          <Art who={who} name={art} p={p} b={b} />
        </AbsoluteFill>
        <Foreground f={f} px={pxCam} tint={tint} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const Wide = ({shot, f}) => {
  const names = shot.who, n = names.length;
  const wmax = Math.max(...ORDER.filter((w) => names.includes(w)).map(widthRatio));
  const zmax = Math.max(...shot.z);
  const WY = underBanner(shot) ? BANNER_Y : WIDE_Y;
  const Hlim = Math.min(1840 / ((n - 1) * 0.98 + 1) / wmax, HH - 20 - WY);
  const k = clamp01((f - shot.f0) / Math.max(1, shot.f1 - shot.f0));
  const H = Hlim * lerp(shot.z[0], shot.z[1], eIO(k)) / zmax;
  const gap = 0.98 * wmax * H;
  const sp = speakersAt(f);
  const tint = sp.length ? ACCENT[sp[sp.length - 1]] : "#8f9bff";
  const order = names.slice().sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b));
  const xs = Object.fromEntries(order.map((w, i) => [w, 960 + (i - (n - 1) / 2) * gap]));
  const items = order.map((w, i) => {
    const base = shot.art[w];
    const art = artFor(shot, w, base, f);
    const p = placeFull(w, art, H, xs[w], WY, "bbox");
    const b = body(shot, w, art, f, i);
    if (shot.id === "S03" && (w === "Claude" || w === "ChatGPT")) {   // pop up from below, staggered 6 frames
      const st = shot.f0 + (w === "ChatGPT" ? 6 : 0), q = clamp01((f - st) / 14);
      b.dy += (1 - eBack(q)) * 900;
    }
    if (shot.id === "S41" && w === "Gemini") { const q = clamp01((f - shot.f0) / 8); b.dx += (1 - eOut(q)) * 900; }
    const speaking = sp.includes(w);
    const dim = sp.length && !speaking && !shot.card ? 1 : 0;
    return {w, art, p, b, dim, i};
  });
  const gem = items.find((x) => x.w === "Gemini");
  return (
    <AbsoluteFill>
      <Backdrop f={f} px={0} zoom={0.8} tint={tint} halo={{x: 960, y: 560, r: 900, o: 0.6}} />
      {gem && clonesVisible(f) && <Clones f={f} H={H} gx={xs.Gemini + gem.b.dx} gy={WY} shot={shot} />}
      {items.map(({w, art, p, b, dim}) => <Art key={w} who={w} name={art} p={p} b={b} bright={dim ? 0.62 : 1} sat={dim ? 0.75 : 1} rim={dim ? 0.35 : 1} soft={dim ? 1.2 : 0} />)}
      {SH.tags.filter((tg) => (tg.kind === "small" || tg.kind === "over") && f >= tg.f_in && f < tg.f_out && names.includes(tg.who)).map((tg) => {
        const it = items.find((x) => x.w === tg.who); const sc = tg.kind === "small" ? 0.5 : 0.7;
        const headTop = WY + it.b.dy;
        return <BigTag key={tg.who} who={tg.who} f={f} f_in={tg.f_in} scale={sc} left={xs[tg.who] + it.b.dx - 260 * sc} top={headTop - 14 - 230 * sc} origin="0 0" />;
      })}
      <Foreground f={f} px={0} tint={tint} />
    </AbsoluteFill>
  );
};

const Split = ({shot, f}) => {
  const lt = f - shot.f0, q = eOut(clamp01(lt / 11));
  const [a, bb] = shot.who;
  const panel = (who, left) => {
    const art = artFor(shot, who, shot.art[who], f);
    const z = lerp(shot.z[0], shot.z[1], clamp01(lt / Math.max(1, shot.f1 - shot.f0)));
    const x = left ? 470 : 1450;
    const p = placeBust(who, art, z * U, x, HEAD_Y);
    const b = body(shot, who, art, f, left ? 0 : 1);
    b.dx += (left ? -1 : 1) * (1 - q) * 300;   // only the figure slides in; panels are there from the first frame
    const clip = left ? "polygon(0 0, 55% 0, 45% 100%, 0 100%)" : "polygon(55% 0, 100% 0, 100% 100%, 45% 100%)";
    return (
      <AbsoluteFill key={who} style={{clipPath: clip}}>
        <Backdrop f={f} px={ORDER.indexOf(who) * 620 + lt * 0.4} zoom={1.5} tint={ACCENT[who]} halo={{x, y: 430, r: 620}} />
        <Art who={who} name={art} p={p} b={b} />
      </AbsoluteFill>
    );
  };
  const glint = SH.fx.glint.includes(shot.f0) ? clamp01(lt / 14) : -1;
  return (
    <AbsoluteFill style={{background: "#0a0d28"}}>
      {panel(a, true)}{panel(bb, false)}
      <div style={{position: "absolute", left: 960 - 5, top: -200, width: 10, height: 1480, background: "#fff", transform: `rotate(10.08deg) scaleY(${0.35 + 0.65 * q})`, boxShadow: "0 0 26px 6px rgba(255,255,255,0.75)", opacity: 0.95}} />
      {glint >= 0 && glint < 1 && <div style={{position: "absolute", left: 960 - 60 + Math.tan(10.08 * Math.PI / 180) * -(lerp(-200, 1280, glint) - 540), top: lerp(-200, 1280, glint) - 120, width: 120, height: 240,
        background: "radial-gradient(ellipse, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0.3) 40%, transparent 70%)", transform: "rotate(10deg)"}} />}
    </AbsoluteFill>
  );
};

const Empty = ({shot, f}) => {
  const e = SH.fx.s79, lt = f - e.f0;
  const tIn = clamp01((lt - e.text_in) / 10), fade = clamp01((lt - e.text_in - e.text_hold) / e.fade);
  return (
    <AbsoluteFill style={{background: "#000"}}>
      <AbsoluteFill style={{opacity: 1 - fade}}>
        <Backdrop f={f} px={0} zoom={0.8} tint="#8f9bff" />
        <div style={{position: "absolute", left: 0, right: 0, top: 560, textAlign: "center", fontFamily, fontSize: 36, color: BONE, opacity: 0.7 * tIn, letterSpacing: "0.04em"}}>{e.text}</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- overlays
const Sparks = ({f}) => (
  <>
    {SH.fx.sparks.map((s, j) => {
      const a = f - s.f; if (a < 0 || a > 50) return null;
      return Array.from({length: s.n}, (_, i) => {
        const ang = rnd(i + j * 97) * Math.PI * 2, sp = 6 + rnd(i * 3 + j) * 16, d = sp * a * (1 - a / 120);
        const r = 3 + rnd(i * 7 + j) * 5, o = (1 - a / 50) * (0.6 + 0.4 * Math.sin(a * 0.7 + i));
        return <div key={`${j}-${i}`} style={{position: "absolute", left: s.x + Math.cos(ang) * d - r, top: s.y + Math.sin(ang) * d - r + a * a * 0.02, width: r * 2, height: r * 2, borderRadius: "50%",
          background: `radial-gradient(circle, #ffffff 0%, ${s.col} 45%, transparent 72%)`, opacity: o}} />;
      });
    })}
  </>
);
const SpeedLines = ({f}) => {
  const h = SH.fx.hit, a = f - h.f;
  if (a < 0 || a >= h.lines) return null;
  const op = 1 - a / h.lines, seed = a;
  const stops = []; let ang = 0, i = 0;
  while (ang < 360) { const gap = 2.2 + rnd(seed * 7 + i) * 6, w = 0.25 + rnd(seed * 13 + i) * 1.1; stops.push(`transparent ${ang}deg ${ang + gap}deg`, `rgba(255,255,255,0.95) ${ang + gap}deg ${ang + gap + w}deg`); ang += gap + w; i++; }
  const m = "radial-gradient(ellipse 50% 50% at 50% 42%, transparent 58%, #000 100%)";
  return <AbsoluteFill style={{opacity: op * 0.9, background: `conic-gradient(from ${seed * 37}deg at 50% 42%, ${stops.join(",")})`, maskImage: m, WebkitMaskImage: m}} />;
};

const SUBS = SH.subs;
const Subtitle = ({f}) => {
  let s = null; for (const x of SUBS) if (f >= x.f0 && f < x.f1) s = x;
  const on = !!s; if (!s) s = {who: "Claude", text: "", f0: f};
  const k = clamp01((f - s.f0) / 6);
  const ss = SH.fx.sub_shake; const sh = f >= ss.f && f < ss.f + ss.n ? (f - ss.f ? -6 : 6) : 0;
  const glow = f < SHOTS[1].f0 ? 8 + 6 * Math.sin(f * 0.21) : 6;   // S01: the only light in the black, breathing
  return (
    <div style={{position: "absolute", left: 0, right: 0, bottom: 50, display: "flex", justifyContent: "center", transform: `translateX(${sh}px)`}}>
      <div style={{padding: "8px 34px 13px", borderRadius: 16, background: "rgba(6,8,26,0.82)", border: `1.5px solid ${ACCENT[s.who]}77`, color: "#fff", fontFamily, fontSize: 54, lineHeight: 1.1,
        whiteSpace: "nowrap", textShadow: `0 2px ${glow}px rgba(0,0,0,.5)`, opacity: on ? 0.4 + 0.6 * k : 0, transform: `translateY(${(1 - k) * 6}px)`}}>
        <span style={{color: NAME_COL[s.who]}}>{s.who}: </span>{s.text}
      </div>
    </div>
  );
};
const Banner = ({f}) => {
  const B = SH.banner; if (f < B.f_in - 2 || f >= B.f_out) return null;
  const o = 1 - clamp01((f - (B.f_out - B.fade)) / B.fade);   // gone by the cut to S76
  const word = (x, i) => { const q = clamp01((f - x.f) / 5); return <span key={i} style={{display: "inline-block", marginRight: 16, opacity: q, transform: `translateY(${(1 - eOut(q)) * 14}px)`}}>{x.w}</span>; };
  const done2 = B.lines[1].every((x) => f >= x.f), p = done2 ? bump(clamp01((f - B.lines[1][B.lines[1].length - 1].f) / 24)) : 0;
  return (
    <div style={{position: "absolute", top: 0, left: 0, right: 0, padding: "12px 0 10px", textAlign: "center", fontFamily, color: BONE, opacity: o,
      background: "linear-gradient(180deg, rgba(8,10,32,0.9) 0%, rgba(8,10,32,0.78) 80%, rgba(8,10,32,0) 100%)"}}>
      <div style={{fontSize: 56, lineHeight: 1.08, whiteSpace: "nowrap"}}>{B.lines[0].map(word)}</div>
      <div style={{fontSize: 56, lineHeight: 1.08, whiteSpace: "nowrap", fontStyle: "italic", color: ACCENT.ChatGPT, textShadow: `0 0 ${30 * p}px ${ACCENT.ChatGPT}`}}>{B.lines[1].map(word)}</div>
    </div>
  );
};

// ---------------------------------------------------------------- closing card: all sources and credits in one place
const CREDIT_SOURCES = [
  ["Scorpion venom binders", "Anthropic, 20 Oct 2026; lab tests by Adaptyv Bio & Twist Bioscience"],
  ["Stem-cell proteins", "OpenAI, “Accelerating life sciences research”, 22 Aug 2025"],
  ["Super Bowl LX ad", "Adweek; The Register, Feb 2026"],
  ["Project Vend", "Anthropic, Jun 2025"],
  ["Protocol QA benchmark", "Anthropic, “Claude for Life Sciences”, Oct 2025"],
  ["Novo Nordisk", "customer story, claude.com"],
  ["Nobel Prize in Chemistry 2024", "Royal Swedish Academy of Sciences"],
  ["Isomorphic Labs", "funding announcement, Mar 2025"],
  ["Roadshow parody (satire)", "Business Insider, Nov 2026"],
  ["Rentosertib", "Xu et al., Nature Medicine 2025 (Insilico Medicine)"],
];
const CREDIT_CHARS = [
  ["DeepSeek", "after “Mingyue” by Shangshan Wuxing (CC BY-NC-SA 4.0); whale maid version by ZipZipPipe (Bilibili)"],
  ["Claude", "after a popular community fan design"],
  ["ChatGPT", "after the White Dragon design by ZipZipPipe (Bilibili)"],
  ["Gemini", "Gemini character design by ZipZipPipe. Reference images: genderswapai.com."],
];
const CREDIT_ART = "Character art drawn with ChatGPT / Codex from these designs.";
const CREDIT_NOTE = "Fictional AI characters. Synthetic voices (Chatterbox TTS). Not affiliated with or endorsed by DeepSeek, Anthropic, OpenAI or Google.";
export const CREDITS_TEXT = {sources: CREDIT_SOURCES, chars: CREDIT_CHARS, art: CREDIT_ART, note: CREDIT_NOTE};
const CreditsCard = ({f}) => {
  const o = clamp01(f / 12) * (1 - clamp01((f - (CREDITS_F - 14)) / 14));
  const row = (k, v, i, col) => <div key={i} data-credit="1" style={{fontSize: 30, lineHeight: "37px", marginBottom: 11}}>
    <span style={{color: col}}>{k}</span><span style={{color: "rgba(246,243,255,0.55)"}}> · </span><span>{v}</span></div>;
  const head = (t) => <div style={{fontSize: 34, fontStyle: "italic", color: "#c8b8ff", letterSpacing: "0.04em", marginBottom: 14, borderBottom: "1.5px solid rgba(200,184,255,0.45)", paddingBottom: 6}}>{t}</div>;
  return (
    <AbsoluteFill style={{opacity: o, fontFamily, color: "#f6f3ff", background: "linear-gradient(180deg, #080a22 0%, #121848 55%, #1d2468 100%)"}}>
      <div style={{position: "absolute", left: 96, right: 96, top: 64, fontSize: 60, lineHeight: 1}}>Sources &amp; Credits</div>
      <div style={{position: "absolute", left: 96, top: 156, width: 840}}>
        {head("Skit sources")}
        {CREDIT_SOURCES.map(([k, v], i) => row(k, v, i, "#ffb27a"))}
      </div>
      <div style={{position: "absolute", left: 1000, top: 156, width: 824}}>
        {head("Characters")}
        {CREDIT_CHARS.map(([k, v], i) => row(k, v, i, NAME_COL[k]))}
        <div data-credit="1" style={{fontSize: 30, lineHeight: "37px", marginTop: 8, color: "rgba(246,243,255,0.85)", fontStyle: "italic"}}>{CREDIT_ART}</div>
      </div>
      <div data-credit="1" style={{position: "absolute", left: 96, right: 96, top: 930, fontSize: 30, lineHeight: "37px", color: "rgba(246,243,255,0.85)", textAlign: "center"}}>{CREDIT_NOTE}</div>
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- main
export const MascotTag = () => {
  const f = useCurrentFrame();
  if (f >= NF) return <AbsoluteFill style={{background: "#000"}}><CreditsCard f={f - NF} /></AbsoluteFill>;
  const shot = shotAt(f);
  let shx = 0, shy = 0;
  for (const s of SH.shake) if (f >= s.f && f < s.f + s.n) { shx += (f - s.f) % 2 ? -s.amp : s.amp; shy += (f - s.f) % 2 ? s.amp * 0.6 : -s.amp * 0.6; }
  const hit = SH.fx.hit; if (f >= hit.f && f < hit.f + hit.shake) { shx += (f - hit.f) % 2 ? -12 : 12; shy += (f - hit.f) % 2 ? 7 : -7; }
  const card = cardNow(shot, f);
  const bigTag = SH.tags.find((tg) => tg.kind === "big" && f >= tg.f_in && f < tg.f_out);
  const flash = f >= hit.f && f < hit.f + hit.flash ? (f === hit.f ? 0.9 : 0.45) : 0;
  const lu = SH.fx.light_up, sw = f >= lu.f && f < lu.f + lu.sweep ? (f - lu.f + 0.5) / lu.sweep : -1;
  return (
    <AbsoluteFill style={{background: "#000", overflow: "hidden"}}>
      <Audio src={staticFile("m/egg_mix.wav")} />
      <AbsoluteFill style={{transform: `translate(${shx}px, ${shy}px)`}}>
        {shot.kind === "black" && <AbsoluteFill style={{background: "#000"}} />}
        {(shot.kind === "half" || shot.kind === "bust" || shot.kind === "dual") && <Single shot={shot} f={f} />}
        {shot.kind === "wide" && <Wide shot={shot} f={f} />}
        {shot.kind === "split" && <Split shot={shot} f={f} />}
        {shot.kind === "empty" && <Empty shot={shot} f={f} />}
        <SpeedLines f={f} />
        {shot.kind !== "black" && shot.kind !== "empty" && <AbsoluteFill style={{background: "radial-gradient(ellipse at 50% 48%, rgba(0,0,0,0) 58%, rgba(0,0,12,0.5) 100%)"}} />}
        {shot.kind !== "black" && <AbsoluteFill style={{background: "linear-gradient(180deg, transparent 74%, rgba(5,7,24,0.7) 100%)", opacity: shot.kind === "empty" ? 0 : 1}} />}
        {card && <CardView c={card.c} f={f} side={card.side} op={card.op} mode={card.mode} settle={card.settle} />}
        {bigTag && <BigTag who={bigTag.who} f={f} f_in={bigTag.f_in} left={64} top={860 - 218} />}
        <Banner f={f} />
        <Sparks f={f} />
      </AbsoluteFill>
      <Subtitle f={f} />
      {sw >= 0 && <AbsoluteFill style={{background: `linear-gradient(110deg, rgba(255,248,235,0) ${-40 + sw * 180 - 35}%, rgba(255,246,228,0.95) ${-40 + sw * 180}%, rgba(255,248,235,0) ${-40 + sw * 180 + 35}%)`}} />}
      <AbsoluteFill style={{background: "#fff", opacity: flash}} />
    </AbsoluteFill>
  );
};
