// HKBU SCIE1007 课程作业的科普视频：v2「铜版说明书页」的墨线部件与版式道具。
// 供 4-03 / 4-10 两页 import（写在 _wip 里，合并时原样搬进 src/v3/manual/）。
//
// 约定（写页面时照这个用）：
//   · 颜色只走 PAPER / INK / SOFT / RED。排线、网点一律用 INK 的透明度，不许第五种颜色。
//   · 线重三级：发丝 1.2（op .45）/ 中锋 2.4 / 主角 5.5（+ 1.6px 影子线 偏移 1.6,1.6 op .35）。
//   · 绘图类道具（CircNum / Leader / Rule / Scale / InkLock / InkKey / InkCross）返回 <g>，
//     用绝对坐标，放进页面那个 1920×1080 的 <svg> 里；排版类（Caption / Kick / Folio / Stamp）返回 div。
//   · 每个道具都吃 f（当前帧）和 at（起画帧），默认用 stroke-dashoffset 从 0 画到 1；
//     把 at 设成负数就是「一开始就印好了」（静帧样板会这么用）。
//   · 抖动是确定性的：路径按点采样后按序号加正弦偏移，同一帧渲染两次长得一模一样。
import React from "react";
import {PAPER, INK, SOFT, RED, span, ease, out} from "../kit.jsx";

const PI2 = Math.PI * 2;
const FAR = -1e4; // 默认起画帧：负数 = 第 0 帧就已经画完

// 子进度：把 0–1 的进度 q 划成 a→b 的一段。注意不能用 kit 的 span ——
// span 把分母 clamp 到 ≥1（给帧号用的），拿它跑 0–1 的子段会被压成三分之一。页面拼自己的动作时也用它。
export const seg = (q, a, b, fn = (x) => x) => (q <= a ? 0 : q >= b ? 1 : fn((q - a) / Math.max(1e-6, b - a)));

/* ───────────────────────── 手绘抖动 ───────────────────────── */

// 手绘抖动：给一串 [[x,y],...] 的采样点各加 ±amp 的确定性偏移（约 ±0.8–1.5px 的观感）。
// f 只贡献一点相位，让线在动起来时微微「呼吸」，静帧时是一张固定的手绘线。
export const wob = (f, pts, amp = 1.1) => {
  const ph = (Number.isFinite(f) ? f : 0) * 0.012;
  return pts.map(([x, y], i) => [
    x + (Math.sin(i * 7.3 + ph) * 0.72 + Math.sin(i * 2.17 + 1.9 + ph * 0.7) * 0.28) * amp,
    y + (Math.cos(i * 5.13 + 0.61 + ph) * 0.72 + Math.sin(i * 3.31 + 2.4 + ph * 0.6) * 0.28) * amp,
  ]);
};

// 点列 → 路径。采样点密，所以用 L 连也像笔画；closed 时闭合成环。
export const wobblyPath = (pts, closed = false) => {
  if (!pts || !pts.length) return "";
  let d = `M${pts[0][0].toFixed(2)},${pts[0][1].toFixed(2)}`;
  for (let i = 1; i < pts.length; i++) d += `L${pts[i][0].toFixed(2)},${pts[i][1].toFixed(2)}`;
  return closed ? d + "Z" : d;
};

/* 采样器（页面自己拼形状时用） */
export const linePts = (x1, y1, x2, y2, n) => {
  const N = n || Math.max(2, Math.round(Math.hypot(x2 - x1, y2 - y1) / 16));
  const o = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    o.push([x1 + (x2 - x1) * t, y1 + (y2 - y1) * t]);
  }
  return o;
};

export const arcPts = (cx, cy, r, a0, a1, n) => {
  const N = n || Math.max(6, Math.round((Math.abs(a1 - a0) * r) / 12));
  const o = [];
  for (let i = 0; i <= N; i++) {
    const a = a0 + (a1 - a0) * (i / N);
    o.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
  }
  return o;
};

export const roundRectPts = (x, y, w, h, r, n = 5) => {
  const o = [];
  const corner = (cx, cy, a0) => {
    for (let i = 0; i <= n; i++) {
      const a = a0 + (Math.PI / 2) * (i / n);
      o.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
    }
  };
  corner(x + w - r, y + r, -Math.PI / 2); // 右上
  corner(x + w - r, y + h - r, 0); // 右下
  corner(x + r, y + h - r, Math.PI / 2); // 左下
  corner(x + r, y + r, Math.PI); // 左上
  return o;
};

export const bezPts = (p0, p1, p2, p3, n = 18) => {
  const o = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, u = 1 - t;
    o.push([
      u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
      u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1],
    ]);
  }
  return o;
};

