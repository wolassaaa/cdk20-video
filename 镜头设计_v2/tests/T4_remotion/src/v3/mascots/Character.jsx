// HKBU SCIE1007 coursework video: AI mascot insert. Three chibi SVG characters redrawn by us from the
// community designs "Claude娘 / GPT娘 / DeepSeek娘" (see 镜头设计_v3/深化/09_AI角色插段.md, 形象来源表).
// Layers (back to front): back extras, back hair, body, head, face parts, front hair, accessories.
// Pure function of state => string; Stage.jsx turns it into a texture. Same props drive a PNG-frame replacement (see Stage).
import React from "react";
import {renderToStaticMarkup} from "react-dom/server";

export const VB_W = 400, VB_H = 560;
const INK = "#3a2a33";
const SKIN = "#ffe7dc", SKIN_SH = "#f7cdbf";

const PAL = {
  Claude: {hair: "#f2711f", hairDk: "#d4560f", hairLt: "#ff9a52", eye: "#e8922e", eyeDk: "#8a3d0c", cloth: "#fbf1e6", clothSh: "#ead9c6", accent: "#ee6a1c", dark: "#2b2224", gold: "#d9a441"},
  GPT:    {hair: "#f6f4ff", hairDk: "#cfc8ee", hairLt: "#ffffff", eye: "#a99be0", eyeDk: "#5b4a9e", cloth: "#fdfcff", clothSh: "#e3def5", accent: "#8bd8cf", dark: "#6b6290", gold: "#c9c3e8"},
  DeepSeek: {hair: "#27409a", hairDk: "#1b2c73", hairLt: "#58a9ee", eye: "#4aa3f0", eyeDk: "#143a78", cloth: "#fdfdff", clothSh: "#dfe6f5", accent: "#4a8fe0", dark: "#1c2766", gold: "#d9b25f"},
};

const Flower = ({cx, cy, r, petals = 10, fill, mid, stroke}) => (
  <g transform={`translate(${cx} ${cy})`}>
    {Array.from({length: petals}).map((_, i) => (
      <ellipse key={i} cx={0} cy={-r * 0.62} rx={r * 0.2} ry={r * 0.42} fill={fill} stroke={stroke} strokeWidth="1.2" transform={`rotate(${(360 / petals) * i})`} />
    ))}
    <circle r={r * 0.3} fill={mid} stroke={stroke} strokeWidth="1.2" />
  </g>
);

// rounded knot-like rosette used by GPT (six overlapping loops; generic, not a logo copy)
const Rosette = ({cx, cy, r, stroke, fill}) => (
  <g transform={`translate(${cx} ${cy})`} fill={fill} stroke={stroke} strokeWidth="2">
    {[0, 60, 120].map((a) => <ellipse key={a} rx={r} ry={r * 0.42} transform={`rotate(${a})`} fill="none" />)}
    <circle r={r * 0.22} />
  </g>
);

const Star = ({cx, cy, r, fill}) => (
  <path d={`M${cx} ${cy - r} L${cx + r * 0.3} ${cy - r * 0.3} L${cx + r} ${cy} L${cx + r * 0.3} ${cy + r * 0.3} L${cx} ${cy + r} L${cx - r * 0.3} ${cy + r * 0.3} L${cx - r} ${cy} L${cx - r * 0.3} ${cy - r * 0.3} Z`} fill={fill} />
);

const Eye = ({id, cx, cy, p, open, closedArc}) => {
  if (closedArc) {
    return <path d={`M${cx - 22} ${cy + 8} Q${cx} ${cy - 16} ${cx + 22} ${cy + 8}`} fill="none" stroke={INK} strokeWidth="6" strokeLinecap="round" />;
  }
  const o = Math.max(0.12, open);
  return (
    <g transform={`translate(${cx} ${cy}) scale(1 ${o}) translate(${-cx} ${-cy})`}>
      <clipPath id={`${id}clip`}><ellipse cx={cx} cy={cy} rx="23" ry="30" /></clipPath>
      <ellipse cx={cx} cy={cy} rx="23" ry="30" fill="#fff" />
      <g clipPath={`url(#${id}clip)`}>
        <ellipse cx={cx} cy={cy + 3} rx="19" ry="28" fill={`url(#${id}iris)`} />
        <ellipse cx={cx} cy={cy + 4} rx="9" ry="14" fill={INK} />
        <ellipse cx={cx} cy={cy + 12} rx="14" ry="9" fill={p.eye} opacity="0.55" />
      </g>
      <ellipse cx={cx - 7} cy={cy - 10} rx="6.5" ry="8" fill="#fff" />
      <circle cx={cx + 8} cy={cy + 12} r="3.2" fill="#fff" opacity="0.9" />
      <path d={`M${cx - 25} ${cy - 2} Q${cx} ${cy - 38} ${cx + 25} ${cy - 2}`} fill="none" stroke={INK} strokeWidth="5.5" strokeLinecap="round" />
    </g>
  );
};

