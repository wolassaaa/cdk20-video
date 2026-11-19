// HKBU SCIE1007 课程作业的科普视频：第 8 章二维说明书页 8-03（画外音）总结目标 2。
// 接着 8-02：七站路和 Our objectives 便签已在（第 1 条打勾）。圈号 2 亮，写 assess candidates fast；
// 左上一大片点（millions）收缩成 13 个，变成 13 个小瓶；路下长括号 years，Target→Hit 红括号 30 days；Improve 上方钥匙在锁里转（round two）。
// 时间全读 keys_8-03.json（事件表 映射/events/8-03.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_8-03.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, evMap, Label, PageFrame, Source, Lens, guidePlan} from "./kit.jsx";

const E = evMap(K);
const GP = guidePlan(K);   // 视线引导（11-20，替代红色料珠）：事件表 guide 字段 → resolve.py → keys.guides
const ST = ["Target", "Hit", "Improve", "Cells", "Animals", "Trials", "Approval"];
const RX0 = 230, RX1 = 1690, RY = 720;
const sx = (i) => RX0 + ((RX1 - RX0) * i) / (ST.length - 1);
// 一大片点：固定的伪随机位置；前 13 个最后留下
const N = 420;
const rnd = (k) => { const v = Math.sin(k * 12.9898) * 43758.5453; return v - Math.floor(v); };
const DOTS = [...Array(N)].map((_, i) => ({x: 140 + rnd(i + 1) * 870, y: 270 + rnd(i + 501) * 260, d: Math.floor(rnd(i + 999) * 23)}));
const KEEP = [...Array(13)].map((_, k) => ({x: 190 + k * 64, y: 440}));

