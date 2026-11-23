// HKBU SCIE1007 课程作业的科普视频：第 4 章二维说明书页 4-10 v2（铜版说明书页 / 印出来的图版）。
// v1 被否：3D 零件当主角、没有版面结构、大片空白、红失控。v2 按 映射/_wip/v2_BRIEF.md 第 6 节 4-10 重画。
//
// 版面：页眉 kicker + PLATE 4-10 + 1.2px 规矩线；标题 Docking 54px 在左上。
//   左栏 x 96–900：整片随机密度场（s1–s2 均匀铺满、四边渐隐；s5 收拢成 8 簇）→ 8,918 / 54 / 7
//                  → 7 把手绘钥匙（InkKey）。
//   右栏 x 880–1820：网点照片插图（290×190，锁的局部，灰度 + 网点）+ 图例栏 + 手绘锁（InkLock，主角）
//                  + 钥匙从左侧水平飞入（InkKey）+ 右下三行排线打分条。
// 三段主角区：s1–s2 左上密度场；s3–s4 右半（锁 / 钥匙 / 锁孔红圈 / 打分条）；s5 下半（簇 / 54 / 7 / 7 把钥匙）。
// 红三处：①红笔 too many to make ②锁孔红圈 ③7 个红点。料珠是固定件，不算红预算。
// 时间全读 keys_4-10.json（事件表 映射/events/4-10.json，26 个事件不改），画面全挂 E.<id>.s / .l / .e。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_4-10.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Pen, evMap, PageFrame, Source, Lens, guidePlan} from "./kit.jsx";
import {InkLock, InkKey, lockGeo} from "./_wip/inkkit.jsx";

const E = evMap(K);
const GP = guidePlan(K);   // 视线引导（11-20，替代红色料珠）：事件表 guide 字段 → resolve.py → keys.guides
const ink = (a) => `rgba(31,30,28,${a})`;
const comma = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
const rnd = (i, k = 0) => { const x = Math.sin(i * 12.9898 + k * 78.233) * 43758.5453; return x - Math.floor(x); };

/* ---------- 手绘抖动（和 inkkit 同一种做法：按点采样后加确定性正弦偏移） ---------- */
const shake = (pts, amp, seed, closed = false) => {
  const n = pts.length, last = n - 1;
  return pts.map(([x, y], i) => {
    const w = (Math.sin(i * 7.31 + seed) + 0.45 * Math.sin(i * 3.17 + seed * 2.1)) * amp;
    const v = (Math.cos(i * 5.77 + seed * 1.3) + 0.4 * Math.cos(i * 9.13 + seed)) * amp;
    const fade = closed ? 1 : i === 0 || i === last ? 0.25 : 1;
    return [x + w * fade, y + v * fade];
  });
};
const toPath = (pts, closed = true) =>
  "M" + pts.map(([x, y]) => `${x.toFixed(1)} ${y.toFixed(1)}`).join(" L") + (closed ? " Z" : "");
const densify = (pts, step = 12, closed = true) => {
  const out = [], n = pts.length, m = closed ? n : n - 1;
  for (let i = 0; i < m; i++) {
    const a = pts[i], b = pts[(i + 1) % n];
    const k = Math.max(1, Math.round(Math.hypot(b[0] - a[0], b[1] - a[1]) / step));
    for (let j = 0; j < k; j++) out.push([a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k]);
  }
  if (!closed) out.push(pts[n - 1]);
  return out;
};
const ellPts = (rx, ry, cx, cy, seg = 46) =>
  [...Array(seg)].map((_, i) => { const a = (i / seg) * Math.PI * 2; return [cx + Math.cos(a) * rx, cy + Math.sin(a) * ry]; });

/* ---------- 左栏：整片密度场（x 96–900 / y 216–620，四边渐隐） ---------- */
const FX0 = 96, FY0 = 216, FX1 = 1180, FY1 = 620;
const CW = [[218, 300], [404, 300], [590, 300], [776, 300], [218, 470], [404, 470], [590, 470], [776, 470]];

