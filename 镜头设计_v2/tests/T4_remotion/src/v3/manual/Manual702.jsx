// HKBU SCIE1007 课程作业的科普视频：第 7 章二维说明书页 7-02（画外音）：把 048 再往前走一步。
// 路和 048 小牌子（牌子上带一把小锁，停在 Cells）；牌子往前走一步，public 时小锁打开，三个小人来试；
// 三张清单卡依次从旁边飞到路上（细胞 / animals / 身体怎么处理它、还打中什么），last 句三张卡一起打勾、红框。
// 时间全读 keys_7-02.json（事件表 映射/events/7-02.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_7-02.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const ST = ["Target", "Hit", "Improve", "Cells", "Animals", "Trials", "Approval"];
const RX0 = 230, RX1 = 1690, RY = 700;
const sx = (i) => RX0 + ((RX1 - RX0) * i) / (ST.length - 1);
const GREY = "#8A867C", PAPER2 = "#F4F1EA";
const draw = (p) => ({pathLength: 1, strokeDasharray: "1 1", strokeDashoffset: 1 - p});
const CARD = [   // 三张卡：落在 Cells / Animals / Trials 上方；从哪个方向飞来；各行字（每行挂哪个事件）
  {i: 3, from: [-420, -160], lines: [["liver cancer cells", "c1a"], ["and normal", "c1b"], ["liver cells", "c1b"]], ev: "c1"},
  {i: 4, from: [0, -260], lines: [["animals", "c2"]], ev: "c2"},
  {i: 5, from: [420, -160], lines: [["how the body", "c3a"], ["handles it", "c3a"], ["and what else", "c3b"], ["it hits", "c3b"]], ev: "c3"},
];
const CW = 230, CH = 170, CY = RY - 260;

