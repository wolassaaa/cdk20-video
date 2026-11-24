// HKBU SCIE1007 课程作业的科普视频：二维说明书页共用部件（从 Manual205.jsx 提出来，第 1 章起各页共用）。
// 零件图由 镜头设计_v3/inserts/manual_parts.py 从零件库正上方图做出（<名>_c.png 平涂、<名>_l.png 线稿、meta.json 尺寸）。
import React, {createContext, useContext} from "react";
import {Easing, Img, staticFile, continueRender, delayRender, getInputProps} from "remotion";
import META from "./parts_meta.json";   // 零件图真实宽高（manual_parts.py 写的 meta.json 的拷贝）

export const PAPER = "#EDE9DF", INK = "#1F1E1C", SOFT = "#6E6B63", RED = "#C8102E";
export const ease = Easing.bezier(0.33, 0, 0.2, 1);
export const out = Easing.out(Easing.cubic);
export const span = (f, a, b, fn = (x) => x) => (f <= a ? 0 : f >= b ? 1 : fn((f - a) / Math.max(1, b - a)));

const fh = typeof window !== "undefined" ? delayRender("fonts") : null;
if (typeof window !== "undefined") {
  Promise.all([["Serif", "InstrumentSerif-Regular.ttf", "normal"], ["Serif", "InstrumentSerif-Italic.ttf", "italic"], ["Hand", "Caveat.ttf", "normal"]]
    .map(([n, file, st]) => new FontFace(n, `url(${staticFile("fonts/" + file)})`, {style: st}).load().then((x) => document.fonts.add(x))))
    .then(() => continueRender(fh)).catch(() => continueRender(fh));
}

// 零件：线稿先画出（左→右），平涂色从浇口点漫开，前沿一圈亮料，长满轻微过冲
// gid：视线引导里的目标名（不给就用 name）。在 <Lens> 里、又不在 <Layer> 里时，零件自己读引导：没被点名就略虚，被点名加轮廓光和预颤。
export const Part = ({name, gid, cx, cy, w, ar: arGiven, at, gate = [0.5, 1], f, wipe = 12, flood = 24, children}) => {
  // 宽高比一律按零件图实际尺寸，页面传的 ar 只在尺寸表里没有这个零件时才用
  const ar = META[name] ? META[name][0] / META[name][1] : arGiven;
  const h = w / ar;
  const C = withDefaults(useContext(GuideCtx), useContext(LensDefaults));
  const L = C && !C.layered ? guideLook(C, [gid ?? name], at) : null;
  const ndg = L && L.nudge ? nudge(f, L.nudge.land, {dir: [gate[0] - 0.5, gate[1] - 0.5], R: Math.hypot(w, h) / 2}) + " " : "";
  const pl = span(f, at - 2, at - 2 + wipe, out);
  const pc = span(f, at + 3, at + 3 + flood, Easing.inOut(Easing.quad));
  const r = pc * 150;
  const bump = f > at + 3 + flood ? 0.028 * Math.exp(-(f - at - 3 - flood) / 5) * Math.cos((f - at - 3 - flood) / 3.2) : 0;
  const lx = -6 + 112 * pl;
  const g = `${gate[0] * 100}% ${gate[1] * 100}%`;
  const mLine = `linear-gradient(90deg,#000 ${lx - 5}%,transparent ${lx}%)`;
  const mCol = `radial-gradient(circle at ${g},#000 ${r - 6}%,transparent ${r}%)`;
  const mRing = `radial-gradient(circle at ${g},transparent ${r - 16}%,#000 ${r - 5}%,transparent ${r}%)`;
  const box = {position: "absolute", left: 0, top: 0, width: w, height: h};
  return (
    <div style={{position: "absolute", left: cx - w / 2, top: cy - h / 2, width: w, height: h, transform: `${ndg}scale(${1 + bump})`, ...(L ? L.style : null)}}>
      <Img src={staticFile(`parts/${name}_c.png`)} style={{...box, WebkitMaskImage: mCol, maskImage: mCol}} />
      {pc > 0 && pc < 1 && <Img src={staticFile(`parts/${name}_c.png`)} style={{...box, WebkitMaskImage: mRing, maskImage: mRing, filter: "brightness(1.7) saturate(0.55)"}} />}
      <Img src={staticFile(`parts/${name}_l.png`)} style={{...box, opacity: 1 - 0.55 * pc, WebkitMaskImage: mLine, maskImage: mLine}} />
      {children}
    </div>
  );
};

