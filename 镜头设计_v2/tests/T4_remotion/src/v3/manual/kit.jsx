// HKBU SCIE1007 课程作业的科普视频：二维说明书页共用部件（从 Manual205.jsx 提出来，第 1 章起各页共用）。
// 零件图由 镜头设计_v3/inserts/manual_parts.py 从零件库正上方图做出（<名>_c.png 平涂、<名>_l.png 线稿、meta.json 尺寸）。
import React from "react";
import {Easing, Img, staticFile, continueRender, delayRender} from "remotion";
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
export const Part = ({name, cx, cy, w, ar: arGiven, at, gate = [0.5, 1], f, wipe = 12, flood = 24, children}) => {
  // 宽高比一律按零件图实际尺寸，页面传的 ar 只在尺寸表里没有这个零件时才用
  const ar = META[name] ? META[name][0] / META[name][1] : arGiven;
  const h = w / ar;
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
    <div style={{position: "absolute", left: cx - w / 2, top: cy - h / 2, width: w, height: h, transform: `scale(${1 + bump})`}}>
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
export const Bead = ({K, f}) => {
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