const Mouth = ({open}) => {
  if (open < 0.1) return <path d="M186 240 Q200 252 214 240" fill="none" stroke={INK} strokeWidth="4.5" strokeLinecap="round" />;
  const h = 4 + 20 * open, w = 11 + 8 * open;
  return (
    <g>
      <clipPath id="mclip"><path d={`M${200 - w} 238 Q200 ${238 + h * 1.9} ${200 + w} 238 Q200 ${236 - 1} ${200 - w} 238 Z`} /></clipPath>
      <path d={`M${200 - w} 238 Q200 ${238 + h * 1.9} ${200 + w} 238 Q200 235 ${200 - w} 238 Z`} fill="#8e2f3f" stroke={INK} strokeWidth="3.5" strokeLinejoin="round" />
      <ellipse cx="200" cy={238 + h * 1.15} rx={w * 0.62} ry={h * 0.42} fill="#ff8aa0" clipPath="url(#mclip)" />
    </g>
  );
};

// ---------------------------------------------------------------- per-character art
const HAIR_BACK = "M96 160 C82 48 318 48 304 160 C326 250 338 370 312 452 Q290 476 268 446 L268 300 L132 300 L132 446 Q110 476 88 452 C62 370 74 250 96 160 Z";
const HAIR_CAP = "M94 168 C84 40 316 40 306 168 C292 128 270 112 248 134 C238 108 214 104 200 128 C186 104 162 108 152 134 C130 112 108 128 94 168 Z";
const SIDE_L = "M96 150 C84 210 92 280 108 330 C122 280 118 210 134 150 Z";
const SIDE_R = "M304 150 C316 210 308 280 292 330 C278 280 282 210 266 150 Z";