// 圈号：盖章一样落下
export const Tag = ({n, x, y, at, f}) => {
  const p = span(f, at, at + 6, out);
  return p <= 0 ? null : (
    <div style={{position: "absolute", left: x - 23, top: y - 23, width: 46, height: 46, borderRadius: 23, border: `2.5px solid ${INK}`, boxSizing: "border-box",
                 font: "28px/41px Serif", textAlign: "center", color: INK, opacity: p, transform: `scale(${1.25 - 0.25 * p})`, background: PAPER}}>{n}</div>
  );
};

// 手画箭头：路径描出来，箭头尖在最后长出
export const Arrow = ({d, tip, ang, a, b, f, color = INK, sw = 4, dash}) => {
  const p = span(f, a, b, ease);
  if (p <= 0) return null;
  const k = span(p, 0.8, 1);
  return (
    <g fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
      <path d={d} pathLength={1} strokeDasharray={dash ? undefined : "1 1"} strokeDashoffset={dash ? undefined : 1 - p}
            style={dash ? {strokeDasharray: dash, clipPath: `inset(0 ${100 - p * 100}% 0 0)`} : undefined} />
      <g transform={`translate(${tip[0]},${tip[1]}) rotate(${ang}) scale(${k})`}><path d="M-20,-11 L0,0 L-20,11" /></g>
    </g>
  );
};

export const Write = ({p, children, style}) => {
  const x = -8 + 116 * p;
  const m = `linear-gradient(90deg,#000 ${x - 6}%,transparent ${x}%)`;
  // 左右各留 0.3em 的遮罩余量再用负外边距抵消：斜体 d、f 之类出头的笔画不会被遮罩切掉，排版位置不变
  return <span style={{padding: "0 0.3em", margin: "0 -0.3em", ...style, WebkitMaskImage: m, maskImage: m, display: "inline-block", whiteSpace: "pre"}}>{children}</span>;
};

// 步骤框：边框一笔画出，步骤号落章
export const Step = ({n, x, y, w, h, at, f, children}) => {
  const p = span(f, at - 4, at + 30, ease);
  const s = span(f, at, at + 6, out);
  const per = 2 * (w + h);
  return (
    <div style={{position: "absolute", left: x, top: y, width: w, height: h}}>
      <svg width={w} height={h} style={{position: "absolute", overflow: "visible"}}>
        <rect x={0} y={0} width={w} height={h} rx={10} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray={per} strokeDashoffset={per * (1 - p)} opacity={0.85} />
      </svg>
      <div style={{position: "absolute", left: -2, top: -2, width: 92, height: 92, background: INK, color: PAPER, borderRadius: "10px 0 10px 0",
                   font: "78px/90px Serif", textAlign: "center", opacity: s, transform: `scale(${1.2 - 0.2 * s})`, transformOrigin: "0 0"}}>{n}</div>
      {children}
    </div>
  );
};