/* ───────────────────────── 墨线：双线墨描 ───────────────────────── */

// 双线墨描：主线 + 一条 1.6px、偏移 (1.6,1.6)、op .35 的影子线（墨吃进纸里）。
// p = 0→1 是 dashoffset 画出进度；dash 传 "18 12" 这种就是断续线（低把握用）。
export const inked = (d, w = 5.5, color = INK, op = 1, p = 1, o = {}) => {
  const {shadow = 1.6, dash, dur} = o;
  const prog = Math.max(0, Math.min(1, p));
  const draw = !dash && prog < 1;
  // 注意：pathLength=1 会把 dash 数组一起缩放，所以断续线一律不设 pathLength，进度改用透明度。
  const one = (sw, opa, extra) => (
    <path
      d={d}
      fill="none"
      stroke={color}
      strokeWidth={sw}
      opacity={dash ? opa * prog : opa}
      strokeLinecap="round"
      strokeLinejoin="round"
      pathLength={dash ? undefined : 1}
      strokeDasharray={dash || "1 1"}
      strokeDashoffset={dash ? undefined : 1 - prog}
      {...extra}
    />
  );
  return (
    <g>
      {shadow ? one(shadow, 0.35 * op, {transform: "translate(1.6,1.6)", stroke: INK}) : null}
      {one(w, op)}
    </g>
  );
};

/* ───────────────────────── 排线 / 网点 ───────────────────────── */

// 45° 排线：返回一个 <pattern>，放进 <defs>，然后 fill={`url(#${id})`}。
// gap = 线距 7，ang = 45°，op = .5，线粗 1.1（BRIEF §2）。
// 也吃 BRIEF 写的 hatch(id, path, gap, ang) 形式：第二个参数给路径时忽略它（排线靠 clipPath 裁）。
export const hatch = (id, gap = 7, ang = 45, op = 0.5) => {
  if (typeof gap === "string") {
    gap = 7;
    ang = 45;
    op = 0.5;
  }
  return (
    <pattern id={id} width={gap} height={gap} patternUnits="userSpaceOnUse" patternTransform={`rotate(${ang})`}>
      <line x1={0} y1={-0.5} x2={0} y2={gap + 0.5} stroke={INK} strokeWidth={1.1} opacity={op} />
      <line x1={gap} y1={-0.5} x2={gap} y2={gap + 0.5} stroke={INK} strokeWidth={1.1} opacity={op} />
    </pattern>
  );
};

// 直接给一块形状排线（自己带 defs 和裁切），p = 排线的浓度进度。
export const HatchPath = ({id, d, gap = 7, ang = 45, op = 0.5, p = 1}) => (
  <g>
    <defs>{hatch(id, gap, ang, op)}</defs>
    <path d={d} fill={`url(#${id})`} opacity={Math.max(0, Math.min(1, p))} stroke="none" />
  </g>
);

// 网点 CSS（只给照片插图用）：盖在零件图上，整块 op .28。
export const halftoneStyle = (pitch = 3.6, dot = 0.9, op = 0.28) => ({
  position: "absolute",
  inset: 0,
  pointerEvents: "none",
  backgroundImage: `radial-gradient(circle, rgba(31,30,28,0.85) ${dot}px, transparent ${dot + 0.15}px)`,
  backgroundSize: `${pitch}px ${pitch}px`,
  opacity: op,
});

/* ───────────────────────── 文字的「写出来」遮罩 ───────────────────────── */

const wipeStyle = (p) => {
  const q = Math.max(0, Math.min(1, p));
  if (q >= 1) return null;
  const x = -8 + 116 * q;
  const m = `linear-gradient(90deg,#000 ${x - 6}%,transparent ${x}%)`;
  return {WebkitMaskImage: m, maskImage: m};
};

/* ───────────────────────── 编号圈 + 引线 ───────────────────────── */

// 34px 空心圈（1.6px 环）+ 15px 数字，压在图形上；圈心 = (x,y)。
export const CircNum = ({n, x, y, f = 0, at = FAR, r = 17, sw = 1.6, size = 15, color = INK, bg = PAPER, dur = 12}) => {
  const p = span(f, at, at + dur, out);
  if (p <= 0) return null;
  const ring = wobblyPath(wob(f, arcPts(x, y, r, 0, PI2, 26), 0.55), true);
  return (
    <g>
      <circle cx={x} cy={y} r={r - 0.8} fill={bg} opacity={Math.min(1, p * 1.6)} />
      <path
        d={ring}
        fill="none"
        stroke={color}
        strokeWidth={sw}
        pathLength={1}
        strokeDasharray={p < 1 ? "1 1" : undefined}
        strokeDashoffset={p < 1 ? 1 - p : undefined}
      />
      <text
        x={x}
        y={y + size * 0.36}
        textAnchor="middle"
        fontFamily="Serif"
        fontSize={size}
        fill={color}
        opacity={seg(p, 0.45, 1)}
      >
        {n}
      </text>
    </g>
  );
};

