// HKBU SCIE1007 coursework science video. Second-pass stills after looking at Marathon's real imagery, see research/marathon_refs_v2_20261031.md.
// Methods only: extreme type weight, supergraphics that bleed off frame, small data clusters, registration marks. No Marathon logo, font, UI layout or asset.
// Every graphic here is drawn from real data (346 pLDDT scores, the sequence) so nothing is decoration without a source.
import React from "react";
import {continueRender, cancelRender, delayRender} from "remotion";
import {K, N_RES, PLDDT, SEQUENCE, MONO, W, H} from "./kit";

// ---------- display face: Anybody (SIL OFL, Google Fonts), one variable file from ultra-condensed to ultra-wide ----------
export const DISP = "AnybodyVar";
const FONT_URL = "https://fonts.gstatic.com/s/anybody/v13/VuJxdNvK2Ib2ppdWSKHdOQ.woff2";
const hold = delayRender("Anybody variable font");
new FontFace(DISP, `url(${FONT_URL})`, {weight: "100 900", stretch: "50% 150%"}).load().then(f => { document.fonts.add(f); continueRender(hold); }, cancelRender);

export const Disp = ({x, y, size = 200, wide = 150, weight = 900, color = K.bg, line = 0.86, track = "-0.02em", style, children}) => <div style={{
  position: "absolute", left: x, top: y, fontFamily: DISP, fontWeight: weight, fontStretch: `${wide}%`, fontVariationSettings: `"wdth" ${wide}, "wght" ${weight}`,
  fontSize: size, lineHeight: line, letterSpacing: track, color, whiteSpace: "nowrap", ...style}}>{children}</div>;

// Small mono text outside the six settings: data clusters that sit as texture and are not meant to be read aloud.
export const Micro = ({x, y, w, size = 13, color = K.bone, line = 1.45, align, style, children}) => <div style={{position: "absolute", left: x, top: y, width: w,
  fontFamily: MONO, fontWeight: 400, fontSize: size, lineHeight: line, letterSpacing: "0.02em", color, textAlign: align, whiteSpace: "pre", ...style}}>{children}</div>;

// Solid plate for a colour field, where the blue evidence plate would vanish. Black fill, dotted ring kept, so it still reads as the AI plate.
export const FieldPlate = ({x, y, children, ink = K.bone, fill = K.bg, ring = K.bone}) => <div style={{position: "absolute", left: x, top: y, padding: "10px 18px",
  background: fill, outline: `2px dotted ${ring}`, outlineOffset: 5, fontFamily: MONO, fontWeight: 500, fontSize: 26, lineHeight: 1.3, color: ink, whiteSpace: "nowrap"}}>{children}</div>;

export const Cross = ({x, y, s = 14, color = K.bone, weight = 2}) => <svg style={{position: "absolute", left: x - s, top: y - s, overflow: "visible"}} width={2 * s} height={2 * s}>
  <path d={`M${s} 0V${2 * s}M0 ${s}H${2 * s}`} stroke={color} strokeWidth={weight} fill="none"/>
</svg>;

// A field of crosses on an even grid. skip(x, y) leaves holes.
export const CrossField = ({x0, y0, x1, y1, step = 120, s = 7, color = K.bone, weight = 1.5, skip}) => {
  const out = [];
  for (let y = y0; y <= y1; y += step) for (let x = x0; x <= x1; x += step) if (!skip || !skip(x, y)) out.push(`M${x} ${y - s}V${y + s}M${x - s} ${y}H${x + s}`);
  return <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}><path d={out.join("")} stroke={color} strokeWidth={weight} fill="none"/></svg>;
};

// Corner registration: a solid square and a tick.
export const Reg = ({x, y, color = K.bone, flip = false}) => <svg style={{position: "absolute", left: x, top: y, overflow: "visible"}} width={40} height={40}>
  <rect x={flip ? 22 : 0} y={0} width={18} height={18} fill={color}/><path d={flip ? "M40 26V40H26" : "M0 26V40H14"} stroke={color} strokeWidth={2} fill="none"/>
</svg>;

// 346 bars round a circle, length = the residue's real pLDDT. r0 inner radius, len length at score 100, start = degrees for residue 1, clockwise from east.
export const angleOf = (res, start) => (start + 360 * (res - 1) / N_RES) * Math.PI / 180;
export const RingCode = ({cx, cy, r0 = 470, len = 300, start = 54, color = K.bg, tail = K.bone, cut = 302, widthPx = 5.2}) => {
  const seg = PLDDT.map((s, i) => {
    const t = angleOf(i + 1, start), c = Math.cos(t), n = Math.sin(t), l = len * s / 100;
    return {d: `M${(cx + r0 * c).toFixed(2)} ${(cy + r0 * n).toFixed(2)}L${(cx + (r0 + l) * c).toFixed(2)} ${(cy + (r0 + l) * n).toFixed(2)}`, tail: i + 1 > cut};
  });
  const path = f => seg.filter(f).map(s => s.d).join("");
  return <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
    <path d={path(s => !s.tail)} stroke={color} strokeWidth={widthPx} fill="none"/>
    <path d={path(s => s.tail)} stroke={tail} strokeWidth={widthPx} fill="none"/>
  </svg>;
};

// All 346 letters of the real sequence on a circle, one to a bar. Drawn at 3x and scaled so no browser minimum font size touches them.
export const RingLetters = ({cx, cy, r = 452, start = 54, size = 8, color = K.bone}) => <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
  <g transform="scale(0.33333)" fill={color} fontFamily={MONO} fontSize={size * 3} textAnchor="middle">
    {SEQUENCE.split("").map((ch, i) => {
      const t = angleOf(i + 1, start), x = (cx + r * Math.cos(t)) * 3, y = (cy + r * Math.sin(t)) * 3;
      return <text key={i} x={x} y={y} dy="0.35em" transform={`rotate(${(t * 180 / Math.PI + 90).toFixed(2)} ${x} ${y})`}>{ch}</text>;
    })}
  </g>
</svg>;

// Residue numbers at their true place on the ring.
export const RingTicks = ({cx, cy, r = 508, start = 54, list = [1, 50, 100, 150, 200, 250, 300, 346], color = K.bone, fill = K.bg, size = 12}) => <>
  {list.map(res => {
    const t = angleOf(res, start), x = cx + r * Math.cos(t), y = cy + r * Math.sin(t);
    return <div key={res} style={{position: "absolute", left: x, top: y, transform: "translate(-50%, -50%)", background: fill, padding: "1px 5px",
      fontFamily: MONO, fontSize: size, lineHeight: 1.3, letterSpacing: "0.02em", color}}>{String(res).padStart(3, "0")}</div>;
  })}
</>;