function ClaudeArt({layer, p, id, t, o}) {
  if (layer === "backExtras") return null;
  if (layer === "backHair") return <g><path d={HAIR_BACK} fill={`url(#${id}hair)`} /><path d="M120 300 Q116 400 108 452 M280 300 Q284 400 292 452" stroke={p.hairDk} strokeWidth="3" fill="none" opacity="0.5" /></g>;
  if (layer === "body") {
    return (
      <g>
        {/* skirt: cream with black underlayer and orange panel, lace hem */}
        <path d="M150 318 L250 318 L312 500 Q200 524 88 500 Z" fill={p.dark} />
        <path d="M150 318 L250 318 L298 492 Q200 512 102 492 Z" fill={p.cloth} />
        <path d="M200 318 L246 318 L276 494 Q236 502 216 498 Z" fill={p.accent} opacity="0.95" />
        <path d="M118 478 Q200 506 286 478" stroke={p.accent} strokeWidth="2.5" fill="none" strokeDasharray="3 5" />
        <path d="M92 500 Q200 528 308 500" stroke={p.cloth} strokeWidth="9" fill="none" />
        {/* blouse + cape */}
        <path d="M146 268 Q200 252 254 268 L264 334 Q200 344 136 334 Z" fill={p.cloth} />
        <path d="M128 276 Q200 246 272 276 L280 304 Q200 290 120 304 Z" fill={p.clothSh} />
        <path d="M138 322 Q200 338 262 322 L262 348 Q200 358 138 348 Z" fill={p.dark} />
        <path d="M188 296 L200 322 L212 296 Z" fill={p.dark} />
        {/* boots */}
        <ellipse cx="172" cy="522" rx="22" ry="12" fill="#f5e8da" stroke={p.clothSh} strokeWidth="2" />
        <ellipse cx="228" cy="522" rx="22" ry="12" fill="#f5e8da" stroke={p.clothSh} strokeWidth="2" />
        {/* arms: puff sleeves */}
        <g transform={`rotate(${4 + o.armL} 146 280)`}><ellipse cx="136" cy="318" rx="20" ry="40" fill={p.cloth} stroke={p.clothSh} strokeWidth="2" /><ellipse cx="132" cy="352" rx="13" ry="10" fill={SKIN} /></g>
        <g transform={`rotate(${-4 + o.armR} 254 280)`}><ellipse cx="264" cy="318" rx="20" ry="40" fill={p.cloth} stroke={p.clothSh} strokeWidth="2" /></g>
        {/* book held in front */}
        <g transform="translate(236 336) rotate(-8)">
          <rect x="-4" y="-6" width="66" height="78" rx="6" fill={p.dark} />
          <rect x="0" y="-2" width="58" height="70" rx="5" fill="#fbf1e6" stroke={p.gold} strokeWidth="2" />
          <Flower cx={29} cy={33} r={17} petals={9} fill={p.accent} mid={p.gold} stroke={p.hairDk} />
        </g>
        <ellipse cx="240" cy="352" rx="13" ry="10" fill={SKIN} />
        <Flower cx={200} cy={296} r={16} petals={10} fill={p.accent} mid={p.gold} stroke={p.hairDk} />
      </g>
    );
  }
  if (layer === "frontHair") return <g><path d={SIDE_L} fill={p.hair} /><path d={SIDE_R} fill={p.hair} /><path d={HAIR_CAP} fill={`url(#${id}hair)`} /><path d="M200 74 C170 96 150 120 150 134 M200 74 C226 94 244 116 250 134" stroke={p.hairLt} strokeWidth="5" fill="none" opacity="0.7" strokeLinecap="round" /></g>;
  if (layer === "accessory") {
    return (
      <g transform={`rotate(${o.hairSway * 0.6} 280 110)`}>
        <path d="M288 112 L306 168 L292 160 L282 176 L272 118 Z" fill={p.dark} />
        <path d="M294 150 L302 196" stroke={p.cloth} strokeWidth="6" strokeLinecap="round" />
        <path d="M300 190 L304 214" stroke={p.gold} strokeWidth="5" strokeLinecap="round" />
        <Flower cx={280} cy={102} r={30} petals={12} fill={p.accent} mid={p.gold} stroke={p.hairDk} />
      </g>
    );
  }
  return null;
}