// 1.2px 引线 + 端点小圆（r 2.5）。dot 落在 from（图形那头）默认。
export const Leader = ({from, to, f = 0, at = FAR, dot = true, dotAt = "from", dash, w = 1.2, color = INK, op = 0.45, dur = 14, amp = 0.6}) => {
  const p = span(f, at, at + dur, out);
  if (p <= 0) return null;
  const [x1, y1] = from, [x2, y2] = to;
  const d = wobblyPath(wob(f, linePts(x1, y1, x2, y2), amp));
  const dx = dotAt === "to" ? x2 : x1;
  const dy = dotAt === "to" ? y2 : y1;
  return (
    <g fill="none" strokeLinecap="round">
      <path d={d} stroke={color} strokeWidth={w} opacity={dash ? op * p : op} pathLength={dash ? undefined : 1}
            strokeDasharray={dash || "1 1"} strokeDashoffset={dash ? undefined : 1 - p} />
      {dot ? <circle cx={dx} cy={dy} r={2.5} fill={INK} stroke="none" opacity={seg(p, 0.8, 1)} /> : null}
    </g>
  );
};

/* ───────────────────────── 细线规矩 ───────────────────────── */

// 1.2px 发丝线，从起点画到终点（规矩线 / 页眉页脚 / 分隔）。
export const Rule = ({x1 = 96, y1 = 140, x2 = 1820, y2 = 140, f = 0, at = FAR, w = 1.2, op = 0.45, color = INK, dur = 16, dash, amp = 0.35}) => {
  const p = span(f, at, at + dur, ease);
  if (p <= 0) return null;
  const d = wobblyPath(wob(f, linePts(x1, y1, x2, y2), amp));
  return (
    <path
      d={d}
      fill="none"
      stroke={color}
      strokeWidth={w}
      opacity={dash ? op * p : op}
      strokeLinecap="round"
      pathLength={dash ? undefined : 1}
      strokeDasharray={dash || "1 1"}
      strokeDashoffset={dash ? undefined : 1 - p}
    />
  );
};

/* ───────────────────────── 刻度 / 数据条 ───────────────────────── */

// 带端刺的细线：横线 + ticks 根 6px 竖刺 + 两端长刺。不写数字。
// pointer：0–1，红色小三角指向刻度上的位置；left / right：两端小字（旁白里没这两个词就留空）。
export const Scale = ({x = 96, y = 940, w = 664, ticks = 5, f = 0, at = FAR, h = 6, color = INK, op = 0.5, dur = 18,
                      pointer, left, right, size = 18, track = 2}) => {
  const p = span(f, at, at + dur, ease);
  if (p <= 0) return null;
  const base = wobblyPath(wob(f, linePts(x, y, x + w, y), 0.35));
  const px = x + w * Math.max(0, Math.min(1, pointer == null ? 0 : pointer));
  return (
    <g strokeLinecap="round">
      <g fill="none" stroke={color} strokeWidth={1.2} opacity={op}>
        <path d={base} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
        {Array.from({length: Math.max(2, ticks)}).map((_, i) => {
          const tx = x + (w * i) / (Math.max(2, ticks) - 1);
          const end = i === 0 || i === ticks - 1;
          const q = seg(p, 0.35 + 0.5 * (i / Math.max(1, ticks - 1)), 0.62 + 0.45 * (i / Math.max(1, ticks - 1)));
          const d = end ? `M${tx},${y - h - 3}L${tx},${y + h + 3}` : `M${tx},${y}L${tx},${y - h}`;
          return <path key={i} d={d} opacity={q} />;
        })}
      </g>
      {pointer != null ? (
        <path d={`M${px - 8},${y - 30}L${px + 8},${y - 30}L${px},${y - 13}Z`} fill={RED} stroke="none" opacity={seg(p, 0.55, 1) * 0.95} />
      ) : null}
      {left ? (
        <text x={x} y={y + h + 21} fontFamily="Serif" fontSize={size} letterSpacing={track} fill={SOFT} opacity={seg(p, 0.4, 1)}>
          {String(left).toUpperCase()}
        </text>
      ) : null}
      {right ? (
        <text x={x + w} y={y + h + 21} textAnchor="end" fontFamily="Serif" fontSize={size} letterSpacing={track} fill={SOFT} opacity={seg(p, 0.4, 1)}>
          {String(right).toUpperCase()}
        </text>
      ) : null}
    </g>
  );
};

