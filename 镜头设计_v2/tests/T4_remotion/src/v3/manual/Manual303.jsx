// HKBU SCIE1007 课程作业的科普视频：第 3 章二维说明书页 3-03（D 画外音）"Scientists call the lock the target …"
// 主线物件：一把钥匙和三把锁。lock 第一把锁长出 → target 红圈收拢、写 the target → key 钥匙长出 → candidate 写 a candidate molecule →
// good 另两把不同的锁长出 → fits 钥匙滑进自己的锁 → tightly 锁一颤、打勾 → opens 拔出跳到第二把 → no 撞上弹回、打叉 →
// else's 跳到第三把、弹回、打叉、批注 → That's 钥匙回到自己的锁，三个结果框成一行 → selectivity 字牌落下。
// 时间全读 keys_3-03.json（事件表 映射/events/3-03.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_3-03.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source, Plate} from "./kit.jsx";

const E = evMap(K);
const io = Easing.inOut(Easing.cubic);
const LY = 520, LW = 190, LH = LW * 743 / 520;
const LOCK = [{x: 700, sx: 1, sy: 1}, {x: 1160, sx: 0.82, sy: 1.12}, {x: 1620, sx: 1.22, sy: 0.84}];
const hole = (i) => LY + 0.143 * LH * LOCK[i].sy;                 // 锁孔高度
const left = (i) => LOCK[i].x - LW * LOCK[i].sx / 2;              // 锁身左边
const KW = 240, KH = KW * 312 / 1096;
const MY = 310;                                                   // 勾叉一行

// 钥匙位置（中心）：只由事件帧决定
const keyAt = (f) => {
  const home = [450, hole(0)], in1 = [580, hole(0)];
  const at2 = [left(1) + 20 - KW / 2, hole(1)], at3 = [left(2) + 20 - KW / 2, hole(2)];
  const hop = (a, b, p, h) => [a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p - Math.sin(Math.PI * p) * h];
  // 撞上锁身后弹回：先顶进 26 px，再退到 -20 px，带一点余振
  const hit = (p, t0) => (f < t0 ? 26 * p : 26 - 46 * span(f, t0, t0 + 14, out) + 3 * Math.exp(-(f - t0 - 14) / 6) * Math.sin(Math.max(0, f - t0 - 14) / 2));
  if (f < E.fits.s) return home;
  if (f < E.opens.s) return hop(home, in1, span(f, E.fits.s, E.fits.l, io), 0);
  if (f < E.no.s) {
    const p = span(f, E.opens.s, E.opens.l, io);
    return p < 0.25 ? [in1[0] - 130 * span(p, 0, 0.25, ease), in1[1]] : hop([in1[0] - 130, in1[1]], at2, span(p, 0.25, 1, io), 230);
  }
  if (f < E.else.s) { const p = span(f, E.no.s, E.no.l, Easing.in(Easing.quad)); return [at2[0] + hit(p, E.no.l), at2[1]]; }
  if (f < E.back.s) {
    const p = span(f, E.else.s, E.else.l - 8, io), q = span(f, E.else.l - 8, E.else.l, Easing.in(Easing.quad));
    const from = [at2[0] - 20, at2[1]];
    const [x, y] = hop(from, at3, p, 220);
    return [x + (f < E.else.l ? 26 * q : hit(1, E.else.l)), y];
  }
  return hop([at3[0] - 20, at3[1]], in1, span(f, E.back.s, E.back.l, io), 330);
};

// 另两把锁换掉锁孔：第二把是十字锁孔，第三把是密码转盘（盖在原锁孔上，锁身色补底）
const BODY = "#2D41A4";
const Hole = ({kind, x, p}) => {
  if (p <= 0) return null;
  const cy = LY + 0.16 * LH;
  return (
    <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, opacity: p}}>
      <rect x={x - 30} y={LY + 0.04 * LH} width={60} height={0.3 * LH} rx={10} fill={BODY} />
      {kind === 1 ? (
        <path d={`M${x - 7},${cy - 24} h14 v17 h17 v14 h-17 v17 h-14 v-17 h-17 v-14 h17 Z`} fill="#1E1E22" stroke="#5A6FD0" strokeWidth={1.5} />
      ) : (
        <g>
          <circle cx={x} cy={cy} r={27} fill="#1E1E22" stroke="#C9CCD8" strokeWidth={3} />
          {[...Array(12)].map((_, k) => { const a = k * 30 * Math.PI / 180; return <line key={k} x1={x + 19 * Math.cos(a)} y1={cy + 19 * Math.sin(a)} x2={x + 25 * Math.cos(a)} y2={cy + 25 * Math.sin(a)} stroke="#C9CCD8" strokeWidth={2} />; })}
          <circle cx={x} cy={cy} r={8} fill="#C9CCD8" />
          <line x1={x} y1={cy} x2={x} y2={cy - 16} stroke="#C9CCD8" strokeWidth={3} strokeLinecap="round" />
        </g>
      )}
    </svg>
  );
};
const Check = ({x, y, p}) => p <= 0 ? null : (
  <path d={`M${x - 24},${y} L${x - 6},${y + 20} L${x + 28},${y - 26}`} fill="none" stroke={RED} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round"
        pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
);
const Cross = ({x, y, p}) => p <= 0 ? null : (
  <g stroke={RED} strokeWidth={6} strokeLinecap="round">
    <line x1={x - 22} y1={y - 22} x2={x - 22 + 44 * span(p, 0, 0.5)} y2={y - 22 + 44 * span(p, 0, 0.5)} />
    <line x1={x + 22} y1={y - 22} x2={x + 22 - 44 * span(p, 0.5, 1)} y2={y - 22 + 44 * span(p, 0.5, 1)} />
  </g>
);

