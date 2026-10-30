// s2plus shared kit (research/marathon_refs_20261031.md section 2): tokens, grid, six type settings, evidence plates, barcode, spec sheet, stand-ins.
// Imports nothing from ../core: that would load Knewave and Martian Mono 700/800 on every still and put cyan and acid within reach.
// Pure ramp/hash/rng from ../core are fine in a still if it needs them; tokens and type come from here.
import React from "react";
import {AbsoluteFill} from "remotion";
import {loadFont as loadSans} from "@remotion/google-fonts/InterTight";
import {loadFont as loadSerif} from "@remotion/google-fonts/InstrumentSerif";
import {loadFont as loadMono} from "@remotion/google-fonts/MartianMono";
import PL from "./data/plddt.json";
import SQ from "./data/sequence.json";

// ---------- tokens ----------
export const K = {bg: "#060606", bone: "#EDEBE4", red: "#E8190F", blue: "#1F3BFF", klein: "#002FA7"};  // same hex as core.jsx C
export const DIM = "rgba(237,235,228,0.55)", FAINT = "rgba(237,235,228,0.2)";  // core.jsx C.dim, C.faint. DIM is 5.4:1 on black only, 2.6:1 on blue
export const SANS = loadSans("normal", {weights: ["500", "600"], subsets: ["latin"]}).fontFamily;
export const SERIF = loadSerif("normal", {weights: ["400"], subsets: ["latin"]}).fontFamily;
export const MONO = loadMono("normal", {weights: ["400", "500"], subsets: ["latin"]}).fontFamily;

// ---------- 12-column grid ----------
export const W = 1920, H = 1080, M = 96, GUT = 24, COL = (W - 2 * M - 11 * GUT) / 12;  // COL = 122
export const colX = i => M + i * (COL + GUT);        // left edge of column i (0..11)
export const colW = n => n * COL + (n - 1) * GUT;    // width of n columns

// ---------- real data (make_data.py) ----------
export const PLDDT = PL.score, PLDDT_CAT = PL.cat, SEQUENCE = SQ.seq, N_RES = PLDDT.length;

// ---------- section 2.1 as data ----------
// {ground: {ink: smallest px allowed}}; a pair not listed is banned. on={null} skips the check (flat on a render or footage).
// "Big only" is set at Body 36, not WCAG's 24 px, so the two small settings (PlateText 26, Foot 22) stay off red, as 2.1 asks.
const BIG = 36;
const LEGAL = {
  [K.bg]: {[K.bone]: 0, [DIM]: 0, [K.red]: BIG},
  [K.blue]: {[K.bone]: 0},
  [K.klein]: {[K.bone]: 0},
  [K.red]: {[K.bone]: BIG, [K.bg]: BIG},
  [K.bone]: {[K.bg]: 0},
};
const legal = (on, ink, px) => { if (LEGAL[on] && !(LEGAL[on][ink] <= px)) throw new Error(`section 2.1 bans ${ink} text at ${px} px on ${on}`); };

// ---------- six type settings (section 2.2) ----------
// No Google subset of these fonts covers U+2192, so the arrow in "millions → 13" is drawn; type the string verbatim and setting() swaps it in.
export const Arrow = ({style}) => <svg viewBox="0 0 100 100" style={{display: "inline-block", width: "0.86em", height: "0.86em", verticalAlign: "-0.1em", ...style}}>
  <path d="M8 50H90M58 18L90 50L58 82" fill="none" stroke="currentColor" strokeWidth="9"/>
</svg>;
const arrows = kids => React.Children.map(kids, c => typeof c === "string" && c.includes("→") ? c.split("→").flatMap((s, i) => i ? [<Arrow key={i}/>, s] : [s]) : c);

// x given = absolute at x, y, w. Size clamps to the table. on = the ground under the text; set it on any colour field so the 2.1 check can run.
const setting = (font, weight, def, lo, hi, lineHeight, letterSpacing) => ({x, y, w, size = def, color, on = K.bg, style, children}) => {
  const px = Math.min(hi, Math.max(lo, size)), ink = color ?? (on === K.bone ? K.bg : K.bone);
  legal(on, ink, px);
  return <div style={{...(x === undefined ? {} : {position: "absolute", left: x, top: y, width: w}), fontFamily: font, fontWeight: weight, fontSize: px, lineHeight, letterSpacing, color: ink, ...style}}>{arrows(children)}</div>;
};
export const Giant = setting(SANS, 600, 400, 280, 480, 0.88, "-0.04em");   // one number per screen
export const Big = setting(SANS, 500, 80, 64, 96, 1.04, "-0.02em");        // main label
export const Voice = setting(SERIF, 400, 96, 56, 120, 1.06, "-0.01em");    // questions, spoken words
export const Body = setting(SANS, 500, 36, 36, 36, 1.25, "-0.005em");      // explanation
export const PlateText = setting(MONO, 500, 26, 26, 26, 1.3, 0);           // evidence plates, corner tags. Martian Mono renders 0.7 em wide: 18.2 px a character
export const Foot = setting(MONO, 400, 22, 22, 22, 1.4, 0);                // sources: 15.4 px a character