/* ───────────────────────── 小字图注 / 页眉页脚 ───────────────────────── */

// 小字图注：默认全大写 + 字距；图注抬头用 `FIG. 1 — …` 时不放大写、走 italic。
export const Caption = ({
  x, y, children, size = 20, align = "left", color = SOFT, italic = false, caps = true,
  track = 1.6, f = 0, at = FAR, width = 900, dur = 14,
}) => {
  const p = span(f, at, at + dur, ease);
  if (p <= 0) return null;
  const text = caps ? String(children).toUpperCase() : children;
  return (
    <div
      style={{
        position: "absolute",
        left: align === "center" ? x - width / 2 : x,
        top: y,
        width,
        textAlign: align,
        fontFamily: "Serif",
        fontSize: size,
        lineHeight: `${Math.round(size * 1.35)}px`,
        letterSpacing: caps ? track : 0,
        color,
        fontStyle: italic ? "italic" : "normal",
        whiteSpace: caps ? "nowrap" : "normal",
        ...(wipeStyle(p) || {}),
      }}
    >
      {text}
    </div>
  );
};

const headerItem = ({x, y, children, size, track, color, p, align}) => (
  <div
    style={{
      position: "absolute",
      left: align === "right" ? 0 : x,
      top: y - size * 0.78,
      width: align === "right" ? x : undefined,
      textAlign: align,
      fontFamily: "Serif",
      fontSize: size,
      lineHeight: 1,
      letterSpacing: track,
      color,
      whiteSpace: "nowrap",
      ...(wipeStyle(p) || {}),
    }}
  >
    {String(children).toUpperCase()}
  </div>
);

// 页眉左：kicker（18px 全大写 字距 3 SOFT），基线 y 96。
export const Kick = ({children, x = 96, y = 96, f = 0, at = FAR, size = 18, track = 3, color = SOFT, dur = 14}) => {
  const p = span(f, at, at + dur, ease);
  if (p <= 0) return null;
  return headerItem({x, y, children, size, track, color, p, align: "left"});
};

// 页眉右：folio，右对齐到 x（默认 1820），基线 y 96。
export const Folio = ({children, x = 1820, y = 96, f = 0, at = FAR, size = 18, track = 3, color = SOFT, dur = 14}) => {
  const p = span(f, at, at + dur, ease);
  if (p <= 0) return null;
  return headerItem({x, y, children, size, track, color, p, align: "right"});
};

// 页框：沿用 kit 的 <PageFrame /> 尺寸（x 40–1880，y 34–1036）。
export const PaperFrame = ({inset = "34px 40px 44px 40px", op = 0.22}) => (
  <div style={{position: "absolute", inset, border: `1.5px solid rgba(31,30,28,${op})`, borderRadius: 4}} />
);

/* ───────────────────────── 印章 ───────────────────────── */

// −6° 红框印章：3px 红框 + 30px 红字，落章用缩放（唯一允许缩放出现的元素）。
// worn：缺墨的小口子（2–3px 的纸色小方块压在框和字上，近看不至于像贴纸）。
const WORN_GAPS = [
  {left: "11%", top: -3, width: 17, height: 4, rot: -3},
  {left: "64%", top: "100%", mt: -3, width: 13, height: 4, rot: 2},
  {left: "89%", top: "30%", width: 3, height: 12, rot: 1},
  {left: "34%", top: "44%", width: 7, height: 3, rot: 7},
  {left: "72%", top: "52%", width: 4, height: 2, rot: -4},
];

export const Stamp = ({x, y, children, rot = -6, p, f = 0, at = FAR, size = 30, color = RED, track = 5, dur = 10, op = 0.92, worn = 4}) => {
  const q = p !== undefined ? Math.max(0, Math.min(1, p)) : span(f, at, at + dur, out);
  if (q <= 0) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `rotate(${rot}deg) scale(${1.18 - 0.18 * q})`,
        transformOrigin: "50% 50%",
        opacity: q * op,
        border: `3px solid ${color}`,
        padding: `${Math.round(size * 0.22)}px ${Math.round(size * 0.62)}px`,
        fontFamily: "Serif",
        fontSize: size,
        lineHeight: 1,
        letterSpacing: track,
        color,
        whiteSpace: "nowrap",
      }}
    >
      {String(children).toUpperCase()}
      {WORN_GAPS.slice(0, Math.max(0, worn)).map((g, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: g.left,
            top: g.top,
            marginTop: g.mt || 0,
            width: g.width,
            height: g.height,
            background: PAPER,
            transform: `rotate(${g.rot}deg)`,
          }}
        />
      ))}
    </div>
  );
};

/* ───────────────────────── 手绘锁 ───────────────────────── */