const Scene = () => {
  const f = useCurrentFrame();
  const [kx, ky] = keyAt(f);
  const shake = (t0) => (f > t0 ? 2.2 * Math.exp(-(f - t0) / 8) * Math.sin((f - t0) / 1.6) : 0);
  const rot = [shake(E.tight.s), shake(E.no.l), shake(E.else.l)];
  const ring = span(f, E.target.s, E.target.l + 10, out);
  const ringOut = span(f, E.target.l + 30, E.target.l + 60);
  const pulse = f > E.cand.l ? 0.08 * Math.exp(-(f - E.cand.l) / 8) * Math.cos((f - E.cand.l) / 3) : 0;
  const box = span(f, E.back.s, E.back.l, ease);
  const bead = [[0, 130, 96], [E.title.l, 560, 96], [E.lock.l, 930, 520], [E.target.l, 940, 760], [E.key.l, 250, 450], [E.cand.l, 230, 680],
                [E.good.l, 1390, 790], [E.fits.l, 450, 450], [E.tight.l, 820, 300], [E.opens.l, 1160, 210], [E.no.l, 1290, 320],
                [E.else.l, 1770, 330], [E.back.l, 960, 210], [E.sel.l, 1100, 830], [K.len_f, 1101, 831]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("3-03.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>The target and the key</Write></div>

      {/* 钥匙在锁下面一层：插进去时尖藏到锁后面 */}
      {f >= E.key.s && (
        <div style={{position: "absolute", left: kx - KW / 2, top: ky - KH / 2, width: KW, height: KH, transform: `scale(${1 + pulse})`}}>
          <Part name="key" cx={KW / 2} cy={KH / 2} w={KW} at={E.key.s} f={f} gate={[0.1, 0.5]} />
        </div>
      )}
      {LOCK.map((L, i) => (
        <div key={i} style={{position: "absolute", left: 0, top: 0, transform: `rotate(${rot[i]}deg) scale(${L.sx}, ${L.sy})`, transformOrigin: `${L.x}px ${LY}px`}}>
          <Part name="lock" cx={L.x} cy={LY} w={LW} at={i === 0 ? E.lock.s : E.good.s + 10 * (i - 1)} f={f} gate={[0.5, 1]} />
          {i > 0 && <Hole kind={i} x={L.x} p={span(f, E.good.s + 10 * (i - 1) + 6, E.good.s + 10 * (i - 1) + 26)} />}
        </div>
      ))}

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {ring > 0 && ringOut < 1 && <circle cx={700} cy={LY - 12} r={250 - 82 * ring} fill="none" stroke={RED} strokeWidth={4} strokeDasharray="10 8" opacity={ring * (1 - ringOut)} />}
        {ring > 0 && ringOut < 1 && [0, 180, 270].map((a) => {
          const r = 250 - 82 * ring, t = a * Math.PI / 180;
          return <line key={a} x1={700 + (r - 22) * Math.cos(t)} y1={LY - 12 + (r - 22) * Math.sin(t)} x2={700 + (r + 22) * Math.cos(t)} y2={LY - 12 + (r + 22) * Math.sin(t)}
                       stroke={RED} strokeWidth={4} opacity={ring * (1 - ringOut)} />;
        })}
        <Check x={700} y={MY} p={span(f, E.tight.s, E.tight.l + 10, ease)} />
        <Cross x={1160} y={MY} p={span(f, E.no.l - 2, E.no.l + 10, ease)} />
        <Cross x={1620} y={MY} p={span(f, E.else.l - 2, E.else.l + 10, ease)} />
        {box > 0 && <rect x={600} y={MY - 48} width={1120} height={92} rx={14} fill="none" stroke={SOFT} strokeWidth={2.5} strokeDasharray="9 8" opacity={0.9}
                          transform={`translate(1160 ${MY}) scale(${box} 1) translate(-1160 ${-MY})`} />}
      </svg>

      <Label x={700} y={692} w={260} size={30} italic color={RED} p={span(f, E.target.s, E.target.l + 8)}>the target</Label>
      <Label x={450} y={606} w={320} size={26} italic p={span(f, E.cand.s, E.cand.l + 18)}>a candidate molecule</Label>
      <Pen x={1270} y={700} p={span(f, E.else.l, E.else.e)} size={40} rot={-3}>no one else's</Pen>
      <Plate x={120} y={790} w={560} p={span(f, E.sel.s, E.sel.l, out)} style={{fontSize: 76, lineHeight: "90px", textAlign: "left"}}>selectivity</Plate>
      <Label x={126} y={900} w={900} size={32} italic color={SOFT} align="left" p={span(f, E.sel.l, E.sel.e)}>fits its own lock tightly, and opens no one else's</Label>

      <Source p={span(f, E.title.l, E.title.l + 20)}>Lengauer 2007 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual303" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