const Scene = () => {
  const f = useCurrentFrame();
  const road = span(f, E.road.s, E.road.l, ease);
  const tagP = span(f, E.road.s + 14, E.road.l + 6, Easing.out(Easing.back(1.6)));
  const wk = span(f, E.walk.s, E.walk.l, ease);
  const tx = sx(3) + (sx(4) - sx(3)) * wk, hy = f >= E.walk.s && f <= E.walk.l ? Math.sin(Math.PI * wk) * 18 : 0;
  const op = span(f, E.pub.s, E.pub.l + 10, ease);                       // 小锁打开
  const tick = (i) => span(f, E.ticks.s + 6 * i, E.ticks.s + 6 * i + 16, ease);
  const red = f >= E.step.s ? span(f, E.step.s, E.step.l + 6) : 0;
  const tryP = span(f, E.try.s, E.try.l + 8, ease);
  const auth = span(f, E.auth.s, E.auth.l + 10);
  const bead = [[0, 130, 96], [E.title.l, 800, 96], [E.road.l, 1700, RY - 130], [E.walk.l, 1203, RY + 190], [E.pub.l, 1340, RY + 120], [E.any.l, 1500, RY - 80], [E.try.l, 1500, RY - 130],
                [E.c1.l, 760, RY - 260], [E.c1a.l, 760, RY - 300], [E.c1b.l, 760, RY - 220], [E.c2.l, 1203, CY - CH / 2 - 30], [E.c3.l, 1447, CY - CH / 2 - 30], [E.c3a.l, 1520, CY - CH / 2 - 30],
                [E.c3b.l, 1590, CY - CH / 2 - 30], [E.auth.l, 1590, 330], [E.al.l, 1700, 570], [E.ticks.l, 1830, 430], [E.step.l, 1820, 600], [K.len_f, 1821, 601]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("7-02.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>One: walk 048 further</Write></div>
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <path d={`M${RX0 - 110},${RY} L${RX1 + 60},${RY}`} fill="none" stroke={INK} strokeWidth={7} strokeLinecap="round" {...draw(road)} />
        {ST.map((s, i) => {
          const p = span(road, (i + 0.4) / (ST.length + 0.6), (i + 1.2) / (ST.length + 0.6), out);
          const grey = i >= 4 && !(i === 4 && f >= E.walk.l);
          return <circle key={s} cx={sx(i)} cy={RY} r={16 * p} fill={i < 4 ? RED : PAPER} stroke={grey ? "#9A968C" : INK} strokeWidth={4} />;
        })}
        {/* 三张清单卡 */}
        {CARD.map((c, k) => {
          const ev = E[c.ev], p = span(f, ev.s, ev.l, out), cx = sx(c.i);
          if (p <= 0) return null;
          const q = tick(k);
          return (
            <g key={k} transform={`translate(${cx + c.from[0] * (1 - p)} ${CY + c.from[1] * (1 - p)}) rotate(${-8 * (1 - p)})`} opacity={Math.min(1, p * 2)}>
              <rect x={-CW / 2} y={-CH / 2} width={CW} height={CH} rx={12} fill={PAPER2} stroke={red > 0 ? RED : INK} strokeWidth={2.5 + 2 * red} />
              {q > 0 && <g transform={`translate(${CW / 2 - 14} ${-CH / 2 - 6}) scale(${0.9 + 0.2 * Math.sin(Math.PI * Math.min(1, q))})`}>
                <circle r={19} fill={PAPER2} stroke={RED} strokeWidth={3} opacity={Math.min(1, q * 3)} />
                <path d="M-9,1 L-3,8 L10,-8" fill="none" stroke={RED} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" {...draw(q)} /></g>}
            </g>
          );
        })}
        {/* try：小人指向牌子的弧箭头 */}
        {tryP > 0 && <g fill="none" stroke={RED} strokeWidth={3.5} strokeLinecap="round" strokeLinejoin="round">
          <path d={`M1376,${RY - 122} C1376,${RY - 160} 1141,${RY - 160} 1141,${RY - 112}`} {...draw(tryP)} />
          {tryP > 0.92 && <path d={`M1131,${RY - 124} L1141,${RY - 110} L1152,${RY - 123}`} />}
        </g>}
        {/* 048 小牌子，带小锁 */}
        {tagP > 0 && <g transform={`translate(${tx} ${RY - 74 - hy}) scale(${tagP})`}>
          <rect x={-85} y={-28} width={170} height={56} rx={9} fill={INK} />
          <path d="M-11,28 L0,44 L11,28 Z" fill={INK} />
          <g transform="translate(-56 0)" fill="none" stroke={PAPER} strokeWidth={3.5} strokeLinecap="round">
            <rect x={-12} y={-2} width={24} height={18} rx={3} fill={PAPER} />
            <path d={`M-7,-2 L-7,${-9 - 6 * op} A7,7 0 0 1 7,${-9 - 6 * op} L7,${-2 - 7 * op}`} />
          </g>
          <text x={22} y={13} textAnchor="middle" fontFamily="Serif" fontSize={40} fill={PAPER}>048</text>
        </g>}
        {/* the authors 的论文图标旁的小框 */}
      </svg>
      {ST.map((s, i) => (
        <Label key={s} x={sx(i)} y={RY + 30} w={180} size={30} color={i >= 5 || (i === 4 && f < E.walk.l) ? GREY : INK} p={span(road, (i + 0.6) / (ST.length + 0.6), (i + 1.4) / (ST.length + 0.6))}>{s}</Label>
      ))}
      <Label x={sx(4) - 225} y={RY - 90} w={160} size={30} italic p={span(f, E.pub.s, E.pub.e)}>public</Label>
      {[0, 1, 2].map((i) => <Part key={i} name="person_w" cx={1330 + 46 * i} cy={RY - 80} w={42} at={E.any.s + 5 * i} f={f} gate={[0.5, 0.5]} />)}
      {/* 卡片上的字 */}
      {CARD.map((c, k) => {
        const ev = E[c.ev], p = span(f, ev.s, ev.l, out), cx = sx(c.i);
        const y0 = CY - (c.lines.length * 32) / 2 + 3;
        return c.lines.map(([t, key], j) => (
          <div key={k + "_" + j} style={{position: "absolute", left: cx + c.from[0] * (1 - p) - CW / 2, top: y0 + j * 32 + c.from[1] * (1 - p), width: CW, textAlign: "center", fontSize: c.lines.length === 1 ? 38 : 26,
                                       lineHeight: "32px", transform: `rotate(${-8 * (1 - p)}deg)`, opacity: p > 0 ? 1 : 0}}>
            <Write p={span(f, E[key].s, E[key].l + 12)}>{t}</Write>
          </div>
        ));
      })}
      {/* the authors：论文图标和红批注 */}
      <Part name="paper1" cx={1700} cy={330} w={100} at={E.auth.s} f={f} gate={[0.5, 0.5]} />
      <Label x={1700} y={410} w={160} size={26} italic color={SOFT} p={span(f, E.auth.s + 4, E.auth.e)}>the authors</Label>
      <Pen x={1585} y={465} size={44} rot={-3} p={span(f, E.al.s, E.al.e)}>already listed&nbsp;</Pen>
      <Source p={span(f, E.title.l, E.title.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual702" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
