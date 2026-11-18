// HKBU SCIE1007 课程作业的科普视频：第 7 章二维说明书页 7-03（A 画外音）"Two: check the AlphaFold model against a lab-measured structure ... feed every result back"。
// 左框：AlphaFold 芯片吐出珠子，折成预测形状（同 4-01 的珠子串）；右框（虚线框）：flask 和同一形状的虚线（once one exists）；中间天平，左右两框各连到一个盘，打问号、来回晃；
// 下方循环箭头：两框飞出结果卡进循环，一张打红叉的卡也进去；循环引出箭头回到左框（next round），循环带着卡转一整圈，左框形状微调。
// 时间全读 keys_7-03.json（事件表 映射/events/7-03.json，用 ev_make.py 简写生成）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_7-03.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const LF = {x: 130, y: 300, w: 520, h: 370}, RF = {x: 1270, y: 300, w: 520, h: 370};
const FOLD = [[-80, 50], [-40, 70], [0, 54], [22, 16], [-14, -14], [-54, -24], [-86, -58], [-46, -92], [-4, -72], [36, -48], [74, -10], [112, 28]];
const NUDGE = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [6, 8], [10, 12], [8, 10], [-6, 8], [-10, 4]];   // next round：形状微调
const SC = 1.45, MC = [440, 520], DC = [1580, 520], CHIP = [215, 380];
const PV = [960, 380], ARM = 170, STR = 70;                       // 天平
const LC = [960, 870], LR = 95, CR = LR + 36;                                    // 循环
const CARDS = [{a: -150, src: "L"}, {a: -95, src: "R"}, {a: -40, src: "L"}, {a: 25, src: "R"}, {a: 145, src: "F"}];

const Frame = ({b, p, dash}) => (
  <rect x={b.x} y={b.y} width={b.w} height={b.h} rx={16} fill="none" stroke={INK} strokeWidth={3} strokeDasharray={dash ? "14 10" : undefined}
        style={{clipPath: `inset(0 ${100 - 100 * p}% 0 0)`}} />
);

