// Type system. HAND = Knewave (brush hand-lettering, headlines + annotations). MONO = Martian Mono (data, labels, UI).
import React from "react";
import {C, HAND, MONO, hash, useBoil, clamp01} from "./core";
import {Highlight} from "./marks";

/**
 * Hand-lettered text. Each glyph gets its own tiny rotation / baseline jitter that re-rolls with the boil clock,
 * and the whole run passes through the displacement filter so edges crawl like re-inked lettering.
 * reveal 0..1 reveals glyph by glyph (pop-on).
 */
export const HandText = ({x, y, size = 80, color = C.ink, anchor = "start", children, seed = 1, wob = 1, rotate = 0, letterSpacing = 0,
  filter = true, reveal = 1, opacity = 1, stroke, strokeWidth = 0, skew = 0, split = 0}) => {
  const b = useBoil();
  const str = String(children);
  const chars = [...str];
  const shown = reveal >= 1 ? chars.length : Math.floor(chars.length * clamp01(reveal));
  const vis = chars.slice(0, shown);
  if (!vis.length) return null;
  const rot = vis.map((_, i) => ((hash(i, seed, b) - 0.5) * 6 * wob).toFixed(2)).join(" ");
  let prev = 0;
  const dy = vis.map((_, i) => { const j = (hash(i, seed + 7, b) - 0.5) * size * 0.045 * wob; const d = j - prev; prev = j; return d.toFixed(2); }).join(" ");
  const run = (fill, dx = 0, ddy = 0, extra = {}) => <text x={x + dx} y={y + ddy} fontFamily={HAND} fontSize={size} fill={fill} textAnchor={anchor} rotate={rot} dy={dy} letterSpacing={letterSpacing}
    transform={rotate || skew ? `rotate(${rotate} ${x} ${y}) skewX(${skew})` : undefined} filter={filter ? "url(#v3-boil-text)" : undefined}
    stroke={stroke} strokeWidth={strokeWidth} paintOrder="stroke" strokeLinejoin="round" {...extra}>{vis.join("")}</text>;
  if (!split) return React.cloneElement(run(color), {opacity});
  // misregistered print: cyan + vermilion plates slipped under the ink plate (digital x hand collision)
  const k = split * (0.75 + 0.5 * hash(b, seed, 99));
  return <g opacity={opacity}>
    {run(C.cyan, -k, -k * 0.3, {style: {mixBlendMode: "screen"}, opacity: 0.85})}
    {run(C.verm, k, k * 0.4, {style: {mixBlendMode: "screen"}, opacity: 0.85})}
    {run(color)}
  </g>;
};

/** Clean mono text (the computer's voice). reveal types it on. */
export const Mono = ({x, y, size = 22, color = C.ink, weight = 400, anchor = "start", children, letterSpacing = 0, reveal = 1, opacity = 1, cursor = false}) => {
  const str = String(children);
  const n = reveal >= 1 ? str.length : Math.floor(str.length * clamp01(reveal));
  const showCursor = cursor && reveal < 1;
  return <text x={x} y={y} fontFamily={MONO} fontSize={size} fontWeight={weight} fill={color} textAnchor={anchor} letterSpacing={letterSpacing} opacity={opacity}
    style={{fontVariantNumeric: "tabular-nums"}}>{str.slice(0, n)}{showCursor ? "█" : ""}</text>;
};

/** Mono advance width estimate (Martian Mono advance ~0.7 em). Used for boxes/underlines. */
export const monoW = (str, size, ls = 0) => String(str).length * (size * 0.7 + ls);

/** Data tag: [LABEL] value — label in a solid tab, value in big mono. */
export const DataTag = ({x, y, label, value, unit, color = C.cyan, size = 46, reveal = 1, valueColor = C.ink, hl = 0, seed = 90}) => {
  const lw = monoW(label, 16, 1) + 22;
  const vw = monoW(value, size), uw = unit ? monoW(unit, size * 0.5) + 14 : 0;
  return <g>
    {hl > 0 ? <g filter="url(#v3-ink)"><Highlight x={x - 18} y={y - size * 0.82} w={(vw + uw + 52) * Math.min(1, hl)} h={size * 1.12} seed={seed} progress={1}/></g> : null}
    <rect x={x} y={y - size - 34} width={lw} height={28} fill={color}/>
    <text x={x + 11} y={y - size - 14} fontFamily={MONO} fontSize={16} fontWeight={700} fill={C.bg} letterSpacing={1}>{label}</text>
    <Mono x={x} y={y} size={size} weight={800} color={hl > 0 ? C.bg : valueColor} reveal={reveal}>{value}</Mono>
    {unit && reveal >= 1 ? <Mono x={x + vw + 12} y={y} size={size * 0.5} weight={700} color={hl > 0 ? C.bg : color}>{unit}</Mono> : null}
  </g>;
};
