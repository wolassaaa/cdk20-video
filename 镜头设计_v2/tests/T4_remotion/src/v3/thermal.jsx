// Thermal false colour: draw heat as white-on-black (brightness = heat), then map brightness through our own palette.
// Cold → hot: black, deep teal, teal, cyan, acid fringe, vermilion, orange, yellow, white. Banded like a 12-colour print.
import React from "react";
import {C} from "./core";

export const HEAT_STOPS = [
  [0.00, "#050505"], [0.12, "#03171A"], [0.26, "#08454A"], [0.38, "#11949A"], [0.48, C.cyan], [0.52, C.acid],
  [0.56, C.verm], [0.70, "#FF6A1A"], [0.82, "#FFB21F"], [0.92, "#FFF04A"], [1.00, "#FFFFFF"],
];
const rgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16) / 255);

/** Palette colour at heat t (0..1), for legends and UI drawn outside the filter. */
export const heatColor = t => {
  let i = 0;
  while (i < HEAT_STOPS.length - 2 && t > HEAT_STOPS[i + 1][0]) i++;
  const [t0, a] = HEAT_STOPS[i], [t1, b] = HEAT_STOPS[i + 1], u = Math.min(1, Math.max(0, (t - t0) / (t1 - t0)));
  const A = rgb(a), B = rgb(b);
  return `rgb(${A.map((v, k) => Math.round(255 * (v + (B[k] - v) * u))).join(",")})`;
};
const tables = (steps) => {
  const out = [[], [], []];
  for (let s = 0; s < steps; s++) {
    const c = heatColor(s / (steps - 1)).slice(4, -1).split(",").map(v => (v / 255).toFixed(3));
    c.forEach((v, k) => out[k].push(v));
  }
  return out.map(t => t.join(" "));
};
const TABLES = tables(26);

/**
 * <filter> that turns brightness into false colour. Put it in an <svg><defs>; use it on an SVG group
 * (filter="url(#id)") or on HTML like video (style.filter = "url(#id)").
 * noise: film grain mixed into the heat before mapping (it re-rolls with seed).
 */
export const ThermalFilter = ({id, seed = 1, noise = 0.14, blur = 0}) => <filter id={id} x="0" y="0" width="100%" height="100%" colorInterpolationFilters="sRGB">
  {blur ? <feGaussianBlur stdDeviation={blur} result="b"/> : null}
  <feColorMatrix type="saturate" values="0" result="g"/>
  <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="1" seed={seed} result="n"/>
  <feColorMatrix in="n" type="saturate" values="0" result="ng"/>
  <feComposite in="g" in2="ng" operator="arithmetic" k1="0" k2="1" k3={noise} k4={-noise / 2} result="gn"/>
  <feComponentTransfer in="gn">
    <feFuncR type="discrete" tableValues={TABLES[0]}/>
    <feFuncG type="discrete" tableValues={TABLES[1]}/>
    <feFuncB type="discrete" tableValues={TABLES[2]}/>
  </feComponentTransfer>
</filter>;
