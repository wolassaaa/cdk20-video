// SCAN (S1 v3 frontier test): shared palette, type and the orthographic stack camera.
import React from "react";
import {loadFont as loadGrot} from "@remotion/google-fonts/InterTight";
import {loadFont as loadMonoF} from "@remotion/google-fonts/MartianMono";

export const GROT = loadGrot("normal", {weights: ["200", "300", "400"], subsets: ["latin"]}).fontFamily;
export const MONO = loadMonoF("normal", {weights: ["300", "400", "500"], subsets: ["latin"]}).fontFamily;

export const W = 1920, H = 1080, FPS = 30;
export const K = {
  bg: "#060606",
  bone: "#EDEBE4",
  red: "#E8190F",
  redDeep: "#9A0E08",
  b: a => `rgba(237,235,228,${a})`,
  r: a => `rgba(232,25,15,${a})`,
};

// ---------------------------------------------------------------- easing / timing
export const clamp01 = x => Math.min(1, Math.max(0, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const ramp = (f, a, b) => clamp01((f - a) / (b - a));
export const smooth = x => { x = clamp01(x); return x * x * (3 - 2 * x); };
export const smoother = x => { x = clamp01(x); return x * x * x * (x * (6 * x - 15) + 10); };

// ---------------------------------------------------------------- number formatting (real values only)
export const fmt = (v, dec = 0) => v.toLocaleString("en-US", {minimumFractionDigits: dec, maximumFractionDigits: dec});
// ---------------------------------------------------------------- orthographic camera
// body frame: x (patient right = -x), y (anterior = -y), z up. Viewed from the front (anterior), so the
// patient's right lobe sits on the viewer's left, the same handedness as a radiological axial image.
export const makeCam = ({yaw, el, s, cx, cy, m}) => {
  const c = Math.cos(yaw), sn = Math.sin(yaw), ce = Math.cos(el), se = Math.sin(el);
  // sx = cx + s*(c*dx - sn*dy); sy = cy - s*(ce*dz + se*(sn*dx + c*dy))
  const A = s * c, B = -s * sn, D = -s * se * sn, E = -s * se * c;
  const pt = (x, y, z) => [cx + A * (x - m[0]) + B * (y - m[1]), cy + D * (x - m[0]) + E * (y - m[1]) - s * ce * (z - m[2])];
  const path = (P, z, closed = false, dx = 0, dy = 0) => {
    const zz = cy - s * ce * (z - m[2]) + dy;
    let d = "";
    for (let i = 0; i < P.length; i += 2) {
      const x = P[i] - m[0], y = P[i + 1] - m[1];
      d += (i ? "L" : "M") + (cx + dx + A * x + B * y).toFixed(1) + " " + (zz + D * x + E * y).toFixed(1);
    }
    return closed ? d + "Z" : d;
  };
  return {pt, path, s, ce, se};
};

// ---------------------------------------------------------------- type
export const T = ({x, y, size = 14, font = MONO, w = 400, color = K.bone, anchor = "start", ls = 0, op = 1, children, style}) =>
  <text x={x} y={y} fontFamily={font} fontSize={size} fontWeight={w} fill={color} textAnchor={anchor} letterSpacing={ls} opacity={op}
    style={{fontVariantNumeric: "tabular-nums", ...style}}>{children}</text>;
