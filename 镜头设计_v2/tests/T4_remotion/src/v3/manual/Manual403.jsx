// HKBU SCIE1007 课程作业的科普视频：第 4 章二维说明书页 4-03 v2（铜版说明图版重做）。
// 版面按 镜头设计_v3/映射/_wip/v2_BRIEF.md + critique.md：手绘锁当主角（Part 只进网点照片插图）、
// 页眉 CH. 4 / PLATE 4-03 / 发丝规矩线 / 编号引注 / 右栏图例 / 底部把握刻度 / 三把手绘钥匙 + 第一把红杠 + 锁孔红叉。
// 红只三处：①红笔 really low confidence ②锁孔红叉 ③第一把钥匙红杠。
// 尾巴走共用件 inkkit 的 InkTail（纸色垫层 + 8% 墨面），残影关掉（ghosts=0）。
// 时间全读 keys_4-03.json（事件表 映射/events/4-03.json，24 个事件，画面全挂 E.<id>）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_4-03.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Pen, PageFrame, Source, evMap, Lens, guidePlan} from "./kit.jsx";
// 共用墨线部件：0–1 的子进度一律用它家的 seg（kit 的 span 把分母 clamp 到 ≥1，会把 (0.55,0.85) 压成三分之一）
import {InkTail, tailPts, seg} from "./_wip/inkkit.jsx";

const E = evMap(K);
const GP = guidePlan(K);   // 视线引导（11-20，替代红色料珠）：事件表 guide 字段 → resolve.py → keys.guides

/* ─────────────── 手绘底子：抖动 / 采样 / 描线 ─────────────── */
const jit = (i, seed, f) =>
  (Math.sin(i * 7.31 + seed * 3.1) * 0.55 + Math.sin(i * 2.71 + seed * 1.7) * 0.28 + Math.sin(i * 1.93 + f * 0.055 + seed) * 0.3) * 1.15;

const jd = (pts, f, seed = 0, amp = 1) =>
  pts.map(([x, y], i) => {
    const p = pts[Math.max(0, i - 1)], q = pts[Math.min(pts.length - 1, i + 1)];
    const dx = q[0] - p[0], dy = q[1] - p[1], L = Math.hypot(dx, dy) || 1;
    const a = jit(i, seed, f) * amp;
    return `${i ? "L" : "M"}${(x + (-dy / L) * a).toFixed(1)},${(y + (dx / L) * a).toFixed(1)}`;
  }).join(" ");

const arcPts = (cx, cy, r, a0, a1, step = 9) => {
  const n = Math.max(3, Math.round((Math.abs(a1 - a0) * r) / step));
  return Array.from({length: n + 1}, (_, i) => {
    const a = a0 + ((a1 - a0) * i) / n;
    return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
  });
};
const rrPts = (x, y, w, h, r, step = 11) => [
  ...arcPts(x + r, y + r, r, Math.PI, Math.PI * 1.5, step),
  ...arcPts(x + w - r, y + r, r, Math.PI * 1.5, Math.PI * 2, step),
  ...arcPts(x + w - r, y + h - r, r, 0, Math.PI * 0.5, step),
  ...arcPts(x + r, y + h - r, r, Math.PI * 0.5, Math.PI, step),
];

const Ink = ({d, w = 2.4, o = 1, p = 1, color = INK, dash}) =>
  p <= 0 ? null : (
    <path d={d} fill="none" stroke={color} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" opacity={o}
      pathLength={dash ? undefined : 1} strokeDasharray={dash || "1 1"} strokeDashoffset={dash ? undefined : 1 - p} />
  );

/* ─────────────── 版面坐标（BRIEF 第 3 节） ─────────────── */
const X0 = 96, X1 = 1820, HY = 140, FY = 1008;
const VCOL = 1252;
const BAX = 348;

// 主角：手绘锁（中心 (600,520)，宽 500）
const BX = 350, BY = 410, BW = 500, BH = 372, BRR = 26;
const SCX = 600, SCY = 340, SR1 = 128, SR2 = 104;
const KHX = 600, KHY = 545, KHR = 30;
const POCK = {x: 556, y: 650, w: 88, h: 60};
const BLK = {x: 568, y: 660, w: 64, h: 40};
const BAL = 78;