const FIELD = (() => {
  const out = [];
  let i = 0;
  for (let y = FY0 + 3; y <= FY1 - 3; y += 12) {
    for (let x = FX0 + 3; x <= FX1 - 3; x += 12) {
      i++;
      const px = x + (rnd(i, 1) - 0.5) * 11;
      const py = y + (rnd(i, 2) - 0.5) * 11;
      // 四边渐隐：越靠边越稀、越淡（没有硬边）
      const edge = Math.min(Math.min(px - FX0, FX1 - px) / 150, Math.min(py - FY0, FY1 - py) / 150, 1);
      if (edge <= 0.02) continue;
      // 场的尾巴：x 越往右越稀越淡，到 FX1 归零（s1–s3 右半不是空纸）
      const tail = Math.min(1, Math.max(0, (FX1 - px) / 300));
      const den = Math.pow(edge, 0.55) * (0.16 + 0.84 * Math.pow(tail, 0.7));
      if (rnd(i, 3) > 0.1 + 0.9 * den) continue;
      let ci = 0, bd = 1e9;
      CW.forEach(([cx, cy], k) => { const d = Math.hypot(px - cx, py - cy); if (d < bd) { bd = d; ci = k; } });
      out.push({i: out.length, x: px, y: py, r: 2.3 + 1.5 * rnd(i, 4), dark: 0.5 + 0.45 * rnd(i, 7), ci, d: bd,
                edge: Math.pow(edge, 1.15), tail: Math.pow(tail, 0.9), yk: (py - FY0) / (FY1 - FY0), s: rnd(i, 5)});
    }
  }
  return out;
})();
const CL = CW.map((_, k) => FIELD.filter((d) => d.ci === k));
// 收拢：簇内按叶序排紧（细点先占中心），八个团之间留缝
CL.forEach((arr, k) => {
  const order = arr.map((_, j) => j).sort((a, b) => arr[a].r - arr[b].r);
  const rot = rnd(k + 5, 7) * 6.283;
  order.forEach((j, q) => {
    const th = q * 2.39996 + rot;
    const rr = 3.35 * Math.sqrt(q + 0.55) * (0.86 + 0.14 * Math.sin(th * 3 + k * 1.7));
    arr[j].slot = q;
    arr[j].tx = CW[k][0] + Math.cos(th) * rr * 1.14 + (rnd(arr[j].i, 8) - 0.5) * 5;
    arr[j].ty = CW[k][1] + Math.sin(th) * rr * 0.96 + (rnd(arr[j].i, 9) - 0.5) * 5;
  });
});
const SHORT = new Set(FIELD.filter((d) => d.slot !== undefined).sort((a, b) => a.slot - b.slot).slice(0, 54).map((d) => d.i));
// 7 个挑出来：前 7 个簇各挑最靠心的一颗（跟旁白的 seven 对上，第 8 簇不挑）
const PICK = new Set(CL.slice(0, 7).filter((a) => a.length).map((a) => a.reduce((m, d) => (d.slot < m.slot ? d : m), a[0]).i));

/* ---------- 右栏：锁 / 钥匙 / 打分条 ---------- */
const LK = {cx: 1394, cy: 420, w: 300};
const LG = lockGeo(LK.cx, LK.cy, LK.w);            // {bl,br,bt,bb,kh,ro,ay,top}
const PB = {x: 880, y: 230, w: 290, h: 190};       // 网点照片插图
const BR = {x: 1180, w: 620, y: 700, h: 34, gap: 14};
const BARS = [0.42, 0.88, 0.6];
const KY = {cx: 1283, cy: LG.kh.y, w: 275};        // 终位：bow 左缘 1145、右缘 1239（离锁体左缘 5px），尖在锁孔右侧 18px

// 钥匙飞入轨迹：一条 1.2px 弧线，从起点弯到锁孔
const flyBez = (t) => {
  const p0 = [980, 604], p1 = [1080, 452], p2 = [1240, LG.kh.y - 4], p3 = [LG.kh.x - 30, LG.kh.y];
  const u = 1 - t;
  return [u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0],
          u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]];
};
const keyAt = (t) => { const [x, y] = flyBez(Math.min(1, t * 0.82)); return [x, y]; };

