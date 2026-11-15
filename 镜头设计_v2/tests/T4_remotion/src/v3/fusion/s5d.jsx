// HKBU SCIE1007 coursework science video. Chapter 5 voice-over shots retimed to the recorded voice (11-16): 5-01, 5-03, 5-07, 5-08, W4, 5-10.
// The 3D take comes from inserts/bl_s5d.py; every mark here is an event in 镜头设计_v3/粗剪/对时/beats/<seg>.json (beats_resolve.py puts each on the frame its word is said).
// Props: seg, beats (the resolved JSON), pts (screen points measured with S5D_PROJ), file (the take), audio (the condensed voice / music). All type is Instrument Serif; pen notes are Caveat.
// Numbers on screen: s4/<段号>_数字对照.md with their page in Ren 2023.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, OffthreadVideo, Audio, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";

const W = 1920, H = 1080;
const INK = "#111113", SOFT = "#545458", RED = "#E8190F", BLUE = "#2A4BD7", BONE = "#EDEBE4";
const SERIF = "Instrument Serif", HAND = "Caveat";
const faces = [new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Regular.ttf")})`), new FontFace(SERIF, `url(${staticFile("fusion_s1/fonts/InstrumentSerif-Italic.ttf")})`, {style: "italic"}), new FontFace(HAND, `url(${staticFile("fusion_s1/fonts/Caveat.ttf")})`, {weight: "400 700"})];
const fontHandle = delayRender("fonts");
Promise.all(faces.map(f => f.load())).then(l => { l.forEach(f => document.fonts.add(f)); continueRender(fontHandle); });

const clamp = x => Math.min(1, Math.max(0, x));
const smooth = x => { x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10); };
const colour = c => c === "red" ? RED : c === "blue" ? BLUE : c || INK;
const ruler = document.createElement("canvas").getContext("2d");
const measure = (s, size, font = SERIF, italic = false) => { ruler.font = `${italic ? "italic " : ""}${font === HAND ? 600 : 400} ${size}px "${font}"`; return ruler.measureText(s).width; };
let uid = 0;

// f is the 60 fps frame. p(e) = how far the event's own motion has run (0..1), from f_start (or f_land when there is no lead) over dur frames.
const prog = (f, e, dur) => smooth((f - (e.f_start ?? e.f_land)) / Math.max(1, dur ?? e.dur ?? 20));