// 尾巴四态：共用件 tailPts（anchor = 锁体面右上、锁梁右足内侧；这位置让 across 那一摆正好横过锁孔）
const ROOT = [650, 444];
const TA = tailPts("straight", ROOT, 0.8);
const TB = tailPts("droop", ROOT, 1.05);
const TC = tailPts("droop2", ROOT, 1.12);
const TD = tailPts("across", ROOT, 0.82);
const mix1 = (A, B, t) => A.map((p, i) => [p[0] + (B[i][0] - p[0]) * t, p[1] + (B[i][1] - p[1]) * t]);
// 三次贝塞尔上的点（与 InkTail 带面中心线同一族，引注端点才落得准）
const bezAt = (P, t) => {
  const u = 1 - t;
  return [
    u * u * u * P[0][0] + 3 * u * u * t * P[1][0] + 3 * u * t * t * P[2][0] + t * t * t * P[3][0],
    u * u * u * P[0][1] + 3 * u * u * t * P[1][1] + 3 * u * t * t * P[2][1] + t * t * t * P[3][1],
  ];
};

const IX = 1450, IY = 350, IR = 150;
const KEYS = [[890, 868], [1070, 868], [1250, 868]], KW = 170;
const N1 = [800, 424], N2 = [830, 700], N3 = [702, 658];
const SLOT = {y: 862, x0: 890, x1: 1425};   // 钥匙的预留印位基线

// 红珠落点：每个事件落地时停在空白处，末帧停稳
const BEAD = [
  [0, 1750, 186], [E.lock.l, 1750, 186], [E.title.l, 1180, 214], [E.zoom.l, 1020, 262],
  [E.end.l, 960, 300], [E.protein.l, 860, 240], [E.floppy.l, 1120, 360], [E.tail.l, 1150, 400],
  [E.had.l, 1230, 300], [E.low.l, 1060, 745], [E.conf.l, 1200, 690], [E.model.l, 600, 852],
  [E.across.l, 1700, 560], [E.keyhole.l, 768, 300], [E.with.l, 1700, 630], [E.block.l, 1080, 560],
  [E.sitting.l, 960, 180], [E.pocket.l, 1150, 745], [E.trust.l, 1700, 690], [E.blindly.l, 200, 560],
  [E.and.l, 500, 850], [E.cut.l, 700, 970], [E.keys.l, 1470, 800], [E.blocked.l, 1750, 860],
  [E.door.l, 1755, 975], [K.len_f, 1756, 976],
];

/* ─────────────── 小部件 ─────────────── */
const Num = ({n, x, y, tx, ty, p, f}) => {
  if (p <= 0) return null;
  const dx = tx - x, dy = ty - y, L = Math.hypot(dx, dy) || 1;
  const ax = x + (dx / L) * 21, ay = y + (dy / L) * 21;
  const bp = seg(p, 0.2, 1);
  return (
    <g opacity={Math.min(1, p * 2.2)}>
      <line x1={ax} y1={ay} x2={ax + (tx - ax) * bp} y2={ay + (ty - ay) * bp} stroke={INK} strokeWidth={1.2} opacity={0.45} />
      {bp >= 0.98 && <circle cx={tx} cy={ty} r={2.5} fill={INK} stroke={PAPER} strokeWidth={1.5} opacity={0.95} />}
      <circle cx={x} cy={y} r={17} fill={PAPER} stroke={INK} strokeWidth={1.6} />
      <text x={x} y={y + 5.4} textAnchor="middle" fontSize={15} fontFamily="Serif" fill={INK}>{n}</text>
    </g>
  );
};

const InkKey = ({x, y, w, p, f, seed = 0}) => {
  if (p <= 0) return null;
  const bc = [x + 30, y + 30], br = 25, ex = x + w;
  const bow = jd(arcPts(bc[0], bc[1], br, 0, Math.PI * 2), f, seed + 1) + " Z";
  const hole = jd(arcPts(bc[0], bc[1], 9.5, 0, Math.PI * 2), f, seed + 2);
  const top = jd([[x + 50, y + 23], [x + w * 0.6, y + 23], [ex, y + 24]], f, seed + 3, 0.8);
  const bot = jd([[x + 50, y + 37], [x + w * 0.55, y + 37], [ex, y + 37]], f, seed + 4, 0.8);
  const cap = jd([[ex, y + 24], [ex + 1, y + 37]], f, seed + 5, 0.5);
  const t1 = jd([[x + w * 0.58, y + 37], [x + w * 0.58, y + 55], [x + w * 0.68, y + 55], [x + w * 0.68, y + 37]], f, seed + 6, 0.7);
  const t2 = jd([[x + w * 0.76, y + 37], [x + w * 0.76, y + 47], [x + w * 0.84, y + 47], [x + w * 0.84, y + 37]], f, seed + 7, 0.7);
  const q = (k) => seg(p, k, k + 0.22);
  return (
    <g stroke={INK} fill="none" strokeLinecap="round" strokeLinejoin="round">
      <Ink d={bow} w={2.4} p={q(0)} />
      <Ink d={hole} w={1.4} o={0.55} p={q(0.14)} />
      <Ink d={top} w={2.4} p={q(0.1)} />
      <Ink d={bot} w={2.4} p={q(0.1)} />
      <Ink d={cap} w={2.4} p={q(0.18)} />
      <Ink d={t1} w={2.4} p={q(0.24)} />
      <Ink d={t2} w={2.4} p={q(0.34)} />
    </g>
  );
};