const Scene = () => {
  const f = useCurrentFrame();
  const io = Easing.inOut(Easing.cubic);
  const shrink = span(f, E.became.s, E.thirteen.l, io);
  const tube = span(f, E.mols.s, E.mols.l + 10, out);
  const hitJ = f > E.hit.s ? Math.exp(-(f - E.hit.s) / 8) * Math.sin((f - E.hit.s) / 2.2) : 0;
  const turn = span(f, E.turn.s, E.turn.l, Easing.out(Easing.back(1.4)));
  const flash = f >= E.road.s && f < E.road.e ? 0.5 - 0.5 * Math.cos((f - E.road.s) / 5) : 0;
  return (
    <Lens plan={GP} f={f}>
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("8-03.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.second.s, E.second.e)}>Objective 2</Write></div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 路（8-02 结束的样子） */}
        <path d={`M${RX0 - 110},${RY} L${RX1 + 60},${RY}`} stroke={flash > 0 ? `rgb(${31 + 169 * flash},${30 - 14 * flash},${28 + 18 * flash})` : INK} strokeWidth={7} strokeLinecap="round" />
        {ST.map((s, i) => <circle key={s} cx={sx(i)} cy={RY} r={16 * (i === 1 ? 1 + 0.4 * hitJ : 1)} fill={i < 2 ? RED : PAPER} stroke={i < 4 ? INK : "#9A968C"} strokeWidth={4} />)}
        {/* assess 括号变红 */}
        {(() => { const c = span(f, E.methods.s, E.methods.l + 8); const x0 = sx(2) - 50, x1 = sx(3) + 50; return (
          <path d={`M${x0},${RY + 72} L${x0},${RY + 84} L${x1},${RY + 84} L${x1},${RY + 72}`} fill="none" stroke={c > 0.5 ? RED : SOFT} strokeWidth={3.5 + 1.5 * c} />); })()}
        {/* years 长括号 */}
        {f >= E.years.s && (() => { const p = span(f, E.years.s, E.years.l + 10, ease), x0 = RX0 - 80, x1 = RX1 + 40; return (
          <path d={`M${x0},${RY + 150} L${x0},${RY + 162} L${x0 + (x1 - x0) * p},${RY + 162}${p > 0.98 ? ` L${x1},${RY + 150}` : ""}`} fill="none" stroke={INK} strokeWidth={3} />); })()}
        {/* 30 days：Target→Hit */}
        {f >= E.days.s && (() => { const p = span(f, E.days.s, E.days.l + 6, ease), x0 = sx(0), x1 = sx(1); return (
          <path d={`M${x0},${RY - 40} L${x0},${RY - 52} L${x0 + (x1 - x0) * p},${RY - 52}${p > 0.98 ? ` L${x1},${RY - 40}` : ""}`} fill="none" stroke={RED} strokeWidth={4} />); })()}
        {/* 一大片点 → 13 */}
        {f >= E.screen.s && tube < 1 && DOTS.map((d, i) => {
          const g = span(f, E.screen.s + d.d, E.screen.s + d.d + 14, out);
          const keep = i < 13, t = keep ? shrink : 0;
          const x = keep ? d.x + (KEEP[i].x - d.x) * t : d.x + (575 - d.x) * shrink * 0.5, y = keep ? d.y + (KEEP[i].y - d.y) * t : d.y + (380 - d.y) * shrink * 0.5;
          const op = keep ? 1 - tube : (1 - span(shrink, 0.1, 0.7));
          return <circle key={i} cx={x} cy={y} r={keep ? 5 + 5 * t : 5} fill={keep && t > 0.5 ? RED : INK} opacity={g * op * (keep ? 1 : 0.6)} />;
        })}
        {/* 速度线 */}
        {f >= E.fast.s && [0, 1, 2].map((k) => { const p = span(f, E.fast.s + 3 * k, E.fast.l + 8 + 3 * k, out); return (
          <line key={k} x1={1800} y1={404 + k * 14} x2={1800 + 46 * p} y2={404 + k * 14} stroke={RED} strokeWidth={3} strokeLinecap="round" />); })}
        {/* 红弧箭头：钥匙转动 */}
        {turn > 0 && <path d={`M${sx(2) + 40},${RY - 150} A44,44 0 0 1 ${sx(2) + 50},${RY - 80}`} fill="none" stroke={RED} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - Math.min(1, turn)} />}
      </svg>
      {ST.map((s, i) => <Label key={s} x={sx(i)} y={RY + 26} w={180} size={28} color={i < 4 ? INK : "#8A867C"} p={1}>{s}</Label>)}
      <Label x={(sx(2) + sx(3)) / 2} y={RY + 92} w={200} size={30} italic color={span(f, E.methods.s, E.methods.l) > 0.5 ? RED : SOFT} p={1}>assess</Label>
      <Label x={(RX0 + RX1) / 2 - 20} y={RY + 172} w={300} size={30} italic p={span(f, E.years.s, E.years.e)}>years</Label>
      <Label x={(sx(0) + sx(1)) / 2} y={RY - 100} w={220} size={34} color={RED} p={span(f, E.days.s, E.days.l + 10)}>30 days</Label>
      {/* 候选钥匙：Cells 上方 */}
      {[0, 1, 2].map((k) => <Part key={k} name="key" cx={sx(3) + 6 * k} cy={RY - 50 - 22 * k} w={70} at={E.cands.s + 4 * k} f={f} gate={[0.1, 0.5]} />)}
      {/* 13 个小瓶 */}
      {tube > 0 && KEEP.map((k, i) => <Part key={i} name="tube" cx={k.x} cy={k.y} w={34} at={E.mols.s + i} f={f} gate={[0.5, 1]} />)}
      <Label x={575} y={210} w={400} size={32} italic p={span(f, E.millions.s, E.millions.e) * (1 - span(f, E.thirteen.s, E.thirteen.l))}>screening by the millions</Label>
      <div style={{position: "absolute", left: 425, top: 250, width: 300, textAlign: "center", fontSize: 96, color: RED, opacity: span(f, E.thirteen.l - 10, E.thirteen.l + 6),
                   transform: `scale(${1 + 0.2 * Math.exp(-Math.max(0, f - E.thirteen.l) / 6)})`}}>13</div>
      <Label x={575} y={500} w={400} size={30} italic p={span(f, E.made.s, E.made.e)}>molecules made</Label>
      {/* round two：Improve 上方的锁和钥匙 */}
      <Part name="lock" cx={sx(2)} cy={RY - 120} w={64} at={E.round.s} f={f} gate={[0.5, 1]} />
      {f >= E.round.s && <div style={{position: "absolute", left: 0, top: 0, transformOrigin: `${sx(2)}px ${RY - 108}px`, transform: `scaleY(${Math.cos(Math.PI * Math.min(1, turn))})`}}>
        <Part name="key" cx={sx(2) - 52} cy={RY - 108} w={84} at={E.round.s + 4} f={f} gate={[0.1, 0.5]} /></div>}
      <Label x={sx(2) - 170} y={RY - 150} w={200} size={28} italic p={span(f, E.round.s, E.round.e)}>round two</Label>

      {/* 便签（8-02 结束时的位置） */}
      <div style={{position: "absolute", left: 1220, top: 210, width: 560, height: 300, background: "#F7F3E8", boxShadow: "0 6px 18px rgba(0,0,0,0.12)",
                   border: "1.5px solid rgba(31,30,28,0.25)", transform: "rotate(-2deg)"}}>
        <div style={{position: "absolute", left: 32, top: 22, fontSize: 40}}>Our objectives</div>
        {[0, 1].map((r) => {
          const on = r === 0 ? 1 : span(f, E.second.s, E.second.l + 6);
          return <div key={r} style={{position: "absolute", left: 32, top: 100 + r * 84, width: 44, height: 44, borderRadius: 22, border: `3px solid ${on > 0.5 ? RED : "#9A968C"}`,
                                      color: on > 0.5 ? RED : "#9A968C", textAlign: "center", font: "28px/38px Serif", transform: `scale(${r ? 1 + 0.3 * Math.sin(Math.PI * on) : 1})`}}>{r + 1}</div>;
        })}
        <div style={{position: "absolute", left: 92, top: 104, fontSize: 28}}>computer-aided methods help</div>
        <svg width={90} height={80} style={{position: "absolute", left: 460, top: 70}}><path d="M10,40 L34,64 L82,8" fill="none" stroke={RED} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" /></svg>
        <div style={{position: "absolute", left: 92, top: 200, width: 400, borderBottom: `2px ${f >= E.helped.l ? "solid" : "dashed"} ${f >= E.helped.l ? INK : "#B9B4A8"}`, height: 24,
                     opacity: 1 - 0.6 * span(f, E.assess.s, E.assess.l)}} />
        <div style={{position: "absolute", left: 92, top: 188, fontSize: 28}}><Write p={span(f, E.assess.s, E.fast.l)}>assess candidates fast</Write></div>
      </div>
      <Part name="person" cx={1170} cy={600} w={90} at={E.team.s} f={f} gate={[0.5, 1]} />
      <Label x={1170} y={650} w={160} size={22} italic color={SOFT} p={span(f, E.team.s, E.team.e)}>the team</Label>

      <Source p={1}>Ren et al., Chem. Sci. 2023; Bender et al., Nat. Rev. Drug Discov. 2026 · Illustration</Source>
    </AbsoluteFill>
    </Lens>
  );
};

const Root = () => <Composition id="Manual803" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