// 锁的几何：页面拿它来挂引注 / 引线 / 红叉，不用猜坐标。
// 锁梁：两足在 cx±ro，拱心 ay，拱顶 top；锁梁高约锁体的 0.65（手绘铜版画里的挂锁就是这个比例）。
export const lockGeo = (cx, cy, w) => {
  const bw = w, bh = w * 0.66;
  const bl = cx - bw / 2, br = cx + bw / 2;
  const bt = cy - w * 0.16, bb = bt + bh;
  const ro = w * 0.26, ri = w * 0.183, ay = bt - w * 0.175;
  const kh = {x: cx, y: bt + bh * 0.6, r: w * 0.075};
  const rivets = [0.16, 0.5, 0.84].map((k) => [bl + w * 0.11, bt + bh * k]);
  return {bw, bh, bl, br, bt, bb, ro, ri, ay, top: ay - ro, kh, rivets};
};

// 手绘锁：锁梁双弧（外 + 内）→ 锁体圆角矩形 → 实心锁孔（圆头 + 梯形槽 + 6 根放射短线）→ 三铆钉 → 右侧 45° 排线。
// 线重：主角 5.5 + 影子线；锁孔 2.4 的边；排线 1.1。
export const InkLock = ({cx = 600, cy = 520, w = 460, f = 0, at = FAR, dur = 30, rays = true, shadow = true, seam = true}) => {
  const uid = React.useId().replace(/[^a-zA-Z0-9_-]/g, "");
  const g = lockGeo(cx, cy, w);
  const p = span(f, at, at + dur, out);
  if (p <= 0) return null;
  const sub = (a, b) => seg(p, a, b);

  const outer = wobblyPath([
    ...wob(f, linePts(cx - g.ro, g.bt + 6, cx - g.ro, g.ay, 8), 1.0),
    ...wob(f, arcPts(cx, g.ay, g.ro, Math.PI, PI2, 26), 1.0),
    ...wob(f, linePts(cx + g.ro, g.ay, cx + g.ro, g.bt + 6, 8), 1.0),
  ]);
  const inner = wobblyPath([
    ...wob(f, linePts(cx - g.ri, g.bt + 2, cx - g.ri, g.ay, 7), 0.9),
    ...wob(f, arcPts(cx, g.ay, g.ri, Math.PI, PI2, 22), 0.9),
    ...wob(f, linePts(cx + g.ri, g.ay, cx + g.ri, g.bt + 2, 7), 0.9),
  ]);
  const body = wobblyPath(wob(f, roundRectPts(g.bl, g.bt, g.bw, g.bh, w * 0.085, 6), 1.2), true);

  // 锁梁这条圆管的闭合环带（外弧 + 内弧反向），排线裁在里面
  const band = wobblyPath([
    ...wob(f, linePts(cx - g.ro, g.bt, cx - g.ro, g.ay, 8), 1.0),
    ...wob(f, arcPts(cx, g.ay, g.ro, Math.PI, PI2, 26), 1.0),
    ...wob(f, linePts(cx + g.ro, g.ay, cx + g.ro, g.bt, 8), 1.0),
    [cx + g.ri, g.bt],
    ...wob(f, linePts(cx + g.ri, g.bt, cx + g.ri, g.ay, 7), 0.9),
    ...wob(f, arcPts(cx, g.ay, g.ri, PI2, Math.PI, 22), 0.9),
    ...wob(f, linePts(cx - g.ri, g.ay, cx - g.ri, g.bt, 7), 0.9),
  ], true);

  // 锁孔：圆头 + 梯形槽（槽比圆头窄，才像真正的锁孔）
  const hr = g.kh.r;
  const head = wob(f, arcPts(g.kh.x, g.kh.y, hr, 0, PI2, 22), 0.5);
  const slot = [
    [g.kh.x - hr * 0.34, g.kh.y + 2],
    [g.kh.x + hr * 0.34, g.kh.y + 2],
    [g.kh.x + hr * 0.56, g.kh.y + hr * 1.2],
    [g.kh.x - hr * 0.56, g.kh.y + hr * 1.2],
  ];
  const holeD = wobblyPath(head, true) + wobblyPath(slot, true);

  const rayAng = [-90, -35, -145, 20, 160, 180].map((a) => (a * Math.PI) / 180);
  const hp = sub(0.55, 0.85);

  return (
    <g>
      <defs>
        <clipPath id={`${uid}b`}>
          <path d={body} />
        </clipPath>
        <clipPath id={`${uid}r`}>
          <path d={`M${g.br - w * 0.3},${g.bt - 6}L${g.br + 8},${g.bt - 6}L${g.br + 8},${g.bb + 10}L${g.br - w * 0.22},${g.bb + 10}Z`} />
        </clipPath>
        <clipPath id={`${uid}s`}>
          <path d={band} />
        </clipPath>
        <clipPath id={`${uid}sr`}>
          <rect x={cx - w * 0.03} y={g.top - 12} width={g.ro + w * 0.05} height={g.bt - g.top + 20} />
        </clipPath>
      </defs>

      {/* 锁梁右侧的排线：让圆管有金属的暗面（画在轮廓下面） */}
      <g clipPath={`url(#${uid}s)`}>
        <g clipPath={`url(#${uid}sr)`}>
          <g opacity={seg(p, 0.3, 0.7) * 0.75}>
            {Array.from({length: Math.ceil((2 * g.ro + (g.bt - g.top)) / 7) + 4}).map((_, i) => {
              const h = g.bt - g.top;
              const x0 = cx - g.ro + i * 7 - h;
              return <line key={i} x1={x0} y1={g.bt + 2} x2={x0 + h + 8} y2={g.top - 6} stroke={INK} strokeWidth={1.1} opacity={0.5} />;
            })}
          </g>
        </g>
      </g>

      {/* 锁梁：外弧先画，内弧随后 */}
      <g>{inked(outer, 5.5, INK, 1, sub(0, 0.4), {shadow: shadow ? 1.6 : 0})}</g>
      <g>{inked(inner, 4.2, INK, 0.9, sub(0.05, 0.42), {shadow: 0})}</g>

      {(() => {
        const lines = Array.from({length: Math.ceil((g.bw + g.bh) / 7) + 4}).map((_, i) => {
          const x0 = g.bl + i * 7 - g.bh;
          return <line key={i} x1={x0} y1={g.bb + 2} x2={x0 + g.bh + 8} y2={g.bt - 6} stroke={INK} strokeWidth={1.1} opacity={0.5} />;
        });
        return (
          <g clipPath={`url(#${uid}b)`}>
            <g clipPath={`url(#${uid}r)`}>
              <g opacity={seg(p, 0.45, 0.9)}>{lines}</g>
            </g>
          </g>
        );
      })()}

      {/* 锁体：主角线 + 影子线 */}
      <g>{inked(body, 5.5, INK, 1, sub(0.18, 0.66), {shadow: shadow ? 1.6 : 0})}</g>

      {/* 锁梁插进锁体的两个筒口（2.4 小横线） */}
      <g opacity={seg(p, 0.42, 0.68)} stroke={INK} strokeWidth={2.4} strokeLinecap="round" fill="none">
        {[cx - g.ro, cx + g.ro].map((lx, i) => (
          <path key={i} d={wobblyPath(wob(f, linePts(lx - 15, g.bt - 2, lx + 15, g.bt - 2, 4), 0.5))} />
        ))}
      </g>

      {/* 中锋：一段接缝（只画左半边，手绘线不会一条通到底） */}
      {seam ? (
        <g opacity={seg(p, 0.55, 0.8)}>
          <path d={wobblyPath(wob(f, linePts(g.bl + 18, g.bt + g.bh * 0.22, cx - w * 0.12, g.bt + g.bh * 0.22, 10), 0.7))} stroke={INK} strokeWidth={2.4} opacity={0.5} fill="none" strokeLinecap="round" />
        </g>
      ) : null}

      {/* 锁孔：实心墨洞 + 放射短线 */}
      <g opacity={hp}>
        <path d={holeD} fill={INK} fillRule="nonzero" stroke={INK} strokeWidth={1.4} strokeLinejoin="round" />
        {rays
          ? rayAng.map((a, i) => {
              const l = 8 + (i % 3) * 2;
              const r0 = hr + 3, r1 = r0 + l;
              return (
                <line
                  key={i}
                  x1={g.kh.x + Math.cos(a) * r0}
                  y1={g.kh.y + Math.sin(a) * r0}
                  x2={g.kh.x + Math.cos(a) * r1}
                  y2={g.kh.y + Math.sin(a) * r1}
                  stroke={INK}
                  strokeWidth={2}
                  strokeLinecap="round"
                  opacity={seg(hp, 0.5, 1) * 0.85}
                />
              );
            })
          : null}
      </g>

      {/* 三铆钉：2.4 环 + 小实心点 */}
      {g.rivets.map(([rx, ry], i) => {
        const q = seg(p, 0.72 + i * 0.06, 0.9 + i * 0.06);
        if (q <= 0) return null;
        return (
          <g key={i} opacity={q}>
            <circle cx={rx} cy={ry} r={w * 0.028} fill="none" stroke={INK} strokeWidth={2.4} />
            <circle cx={rx} cy={ry} r={w * 0.009} fill={INK} />
          </g>
        );
      })}
    </g>
  );
};