function GPTArt({layer, p, id, t, o}) {
  if (layer === "backExtras") {
    const wag = o.wag1;
    return (
      <g>
        <g transform={`rotate(${wag} 300 420)`}>
          <path d="M290 400 C350 410 380 440 372 486 C368 506 340 516 326 500 C346 490 350 470 330 456 C312 444 296 436 282 430 Z" fill="#e8e3f6" stroke={p.hairDk} strokeWidth="2.5" />
          {[0, 1, 2, 3].map((i) => <path key={i} d={`M${316 + i * 9} ${420 + i * 20} q10 8 8 18`} stroke={p.hairDk} strokeWidth="2" fill="none" opacity="0.7" />)}
        </g>
        {/* small wings */}
        <g transform={`rotate(${-o.wing} 150 300)`}><path d="M150 300 C92 250 40 270 24 330 C58 322 78 334 84 352 C100 332 122 326 150 336 Z" fill="#ece7fa" stroke={p.hairDk} strokeWidth="2.5" /></g>
        <g transform={`rotate(${o.wing} 250 300)`}><path d="M250 300 C308 250 360 270 376 330 C342 322 322 334 316 352 C300 332 278 326 250 336 Z" fill="#ece7fa" stroke={p.hairDk} strokeWidth="2.5" /></g>
      </g>
    );
  }
  if (layer === "backHair") {
    return (
      <g>
        <path d={HAIR_BACK} fill={`url(#${id}hair)`} />
        {[100, 130, 270, 300].map((x, i) => <circle key={i} cx={x} cy={452} r={20} fill={p.hair} />)}
        <path d="M110 250 Q96 300 106 350 M290 250 Q304 300 294 350" stroke={p.hairDk} strokeWidth="3" fill="none" opacity="0.5" />
      </g>
    );
  }
  if (layer === "body") {
    return (
      <g>
        <path d="M148 318 L252 318 L320 500 Q200 530 80 500 Z" fill={p.cloth} stroke={p.clothSh} strokeWidth="2" />
        <path d="M200 330 L214 500 L186 500 Z" fill={p.clothSh} opacity="0.7" />
        {[0, 1, 2, 3, 4].map((i) => <path key={i} d={`M${96 + i * 52} 500 q12 14 26 0`} fill="none" stroke={p.hairDk} strokeWidth="3" />)}
        <path d="M146 270 Q200 254 254 270 L258 334 Q200 346 142 334 Z" fill={p.cloth} stroke={p.clothSh} strokeWidth="2" />
        <path d="M168 272 L200 306 L232 272" stroke={p.accent} strokeWidth="3" fill="none" opacity="0.8" />
        <path d="M148 322 Q200 336 252 322" stroke={p.gold} strokeWidth="5" fill="none" />
        <ellipse cx="174" cy="522" rx="22" ry="11" fill="#f7f5ff" stroke={p.hairDk} strokeWidth="2" />
        <ellipse cx="226" cy="522" rx="22" ry="11" fill="#f7f5ff" stroke={p.hairDk} strokeWidth="2" />
        {/* bare arms with big frilled cuffs */}
        <g transform={`rotate(${6 + o.armL} 146 282)`}>
          <ellipse cx="132" cy="322" rx="11" ry="34" fill={SKIN} />
          <path d="M112 322 Q96 380 132 392 Q168 380 152 322 Z" fill={p.cloth} stroke={p.clothSh} strokeWidth="2" />
          <path d="M114 380 q10 10 18 0 q10 10 18 0" fill="none" stroke={p.hairDk} strokeWidth="2" />
        </g>
        <g transform={`rotate(${-6 + o.armR} 254 282)`}>
          <ellipse cx="268" cy="322" rx="11" ry="34" fill={SKIN} />
          <path d="M248 322 Q232 380 268 392 Q304 380 288 322 Z" fill={p.cloth} stroke={p.clothSh} strokeWidth="2" />
          <path d="M250 380 q10 10 18 0 q10 10 18 0" fill="none" stroke={p.hairDk} strokeWidth="2" />
        </g>
        <Rosette cx={200} cy={440} r={20} stroke={p.dark} fill="#ffffff" />
        <Rosette cx={140} cy={478} r={12} stroke={p.hairDk} fill="none" />
        <Rosette cx={268} cy={480} r={12} stroke={p.hairDk} fill="none" />
        <Rosette cx={200} cy={303} r={12} stroke={p.accent} fill="#ffffff" />
      </g>
    );
  }
  if (layer === "frontHair") {
    return (
      <g>
        <path d={SIDE_L} fill={p.hair} stroke={p.hairDk} strokeWidth="1.5" />
        <path d={SIDE_R} fill={p.hair} stroke={p.hairDk} strokeWidth="1.5" />
        <path d={HAIR_CAP} fill={`url(#${id}hair)`} stroke={p.hairDk} strokeWidth="1.5" />
        <path d="M200 80 C150 100 130 140 128 170 M200 80 C244 98 270 134 274 170" stroke={p.hairDk} strokeWidth="2.5" fill="none" opacity="0.6" />
        <path d={`M200 58 C${196 + o.ahoge} 34 ${214 + o.ahoge} 22 ${224 + o.ahoge} 34 C${218 + o.ahoge} 38 ${208 + o.ahoge} 44 ${204 + o.ahoge} 60 Z`} fill={p.hair} stroke={p.hairDk} strokeWidth="2" />
      </g>
    );
  }
  if (layer === "accessory") {
    return (
      <g>
        {/* dragon horns */}
        <path d="M118 96 C84 84 66 52 82 20 C84 52 104 66 134 76 Z" fill="#ece7fa" stroke={p.hairDk} strokeWidth="3" />
        <path d="M282 96 C316 84 334 52 318 20 C316 52 296 66 266 76 Z" fill="#ece7fa" stroke={p.hairDk} strokeWidth="3" />
        <path d="M88 52 l14 4 M92 38 l12 4 M312 52 l-14 4 M308 38 l-12 4" stroke={p.hairDk} strokeWidth="2" />
        {/* pointed ears */}
        <path d="M100 186 L68 170 L98 210 Z" fill={SKIN} stroke={SKIN_SH} strokeWidth="2" />
        <path d="M300 186 L332 170 L302 210 Z" fill={SKIN} stroke={SKIN_SH} strokeWidth="2" />
        <Rosette cx={262} cy={118} r={20} stroke={p.dark} fill="#ffffff" />
        <Rosette cx={262} cy={118} r={9} stroke={p.accent} fill="none" />
      </g>
    );
  }
  return null;
}