const Scene = () => {
  const f = useCurrentFrame();
  const io = Easing.inOut(Easing.cubic);
  const bal = span(f, E.bal.s, E.bal.e, ease);
  const tilt0 = -8 * span(f, E.ag.s, E.ag.l + 10, ease) * (1 - span(f, E.str.s, E.str.l + 14, ease));
  const wob = f > E.ex.s ? Math.sin((f - E.ex.s) / 9) * 7 * (1 - span(f, E.feed.s, E.every.l, ease)) : 0;
  const tilt = (tilt0 + wob) * Math.PI / 180;
  const endL = [PV[0] - ARM * Math.cos(tilt), PV[1] - ARM * Math.sin(tilt)], endR = [PV[0] + ARM * Math.cos(tilt), PV[1] + ARM * Math.sin(tilt)];
  const mdl = span(f, E.mdl.s, E.mdl.l + 18, ease), rnd = span(f, E.rnd.s, E.rnd.e + 10, io);
  const str = span(f, E.str.s, E.str.l + 16, ease);
  const loop = span(f, E.feed.s, E.feed.l + 12, ease);
  const q = span(f, E.ex.s, E.ex.l + 8, out);
  const back = span(f, E.back.s, E.back.e, ease);
  const bp = (i) => {                                               // 左框第 i 颗珠子
    const t = span(mdl, i * 0.05, i * 0.05 + 0.45, ease);
    const fx = MC[0] + FOLD[i][0] * SC + NUDGE[i][0] * rnd, fy = MC[1] + FOLD[i][1] * SC + NUDGE[i][1] * rnd;
    return [CHIP[0] + (fx - CHIP[0]) * t, CHIP[1] + (fy - CHIP[1]) * t - Math.sin(Math.PI * t) * 50, t];
  };
  const LB = [...Array(12)].map((_, i) => bp(i));
  const cardAt = (k) => {
    const c = CARDS[k];
    const ev = c.src === "F" ? E.inc : E.every;
    const t = span(f, ev.s + 4 * (k % 4), ev.l + 16 + 4 * (k % 4), ease);
    const src = c.src === "L" ? [LF.x + LF.w - 60, LF.y + LF.h - 20] : c.src === "R" ? [RF.x + 60, RF.y + LF.h - 20] : [1240, 740];
    const a = (c.a + 360 * rnd) * Math.PI / 180;
    const dst = [LC[0] + CR * Math.cos(a), LC[1] + CR * Math.sin(a)];
    return {x: src[0] + (dst[0] - src[0]) * t, y: src[1] + (dst[1] - src[1]) * t - Math.sin(Math.PI * t) * 60, t, show: f >= ev.s};
  };
  const bead = [[0, 760, 220], [E.two.l, 720, 100], [E.bal.l, 1150, 230], [E.af.l, 690, 215], [E.mdl.l, 240, 760], [E.ag.l, 720, 600],
                [E.lab.l, 1220, 205], [E.str.l, 1800, 740], [E.once.l, 1730, 200], [E.ex.l, 1070, 290], [E.feed.l, 760, 980],
                [E.every.l, 1180, 985], [E.res.l, 1480, 815], [E.inc.l, 1200, 740], [E.fail.l, 1560, 890], [E.back.l, 480, 800],
                [E.nx.l, 560, 965], [E.rnd.l, 1300, 975], [K.len_f, 1301, 976]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("7-03.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.two.s, E.two.e + 30)}>Two: check the model</Write></div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <Frame b={LF} p={span(f, E.af.s, E.af.l + 10, ease)} />
        <Frame b={RF} p={span(f, E.lab.s, E.lab.l + 10, ease)} dash />
        {/* 天平 */}
        <g stroke={INK} strokeWidth={4} strokeLinecap="round" fill="none" opacity={span(bal, 0, 0.2)}>
          <path d={`M${PV[0]},650 L${PV[0]},${650 - (650 - PV[1]) * span(bal, 0, 0.5)}`} />
          <path d={`M${PV[0] - 60},650 L${PV[0] + 60},650`} />
          {bal > 0.4 && <path d={`M${endL[0]},${endL[1]} L${endR[0]},${endR[1]}`} style={{clipPath: `inset(0 ${50 - 50 * span(bal, 0.4, 0.8)}% 0 ${50 - 50 * span(bal, 0.4, 0.8)}%)`}} />}
          {bal > 0.75 && [endL, endR].map(([x, y], i) => (
            <g key={i} opacity={span(bal, 0.75, 1)}>
              <path d={`M${x},${y} L${x - 40},${y + STR} M${x},${y} L${x + 40},${y + STR}`} strokeWidth={2.5} />
              <path d={`M${x - 58},${y + STR} Q${x},${y + STR + 40} ${x + 58},${y + STR} Z`} fill={PAPER} />
            </g>
          ))}
          <circle cx={PV[0]} cy={PV[1]} r={9} fill={INK} stroke="none" opacity={span(bal, 0.4, 0.6)} />
        </g>
        {/* 两框连到两个盘 */}
        {[[E.ag, [LF.x + LF.w, 520], endL], [E.str, [RF.x, 520], endR]].map(([ev, a, b], i) => {
          const p = span(f, ev.s + 4, ev.l + 20, ease), bx = b[0] + (i ? 40 : -40) * 0, by = b[1] + STR + 14;
          return p > 0 && <path key={i} d={`M${a[0]},${a[1]} L${a[0] + (bx - a[0]) * p},${a[1] + (by - a[1]) * p}`} stroke={SOFT} strokeWidth={3} strokeDasharray="8 8" fill="none" />;
        })}
        {/* 左框：珠子串 */}
        {LB.slice(1).map(([x, y, t], i) => t > 0.95 && LB[i][2] > 0.95 &&
          <line key={i} x1={LB[i][0]} y1={LB[i][1]} x2={x} y2={y} stroke={INK} strokeWidth={4} />)}
        {LB.map(([x, y, t], i) => f >= E.mdl.s && <circle key={i} cx={x} cy={y} r={14 * (0.4 + 0.6 * t)} fill={i >= 10 ? PAPER : INK} stroke={INK} strokeWidth={3} />)}
        {/* 右框：同一形状的虚线 */}
        {FOLD.map(([x, y], i) => {
          const p = span(str, i / 12 * 0.8, i / 12 * 0.8 + 0.2);
          const cx = DC[0] + x * SC, cy = DC[1] + y * SC;
          return (
            <g key={i} opacity={p}>
              {i > 0 && <line x1={DC[0] + FOLD[i - 1][0] * SC} y1={DC[1] + FOLD[i - 1][1] * SC} x2={cx} y2={cy} stroke={SOFT} strokeWidth={3} strokeDasharray="6 6" />}
              <circle cx={cx} cy={cy} r={14} fill={PAPER} stroke={SOFT} strokeWidth={3} strokeDasharray="5 5" />
            </g>
          );
        })}
        {/* 循环 */}
        {loop > 0 && (
          <g transform={`rotate(${360 * rnd} ${LC[0]} ${LC[1]})`} fill="none" stroke={INK} strokeWidth={4.5} strokeLinecap="round" strokeLinejoin="round">
            <path d={`M${LC[0] + LR},${LC[1]} A${LR},${LR} 0 1 1 ${LC[0] + LR * Math.cos(-0.5)},${LC[1] + LR * Math.sin(-0.5)}`} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - loop} />
            {loop > 0.9 && (() => { const x = LC[0] + LR * Math.cos(-0.5), y = LC[1] + LR * Math.sin(-0.5); return <path d={`M${x - 20},${y - 14} L${x},${y} L${x - 22},${y + 10}`} transform={`rotate(62 ${x} ${y})`} />; })()}
          </g>
        )}
        {/* 回到左框的箭头 */}
        {back > 0 && (
          <g fill="none" stroke={RED} strokeWidth={4.5} strokeLinecap="round" strokeLinejoin="round">
            <path d={`M${LC[0] - LR - 8},${LC[1] + 5} C720,875 610,810 600,${LF.y + LF.h + 16}`} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - back} />
            {back > 0.85 && <path d={`M588,${LF.y + LF.h + 34} L600,${LF.y + LF.h + 16} L614,${LF.y + LF.h + 32}`} />}
          </g>
        )}
      </svg>
      <Part name="chip" cx={CHIP[0]} cy={CHIP[1]} w={100} at={E.af.s + 6} f={f} gate={[0.5, 1]} flood={16} />
      <Part name="flask" cx={1350} cy={385} w={84} at={E.lab.s + 4} f={f} gate={[0.5, 1]} flood={16} />
      <Label x={LF.x + LF.w / 2} y={LF.y + LF.h + 18} w={400} size={32} italic p={span(f, E.mdl.s, E.mdl.e + 10)}>AlphaFold model</Label>
      <Label x={RF.x + RF.w / 2} y={RF.y + RF.h + 18} w={440} size={32} italic p={span(f, E.str.s, E.str.e)}>lab-measured structure</Label>
      <Pen x={1440} y={232} size={42} p={span(f, E.once.s, E.ex.l + 10)}>once one exists</Pen>
      <div style={{position: "absolute", left: PV[0] - 50, top: 250, width: 100, textAlign: "center", fontSize: 96, lineHeight: "100px", color: RED, opacity: q,
                   transform: `scale(${1.3 - 0.3 * q})`}}>?</div>
      {/* 结果卡：每张一个勾，最后一张打红叉 */}
      {CARDS.map((c, k) => {
        const {x, y, show} = cardAt(k);
        if (!show) return null;
        const fail = c.src === "F";
        return (
          <div key={k} style={{position: "absolute", left: x - 22, top: y - 28, width: 44, height: 56, background: "#F7F3E8", border: `2.5px solid ${fail ? RED : INK}`, borderRadius: 5, boxSizing: "border-box"}}>
            <svg width={44} height={56} style={{position: "absolute", left: -2.5, top: -2.5}}>
              {fail ? <path d="M12,16 L32,40 M32,16 L12,40" stroke={RED} strokeWidth={4} strokeLinecap="round" />
                    : <><path d="M10,14 L34,14 M10,22 L30,22" stroke={SOFT} strokeWidth={2.5} /><path d="M12,36 L19,43 L32,29" fill="none" stroke={INK} strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round" /></>}
            </svg>
          </div>
        );
      })}
      <Label x={1140} y={820} w={340} size={32} italic align="left" p={span(f, E.res.s, E.res.e)}>every result</Label>
      <Label x={1140} y={866} w={360} size={32} italic align="left" color={RED} p={span(f, E.fail.s, E.fail.e)}>including the failures</Label>
      <Label x={720} y={930} w={180} size={32} italic color={RED} p={span(f, E.nx.s, E.rnd.l + 10)}>next round</Label>

      <Source p={span(f, E.af.l, E.af.l + 20)}>Our proposal · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual703" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