/* ───────────────────────── 手绘钥匙 ───────────────────────── */

export const keyGeo = (cx, cy, w) => {
  const r = w * 0.17;
  const bx = cx - w * 0.33;
  const sw = Math.max(3, w * 0.045); // 杆宽：小尺寸给 3px 下限，w<150 不会糊成一条
  const hs = sw / 2;
  const tip = cx + w * 0.47;
  const tw = Math.max(9, w * 0.075); // 齿宽
  const th = Math.max(8, w * 0.09); // 齿高
  const lw = Math.max(2.2, Math.min(4.6, w * 0.0235)); // 线重跟着钥匙大小走
  return {
    r, bx, hs, sw, tip, lw, tw, th,
    collar: bx + r * 1.08,
    teeth: [cx + w * 0.2, cx + w * 0.35].map((x) => ({x, tw, th})),
  };
};

// 手绘钥匙：圆头（带内孔）+ 杆（双线）+ 卡圈 + 两个梯形齿，dashoffset 一段段画出来。
export const InkKey = ({cx = 1200, cy = 700, w = 200, f = 0, at = FAR, rot = 0, dur = 26, color = INK}) => {
  const k = keyGeo(cx, cy, w);
  const p = span(f, at, at + dur, out);
  if (p <= 0) return null;
  const amp = Math.max(0.3, w * 0.0045);
  const bow = wobblyPath(wob(f, arcPts(k.bx, cy, k.r, 0, PI2, 34), amp), true);
  const hole = wobblyPath(wob(f, arcPts(k.bx, cy, k.r * 0.38, 0, PI2, 18), amp * 0.7), true);
  const shaftT = wobblyPath(wob(f, linePts(k.bx + k.r * 0.9, cy - k.hs, k.tip, cy - k.hs, 12), amp * 1.2));
  const shaftB = wobblyPath(wob(f, linePts(k.bx + k.r * 0.9, cy + k.hs, k.tip, cy + k.hs, 12), amp * 1.2));
  const tipD = wobblyPath(wob(f, linePts(k.tip, cy - k.hs, k.tip, cy + k.hs, 4), amp));
  const collar = wobblyPath(wob(f, linePts(k.collar, cy - k.hs - w * 0.04, k.collar, cy + k.hs + w * 0.04, 4), amp * 0.8));
  return (
    <g transform={`rotate(${rot} ${cx} ${cy})`} fill="none" stroke={color} strokeLinecap="round" strokeLinejoin="round">
      {inked(bow, k.lw, color, 1, seg(p, 0, 0.36), {shadow: 0})}
      <path d={hole} strokeWidth={k.lw * 0.55} opacity={seg(p, 0.2, 0.5) * 0.9} />
      {inked(shaftT, k.lw, color, 1, seg(p, 0.28, 0.66), {shadow: 0})}
      {inked(shaftB, k.lw, color, 1, seg(p, 0.3, 0.66), {shadow: 0})}
      <path d={tipD} strokeWidth={k.lw} opacity={seg(p, 0.6, 0.8)} />
      <path d={collar} strokeWidth={k.lw * 0.55} opacity={seg(p, 0.5, 0.72)} />
      {k.teeth.map((t, i) => {
        const q = seg(p, 0.62 + i * 0.1, 0.85 + i * 0.1);
        const y0 = cy + k.hs, y1 = y0 + t.th;
        // 梯形齿：上宽下窄，像被锉过一刀的钥匙齿，不是方疙瘩
        const d = wobblyPath([[t.x, y0], [t.x + t.tw, y0], [t.x + t.tw * 0.76, y1], [t.x + t.tw * 0.28, y1], [t.x, y0]], true);
        return <path key={i} d={d} strokeWidth={k.lw * 0.95} strokeLinejoin="round" opacity={q} />;
      })}
    </g>
  );
};