function DeepSeekArt({layer, p, id, t, o}) {
  if (layer === "backExtras") {
    const wag = o.wag2;
    return (
      <g transform={`rotate(${wag} 290 440)`}>
        <path d="M280 440 C336 446 360 420 366 376 C350 392 330 394 318 388 C340 366 346 340 338 316 C330 348 300 374 278 396 Z" fill="#26418f" stroke={p.dark} strokeWidth="2.5" />
        <path d="M338 316 C352 322 364 336 368 356 M366 376 C378 372 386 360 388 346" fill="none" stroke={p.dark} strokeWidth="2.5" />
        <path d="M300 420 q20 -10 32 -30" stroke="#6d86d0" strokeWidth="3" fill="none" opacity="0.7" />
      </g>
    );
  }
  if (layer === "backHair") {
    return (
      <g>
        <path d={HAIR_BACK} fill={`url(#${id}hair)`} />
        <path d="M110 300 Q96 380 98 452 M290 300 Q304 380 302 452" stroke={p.hairLt} strokeWidth="3.5" fill="none" opacity="0.5" />
      </g>
    );
  }
  if (layer === "body") {
    return (
      <g>
        <path d="M148 318 L252 318 L316 500 Q200 526 84 500 Z" fill={p.dark} />
        <path d="M120 440 L280 440 L304 496 Q200 516 96 496 Z" fill="#4372c4" />
        <path d="M120 440 L280 440" stroke={p.gold} strokeWidth="3" />
        <path d="M84 500 Q200 528 316 500" stroke="#ffffff" strokeWidth="10" fill="none" />
        <path d="M104 482 Q200 508 296 482" stroke={p.gold} strokeWidth="2" fill="none" strokeDasharray="2 6" />
        {/* bodice + apron */}
        <path d="M146 270 Q200 254 254 270 L258 336 Q200 348 142 336 Z" fill={p.dark} />
        <path d="M164 272 Q200 262 236 272 L240 318 Q200 326 160 318 Z" fill="#ffffff" />
        <path d="M166 322 Q200 332 234 322 L262 452 Q200 466 138 452 Z" fill="#ffffff" stroke={p.clothSh} strokeWidth="2" />
        <path d="M138 452 q10 12 20 0 q10 12 20 0 q10 12 22 0 q10 12 20 0 q10 12 20 0 q10 12 22 0" fill="none" stroke={p.clothSh} strokeWidth="3" />
        {/* whale emblem on apron (our own drawing) */}
        <g transform="translate(200 394)">
          <path d="M-18 6 C-18 -8 -4 -12 6 -8 C14 -4 18 -10 22 -14 C22 -6 20 2 12 8 C2 14 -14 14 -18 6 Z" fill={p.hair} />
          <path d="M-4 -12 q2 -8 -2 -12 M-4 -12 q4 -8 8 -10" stroke={p.hairLt} strokeWidth="2" fill="none" />
        </g>
        <path d="M156 276 L200 292 L244 276" stroke={p.dark} strokeWidth="4" fill="none" />
        <path d="M190 292 L200 312 L210 292 Z" fill={p.dark} />
        <circle cx="200" cy="300" r="5" fill={p.eye} />
        {/* legs + shoes */}
        <rect x="160" y="500" width="22" height="20" fill="#fff" />
        <rect x="218" y="500" width="22" height="20" fill="#fff" />
        <ellipse cx="170" cy="526" rx="23" ry="11" fill={p.dark} />
        <ellipse cx="230" cy="526" rx="23" ry="11" fill={p.dark} />
        <rect x="156" y="514" width="30" height="4" fill={p.gold} />
        {/* puff sleeves, bare shoulders */}
        <g transform={`rotate(${5 + o.armL} 146 282)`}>
          <ellipse cx="130" cy="316" rx="20" ry="38" fill={p.dark} />
          <rect x="112" y="344" width="36" height="12" rx="4" fill="#ffffff" stroke={p.clothSh} strokeWidth="1.5" />
          <ellipse cx="130" cy="364" rx="12" ry="10" fill={SKIN} />
        </g>
        <g transform={`rotate(${-5 + o.armR} 254 282)`}>
          <ellipse cx="270" cy="316" rx="20" ry="38" fill={p.dark} />
          <rect x="252" y="344" width="36" height="12" rx="4" fill="#ffffff" stroke={p.clothSh} strokeWidth="1.5" />
          <ellipse cx="270" cy="364" rx="12" ry="10" fill={SKIN} />
        </g>
      </g>
    );
  }
  if (layer === "frontHair") {
    return (
      <g>
        {/* whale head-fins at the sides */}
        <g>
          <path d="M104 170 C70 150 54 168 56 196 C80 198 98 192 110 184 Z" fill="#26418f" stroke={p.dark} strokeWidth="2.5" />
          <path d="M62 190 C80 192 96 188 108 182" stroke="#e7eefc" strokeWidth="4" fill="none" />
          <path d="M296 170 C330 150 346 168 344 196 C320 198 302 192 290 184 Z" fill="#26418f" stroke={p.dark} strokeWidth="2.5" />
          <path d="M338 190 C320 192 304 188 292 182" stroke="#e7eefc" strokeWidth="4" fill="none" />
        </g>
        <path d={SIDE_L} fill={p.hair} />
        <path d={SIDE_R} fill={p.hair} />
        <path d={HAIR_CAP} fill={`url(#${id}hair)`} />
        <path d="M150 134 C160 110 180 108 200 128 C220 108 240 110 250 134" fill="none" stroke={p.hairLt} strokeWidth="3.5" opacity="0.6" />
        <path d={`M200 62 C${190 + o.ahoge} 30 ${214 + o.ahoge} 18 ${222 + o.ahoge} 32 C${216 + o.ahoge} 36 ${208 + o.ahoge} 44 ${204 + o.ahoge} 64 Z`} fill={p.hair} stroke={p.hairDk} strokeWidth="2" />
      </g>
    );
  }
  if (layer === "accessory") {
    return (
      <g>
        {/* maid headdress */}
        <path d="M128 98 C150 68 250 68 272 98 C256 88 240 86 200 86 C160 86 144 88 128 98 Z" fill="#ffffff" stroke={p.clothSh} strokeWidth="2" />
        <path d="M130 100 q8 10 16 0 q8 10 16 0 q8 10 16 0 q8 10 16 0 q8 10 16 0 q8 10 16 0 q8 10 16 0 q8 10 16 0" fill="#fff" stroke={p.clothSh} strokeWidth="2" />
        <g transform="translate(146 120) rotate(-20)"><path d="M0 0 L-18 -10 L-18 12 Z M0 0 L18 -10 L18 12 Z" fill={p.eye} stroke={p.eyeDk} strokeWidth="1.5" /><circle r="4.5" fill={p.eyeDk} /></g>
      </g>
    );
  }
  return null;
}