const Ink = ({e, f, x, y}) => {
  const p = prog(f, e), id = React.useMemo(() => `w${uid++}`, []);
  if (p <= 0) return null;
  const size = e.size || 32, font = e.font === "hand" ? HAND : SERIF;
  const wd = measure(e.text, size, font) + 40, anchor = e.anchor || "start";
  const left = anchor === "start" ? x - 20 : anchor === "end" ? x - wd + 20 : x - wd / 2;
  return <g>
    <clipPath id={id}><rect x={left} y={y - size * 1.2} width={wd * p} height={size * 1.6}/></clipPath>
    <text x={x} y={y} fontFamily={font} fontSize={size} fill={colour(e.fill)} textAnchor={anchor} clipPath={`url(#${id})`}>{e.text}</text>
  </g>;
};
const Note = ({e, f, x, y}) => {
  const p = prog(f, e), id = React.useMemo(() => `n${uid++}`, []);
  if (p <= 0) return null;
  const size = e.size || 48, wd = measure(e.text, size, HAND) + 30;
  const left = e.anchor === "middle" ? x - wd / 2 : x;
  return <g transform={`rotate(${e.rot ?? -1.5} ${x} ${y})`}>
    <clipPath id={id}><rect x={left - 10} y={y - size * 1.1} width={wd * p} height={size * 1.5}/></clipPath>
    <text x={x} y={y} fontFamily={HAND} fontSize={size} fontWeight={600} fill={colour(e.fill)} textAnchor={e.anchor || "start"} clipPath={`url(#${id})`}>{e.text}</text>
  </g>;
};
const Keyed = ({e, f, x, y}) => {
  const p = prog(f, e), id = React.useMemo(() => `k${uid++}`, []);
  if (p <= 0) return null;
  const [a, key, b = ""] = e.parts, size = e.size;
  const x0 = x + measure(a, size), len = measure(key, size, SERIF, true), wd = x0 - x + len + measure(b, size) + 40;
  const u = smooth((f - (e.f_start ?? e.f_land) - e.dur) / 14);
  return <g>
    <clipPath id={id}><rect x={x - 20} y={y - size * 1.2} width={wd * p} height={size * 1.6}/></clipPath>
    <text x={x} y={y} fontFamily={SERIF} fontSize={size} fill={INK} clipPath={`url(#${id})`}>{a}<tspan fontStyle="italic">{key}</tspan>{b}</text>
    {u > 0 && <rect x={x0} y={y + size * 0.18} width={len * u} height={Math.max(4, size * 0.07)} fill={RED}/>}
  </g>;
};
const Under = ({e, f, x, y}) => {
  const p = prog(f, e);
  if (p <= 0) return null;
  const font = e.font === "hand" ? HAND : SERIF, size = e.size;
  const x0 = x + measure(e.before || "", size, font), len = measure(e.key, size, font);
  const tilt = font === HAND ? Math.tan(-1.5 * Math.PI / 180) : 0;
  return <rect x={x0} y={y + size * 0.18 + (x0 - x) * tilt} width={len * p} height={Math.max(4, size * 0.08)} fill={RED} transform={font === HAND ? `rotate(-1.5 ${x} ${y})` : undefined}/>;
};
const Ring = ({e, f, x, y}) => {
  const p = prog(f, e);
  if (p <= 0) return null;
  const rx = e.rx, ry = e.ry, L = Math.PI * (3 * (rx + ry) - Math.sqrt((3 * rx + ry) * (rx + 3 * ry)));
  return <ellipse cx={x} cy={y} rx={rx} ry={ry} fill="none" stroke={colour(e.fill)} strokeWidth={4} strokeLinecap="round" strokeDasharray={`${L * 1.05 * p} ${L * 2}`} transform={`rotate(-8 ${x} ${y})`}/>;
};
const PenLine = ({e, f, a, b}) => {
  const p = prog(f, e);
  if (p <= 0) return null;
  const x = a[0] + (b[0] - a[0]) * p, y = a[1] + (b[1] - a[1]) * p, ang = Math.atan2(b[1] - a[1], b[0] - a[0]), k = e.head || 0;
  return <g stroke={colour(e.fill)} strokeWidth={3} strokeLinecap="round" fill="none">
    <line x1={a[0]} y1={a[1]} x2={x} y2={y} strokeDasharray={e.dash ? "10 8" : undefined}/>
    {k > 0 && p > 0.95 && <path d={`M${x - k * Math.cos(ang - 0.5)} ${y - k * Math.sin(ang - 0.5)} L${x} ${y} L${x - k * Math.cos(ang + 0.5)} ${y - k * Math.sin(ang + 0.5)}`}/>}
  </g>;
};
const Leader = ({e, f, pts}) => {
  const p = prog(f, e);
  if (p <= 0) return null;
  const L = pts.slice(1).reduce((s, q, i) => s + Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]), 0);
  return <g>
    <polyline points={pts.map(q => q.join(",")).join(" ")} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray={`${L * p} ${L}`}/>
    <circle cx={pts[0][0]} cy={pts[0][1]} r={6} fill={INK}/>
    {e.text && p > 0.6 && <text x={e.tx} y={e.ty} fontFamily={SERIF} fontSize={e.size || 34} fill={INK} opacity={smooth((p - 0.6) / 0.4)}>{e.text}</text>}
  </g>;
};
const Tag = ({e, f}) => {
  const p = prog(f, e, 24);
  if (p <= 0) return null;
  const size = 30, r = size / 2, cx = e.x + r, cy = e.y - size * 0.36;
  return <g>
    <Leader e={{...e, text: ""}} f={f} pts={e.leader}/>
    <g opacity={p}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="6 5"/>
      <text x={e.x + size * 1.45} y={e.y} fontFamily={SERIF} fontSize={size + 4} fill={INK}>{e.text}</text>
      {e.sub && <text x={e.x + size * 1.45} y={e.y + 38} fontFamily={SERIF} fontSize={26} fill={SOFT}>{e.sub}</text>}
    </g>
  </g>;
};
const Dots = ({e, f, x, y}) => {
  const n = e.n || 12, out = [];
  for (let i = 0; i < n; i++) {
    const a = i * 2.39996, r = 10 + 9 * Math.sqrt(i);
    const p = smooth((f - e.f_land + e.dur - i * (e.dur / n)) / 8);
    if (p > 0) out.push(<circle key={i} cx={x + r * Math.cos(a)} cy={y + r * Math.sin(a) * 0.6} r={5.5 * p} fill={colour(e.fill)}/>);
  }
  return <g>{out}</g>;
};
const Gauge = ({e, f}) => {
  const p = prog(f, e), x = e.x, y = e.y;
  if (p <= 0) return null;
  return <g>
    <PenLine e={e} f={f} a={[x + 410, y]} b={[x + 10, y]}/>
    {p > 0.95 && <path d={`M${x + 26} ${y - 12} L${x + 10} ${y} L${x + 26} ${y + 12}`} stroke={INK} strokeWidth={3} fill="none"/>}
    {[0, 1, 2, 3, 4].map(k => <line key={k} x1={x + 10 + 100 * k} y1={y - 8} x2={x + 10 + 100 * k} y2={y + 8} stroke={INK} strokeWidth={3} opacity={smooth(p * 5 - k)}/>)}
    <text x={x + 10} y={y + 40} fontFamily={SERIF} fontSize={28} fill={SOFT} opacity={p}>lower · tighter</text>
    <text x={x + 410} y={y + 40} fontFamily={SERIF} fontSize={28} fill={SOFT} textAnchor="end" opacity={p}>higher</text>
  </g>;
};
const Calendar = ({e, f, ev}) => {
  const x0 = e.x, y0 = e.y, c = e.c, grid = prog(f, e, 36);
  const s0 = e.f_land + 30, s1 = Math.max(s0 + 40, ev[e.cross_to_id]?.f_land ?? s0 + 100);
  const W_ = 6 * c, H_ = 5 * c, L = 2 * (W_ + H_), cells = [];
  for (let k = 0; k < 30; k++) {
    const cx = x0 + (k % 6) * c, cy = y0 + Math.floor(k / 6) * c, p = smooth((f - (s0 + (s1 - s0) * k / 30)) / 4);
    if (p > 0) cells.push(<line key={k} x1={cx + 12} y1={cy + c - 12} x2={cx + 12 + (c - 24) * p} y2={cy + c - 12 - (c - 24) * p} stroke={INK} strokeWidth={3} strokeLinecap="round"/>);
  }
  if (grid <= 0) return null;
  return <g>
    <rect x={x0} y={y0} width={W_} height={H_} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray={`${L * grid} ${L}`}/>
    {grid > 0.6 && [1, 2, 3, 4, 5].map(i => <line key={"v" + i} x1={x0 + i * c} y1={y0} x2={x0 + i * c} y2={y0 + H_ * smooth((grid - 0.6) / 0.4)} stroke={INK} strokeWidth={1.5}/>)}
    {grid > 0.6 && [1, 2, 3, 4].map(i => <line key={"h" + i} x1={x0} y1={y0 + i * c} x2={x0 + W_ * smooth((grid - 0.6) / 0.4)} y2={y0 + i * c} stroke={INK} strokeWidth={1.5}/>)}
    {cells}
  </g>;
};
const quad = (d, u) => {          // "M x0 y0 Q cx cy x1 y1"
  const n = d.match(/-?[\d.]+/g).map(Number), [x0, y0, cx, cy, x1, y1] = n, v = 1 - u;
  return [v * v * x0 + 2 * v * u * cx + u * u * x1, v * v * y0 + 2 * v * u * cy + u * u * y1];
};
const Loop = ({e, f}) => {
  const p = prog(f, e);
  if (p <= 0) return null;
  const [ex, ey] = e.end, ang = e.ang;
  return <g stroke={INK} strokeWidth={3.5} fill="none" strokeLinecap="round" strokeLinejoin="round">
    <path d={e.d} pathLength={1} strokeDasharray={`${p} 1`}/>
    {p > 0.97 && <path d={`M${ex + 20 * Math.cos(ang - 0.45)} ${ey + 20 * Math.sin(ang - 0.45)} L${ex} ${ey} L${ex + 20 * Math.cos(ang + 0.45)} ${ey + 20 * Math.sin(ang + 0.45)}`}/>}
  </g>;
};
const Bead = ({e, f, ev}) => {
  const u = (f - e.f_start) / Math.max(1, e.f_land - e.f_start);
  if (u < 0 || u > 1.4) return null;
  const [x, y] = quad(ev[e.along].d, smooth(Math.min(1, u)));
  const a = u > 1 ? 1 - (u - 1) / 0.4 : 1;
  return <circle cx={x} cy={y} r={11} fill={RED} opacity={a}/>;
};
const Pocket = ({e, f}) => {          // an ink pocket: a U in a box, drawn along its length
  const p = prog(f, e);
  if (p <= 0) return null;
  const {x, y, w, h} = e;
  const d = `M${x - w / 2} ${y - h / 2} C ${x - w / 2} ${y + h * 0.6}, ${x + w / 2} ${y + h * 0.6}, ${x + w / 2} ${y - h / 2}`;
  return <path d={d} pathLength={1} strokeDasharray={`${p} 1`} fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round"/>;
};
const MolInk = ({e, f}) => {          // a small skeletal mark for "001", dropping into the pocket
  const p = prog(f, e);
  if (p <= 0) return null;
  const x = e.x, y = e.y + 10 - 120 * (1 - p), r = 26, hex = [...Array(7)].map((_, i) => [x - 40 + r * Math.cos(Math.PI / 3 * i + Math.PI / 6), y + r * Math.sin(Math.PI / 3 * i + Math.PI / 6)]);
  return <g opacity={Math.min(1, p * 2)} stroke={INK} strokeWidth={3.5} fill="none" strokeLinejoin="round">
    <polyline points={hex.map(q => q.join(",")).join(" ")}/>
    <polyline points={`${x - 40 + r * 0.87},${y} ${x + 10},${y - 18} ${x + 38},${y} ${x + 66},${y - 18}`}/>
    <circle cx={x + 66} cy={y - 18} r={5} fill={INK}/>
  </g>;
};
const BAR = {x: 100, len: 210, max: 6000};          // stops short of the tube (x ~380 in the assay view)
const Bar = ({e, f}) => {
  const p = prog(f, e, (e.f_land - e.f_start) || 20);
  if (p <= 0) return null;
  if (e.which === 0) return <g>
    <rect x={BAR.x} y={392} width={BAR.len * p} height={28} fill={INK}/>
    {p > 0.98 && <path d={`M${BAR.x + BAR.len + 6} 406 h44 M${BAR.x + BAR.len + 38} 394 l12 12 l-12 12`} stroke={INK} strokeWidth={3} fill="none" strokeDasharray="8 6"/>}
  </g>;
  return <rect x={BAR.x} y={592} width={Math.max(8, BAR.len * 33.4 / BAR.max) * p} height={28} fill={INK}/>;
};
const KeyTurn = ({e, f, ev}) => {          // the ink key of the road map: all four steps share one drawing, so only the first draws it
  if (e.step !== 1) return null;
  const turns = Object.values(ev).filter(x => x.kind === "keyturn");
  let ang = 0;
  turns.forEach(x => { ang += 22.5 * smooth((f - x.f_land + 8) / 8); });
  const a = smooth((f - turns[0].f_land + 30) / 16);
  if (a <= 0) return null;
  const cx = 1500, cy = 380;
  return <g opacity={a} stroke={INK} strokeWidth={5} fill="none" strokeLinecap="round" strokeLinejoin="round">
    <circle cx={cx} cy={cy} r={120} strokeWidth={4}/>
    <g transform={`rotate(${ang} ${cx} ${cy})`}>
      <circle cx={cx - 70} cy={cy} r={34}/>
      <path d={`M${cx - 36} ${cy} H${cx + 80} M${cx + 50} ${cy} v22 M${cx + 72} ${cy} v16`}/>
    </g>
    <text x={cx} y={cy + 170} fontFamily={SERIF} fontSize={40} fill={INK} stroke="none" textAnchor="middle" opacity={smooth((ang - 80) / 10)}>the key turns</text>
  </g>;
};
const Road = ({e, f}) => {          // the small road map: Target, Hit, Improve, Cells & animals; Improve flares red on its beat
  const a = smooth((f - e.f_land + 40) / 16), flare = smooth((f - e.f_land) / 6), names = ["Target", "Hit", "Improve", "Cells & animals"];
  if (a <= 0) return null;
  const x0 = e.x, y = e.y, gap = 150;
  return <g opacity={a}>
    <line x1={x0} y1={y} x2={x0 + gap * 3} y2={y} stroke={INK} strokeWidth={3}/>
    <line x1={x0} y1={y} x2={x0 + gap * 2 * Math.max(0.5, flare)} y2={y} stroke={RED} strokeWidth={6}/>
    {names.map((n, i) => <g key={n}>
      <circle cx={x0 + gap * i} cy={y} r={i === 2 ? 16 + 10 * flare * (1 - smooth((f - e.f_land - 10) / 20)) + 4 * flare : 14} fill={i < 2 || (i === 2 && flare > 0.3) ? RED : BONE} stroke={INK} strokeWidth={3}/>
      <text x={x0 + gap * i} y={y + 50} fontFamily={SERIF} fontSize={28} fill={i === 2 && flare > 0.3 ? RED : INK} textAnchor="middle">{n}</text>
    </g>)}
  </g>;
};
const MiniCal = ({e, f, ev}) => {          // three pages, one flipped on each of "three", "days", "with"
  const a = prog(f, e);
  if (a <= 0) return null;
  const pages = Object.values(ev).filter(x => x.kind === "minipage");
  const n = pages.filter(x => f >= x.f_land).length;
  const flip = pages.reduce((s, x) => Math.max(s, f >= x.f_land - 8 && f < x.f_land ? (f - x.f_land + 8) / 8 : 0), 0);
  const {x, y} = e;
  return <g opacity={a}>
    <rect x={x} y={y} width={110} height={96} fill={BONE} stroke={INK} strokeWidth={3}/>
    <line x1={x} y1={y + 26} x2={x + 110} y2={y + 26} stroke={INK} strokeWidth={3}/>
    {flip > 0 && <rect x={x} y={y} width={110} height={96 * (1 - flip)} fill={BONE} stroke={INK} strokeWidth={2}/>}
    <text x={x + 55} y={y + 80} fontFamily={SERIF} fontSize={50} fill={INK} textAnchor="middle">{n === 0 ? "" : `day ${n}`.replace("day ", "")}</text>
    <text x={x + 55} y={y + 20} fontFamily={SERIF} fontSize={20} fill={SOFT} textAnchor="middle">day</text>
  </g>;
};
const Bracket = ({e, f, pts}) => {
  const p = prog(f, e), a = pts.huh7_ic, b = pts.hek_ic;
  if (p <= 0 || !a || !b) return null;
  const y = Math.max(a[1], b[1]) + 135;
  return <path d={`M${a[0]} ${y - 16} V${y} H${a[0] + (b[0] - a[0]) * p} ${p > 0.98 ? `V${y - 16}` : ""}`} stroke={RED} strokeWidth={5} fill="none" strokeLinecap="round"/>;
};