/* ───────────────────────── 软塌的带状尾巴 ───────────────────────── */

// 四个状态的控制点（相对 anchor，s 缩放）：直挺 / 垂 / 更垂 / 横过锁孔。
export const tailPts = (state = "straight", anchor = [0, 0], s = 1) => {
  const D =
    {
      straight: [[0, 0], [76, 6], [150, 2], [222, 16]],
      droop: [[0, 0], [66, 26], [120, 80], [150, 142]],
      droop2: [[0, 0], [54, 40], [88, 112], [76, 182]],
      across: [[0, 0], [20, 140], [-80, 230], [-250, 220]],
    }[state] || [[0, 0], [66, 26], [120, 80], [150, 142]];
  return D.map(([x, y]) => [anchor[0] + x * s, anchor[1] + y * s]);
};

// 把一条贝塞尔中心线摊成带状：两侧边线 + 一条闭合的带面；越到末端越窄（软塌下去的尾巴会收梢）。
const ribbon = (pts, w, f, taper = 0.45, n = 34) => {
  const c = wob(f, bezPts(pts[0], pts[1], pts[2], pts[3], n), 0.7);
  const L = [], R = [];
  for (let i = 0; i < c.length; i++) {
    const a = c[Math.max(0, i - 1)], b = c[Math.min(c.length - 1, i + 1)];
    const dx = b[0] - a[0], dy = b[1] - a[1];
    const len = Math.hypot(dx, dy) || 1;
    const nx = -dy / len, ny = dx / len;
    const hw = (w / 2) * (1 - taper * (i / (c.length - 1)));
    L.push([c[i][0] + nx * hw, c[i][1] + ny * hw]);
    R.push([c[i][0] - nx * hw, c[i][1] - ny * hw]);
  }
  let d = `M${L[0][0].toFixed(2)},${L[0][1].toFixed(2)}`;
  for (let i = 1; i < L.length; i++) d += `L${L[i][0].toFixed(2)},${L[i][1].toFixed(2)}`;
  for (let i = R.length - 1; i >= 0; i--) d += `L${R[i][0].toFixed(2)},${R[i][1].toFixed(2)}`;
  return {L, R, D: d + "Z"};
};