const ART = {Claude: ClaudeArt, GPT: GPTArt, DeepSeek: DeepSeekArt};

/**
 * state: {t, open (mouth 0..1), blink (0..1 closed), wink: {side:'L'|'R', amt 0..1}|null, nod (px)}
 * Returns an <svg> element.
 */
export function Character({who, t = 0, open = 0, blink = 0, wink = null, nod = 0, loopP = 0}) {
  // loopP > 0: every idle frequency snaps to a whole number of cycles per loopP seconds (seamless loop)
  const F = (f) => (loopP ? Math.max(1, Math.round((f * loopP) / (2 * Math.PI))) * 2 * Math.PI / loopP : f);
  const p = PAL[who];
  const Art = ART[who];
  const id = `${who}_`;
  const o = {
    armL: Math.sin(t * F(1.9) + 1) * 2.2, armR: Math.sin(t * F(1.9) + 2.2) * 2.2,
    hairSway: Math.sin(t * F(1.7) + 0.4) * 2.4, ahoge: Math.sin(t * F(3.1)) * 4, wing: 4 + Math.sin(t * F(2.6)) * 5,
    wag1: Math.sin(t * F(2.2)) * 5, wag2: Math.sin(t * F(2.4)) * 7,
  };
  const breath = 1 + Math.sin(t * F(2.1)) * 0.012;
  const tilt = Math.sin(t * F(1.3)) * 1.2 + nod * 0.4;
  const winkAmt = wink ? wink.amt : 0;
  const eyeOpen = (side) => {
    let v = 1 - blink;
    if (wink && wink.side === side) v = Math.min(v, 1 - winkAmt);
    return v;
  };
  const arcL = wink && wink.side === "L" && winkAmt > 0.55;
  const arcR = wink && wink.side === "R" && winkAmt > 0.55;
  const blinkArcL = blink > 0.6, blinkArcR = blink > 0.6;
  const faceIdle = {transform: `translate(0 ${nod}) rotate(${tilt} 200 260)`};
  const L = (layer) => <Art layer={layer} p={p} id={id} t={t} o={o} />;
  const sparkSide = wink && winkAmt > 0.5 ? (wink.side === "L" ? 118 : 284) : null;

  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox={`0 0 ${VB_W} ${VB_H}`} width={VB_W} height={VB_H}>
      <defs>
        <linearGradient id={`${id}hair`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={p.hair} />
          <stop offset="0.55" stopColor={p.hair} />
          <stop offset="1" stopColor={who === "DeepSeek" ? p.hairLt : p.hairDk} />
        </linearGradient>
        <radialGradient id={`${id}iris`} cx="0.5" cy="0.35" r="0.8">
          <stop offset="0" stopColor={p.eye} />
          <stop offset="1" stopColor={p.eyeDk} />
        </radialGradient>
      </defs>
      <g transform={`translate(200 540) scale(${breath}) translate(-200 -540)`}>
        <g transform={`rotate(${o.hairSway * 0.5} 200 100)`}>{L("backExtras")}</g>
        <g transform={`rotate(${o.hairSway} 200 120)`}>{L("backHair")}</g>
        {L("body")}
        <g {...faceIdle}>
          {/* neck */}
          <rect x="182" y="250" width="36" height="34" fill={SKIN_SH} />
          {/* head */}
          <ellipse cx="200" cy="175" rx="100" ry="88" fill={SKIN} />
          <path d="M112 200 Q200 290 288 200 Q282 262 200 266 Q118 262 112 200 Z" fill={SKIN_SH} opacity="0.35" />
          {/* face */}
          <Eye id={`${id}L`} cx={158} cy={192} p={p} open={eyeOpen("L")} closedArc={arcL || (blinkArcL && !wink)} />
          <Eye id={`${id}R`} cx={242} cy={192} p={p} open={eyeOpen("R")} closedArc={arcR || (blinkArcR && !wink)} />
          <path d="M132 150 Q156 140 180 150 M220 150 Q244 140 268 150" stroke={p.hairDk} strokeWidth="4.5" fill="none" strokeLinecap="round" opacity="0.8" />
          <ellipse cx="128" cy="226" rx="17" ry="9" fill="#ff9fa8" opacity="0.5" />
          <ellipse cx="272" cy="226" rx="17" ry="9" fill="#ff9fa8" opacity="0.5" />
          <path d="M198 218 q2 4 4 0" stroke={SKIN_SH} strokeWidth="3" fill="none" />
          <Mouth open={open} />
          <g transform={`rotate(${o.hairSway * 0.4} 200 100)`}>{L("frontHair")}</g>
          <g>{L("accessory")}</g>
          {sparkSide !== null && (
            <g opacity={Math.min(1, (winkAmt - 0.4) * 2.5)}>
              <Star cx={sparkSide + (wink.side === "L" ? -26 : 26)} cy={158} r={15} fill="#ffd34d" />
              <Star cx={sparkSide + (wink.side === "L" ? -46 : 46)} cy={186} r={8} fill="#ff8fb0" />
            </g>
          )}
        </g>
      </g>
    </svg>
  );
}

export const characterToSvgString = (props) => renderToStaticMarkup(<Character {...props} />);
export const NAMES = ["Claude", "GPT", "DeepSeek"];
export const NAME_COLOR = {Claude: "#e9691c", GPT: "#6d5fc0", DeepSeek: "#2c55b8"};