const OPACITY_OUT = 20;
const Event = ({e, f, ev, pts}) => {
  const at = e.at_pt && pts[e.at_pt];
  const x = (at ? at[0] : 0) + (e.x || 0) + (e.dx || 0), y = (at ? at[1] : 0) + (e.y || 0) + (e.dy || 0);
  const o = e.out && e.out !== "never" && ev[e.out] ? 1 - smooth((f - ev[e.out].f_land) / OPACITY_OUT) : 1;
  if (o <= 0) return null;
  let el = null;
  switch (e.kind) {
    case "ink": el = <Ink e={e} f={f} x={x} y={y}/>; break;
    case "note": el = <Note e={e} f={f} x={x} y={y}/>; break;
    case "keyed": el = <Keyed e={e} f={f} x={x} y={y}/>; break;
    case "ul": el = <Under e={e} f={f} x={x} y={y}/>; break;
    case "ring": el = <Ring e={e} f={f} x={at ? at[0] + (e.cx || 0) : e.cx} y={at ? at[1] + (e.cy || 0) : e.cy}/>; break;
    case "pen": { const a = e.from_pt ? pts[e.from_pt] : at, b = e.to_pt ? pts[e.to_pt] : at && [at[0], at[1] + 30];
      el = a && b ? <PenLine e={e} f={f} a={a} b={b}/> : null; break; }
    case "leader": el = <Leader e={e} f={f} pts={e.pts_at ? e.pts_at.map(k => pts[k]).filter(Boolean) : e.pts}/>; break;
    case "tag": el = <Tag e={e} f={f}/>; break;
    case "dots": el = <Dots e={e} f={f} x={x} y={y}/>; break;
    case "gauge": el = <Gauge e={e} f={f}/>; break;
    case "calendar": el = <Calendar e={e} f={f} ev={ev}/>; break;
    case "loop": el = <Loop e={e} f={f}/>; break;
    case "bead": el = <Bead e={e} f={f} ev={ev}/>; break;
    case "pocket": el = <Pocket e={e} f={f}/>; break;
    case "molink": el = <MolInk e={e} f={f}/>; break;
    case "bar": el = <Bar e={e} f={f}/>; break;
    case "keyturn": el = <KeyTurn e={e} f={f} ev={ev}/>; break;
    case "road": el = <Road e={e} f={f}/>; break;
    case "minical": el = <MiniCal e={e} f={f} ev={ev}/>; break;
    case "bracket": el = <Bracket e={e} f={f} pts={pts}/>; break;
    default: el = null;
  }
  return el && <g opacity={o}>{el}</g>;
};