/* 手绘箭头（数字之间） */
const HandArrow = ({x1, y1, x2, y2, p, seed = 1, w = 2.4}) => {
  const pts = [...Array(9)].map((_, i) => { const t = i / 8; return [x1 + (x2 - x1) * t, y1 + (y2 - y1) * t - Math.sin(t * Math.PI) * 4]; });
  const d = toPath(shake(pts, 1.0, seed, false), false);
  const ang = (Math.atan2(y2 - y1, x2 - x1) * 180) / Math.PI;
  return (
    <g fill="none" stroke={INK} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round">
      <path d={d} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
      {p > 0.8 && <g transform={`translate(${x2},${y2}) rotate(${ang}) scale(${span(p, 0.8, 1, out)})`}><path d="M-12,-6 L0,0 L-12,6" /></g>}
    </g>
  );
};

const Scene = () => {
  const f = useCurrentFrame();

  /* 左栏 */
  const dim1 = span(f, E.many.s, E.many.l + 8, ease);
  const undim = span(f, E.similar.s, E.similar.l + 22, ease);
  const wallOp = 1 - 0.42 * dim1 * (1 - undim);
  const bandFrom = E.num.s, bandTo = E.num.s + 46;
  const bandY = FY0 + (FY1 - FY0) * span(f, bandFrom, bandTo, ease);
  const settle = span(f, E.new.s, E.new.s + 18, out);
  const drift = span(f, E.similar.s, E.similar.s + 20, ease);
  const e54 = span(f, E.n54.s, E.n54.l + 8, out);
  const pickP = span(f, E.pick.s, E.pick.l, out);
  const count = Math.round(8918 * span(f, E.num.s, E.num.l + 10, ease));
  const numOn = span(f, E.num.s - 6, E.num.s + 4, out);

  /* 右栏 */
  const lockP = span(f, E.lock.s, E.lock.l + 26, ease);
  const panelP = span(f, E.computer.s, E.computer.l + 12, ease);     // 三条柱的框：E.computer（打分的框出现）
  const boardP = span(f, E.docking.s - 4, E.docking.s + 24, ease);   // 面板外框 + 标题：E.docking 一起印出来（框架不是内容）
  const flyP = span(f, E.key.s, E.tried.l, Easing.inOut(Easing.cubic));
  const deepP = span(f, E.molecule.s, E.molecule.l + 8, Easing.inOut(Easing.cubic));
  const sitP = span(f, E.sit.s, E.sit.l + 6, Easing.inOut(Easing.cubic));
  const ringP = span(f, E.predicts.s, E.predicts.l + 6, out);
  const barsP = span(f, E.scores.s, E.scores.s + 12, out);
  const flash = f >= E.fit.l && f < E.fit.l + 40 ? 0.5 + 0.5 * Math.cos((f - E.fit.l) / 3.4) : 0;
  const insOn = span(f, E.lock.s + 22, E.lock.s + 46, out);

  // 钥匙：从左侧水平飞入，插进锁孔后再往里坐一点
  const [kx, ky] = keyAt(flyP);
  const keyX = kx + (KY.cx - kx) * flyP + 7 * deepP;
  const keyY = ky + (KY.cy - ky) * flyP;
  const keyRot = 34 * (1 - flyP) + 9 * Math.sin(Math.PI * sitP) - 5 * deepP;

  // 红珠：每个事件落地时停在空白处；末帧停稳

  return (
    <Lens plan={GP} f={f}>
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("4-10.wav")} />
      <PageFrame />

      {/* ---------- 页眉 ---------- */}
      <div style={{position: "absolute", left: 96, top: 76, fontSize: 18, letterSpacing: 3, color: SOFT, textTransform: "uppercase", whiteSpace: "nowrap"}}>
        <Write p={span(f, 2, 26)}>Tool: docking / virtual screening</Write>
      </div>
      <div style={{position: "absolute", left: 1620, top: 76, width: 200, textAlign: "right", fontSize: 18, letterSpacing: 2, color: SOFT, whiteSpace: "nowrap"}}>
        <Write p={span(f, 6, 30)}>PLATE 4-10</Write>
      </div>
      <div style={{position: "absolute", left: 96, top: 140, width: 1724, height: 1.2, background: ink(0.45)}} />
      <div style={{position: "absolute", left: 96, top: 140, width: 1.2, height: 7, background: ink(0.45)}} />
      <div style={{position: "absolute", left: 1818, top: 140, width: 1.2, height: 7, background: ink(0.45)}} />

      {/* ---------- 标题（BRIEF §4：54px 在页眉左） ---------- */}
      <div style={{position: "absolute", left: 96, top: 146, fontSize: 54, lineHeight: "60px", letterSpacing: 0.5}}>
        <Write p={span(f, E.title.s, E.title.s + 18)}>Docking</Write>
      </div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <defs>
          <pattern id="h410" patternUnits="userSpaceOnUse" width="7" height="7" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="7" stroke={INK} strokeWidth="1.25" opacity="0.8" />
          </pattern>
        </defs>

        {/* 页脚细线（BRIEF §3：y 1008，x 96→1820） */}
        <line x1={96} y1={1008} x2={1820} y2={1008} stroke={INK} strokeWidth={1.2} opacity={0.45} />

        {/* ===== 左上：整片密度场（无边框，四边渐隐） ===== */}
        <g opacity={wallOp}>
          {FIELD.map((d) => {
            const ap = span(f, E.wall.s + d.s * 8, E.wall.s + d.s * 8 + 10, out);
            if (ap <= 0) return null;
            const lit = Math.max(span(f, bandFrom + d.yk * 40, bandFrom + d.yk * 40 + 12), span(f, E.new.s + d.yk * 6, E.new.s + d.yk * 6 + 8, out));
            const dx = d.x + (d.tx - d.x) * drift, dy = d.y + (d.ty - d.y) * drift;
            const isS = SHORT.has(d.i), isP = PICK.has(d.i);
            const rise = isP ? 14 * pickP : 0;
            return (
              <g key={d.i} opacity={ap * d.edge * (1 - drift * (1 - d.tail)) * (isS ? 1 : 1 - 0.62 * e54)}>
                <circle cx={dx} cy={dy - rise} r={d.r} fill={isP && pickP > 0.15 ? RED : INK}
                        fillOpacity={isP && pickP > 0.15 ? 0.45 + 0.55 * pickP : d.dark * (0.82 + 0.18 * lit)} />
                {isP && pickP > 0.05 && <circle cx={dx} cy={dy - rise} r={d.r + 6} fill="none" stroke={INK} strokeWidth={2.4} opacity={0.9 * pickP} />}
              </g>
            );
          })}
          {/* 波带：一条 30px 亮带从上往下扫，上沿 2px 实线 */}
          {f > bandFrom && f < bandTo && (
            <g>
              <rect x={FX0} y={FY0} width={FX1 - FX0} height={Math.max(0, bandY - FY0)} fill={ink(0.04)} />
              <line x1={FX0} y1={bandY} x2={FX1} y2={bandY} stroke={INK} strokeWidth={2} opacity={0.5} />
            </g>
          )}
        </g>

        {/* 8 个手绘抖动椭圆（簇心）；s5 之前先以细虚线占 8 个位置 */}
        {CW.map(([cx, cy], i) => {
          const p = span(f, E.grouped.s + i * 0.8, E.grouped.s + i * 0.8 + 8, ease);
          const ghost = span(f, E.fit.l + 6 + i * 3, E.fit.l + 32 + i * 3, ease);
          if (p <= 0 && ghost <= 0) return null;
          const d = toPath(shake(densify(ellPts(63, 57, cx, cy), 9), 1.35, i * 2.7 + 1), true);
          return (
            <g key={i}>
              {ghost > 0 && p <= 0 && <path d={d} fill="none" stroke={INK} strokeWidth={1.2} opacity={0.3 * ghost} strokeDasharray="7 9" />}
              <path d={d} fill="none" stroke={INK} strokeWidth={2.6} opacity={0.72 * p} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
            </g>
          );
        })}

        {/* ===== 手绘锁（主角，inkkit） ===== */}
        <InkLock cx={LK.cx} cy={LK.cy} w={LK.w} f={f} at={E.lock.s} dur={14} />

        {/* ===== 钥匙飞入的 1.2px 弧线 + 8px 箭头 ===== */}
        {span(f, E.key.s - 8, E.key.s + 10, out) > 0 && (
          <g opacity={span(f, E.key.s - 8, E.key.s + 10, out) * (1 - span(f, E.tried.l - 4, E.tried.l + 22, ease))} fill="none" stroke={INK} strokeLinecap="round" strokeLinejoin="round">
            <path d={toPath([...Array(24)].map((_, i) => flyBez(i / 23)), false)}
                  strokeWidth={1.2} strokeDasharray="6 7" opacity={0.5} />
            <g transform={`translate(${flyBez(1)[0]},${flyBez(1)[1]}) rotate(6)`}>
              <path d="M-8,-4.5 L0,0 L-8,4.5" strokeWidth={1.6} opacity={0.6} />
            </g>
            <circle cx={flyBez(0)[0]} cy={flyBez(0)[1]} r={4.5} strokeWidth={1.2} opacity={0.5} />
          </g>
        )}

        {/* ===== 钥匙（inkkit）：终位 bow 在 x≈1150、杆穿锁孔、尖在锁孔右侧露出 ===== */}
        {f >= E.key.s && (
          <InkKey cx={keyX} cy={keyY} w={KY.w} rot={keyRot} f={f} at={E.key.s} dur={22} />
        )}

        {/* ===== 锁孔红圈（the pocket）—— 红 2/3 ===== */}
        {ringP > 0 && (
          <circle cx={LG.kh.x} cy={LG.kh.y} r={42 + 10 * (1 - ringP)} fill="none" stroke={RED} strokeWidth={3} strokeDasharray="9 6" opacity={ringP} />
        )}

        {/* ===== 打分块：左规矩线 + 上/下规矩线 + 三条 2px 直角框 + 45° 排线 ===== */}
        <g>
          {boardP > 0 && (
            <g opacity={boardP}>
              <line x1={BR.x} y1={620} x2={1800} y2={620} stroke={INK} strokeWidth={1.2} opacity={0.42} />
              <line x1={BR.x} y1={862} x2={1800} y2={862} stroke={INK} strokeWidth={1.2} opacity={0.42} />
              <line x1={BR.x} y1={620} x2={BR.x} y2={862} stroke={INK} strokeWidth={1.2} opacity={0.42} />
              <line x1={1800} y1={620} x2={1800} y2={862} stroke={INK} strokeWidth={1.2} opacity={0.26} />
            </g>
          )}
          {BARS.map((v, i) => {
            const y = BR.y + i * (BR.h + BR.gap);
            const g = span(barsP, i * 0.16, i * 0.16 + 0.62, ease);
            return (
              <g key={i}>
                <rect x={BR.x + 40} y={y} width={BR.w - 40} height={BR.h} fill="none" stroke={INK} strokeWidth={2}
                      pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(panelP, i * 0.14, i * 0.14 + 0.7, ease)} />
                {g > 0 && (
                  <g opacity={0.85 + 0.15 * flash}>
                    <rect x={BR.x + 44} y={y + 4} width={(BR.w - 48) * v * g} height={BR.h - 8} fill="url(#h410)" />
                  </g>
                )}
                {flash > 0.02 && <rect x={BR.x + 40} y={y} width={BR.w - 40} height={BR.h} fill={INK} opacity={0.05 * flash} />}
              </g>
            );
          })}
          {/* 条下刻度：端刺 + 中间小刺（挂在 862 那条基线上） */}
          {[0, 0.25, 0.5, 0.75, 1].map((t, i) => (
            <line key={i} x1={BR.x + 40 + (BR.w - 40) * t} y1={848 - (i === 0 || i === 4 ? 7 : 0)} x2={BR.x + 40 + (BR.w - 40) * t} y2={862}
                  stroke={INK} strokeWidth={1.2} opacity={0.45 * span(panelP, 0.25, 1)} />
          ))}
        </g>

        {/* ===== 数字之间的手绘箭头 ===== */}
        {span(f, E.n54.s - 6, E.n54.s + 14, ease) > 0 && <HandArrow x1={346} y1={712} x2={418} y2={712} p={span(f, E.n54.s - 6, E.n54.s + 14, ease)} seed={1.4} />}
        {span(f, E.seven.s - 4, E.seven.s + 16, ease) > 0 && <HandArrow x1={528} y1={712} x2={584} y2={712} p={span(f, E.seven.s - 4, E.seven.s + 16, ease)} seed={3.8} />}

        {/* 1.2px 竖分隔线 */}
        {[[430, span(f, E.n54.s, E.n54.l)], [594, span(f, E.seven.s, E.seven.l)]].map(([x, p], i) => (
          <line key={i} x1={x} y1={672} x2={x} y2={672 + 122 * p} stroke={INK} strokeWidth={1.2} opacity={0.45} />
        ))}

        {/* ===== 钥匙座：一条基线 + 7 根刻线，s5 之前就在 ===== */}
        {span(f, 200, 248, ease) > 0 && (
          <g opacity={span(f, 200, 248, ease)}>
            <line x1={96} y1={828} x2={96 + 762 * span(f, 200, 248, ease)} y2={828} stroke={INK} strokeWidth={1.2} opacity={0.42} />
            {[...Array(7)].map((_, i) => (
              <line key={i} x1={96 + i * 112 + 45} y1={828} x2={96 + i * 112 + 45} y2={819} stroke={INK} strokeWidth={1.2} opacity={0.42} />
            ))}
          </g>
        )}

        {/* ===== 7 把手绘钥匙（一把一把画出来） ===== */}
        {[...Array(7)].map((_, i) => {
          const at = E.seven.s + i * 2;
          if (f < at) return null;
          return <InkKey key={i} cx={96 + i * 112 + 50} cy={852} w={100} f={f} at={at} dur={8} />;
        })}

        {/* 8,918 左侧小刻度（让大数字像图版上的数据） */}
        {[...Array(6)].map((_, i) => {
          const p = span(f, E.num.s - 8 + i * 2, E.num.s + 2 + i * 2, ease);
          return <line key={i} x1={104} y1={682 + i * 16} x2={104 + (i % 2 ? 6 : 11) * p} y2={682 + i * 16} stroke={INK} strokeWidth={1.2} opacity={0.5} />;
        })}

        {/* ===== 编号引注：短引线 + 图形那头的实心点 ===== */}
        {span(f, E.vlock.l, E.vlock.l + 12, out) > 0 && (
          <g opacity={span(f, E.vlock.l, E.vlock.l + 12, out)}>
            <line x1={1582} y1={390} x2={LG.br + 4} y2={390} stroke={INK} strokeWidth={1.2} opacity={0.6} />
            <circle cx={LG.br + 2} cy={390} r={2.5} fill={INK} opacity={0.7} />
          </g>
        )}
        {span(f, E.pocket.l, E.pocket.l + 10, out) > 0 && (
          <g opacity={span(f, E.pocket.l, E.pocket.l + 10, out)}>
            <line x1={1444} y1={530} x2={1416} y2={516} stroke={INK} strokeWidth={1.2} opacity={0.6} />
            <circle cx={1414} cy={514} r={2.5} fill={INK} opacity={0.7} />
          </g>
        )}
        {span(f, E.scores.l, E.scores.l + 10, out) > 0 && (
          <g opacity={span(f, E.scores.l, E.scores.l + 10, out)}>
            <line x1={1150} y1={717} x2={1218} y2={717} stroke={INK} strokeWidth={1.2} opacity={0.6} />
            <circle cx={1220} cy={717} r={2.5} fill={INK} opacity={0.7} />
          </g>
        )}
      </svg>

      {/* ---------- 数字层：8,918 → 54 → 7（三个一样重） ---------- */}
      <div style={{position: "absolute", left: 122, top: 668, fontSize: 92, lineHeight: "92px", letterSpacing: -1, opacity: numOn}}>
        {numOn > 0 && <Write p={numOn}>{comma(count)}</Write>}
      </div>
      {span(f, E.n54.s, E.n54.l + 6) > 0 && (
        <div style={{position: "absolute", left: 442, top: 668, fontSize: 72, lineHeight: "92px"}}><Write p={span(f, E.n54.s, E.n54.l + 6, out)}>54</Write></div>
      )}
      {span(f, E.seven.s, E.seven.l + 6) > 0 && (
        <div style={{position: "absolute", left: 604, top: 668, fontSize: 72, lineHeight: "92px"}}><Write p={span(f, E.seven.s, E.seven.l + 6, out)}>7</Write></div>
      )}
      <div style={{position: "absolute", left: 122, top: 762, width: 206, height: 1.2, background: ink(0.5), transform: `scaleX(${span(f, E.num.l, E.num.l + 16, out)})`, transformOrigin: "0 50%"}} />
      <div style={{position: "absolute", left: 442, top: 762, width: 70, height: 1.2, background: ink(0.5), transform: `scaleX(${span(f, E.n54.s + 8, E.n54.l, out)})`, transformOrigin: "0 50%"}} />
      <div style={{position: "absolute", left: 604, top: 762, width: 36, height: 1.2, background: ink(0.5), transform: `scaleX(${span(f, E.seven.s + 8, E.seven.l, out)})`, transformOrigin: "0 50%"}} />

      <div style={{position: "absolute", left: 122, top: 778, width: 230, fontSize: 22, whiteSpace: "nowrap"}}><Write p={span(f, E.designs.s, E.designs.l + 12)}>brand-new designs</Write></div>
      <div style={{position: "absolute", left: 442, top: 778, width: 180, fontSize: 22, whiteSpace: "nowrap"}}><Write p={span(f, E.shortlist.s, E.shortlist.s + 18)}>the shortlist</Write></div>
      <div style={{position: "absolute", left: 604, top: 778, width: 140, fontSize: 22, whiteSpace: "nowrap"}}><Write p={span(f, E.tomake.s, E.tomake.s + 12)}>to make</Write></div>

      {/* 小字图注 */}
      <div style={{position: "absolute", left: 96, top: 628, width: 300, fontSize: 18, fontStyle: "italic", color: SOFT, whiteSpace: "nowrap"}}>
        <Write p={span(f, E.wall.l, E.wall.l + 20)}>the wall</Write>
      </div>
      <div style={{position: "absolute", left: 96, top: 892, width: 480, fontSize: 18, fontStyle: "italic", color: SOFT, whiteSpace: "nowrap"}}>
        <Write p={span(f, 260, 278)}>FIG. 2 — the funnel</Write>
      </div>

      {/* 红笔：too many to make（红 1/3，压在点阵场左下方，不压点和数字） */}
      <Pen x={104} y={548} p={span(f, E.make.s, E.make.s + 12)} size={36} rot={-4}>too many to make</Pen>

      {/* ---------- 右栏文字 ---------- */}
      <div style={{position: "absolute", left: 880, top: 432, width: 290, fontSize: 19, fontStyle: "italic", color: SOFT, textAlign: "center", whiteSpace: "nowrap", background: PAPER}}>
        <Write p={span(f, E.lock.s + 4, E.lock.s + 18)}>FIG. 1 — docking</Write>
      </div>

      {/* 图例栏：编号圈 + 文字 + 行下 1.2px 细线 */}
      {[["1", "a virtual lock", E.vlock.l, 486], ["2", "the pocket", E.pocket.l, 524], ["3", "the fit", E.fit.l, 562]].map(([n, tx, at, y]) => {
        const p = span(f, at, at + 14, out);
        if (p <= 0) return null;
        return (
          <div key={n} style={{position: "absolute", left: 900, top: y, width: 240, opacity: p}}>
            <div style={{position: "absolute", left: 0, top: 0, width: 30, height: 30, borderRadius: 15, border: `1.6px solid ${INK}`, boxSizing: "border-box",
                         font: "14px/27px Serif", textAlign: "center"}}>{n}</div>
            <div style={{position: "absolute", left: 44, top: 3, width: 220, fontSize: 20, whiteSpace: "nowrap"}}><Write p={span(f, at, at + 10)}>{tx}</Write></div>
            <div style={{position: "absolute", left: 0, top: 36, width: 240, height: 1.2, background: ink(0.35)}} />
          </div>
        );
      })}

      {/* 压在图形上的编号圈 */}
      {[["1", 1584, 374, E.vlock.l], ["2", 1446, 514, E.pocket.l], ["3", 1128, 701, E.scores.l]].map(([n, x, y, at]) => {
        const p = span(f, at, at + 12, out);
        if (p <= 0) return null;
        return (
          <div key={n} style={{position: "absolute", left: x, top: y, width: 30, height: 30, borderRadius: 15, border: `1.6px solid ${INK}`,
                               boxSizing: "border-box", background: PAPER, font: "14px/27px Serif", textAlign: "center", opacity: p,
                               transform: `scale(${1.2 - 0.2 * p})`}}>{n}</div>
        );
      })}

      {/* 网点照片插图：290×190 直角框，4px INK 边 + 4px 纸色内衬 + 灰度的锁局部 + 网点 */}
      <div style={{position: "absolute", left: PB.x, top: PB.y, width: PB.w, height: PB.h, border: `4px solid ${INK}`, boxSizing: "border-box",
                   background: PAPER, opacity: span(f, E.lock.s - 10, E.lock.s + 16, out), transform: `scale(${0.94 + 0.06 * span(f, E.lock.s - 10, E.lock.s + 26, out)})`}}>
        <div style={{position: "absolute", inset: 4, overflow: "hidden", background: PAPER}}>
          <div style={{position: "absolute", inset: 0, filter: "grayscale(1) contrast(0.88) brightness(1.22)", opacity: 0.82}}>
            {insOn > 0 && <Part name="lock" cx={PB.w / 2 + 4} cy={PB.h / 2 + 16} w={148} at={E.lock.s + 24} f={f} gate={[0.5, 0.45]} />}
          </div>
          <div style={{position: "absolute", inset: 0, opacity: 0.16 + 0.22 * insOn,
                       backgroundImage: "radial-gradient(circle, rgba(31,30,28,.85) 0.9px, transparent 1.05px)", backgroundSize: "3.6px 3.6px"}} />
        </div>
      </div>

      {/* 照片插图右缘的刻度 + 角标 */}
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <g opacity={span(f, E.lock.s - 4, E.lock.s + 22, out)}>
          <line x1={1176} y1={PB.y + 4} x2={1176} y2={PB.y + PB.h - 4} stroke={INK} strokeWidth={1.2} opacity={0.4} />
          {[...Array(9)].map((_, i) => (
            <line key={i} x1={1176} y1={PB.y + 4 + i * ((PB.h - 8) / 8)} x2={1176 + (i % 4 === 0 ? 11 : 6)} y2={PB.y + 4 + i * ((PB.h - 8) / 8)}
                  stroke={INK} strokeWidth={1.2} opacity={0.4} />
          ))}
        </g>
      </svg>
      <div style={{position: "absolute", left: 828, top: 428, width: 44, fontSize: 18, letterSpacing: 2, color: SOFT, whiteSpace: "nowrap", background: PAPER}}>
        <Write p={span(f, E.lock.s + 10, E.lock.s + 32)}>×1</Write>
      </div>

      {/* That's docking：锁的正下方居中 */}
      <div style={{position: "absolute", left: 1274, top: 582, width: 240, fontSize: 24, fontStyle: "italic", textAlign: "center", whiteSpace: "nowrap"}}>
        <Write p={span(f, E.docking.s, E.docking.s + 14)}>That&rsquo;s docking</Write>
      </div>

      {/* scores the fit */}
      <div style={{position: "absolute", left: 1196, top: 638, width: 460, fontSize: 24, letterSpacing: 2.5, color: SOFT, textTransform: "uppercase", whiteSpace: "nowrap"}}>
        <Write p={span(f, E.docking.s + 2, E.docking.s + 24)}>scores the fit</Write>
      </div>

      <Source p={span(f, 2, 22)}>Ren et al., Chem. Sci. 2023; Lengauer 2007; Wang et al., Pharmaceuticals 2023 · Illustration</Source>
    </AbsoluteFill>
    </Lens>
  );
};

const Root = () => <Composition id="Manual410" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