// 零件说明栏（导演 11-18：图要有文字配合）：说明书的零件表，圈号对上框里的圈号，跟着零件出现
export const Legend = ({x, y, w, at, rows, f}) => {
  const p = span(f, at - 4, at + 26, ease);
  return (
    <div style={{position: "absolute", left: x, top: y, width: w}}>
      <svg width={w} height={4} style={{position: "absolute", left: 0, top: 0}}>
        <path d={`M0,2 L${w},2`} stroke={INK} strokeWidth={1.5} opacity={0.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
      </svg>
      {rows.map((row, r) => (
        <div key={r} style={{position: "absolute", left: 0, top: 22 + r * 62, display: "flex", gap: 38, whiteSpace: "nowrap"}}>
          {row.map(([n, text, a]) => {
            const q = span(f, a, a + 14, out);
            return (
              <div key={n} style={{display: "flex", alignItems: "center", gap: 12, opacity: q, transform: `translateY(${8 * (1 - q)}px)`}}>
                <div style={{width: 40, height: 40, borderRadius: 20, border: `2px solid ${INK}`, boxSizing: "border-box", font: "24px/36px Serif", textAlign: "center"}}>{n}</div>
                <Write p={span(f, a + 2, a + 18)} style={{font: "32px Serif", color: INK}}>{text}</Write>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
};

// 料珠：红色小料珠沿页面走，K = [[帧, x, y], ...]，位置只由事件帧决定
export const beadAt = (K, f) => {
  for (let i = 0; i < K.length - 1; i++) {
    if (f <= K[i + 1][0]) {
      const p = span(f, K[i][0], K[i + 1][0], Easing.inOut(Easing.sin));
      const dx = K[i + 1][1] - K[i][1], dy = K[i + 1][2] - K[i][2];
      const arc = Math.sin(Math.PI * p) * Math.min(26, Math.hypot(dx, dy) * 0.08);
      const L = Math.hypot(dx, dy) || 1;
      return [K[i][1] + dx * p + (dy / L) * arc, K[i][2] + dy * p - (dx / L) * arc];
    }
  }
  return [K[K.length - 1][1], K[K.length - 1][2]];
};
// 11-20 导演：红点看久了晃眼。改为：颜色压暗压饱和；停站时几乎不动（只留约 1 px、6 秒一周的慢漂）；
// 拖尾只在移动时出现；停站约 1 秒后淡到 70% 并略缩小，不再一直抢眼。
const BEAD = "#A8423A";
const hover = (f) => [Math.sin(f / 57) * 1.0, Math.cos(f / 71) * 0.8];
const beadPos = (K, f) => { const [x, y] = beadAt(K, f), [hx, hy] = hover(f); return [x + hx, y + hy]; };
const beadSpeed = (K, f) => { const [a, b] = beadAt(K, f), [c, d] = beadAt(K, f - 1); return Math.hypot(a - c, b - d); };
const beadRest = (K, f) => { let n = 0; while (n < 60 && beadSpeed(K, f - n) < 0.3) n++; return n; };
// 11-20 导演：不要红点这类带路标记，全片去掉。保留旧实现备查，直接返回 null。
export const Bead = () => null;
const BeadOld = ({K, f}) => {
  const mv = Math.min(1, beadSpeed(K, f) / 6);
  const rest = Math.min(1, Math.max(0, (beadRest(K, f) - 30) / 30));
  const op = 1 - 0.3 * rest, r = 7 - 1 * rest;
  const [x, y] = beadPos(K, f);
  return (
    <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
      {mv > 0.02 && [...Array(10)].map((_, i) => {
        const [tx, ty] = beadPos(K, f - (10 - i) * 0.8);
        return <circle key={i} cx={tx} cy={ty} r={2 + (i / 10) * 4} fill={BEAD} opacity={mv * (0.04 + 0.025 * i)} />;
      })}
      <circle cx={x} cy={y} r={r} fill={BEAD} opacity={op} />
      <circle cx={x - r * 0.3} cy={y - r * 0.33} r={r * 0.28} fill="#fff" opacity={0.35 * op} />
    </svg>
  );
};

// 事件表：keys/<段>.json → E.id = {s, l, e}（f_start, f_land, f_end）
export const evMap = (K) => Object.fromEntries(K.events.map((e) => [e.id, {s: e.f_start, l: e.f_land, e: e.f_end}]));

// ---------------- 视线引导（替代红色料珠，设计见 镜头设计_v3/深化/05_视线引导.md，11-20）----------------
// 画面上不多出东西：说到哪个零件，别的图层先略虚、变淡，被点名的那个保持清楚并带一点轮廓光；必要时在浇口方向预颤一下；
// 远距离换场时沿页面上已有的线走一段"鼓包"。时间全从事件表来（resolve.py 写进 keys 的 guides；没有时这里按同一规则算）。
// 出片时传 --props='{"noguide":true}' 可整页关掉引导（检查脚本用它做对照，量亮度变化）。
const GDEF = {gOn: 8, pull: 18, minGap: 36, hold: 120, relax: 30, travel: 32, arrive: 4, sameGap: 120};
const G_VERBS = ["grow", "eject", "snap", "move"], SELF_PREP = ["grow", "eject", "snap"];
const ss = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : x * x * (3 - 2 * x));
const noGuide = () => { try { return !!(getInputProps() || {}).noguide; } catch (e) { return false; } };

const sidAt = (S, f) => {
  let best = null;
  for (const s of S || []) {
    if (s.f0 <= f && f <= s.f1) return s.sid;
    const d = Math.min(Math.abs(f - s.f0), Math.abs(f - s.f1));
    if (!best || d < best[0]) best = [d, s.sid];
  }
  return best ? best[1] : null;
};
// K = keys/<段>.json → [{id, target:[…], kind, gs, gon, land, gend, goff, tick, nudge, rim, ev_s, box?}]
export const guidePlan = (K, opts = {}) => {
  const P = {...GDEF, ...opts};
  if (K.guides && !opts.recompute) return K.guides.map((g) => ({...g, target: [].concat(g.target)}));
  const items = [];
  for (const e of [...K.events].sort((a, b) => a.f_land - b.f_land)) {
    const g = e.guide || {};
    const kind = g.kind || (G_VERBS.includes(e.verb) ? "focus" : "none");
    if (kind === "none" || e.obj === "footage") continue;   // 迁移来的变速锚点不是语义事件
    const tg = [].concat(g.target ?? e.obj ?? e.id), land = e.f_land;
    const gon = kind === "runner" ? land - (g.arrive ?? P.arrive) : land - (g.g_on ?? P.gOn);
    const gs = kind === "runner" ? gon - (g.travel ?? P.travel) : gon - (g.pull ?? P.pull);
    if (gs < 0) continue;
    const gend = Math.max(land, Math.min(e.f_end, land + P.hold));
    const selfprep = SELF_PREP.includes(e.verb) && land - e.f_start <= 34;
    const it = {id: e.id, target: tg, kind, gs, gon, land, gend, goff: gend + P.relax, tick: land - 4, nudge: g.nudge ?? !selfprep,
                rim: g.rim ?? true, ev_s: e.f_start, box: g.box, dist: g.dist, path: g.path, events: [e.id]};
    const p = items[items.length - 1];
    if (p) {
      if (p.target.length === tg.length && tg.every((t) => p.target.includes(t)) && gs < p.goff + P.sameGap) { p.events.push(e.id); continue; }
      if (gon - p.gon < P.minGap) {
        p.target = [...p.target, ...tg.filter((t) => !p.target.includes(t))];
        p.gend = Math.max(p.gend, gend); p.goff = p.gend + P.relax; p.events.push(e.id); continue;
      }
      const sid = sidAt(K.sentences, land);
      if ((K.sentences && items.filter((q) => sidAt(K.sentences, q.land) === sid).length >= 3) || items.filter((q) => q.gon > gon - 600).length >= 5) { p.events.push(e.id); continue; }
    }
    items.push(it);
  }
  for (let i = 0; i + 1 < items.length; i++) {
    const p = items[i], n = items[i + 1];
    if (p.goff > n.gs) { p.gend = Math.max(p.land, Math.min(p.gend, n.gs)); p.goff = Math.max(p.gend, Math.min(p.goff, n.gon)); p.handoff = n.id; }
  }
  for (const it of items) { it.goff = Math.min(it.goff, K.len_f - 1); it.gend = Math.min(it.gend, it.goff); }
  return items;
};

// 一个引导的"景深"包络（gs→gon 拉焦，gend→goff 退回）和轮廓光包络（gs 起亮，land 峰值，gend 起退）
const gEnv = (it, f) => (f < it.gs ? 0 : f < it.gon ? ss((f - it.gs) / Math.max(1, it.gon - it.gs)) : f <= it.gend ? 1 : f < it.goff ? 1 - ss((f - it.gend) / Math.max(1, it.goff - it.gend)) : 0);
const gRim = (it, f) => (!it.rim || f < it.gs ? 0 : f < it.land ? ss((f - it.gs) / Math.max(1, it.land - it.gs)) : f <= it.gend ? 1 : f < it.goff ? 1 - ss((f - it.gend) / Math.max(1, it.goff - it.gend)) : 0);

const GuideCtx = createContext(null);

// 给一组目标名（和零件自己的 at）算当前帧的样子：{style:{filter, opacity}, nudge: 正在预颤的引导项或 null, sharp, amt}
export const guideLook = (C, ids, at) => {
  if (!C || C.off) return null;
  const {plan, f} = C;
  const hit = (it) => it.target.some((t) => ids.includes(t)) || (at != null && at >= it.ev_s - 4 && at <= it.land + 4 && C.byAt);
  let tot = 0, sharp = 0, rim = 0, nud = null, last = null;
  for (const it of plan) {
    const e = gEnv(it, f), h = hit(it);
    tot += e;
    if (h) { sharp += e; rim = Math.max(rim, gRim(it, f)); if (it.nudge && f >= it.land - 6 && f <= it.land) nud = it; }
    if (it.gs <= f) last = it;
  }
  tot = Math.min(1, tot); sharp = Math.min(1, sharp);
  const amt = Math.max(0, tot - sharp);
  // 出镜段：零件等待时略虚（idle px），最近一次被点名的那个留在焦点上
  const kept = last && hit(last) ? ss((f - last.gs) / Math.max(1, last.gon - last.gs)) : 0;
  const bpx = Math.max(C.blur * amt, C.idle * (1 - kept));
  const fl = [];
  if (bpx > 0.05) fl.push(`blur(${bpx.toFixed(2)}px)`);
  if (amt > 0.002) fl.push(`saturate(${(1 - (1 - C.desat) * amt).toFixed(3)})`);
  if (rim > 0.002) fl.push(`drop-shadow(${C.rimDx}px 0 ${C.rimPx}px rgba(255,250,235,${(C.rimA * rim).toFixed(3)}))`);
  const style = {};
  if (fl.length) style.filter = fl.join(" ");
  if (amt > 0.002) style.opacity = 1 - (1 - C.dim) * amt;
  return {style, nudge: nud, sharp, amt, rim};
};

// 页面自带零件组件时（如 Manual205）用这个钩子读引导：返回 {style, nudge} 或 null
export const useGuideLook = (ids, at) => {
  const C = withDefaults(useContext(GuideCtx), useContext(LensDefaults));
  return C && !C.layered ? guideLook(C, [].concat(ids), at) : null;
};

// 页面景深：plan = guidePlan(K)。blur/dim/desat 是没被点名的图层到底时的样子（V13：模糊 ≤ 2.5 px、不透明度 ≥ 0.75、饱和度 ≥ 0.7）。
// idle：出镜段零件等待时的模糊（2–4 px）；说明书页为 0。byAt：没有 Layer 的老页面，零件按"它长出的帧落在这次引导的事件里"认领目标。
// LensDefaults：B 档 Stage（在 Lens 里面）给的默认值，Lens 自己显式传的参数优先。11-22 B 档模板加了亮托盘，没点名的图层按 0.82 变淡会透出托盘、
// 整帧变亮超过 V6 的 3%，所以 B 档 Stage 把 dim 提到 0.9（V13 的下限 0.75 不变）。
export const LensDefaults = createContext(null);
const withDefaults = (C, D) => (C && D && D.dim != null && !C.dimSet ? {...C, dim: Math.max(0.75, D.dim)} : C);
export const Lens = ({plan, f, blur = 2.2, dim, desat = 0.75, rimPx = 6, rimA = 0.9, rimDx = 0, idle = 0, byAt = false, children}) => {
  const v = {plan: plan || [], f, blur: Math.min(2.5, blur), dim: Math.max(0.75, dim ?? 0.82), dimSet: dim != null, desat: Math.max(0.7, desat), rimPx, rimA, rimDx, idle, byAt, off: noGuide()};
  return <GuideCtx.Provider value={v}>{children}</GuideCtx.Provider>;
};

// 一个图层（整页大小的绝对定位层）。exempt：标题、标签、批注、出处行，永远不虚。noDim：角标（Objective N）没被点名时不虚不淡，只保留被点名时的轮廓光。dir：预颤方向（指向浇口）。
export const Layer = ({id, exempt, noDim, dir = [0, 1], children, style}) => {
  const C = withDefaults(useContext(GuideCtx), useContext(LensDefaults));
  const L = exempt || !C ? null : guideLook(C, [].concat(id));
  let tf, org;
  if (L && L.nudge && L.nudge.box) {
    const [x, y, w, h] = L.nudge.box;
    org = `${x + w / 2}px ${y + h / 2}px`;
    tf = nudge(C.f, L.nudge.land, {dir, R: Math.hypot(w, h) / 2});
  }
  return (
    <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, ...(L ? (noDim ? (L.rim > 0.002 ? {filter: `drop-shadow(${C.rimDx}px 0 ${C.rimPx}px rgba(255,250,235,${(C.rimA * L.rim).toFixed(3)}))`} : null) : L.style) : null), transform: tf, transformOrigin: org, ...style}}>
      <GuideCtx.Provider value={C ? {...C, layered: true} : null}>{children}</GuideCtx.Provider>
    </div>
  );
};

// 浇口预颤：land−pre 到 land，沿 dir 拉出 amp 像素、转 rot 度再回来（3 帧出 3 帧回，缓入缓出）。
// R = 物体到转心的最远距离：转动会把边缘带出 R·rot 的位移，这里把转角压到总位移 ≤ 6 px（V5）。
export const nudge = (f, land, {pre = 6, amp = 4, rot = 1.2, dir = [0, 1], R = 0} = {}) => {
  if (noGuide() || f < land - pre || f > land) return "";
  const u = (f - (land - pre)) / pre, k = (1 - Math.cos(2 * Math.PI * u)) / 2;
  let [dx, dy] = dir; const n = Math.hypot(dx, dy);
  [dx, dy] = n > 1e-6 ? [dx / n, dy / n] : [0, 1];
  const r = R > 0 ? Math.min(rot, ((6 - amp - 0.5) / R) * 180 / Math.PI) : 0;
  return `translate(${(dx * amp * k).toFixed(2)}px, ${(dy * amp * k).toFixed(2)}px) rotate(${(r * k).toFixed(3)}deg)`;
};

// 走料：沿页面上已经画好的线（d）走一段比原线粗一点、颜色是原线色七成加纸色三成的"鼓包"，a 出发、b 到达，b 后 6 帧被吃掉。不画圆点，不用红色。
const mix = (c1, c2, t) => {
  const p = (c) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
  const a = p(c1), b = p(c2);
  return "#" + a.map((v, i) => Math.round(v * t + b[i] * (1 - t)).toString(16).padStart(2, "0")).join("");
};
export const RunnerPulse = ({d, a, b, f, sw = 4, color = INK, len = 0.08}) => {
  if (noGuide() || f < a || f > b + 6) return null;
  const head = span(f, a, b, Easing.inOut(Easing.sin));
  const L = len * (f > b ? 1 - (f - b) / 6 : 1) * Math.min(1, span(f, a, a + 6) + 0.25);
  const tail = Math.max(0, head - L);
  if (head - tail < 0.002) return null;
  return <path d={d} pathLength={1} fill="none" stroke={mix(color, PAPER, 0.7)} strokeWidth={sw + 2} strokeLinecap="round"
               strokeDasharray={`${(head - tail).toFixed(4)} 3`} strokeDashoffset={(-tail).toFixed(4)} />;
};

// 步骤框标题、零件旁的印字、还没讲到的步骤的虚线占位框（第 2 章起各页共用）
export const Title = ({p, children, size = 48}) => (
  <div style={{position: "absolute", left: 112, top: 14, fontSize: size, lineHeight: "64px", whiteSpace: "nowrap"}}><Write p={p}>{children}</Write></div>
);
export const Label = ({x, y, w = 260, p, children, size = 26, color = INK, italic, align = "center"}) => (
  <div style={{position: "absolute", left: align === "left" ? x : x - w / 2, top: y, width: w, textAlign: align, fontSize: size, color, fontStyle: italic ? "italic" : "normal"}}>
    <Write p={p}>{children}</Write>
  </div>
);
export const Pen = ({x, y, p, children, size = 40, rot = -4, color = RED}) => (
  <div style={{position: "absolute", left: x, top: y, font: `${size}px Hand`, color, transform: `rotate(${rot}deg)`, whiteSpace: "nowrap"}}><Write p={p}>{children}</Write></div>
);
export const Placeholder = ({x, y, w, h, show, hide}) => (
  <div style={{position: "absolute", left: x, top: y, width: w, height: h, border: "2px dashed rgba(31,30,28,0.16)", borderRadius: 10, boxSizing: "border-box", opacity: show * (1 - hide)}} />
);
export const PageFrame = () => <div style={{position: "absolute", inset: "34px 40px 44px 40px", border: "1.5px solid rgba(31,30,28,0.22)", borderRadius: 4}} />;
export const Source = ({children, p = 1}) => <div style={{position: "absolute", left: 44, top: 1046, fontSize: 17, color: SOFT, opacity: p}}>{children}</div>;
// 字牌：盖章一样落下，轻微放大回落
export const Plate = ({x, y, w, p, children, style}) => (
  <div style={{position: "absolute", left: x, top: y, width: w, textAlign: "center", opacity: p, transform: `scale(${1.08 - 0.08 * p})`, ...style}}>{children}</div>
);