// ---------- Stage ----------
// will-change gives the stage its own layer, and Chromium turns LCD text off there: grey antialiasing, no red and blue fringes on small type. Remotion has no switch for --disable-lcd-text.
export const Stage = ({bg = K.bg, style, children}) => <AbsoluteFill style={{width: W, height: H, background: bg, overflow: "hidden", textRendering: "geometricPrecision", willChange: "transform", ...style}}>{children}</AbsoluteFill>;

// ---------- dashed box (empty cells) ----------
export const DashBox = ({x, y, w, h, color = K.bone, weight = 2, dash = "14 10", style, children}) =>
  <div style={{position: x === undefined ? "relative" : "absolute", left: x, top: y, width: w, height: h, ...style}}>
    <svg style={{position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible"}}><rect width="100%" height="100%" fill="none" stroke={color} strokeWidth={weight} strokeDasharray={dash}/></svg>
    {children}
  </div>;

// ---------- evidence plates (section 2.3) ----------
// Told apart by fill and line, not hue, so they survive colour blindness: solid; solid with dotted ring; hollow; thin dashes.
// All four keep one outer size: the frames are inset outlines. Text from section 2.3; pass children for the other wordings
// (<Plate kind="ai">AI GENERATED · Chemistry42</Plate>, <Plate kind="illustrative">schematic</Plate>), fig for measured ones.
const PLATE = {
  measured: {text: "MEASURED · Ren 2023", fill: K.bone},
  ai: {text: "AI PREDICTED · AlphaFold", fill: K.blue, line: {outline: `2px dotted ${K.blue}`, outlineOffset: 5}},
  ours: {text: "OUR RE-DOCKING", line: {outline: `3px solid ${K.blue}`, outlineOffset: -3}},
  illustrative: {text: "ILLUSTRATIVE"},
};
export const Plate = ({kind = "measured", fig, x, y, on = K.bg, style, children}) => {
  const p = PLATE[kind], blueInk = kind === "ai" || kind === "ours";
  if (blueInk && [K.blue, K.klein, K.red].includes(on)) throw new Error(`${kind} plate is blue and vanishes or clashes on ${on}`);
  const faint = kind === "illustrative" ? (on === K.bg ? DIM : K.bone) : null;  // DIM fails on colour fields, W3 needs full bone here
  const ink = p.fill === K.bone ? K.bg : faint ?? K.bone;
  return <div style={{...(x === undefined ? {display: "inline-block"} : {position: "absolute", left: x, top: y}), padding: "10px 18px", whiteSpace: "nowrap", background: p.fill,
    ...p.line, ...(faint ? {outline: `1.5px dashed ${faint}`, outlineOffset: -1.5} : {}), ...style}}>
    <PlateText color={ink} on={p.fill ?? on}>{children ?? p.text + (fig ? `, Fig. ${fig}` : "")}</PlateText>
  </div>;
};

// ---------- objective tag ----------
// The film's first plate (section 3 S2), back in S4, S5 and S8. Klein means we are asking, so it is not one of the four evidence plates. One colour per screen: use it only where nothing else is coloured.
export const Tag = ({x, y, style, children}) => <div style={{...(x === undefined ? {} : {position: "absolute", left: x, top: y}), padding: "10px 18px", background: K.klein, whiteSpace: "nowrap", ...style}}>
  <PlateText on={K.klein}>{children}</PlateText>
</div>;

// ---------- barcode: one bar per residue of CDK20, height = its real pLDDT on a 0-100 scale ----------
// Height keeps it reading as data, not a test pattern (section 0). flat turns that off. The colour rule is open (director's item 2), so it is one prop.
const snap = v => Math.round(v * 2) / 2;  // half a CSS px is one device px at --scale=2, so bars land on whole pixels
export const BAR_MODES = {
  splat: s => s >= 70 ? K.bone : K.blue,  // bone = confident (AlphaFold >= 70), blue = not
  blue: () => K.blue,                     // all blue, confidence by height alone
  red: s => s >= 70 ? K.bone : K.red,     // the S1 1-10 proposal
};
/** Centre x of a residue's bar inside a Barcode of this width, for aligning a mark to it. Tail residues add the gap. */
export const barX = (res, width = 1728) => (res - 0.5) * snap(width / N_RES);
const isLit = (hl, r) => hl.some(h => Array.isArray(h) ? r >= h[0] && r <= h[1] : r === h);

/**
 * width: pitch snaps to a half px, so real width can differ slightly (1728 -> 1730). mode: BAR_MODES key or (score, residue) => colour.
 * bar: bar width in px, default 60% of the pitch.
 * cutAt: last residue kept; the tail shifts right by gap past width, so leave room. tail={false} removes it.
 * highlight: residue, or list of residues and [from, to] ranges; the rest drop to 0.3. highlightColor recolours the lit bars.
 */
export const Barcode = ({x, y, width = 1728, height = 120, bar, mode = "splat", flat = false, cutAt, gap = 40, tail = true, highlight, highlightColor, style}) => {
  const paint = typeof mode === "function" ? mode : BAR_MODES[mode], p = snap(width / N_RES), b = bar ?? Math.max(0.5, snap(p * 0.6));
  const hl = highlight === undefined ? null : [].concat(highlight);
  return <svg width={N_RES * p + (cutAt === undefined ? 0 : gap)} height={height} shapeRendering="crispEdges"
    style={{...(x === undefined ? {} : {position: "absolute", left: x, top: y}), display: "block", overflow: "visible", ...style}}>
    {PLDDT.map((s, i) => {
      const r = i + 1, cut = cutAt !== undefined && r > cutAt, lit = !hl || isLit(hl, r), h = flat ? height : snap(height * s / 100);
      return cut && !tail ? null : <rect key={r} x={i * p + (cut ? gap : 0)} y={height - h} width={b} height={h} fill={hl && lit && highlightColor || paint(s, r)} opacity={lit ? 1 : 0.3}/>;
    })}
  </svg>;
};

// ---------- spec sheet ----------
// A ruled datasheet with no outer frame: reading position is a heavier rule, never a filled row.
/**
 * rows: [{label?, value, empty?, state?}]. empty draws a dashed blank instead of a value. state ("on"|"read"|"active"|"off") overrides active for one row.
 * active: index being spoken; earlier rows read (dim), later rows off (kept in layout, rule only). null = all on.
 * cell: {x?, y?, w?, h?, label?, children?}: large dashed cell, right of the rows unless placed; x, y relative to the sheet.
 */
export const SpecSheet = ({x = M, y = M, w = colW(12), rowsW, labelW = 300, rows = [], active = null, cell, style}) => {
  const rw = rowsW ?? (cell ? colW(5) : w), lw = rows.some(r => r.label) ? labelW : 0;
  return <div style={{position: "absolute", left: x, top: y, width: w, ...style}}>
    <div style={{width: rw}}>{rows.map((r, i) => {
      const st = r.state ?? (active === null ? "on" : i < active ? "read" : i === active ? "active" : "off");
      const hot = st === "active", ink = st === "read" ? DIM : K.bone, vis = st === "off" ? {visibility: "hidden"} : {};
      return <div key={i} style={{display: "flex", alignItems: "baseline", gap: GUT, padding: hot ? "14px 0 16px" : "16px 0", borderTop: hot ? `4px solid ${K.bone}` : `2px solid ${FAINT}`}}>
        {lw ? <Foot color={st === "on" || hot ? K.bone : DIM} style={{width: lw, flexShrink: 0, ...vis}}>{r.label}</Foot> : null}
        {r.empty ? <DashBox h={45} color={ink} style={{flex: 1, alignSelf: "center", ...vis}}/> : <Body color={ink} style={{flex: 1, minWidth: 0, ...vis}}>{r.value}</Body>}
      </div>;
    })}</div>
    {cell ? <DashBox x={cell.x ?? rw + GUT} y={cell.y ?? 0} w={cell.w ?? w - rw - GUT} h={cell.h ?? 640}>
      {cell.children}
      {cell.label ? <Foot style={{position: "absolute", left: 24, bottom: 20}}>{cell.label}</Foot> : null}
    </DashBox> : null}
  </div>;
};

// ---------- phone footage stand-in ----------
// Flat greys are the one exception to the palette: this never ships. Footage is due 11-12. side: left | right | full; x, y, w, h override it.
// lean: px the figure slides, negative is left, and it turns that way, so a half-screen shot looks toward its colour block (section 2.2). eye: draws the eye line, to test framing before the shoot.
export const PersonPlaceholder = ({who = "A", side = "right", x, y = 0, w, h = H, lean = 0, eye = false, style}) => {
  const turn = Math.sign(lean);
  return <div style={{position: "absolute", left: x ?? (side === "right" ? W / 2 : 0), top: y, width: w ?? (side === "full" ? W : W / 2), height: h, background: "#2A2A2A", overflow: "hidden", ...style}}>
    <svg viewBox="0 0 960 1080" preserveAspectRatio="xMidYMax meet" style={{position: "absolute", inset: 0, width: "100%", height: "100%"}}>
      <g transform={`translate(${lean} 0)`} fill="#4A4A4A">
        <ellipse cx="480" cy="430" rx="165" ry="205"/>
        {turn ? <path d={`M${480 + turn * 150} 372L${480 + turn * 198} 462L${480 + turn * 146} 476Z`}/> : null}
        <path d="M80 1080C90 840 240 770 400 725V620H560V725C720 770 870 840 880 1080Z"/>
        {eye ? <path d="M315 430H645" fill="none" stroke="#7A7A7A" strokeWidth="3" strokeDasharray="12 9"/> : null}
      </g>
    </svg>
    <Foot on={null} style={{position: "absolute", left: 24, top: 20}}>PLACEHOLDER · {who}</Foot>
  </div>;
};