// 软塌的带状尾巴：pts = 4 个控制点（用 tailPts 生成），dash 给 "18 12" 就是低把握的断续线，
// ghosts = 2 条错开 11–12px、转 2–3°、透明度 0.13 的残影（频闪式分解动作）；带面先用纸色盖住后面的线。
export const InkTail = ({pts, w = 12, f = 0, at = FAR, dur = 24, dash, ghosts = 2, color = INK, taper = 0.45}) => {
  const p = span(f, at, at + dur, out);
  if (p <= 0 || !pts || pts.length < 4) return null;
  const {L, R, D} = ribbon(pts, w, f, taper);
  const lw = Math.max(2.2, Math.min(4.6, w * 0.24)); // 边线别把带面吃光
  const lD = wobblyPath(L);
  const rD = wobblyPath(R);
  const capD = wobblyPath([L[L.length - 1], R[R.length - 1]]);
  return (
    <g>
      {Array.from({length: Math.max(0, ghosts)}).map((_, i) => {
        const dx = (i % 2 === 0 ? 1 : -1) * 12;
        const dy = (i % 2 === 0 ? -1 : 1) * 11;
        const rr = (i % 2 === 0 ? -1 : 1) * (2 + i * 0.8);
        return (
          <g
            key={i}
            opacity={0.13}
            transform={`rotate(${rr} ${pts[0][0]} ${pts[0][1]}) translate(${dx} ${dy})`}
            fill="none"
            stroke={color}
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d={lD} strokeWidth={lw * 0.65} strokeDasharray={dash || undefined} />
            <path d={rD} strokeWidth={lw * 0.65} strokeDasharray={dash || undefined} />
          </g>
        );
      })}
      {/* 带面：先用纸色盖住后面的线（铜版画里重叠的形状就是这样留白的），再压一层很淡的墨 */}
      {dash ? null : <path d={D} fill={PAPER} fillOpacity={0.94} stroke="none" />}
      {dash ? null : <path d={D} fill={color} fillOpacity={0.08 * seg(p, 0.25, 1)} stroke="none" />}
      {inked(lD, lw, color, 1, p, {shadow: 0})}
      {inked(rD, lw, color, 1, p, {shadow: 0})}
      {dash ? null : <path d={capD} fill="none" stroke={color} strokeWidth={lw} strokeLinecap="round" opacity={p} />}
    </g>
  );
};

/* ───────────────────────── 红叉 ───────────────────────── */

// 手绘红叉（锁孔上打叉那种），两笔先后划出。
export const InkCross = ({x = 600, y = 660, r = 30, rot = 0, f = 0, at = FAR, color = RED, w = 4, dur = 14}) => {
  const p = span(f, at, at + dur, out);
  if (p <= 0) return null;
  const a = wobblyPath(wob(f, linePts(x - r, y - r, x + r, y + r, 9), 1.0));
  const b = wobblyPath(wob(f, linePts(x + r, y - r, x - r, y + r, 9), 1.0));
  return (
    <g transform={`rotate(${rot} ${x} ${y})`} fill="none" stroke={color} strokeWidth={w} strokeLinecap="round">
      <path d={a} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - seg(p, 0, 0.5)} />
      <path d={b} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - seg(p, 0.5, 1)} />
    </g>
  );
};