const Stamp = ({x, y, p}) =>
  p <= 0 ? null : (
    <div style={{position: "absolute", left: x, top: y, padding: "4px 15px", border: `3px solid ${INK}`, boxSizing: "border-box",
                 color: INK, fontSize: 30, letterSpacing: 4, lineHeight: "38px", whiteSpace: "nowrap", opacity: 0.85 * Math.min(1, p * 1.8),
                 transform: `rotate(-6deg) scale(${1.24 - 0.24 * p})`, transformOrigin: "50% 50%"}}>
      BLOCKED
    </div>
  );

const Scale = ({x, y, w, ptr}) => (
  <g>
    <line x1={x} y1={y} x2={x + w} y2={y} stroke={INK} strokeWidth={1.2} opacity={0.55} />
    {[0, 0.25, 0.5, 0.75, 1].map((t, i) => (
      <line key={i} x1={x + w * t} y1={y - 7} x2={x + w * t} y2={y + 7} stroke={INK} strokeWidth={1.2} opacity={0.55} />
    ))}
    {ptr > 0 && <polygon points={`${x + w - 3},${y - 18} ${x + w + 9},${y - 3} ${x + w - 15},${y - 3}`} fill={INK} opacity={ptr} />}
  </g>
);

/* ─────────────── 页面 ─────────────── */
const Scene = () => {
  const f = useCurrentFrame();

  const titleP = span(f, E.title.s, E.title.e, ease);
  const shP = span(f, E.lock.s, E.lock.s + 20, ease);
  const bdP = span(f, E.lock.l + 4, E.lock.l + 32, ease);
  const dtP = span(f, E.lock.l + 10, E.lock.l + 34, ease);
  const zoomP = span(f, E.zoom.s, E.zoom.l + 22, ease);
  const endP = span(f, E.end.s, E.end.l + 8, out);
  const protP = span(f, E.protein.s, E.protein.l + 10, ease);
  const m1 = span(f, E.floppy.s, E.floppy.l + 12, ease);
  const m2 = span(f, E.had.s, E.had.l + 12, ease);
  const m3 = span(f, E.across.s, E.across.l + 14, Easing.inOut(Easing.cubic));
  const insP = span(f, E.floppy.s - 14, E.floppy.l + 26, ease);
  const lowP = span(f, E.low.s, E.low.l + 10, ease);
  const confP = span(f, E.conf.s, E.conf.l + 20);
  const modelP = span(f, E.model.s, E.model.l + 12, ease);
  const khP = span(f, E.keyhole.s, E.keyhole.l + 16, ease);
  const withP = span(f, E.with.s, E.with.l + 10, ease);
  const blkP = span(f, E.block.s, E.block.l + 12, out);
  const sitP = span(f, E.sitting.s, E.sitting.l + 8, ease);
  const pocketP = span(f, E.pocket.s, E.pocket.l + 10, out);
  const trustP = span(f, E.trust.s, E.trust.l + 22);
  const blindP = span(f, E.blindly.s, E.blindly.l + 14, out);
  const andP = span(f, E.and.s, E.and.l + 18, ease);
  const cutP = span(f, E.cut.s, E.cut.l + 30, ease);
  const keysP = span(f, E.keys.s, E.keys.l + 34, ease);
  const blockedP = span(f, E.blocked.s, E.blocked.l + 12, ease);
  const stampP = span(f, E.blocked.s + 3, E.blocked.l + 6, out);
  const doorP = span(f, E.door.s, E.door.l + 16);
  const flash = f >= E.blindly.s && f < E.blindly.l + 30 ? 0.5 + 0.5 * Math.cos((f - E.blindly.s) / 4) : 0;
  const halftoneO = 0.28 + 0.02 * Math.sin(f / 37);

  const tail = mix1(mix1(mix1(TA, TB, m1), TC, m2), TD, m3);
  const tDash = lowP > 0.6 ? "16 10" : undefined;
  const tailMid = bezAt(tail, 0.45);

  const shPts = [[SCX - SR1, BY + 10], ...arcPts(SCX, SCY, SR1, Math.PI, Math.PI * 2, 9), [SCX + SR1, BY + 10]];
  const innerRev = [[SCX + SR2, BY + 10], ...arcPts(SCX, SCY, SR2, Math.PI * 2, Math.PI, 9), [SCX - SR2, BY + 10]];
  const shD = jd(shPts, f, 2.2);
  const shD2 = jd(innerRev, f, 3.1);
  const bodyP = rrPts(BX, BY, BW, BH, BRR, 13);
  const bodyD = jd(bodyP, f, 4.4) + " Z";
  const bodyShadow = jd(bodyP.map(([x, y]) => [x + 1.6, y + 1.6]), f, 4.4) + " Z";
  const bevelD = jd(rrPts(BX + 12, BY + 12, BW - 24, BH - 24, BRR - 8, 14), f, 5.6) + " Z";
  // 暗面：右 1/3 竖带 + 底部一条（底带在 x>BX+336 处停住，不让它跟竖带在右下角叠成十字）
  const shadeR = jd([[BX + 336, BY - 6], [BX + 328, BY + 96], [BX + 342, BY + 208], [BX + 330, BY + 300], [BX + BW + 6, BY + BH + 6], [BX + BW + 6, BY - 6]], f, 6.6) + " Z";
  const shadeB = jd([[BX - 6, BY + BH - 48], [BX + 120, BY + BH - 42], [BX + 240, BY + BH - 50], [BX + 336, BY + BH - 44], [BX + 336, BY + BH + 6], [BX - 6, BY + BH + 6]], f, 6.9) + " Z";
  const keyP = (i) => (i === 0 ? cutP : i === 1 ? seg(keysP, 0.02, 0.62) : seg(keysP, 0.42, 1));

  return (
    <Lens plan={GP} f={f}>
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("4-03.wav")} />
      <PageFrame />

      <div style={{position: "absolute", left: X0, top: 78, fontSize: 18, letterSpacing: 2.6, color: SOFT, textTransform: "uppercase"}}>CH. 4 · AF-Q8IZL9-F1</div>
      <div style={{position: "absolute", left: X1 - 400, top: 78, width: 400, textAlign: "right", fontSize: 18, letterSpacing: 3, color: SOFT, textTransform: "uppercase"}}>PLATE 4-03</div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <defs>
          <pattern id="h7" width="7" height="7" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="7" stroke={INK} strokeWidth="1.1" opacity="0.5" />
          </pattern>
          <pattern id="h11" width="11" height="11" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">
            <line x1="0" y1="0" x2="0" y2="11" stroke={INK} strokeWidth="0.9" opacity="0.26" />
          </pattern>
          <clipPath id="bodyClip"><path d={bodyD} /></clipPath>
          <clipPath id="shadeRc"><path d={shadeR} /></clipPath>
          <clipPath id="shadeBc"><path d={shadeB} /></clipPath>
          {KEYS.map(([kx, ky], i) => (
            <clipPath key={i} id={`bow${i}`}><circle cx={kx + 30} cy={ky + 30} r={25} /></clipPath>
          ))}
        </defs>

        {/* 规矩线 */}
        <line x1={X0} y1={HY} x2={X1} y2={HY} stroke={INK} strokeWidth={1.2} opacity={0.45} />
        <line x1={X0} y1={FY} x2={X1} y2={FY} stroke={INK} strokeWidth={1.2} opacity={0.45} />
        <line x1={VCOL} y1={176} x2={VCOL} y2={790} stroke={INK} strokeWidth={1.2} opacity={0.4} />
        <line x1={BAX} y1={252} x2={BAX} y2={790} stroke={INK} strokeWidth={1.2} opacity={0.4} />
        <line x1={X0} y1={790} x2={X1} y2={790} stroke={INK} strokeWidth={1.2} opacity={0.45} />
        {/* 左栏图注的竖线（从图注顶边起，不碰标题） */}
        <line x1={126} y1={246} x2={126} y2={430} stroke={INK} strokeWidth={1.2} opacity={0.4} />
        {/* 钥匙的预留印位：基线 + 两端小刻 + ×3 角标（钥匙落地前那块也有结构） */}
        <line x1={SLOT.x0} y1={SLOT.y} x2={SLOT.x1} y2={SLOT.y} stroke={INK} strokeWidth={1.2} opacity={0.42} />
        <line x1={SLOT.x0} y1={SLOT.y - 6} x2={SLOT.x0} y2={SLOT.y + 6} stroke={INK} strokeWidth={1.2} opacity={0.42} />
        <line x1={SLOT.x1} y1={SLOT.y - 6} x2={SLOT.x1} y2={SLOT.y + 6} stroke={INK} strokeWidth={1.2} opacity={0.42} />

        {/* 锁底投影 */}
        <g opacity={seg(bdP, 0.7, 1)}>
          <path d={`M${BX + 4},${BY + BH + 2} L${BX + BW + 2},${BY + BH + 2} L${BX + BW + 32},${BY + BH + 30} L${BX + 38},${BY + BH + 30} Z`} fill="url(#h11)" />
        </g>

        {/* 锁钩：外弧 5.5 + 影子线 + 内弧 2.4 + 沿弧走的排线（右半拱 + 右腿） */}
        <Ink d={shD} w={5.5} p={shP} />
        {seg(shP, 0.5, 1) > 0 && <Ink d={jd(shPts.map(([x, y]) => [x + 1.6, y + 1.6]), f, 2.2)} w={1.6} o={0.35 * seg(shP, 0.5, 1)} />}
        <Ink d={shD2} w={2.4} p={seg(shP, 0.35, 1)} />
        {seg(shP, 0.45, 1) > 0 && (
          <g opacity={seg(shP, 0.45, 1)} stroke={INK} strokeWidth={1.2} fill="none" strokeLinecap="round">
            {Array.from({length: 15}).map((_, i) => {
              const a = Math.PI * (1.5 + 0.0315 * i);
              return (
                <path key={i} d={jd([[SCX + SR2 * Math.cos(a), SCY + SR2 * Math.sin(a)], [SCX + SR1 * Math.cos(a), SCY + SR1 * Math.sin(a)]], f, 30 + i, 0.5)}
                  opacity={0.26 + 0.026 * i} />
              );
            })}
            {Array.from({length: 7}).map((_, i) => {
              const y = SCY + 12 + i * 9;
              return <path key={`l${i}`} d={jd([[SCX + SR2 + 1.5, y], [SCX + SR1 - 1.5, y]], f, 46 + i, 0.5)} opacity={0.3} />;
            })}
          </g>
        )}

        {/* 锁体：正面留纸色，右 1/3 竖带 + 底部一条 */}
        <Ink d={bodyD} w={5.5} p={bdP} />
        {seg(bdP, 0.45, 1) > 0 && <Ink d={bodyShadow} w={1.6} o={0.35 * seg(bdP, 0.45, 1)} />}
        <g clipPath="url(#bodyClip)" opacity={seg(bdP, 0.5, 1)}>
          <g clipPath="url(#shadeRc)">
            <rect x={BX + 300} y={BY} width={BW - 300} height={BH} fill="url(#h11)" />
            <rect x={BX + 386} y={BY} width={BW - 386} height={BH} fill="url(#h7)" opacity={0.72} />
          </g>
          <g clipPath="url(#shadeBc)">
            <rect x={BX} y={BY + BH - 52} width={BW} height={52} fill="url(#h11)" opacity={0.9} />
          </g>
        </g>
        {bdP > 0.7 && <Ink d={bevelD} w={1.2} o={0.28} />}
        {[[BX + 42, BY + 48], [BX + BW - 42, BY + 48], [BX + BW / 2, BY + BH - 34]].map(([x, y], i) => (
          <g key={i} opacity={seg(dtP, i * 0.18, i * 0.18 + 0.6)}>
            <circle cx={x} cy={y} r={8} fill={PAPER} stroke={INK} strokeWidth={2.4} />
            <circle cx={x} cy={y} r={2.6} fill={INK} />
          </g>
        ))}

        {/* 锁孔：实心墨洞 + 左半 4 根放射短线 */}
        <g opacity={seg(dtP, 0.3, 1)}>
          <circle cx={KHX} cy={KHY} r={KHR} fill={INK} />
          <path d={`M${KHX - 11},${KHY + 6} L${KHX + 11},${KHY + 6} L${KHX + 5},${KHY + 80} L${KHX - 5},${KHY + 80} Z`} fill={INK} />
          <circle cx={KHX} cy={KHY} r={KHR + 4} fill="none" stroke={INK} strokeWidth={1.2} opacity={0.35} />
        </g>
        {[136, 168, 202, 232].map((a, i) => {
          const r = (a * Math.PI) / 180, l = [8, 12, 11, 9][i];
          return (
            <Ink key={i} w={2} o={0.8 * seg(khP, i * 0.07, i * 0.07 + 0.36)}
              d={`M${KHX + (KHR + 7) * Math.cos(r)},${KHY + (KHR + 7) * Math.sin(r)} L${KHX + (KHR + 7 + l) * Math.cos(r)},${KHY + (KHR + 7 + l) * Math.sin(r)}`} />
          );
        })}
        {/* 锁孔细环：INK 虚线（局部记号，不占红） */}
        <g opacity={zoomP * (0.7 + 0.3 * flash)}>
          <Ink d={jd(arcPts(KHX, KHY, BAL, 0, Math.PI * 2), f, 7.7) + " Z"} w={1.2} o={0.42} p={zoomP} dash="7 7" />
        </g>

        {/* 锁孔 → 插图：起于放大圈圆周，落在插图圆周 */}
        <g opacity={zoomP}>
          <Ink d={jd([[655, 490], [800, 470], [1000, 454], [1140, 440], [1318, 426]], f, 13.3, 0.5)} w={1.2} o={0.55} p={zoomP} />
          <Ink d={jd([[655, 600], [800, 556], [1010, 512], [1190, 490], [1362, 472]], f, 14.7, 0.5)} w={1.2} o={0.55} p={zoomP} />
          {zoomP > 0.96 && (
            <g fill={INK} opacity={0.85}>
              <circle cx={655} cy={490} r={2.5} /><circle cx={1318} cy={426} r={2.5} />
              <circle cx={655} cy={600} r={2.5} /><circle cx={1362} cy={472} r={2.5} />
            </g>
          )}
        </g>

        {/* ATP 口袋 + 积木（先画，好让尾巴的纸色垫层压在上面） */}
        <Ink d={jd(rrPts(POCK.x, POCK.y, POCK.w, POCK.h, 7), f, 12.2) + " Z"} w={2.4} p={withP} />
        {withP > 0.5 && <rect x={BLK.x - 3} y={BLK.y - 3} width={BLK.w + 6} height={BLK.h + 6} fill="none" stroke={INK} strokeWidth={1.2} strokeDasharray="6 5" opacity={0.6 * withP * (1 - blkP)} />}
        {blkP > 0 && (
          <g opacity={blkP}>
            <rect x={BLK.x} y={BLK.y + 7 * (1 - blkP) + 3 * sitP} width={BLK.w} height={BLK.h} fill={PAPER} stroke={INK} strokeWidth={2.4} />
            <rect x={BLK.x + 5} y={BLK.y + 5 + 7 * (1 - blkP) + 3 * sitP} width={BLK.w - 10} height={BLK.h - 10} fill="none" stroke={INK} strokeWidth={1.2} opacity={0.5} />
            <text x={BLK.x + BLK.w / 2} y={BLK.y + 26 + 7 * (1 - blkP) + 3 * sitP} textAnchor="middle" fontSize={15} fontFamily="Serif" fill={INK}>ATP</text>
          </g>
        )}

        {/* 尾巴：共用件 InkTail（纸色垫层 → 压 8% 墨面 → 两条边线），低把握只走断续边线 */}
        <InkTail pts={tail} w={tDash ? 18 : 13} f={f} at={E.end.s} dur={26} dash={tDash} color={INK} ghosts={0} />
        {tDash && (() => {
          // 断续模式下 InkTail 不画端头，这里补一小笔横口，别让两条边线在空气里断掉
          const a = bezAt(tail, 0.97), b = bezAt(tail, 1);
          const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1;
          return <path d={`M${b[0] - (dy / L) * 4.95},${b[1] + (dx / L) * 4.95} L${b[0] + (dy / L) * 4.95},${b[1] - (dx / L) * 4.95}`}
            stroke={INK} strokeWidth={3} strokeLinecap="round" fill="none" opacity={0.9 * endP} />;
        })()}

        {/* 编号引注 */}
        <Num n={1} x={N1[0]} y={N1[1]} tx={ROOT[0] + 3} ty={ROOT[1] + 2} p={endP} f={f} />
        <Num n={2} x={N2[0]} y={N2[1]} tx={tailMid[0]} ty={tailMid[1]} p={span(f, E.tail.s, E.tail.l + 20, out)} f={f} />
        <Num n={3} x={N3[0]} y={N3[1]} tx={POCK.x + POCK.w - 2} ty={POCK.y + 14} p={pocketP} f={f} />

        {/* 三把钥匙（坐在预留印位下面）+ 第一把上的红杠 */}
        <InkKey x={KEYS[0][0]} y={KEYS[0][1]} w={KW} p={cutP} f={f} seed={21} />
        <InkKey x={KEYS[1][0]} y={KEYS[1][1]} w={KW} p={keyP(1)} f={f} seed={31} />
        <InkKey x={KEYS[2][0]} y={KEYS[2][1]} w={KW} p={keyP(2)} f={f} seed={41} />
        {KEYS.map(([kx, ky], i) => (
          <g key={i} clipPath={`url(#bow${i})`} opacity={0.8 * keyP(i)}>
            <rect x={kx} y={ky} width={62} height={62} fill="url(#h11)" />
          </g>
        ))}
        <g opacity={Math.max(cutP, keysP)}>
          <path d={`M${KEYS[0][0] + 4},${KEYS[0][1] + 56} L${KEYS[2][0] + KW},${KEYS[2][1] + 56} L${KEYS[2][0] + KW + 12},${KEYS[2][1] + 62} L${KEYS[0][0] + 12},${KEYS[0][1] + 62} Z`} fill="url(#h11)" />
        </g>
        {blockedP > 0 && <Ink d={jd([[876, 906], [962, 900], [1070, 894]], f, 15.5, 1.3)} w={4.5} color={RED} p={seg(blockedP, 0, 0.5)} />}

        {/* 锁孔红叉 */}
        {blockedP > 0 && (
          <>
            <Ink d={jd([[KHX - 44, KHY - 46], [KHX + 40, KHY + 42]], f, 17.1, 1.2)} w={6.5} color={RED} p={seg(blockedP, 0.1, 0.58)} />
            <Ink d={jd([[KHX + 42, KHY - 46], [KHX - 42, KHY + 42]], f, 18.3, 1.2)} w={6.5} color={RED} p={seg(blockedP, 0.46, 1)} />
          </>
        )}

        {/* and：虚线箭头指向钥匙组 */}
        <g opacity={andP}>
          <Ink d={jd([[1006, 706], [968, 776], [948, 836], [942, 862]], f, 19.1, 0.8)} w={2} o={0.8} p={andP} dash="10 8" />
          {seg(andP, 0.85, 1) > 0 && (
            <g transform="translate(940 872) rotate(88)" opacity={seg(andP, 0.85, 1)}>
              <path d="M-15,-8 L0,0 L-15,8" fill="none" stroke={INK} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />
            </g>
          )}
        </g>

        <Scale x={96} y={900} w={594} ptr={lowP} />
      </svg>

      {/* 网点照片插图：Part 只在这里出现 */}
      {zoomP > 0 && (
        <div style={{position: "absolute", left: IX - IR, top: IY - IR, width: IR * 2, height: IR * 2, borderRadius: IR,
                     border: `4px solid ${INK}`, background: PAPER, boxSizing: "border-box", overflow: "hidden", opacity: Math.min(1, zoomP * 2),
                     transform: `scale(${0.95 + 0.05 * zoomP})`}}>
          <div style={{position: "absolute", left: 4, top: 4, width: IR * 2 - 16, height: IR * 2 - 16, borderRadius: IR,
                       border: `4px solid ${PAPER}`, boxSizing: "border-box", overflow: "hidden", background: "#F0ECE2"}}>
            {zoomP > 0.3 && (
              <div style={{position: "absolute", inset: 0, filter: "grayscale(1) contrast(1.15)", opacity: 0.55 + 0.42 * insP}}>
                <Part name="lock" cx={(IR * 2 - 16) / 2} cy={186} w={240} at={E.zoom.l} f={f} gate={[0.5, 0.3]} />
              </div>
            )}
            <div style={{position: "absolute", inset: 0, backgroundImage: "radial-gradient(circle, rgba(31,30,28,.85) 0.9px, transparent 1.05px)",
                         backgroundSize: "3.6px 3.6px", opacity: (0.17 + 0.11 * insP) * (halftoneO / 0.28)}} />
            <div style={{position: "absolute", inset: 0, boxShadow: "inset 0 0 26px rgba(31,30,28,0.22)"}} />
          </div>
        </div>
      )}

      {/* 标题 */}
      <div style={{position: "absolute", left: X0, top: 176, fontSize: 54, lineHeight: "60px", whiteSpace: "nowrap"}}>
        <Write p={titleP}>Look closer</Write>
      </div>

      {/* 左上两行图注 */}
      <div style={{position: "absolute", left: 148, top: 250, width: 190, fontSize: 20, fontStyle: "italic", lineHeight: "34px"}}>
        <Write p={protP}>FIG. 2 — the protein</Write>
      </div>
      <div style={{position: "absolute", left: 148, top: 290, width: 190, fontSize: 21, fontStyle: "italic", color: SOFT}}>
        <Write p={span(f, E.tail.s, E.tail.l + 14, ease)}>a floppy tail</Write>
      </div>

      {/* 左下：把握刻度 */}
      <div style={{position: "absolute", left: X0, top: 846, fontSize: 22, letterSpacing: 2, color: SOFT, textTransform: "uppercase"}}>confidence</div>
      <div style={{position: "absolute", left: X0, top: 956, fontSize: 18, letterSpacing: 2, color: SOFT}}>×1</div>

      {/* 插图图注 */}
      <div style={{position: "absolute", left: IX - 220, top: 510, width: 440, textAlign: "center", fontSize: 20, fontStyle: "italic"}}>
        <Write p={modelP}>FIG. 1 — in the model</Write>
      </div>

      {/* 右栏图例 */}
      <div style={{position: "absolute", left: 1268, top: 558, fontSize: 18, letterSpacing: 3, color: SOFT, textTransform: "uppercase"}}>Legend</div>
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <line x1={1268} y1={594} x2={1810} y2={594} stroke={INK} strokeWidth={1.2} opacity={0.45} />
        {[[1, "one end", E.end], [2, "a floppy tail", E.tail], [3, "the ATP pocket", E.pocket]].map(([n, t, ev], i) => {
          const q = span(f, ev.s, ev.s + 16, out);
          const y0 = 608 + i * 60;
          return (
            <g key={n}>
              <line x1={1268} y1={y0 + 52} x2={1810} y2={y0 + 52} stroke={INK} strokeWidth={1.2} opacity={0.18 + 0.14 * q} />
              {q > 0 && (
                <g opacity={q}>
                  <circle cx={1301} cy={y0 + 26} r={17} fill={PAPER} stroke={INK} strokeWidth={1.6} />
                  <text x={1301} y={y0 + 31.4} textAnchor="middle" fontSize={15} fontFamily="Serif" fill={INK}>{n}</text>
                  <text x={1336} y={y0 + 33} fontSize={22} fontFamily="Serif" fill={INK}>{t}</text>
                </g>
              )}
            </g>
          );
        })}
        {/* 预留印位的角标 */}
        <text x={1436} y={868} fontSize={18} letterSpacing={2} fontFamily="Serif" fill={SOFT}>×3</text>
      </svg>

      {/* 红笔（唯一红笔）：贴尾巴的软塌段 */}
      <Pen x={930} y={620} p={confP} size={34} rot={-2.5}>really low confidence</Pen>

      {/* 手记（墨色）：Trust it blindly，引线落在锁孔圆周 */}
      <Pen x={96} y={466} p={trustP + blindP * 0.001} size={36} rot={-2.5} color={INK}>Trust it blindly</Pen>
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <Ink d={jd([[330, 516], [400, 524], [470, 534], [528, 542], [566, 545]], f, 27.7, 0.6)} w={1.2} o={0.45 * trustP} p={trustP} />
        {trustP > 0.94 && <circle cx={570} cy={545} r={2.5} fill={INK} opacity={0.85} />}
      </svg>

      {/* for a blocked door */}
      <Pen x={898} y={947} p={doorP} size={30} rot={-1.5} color={INK}>for a blocked door</Pen>

      {/* 印章：右下角落章 */}
      <Stamp x={1470} y={872} p={stampP} />

      <Source p={span(f, E.title.l, E.title.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration (not to scale)</Source>
    </AbsoluteFill>
    </Lens>
  );
};

const Root = () => <Composition id="Manual403" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