export const Seg = ({beats, pts = {}, file, audio, fps = 30, title = "Objective 2 / Results"}) => {
  const f = useCurrentFrame() * (60 / fps);
  const ev = {};
  beats.events.forEach(e => { ev[e.id] = e; });
  beats.events.forEach(e => { if (e.kind === "calendar") e.cross_to_id = beats.events.find(x => x.word === e.cross_to)?.id; });
  const src = beats.source || [];
  let line = src[0], s0 = 0;
  src.forEach(s => { const at = s[0] === 0 ? 0 : ev[s[0]]?.f_land ?? 0; if (f >= at) { line = s; s0 = at; } });
  const so = smooth((f - s0) / 20);
  return <AbsoluteFill style={{background: BONE}}>
    {file && <OffthreadVideo src={staticFile(file)} muted style={{width: W, height: H}}/>}
    {audio && <Audio src={staticFile(audio)}/>}
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: "absolute", left: 0, top: 0}}>
      <text x={1856} y={92} fontFamily={SERIF} fontSize={40} fill={INK} textAnchor="end">{title}</text>
      <g opacity={beats.fade_end ? 1 - smooth((f - beats.fade_end) / 18) : 1}>{beats.events.map(e => <Event key={e.id} e={e} f={f} ev={ev} pts={pts}/>)}</g>
      {line && <g opacity={so}>{line.slice(1).filter(Boolean).map((s, i) => <text key={i} x={1848} y={1024 + 30 * i} fontFamily={SERIF} fontSize={24} fill={SOFT} textAnchor="end">{s}</text>)}</g>}
    </svg>
  </AbsoluteFill>;
};

const Root5d = () => <>
  <Composition id="S5D" component={Seg} durationInFrames={900} fps={30} width={W} height={H} defaultProps={{beats: {events: []}}}
    calculateMetadata={({props}) => ({durationInFrames: Math.round((props.beats.frames?.len || 1800) / (60 / (props.fps || 30))), fps: props.fps || 30})}/>
</>;
registerRoot(Root5d);
