// HKBU SCIE1007 课程作业的科普视频：第 4 章二维说明书页 4-01（画外音）目标 1：结构预测。
// 小人 → 想法云 "science fiction"；问 AI（芯片）猜形状；一串积木（12 颗珠子）折成三维；编号 = 序列；
// AlphaFold 从已知结构学；序列送进芯片 → 预测形状，每颗珠子按把握程度上色（实心 = sure，红虚线 = less sure）。
// 时间全读 keys_4-01.json（事件表 映射/events/4-01.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_4-01.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const N = 12, RX = 160, RY = 768, RS = 58, BR = 19;               // 一串珠子
const FX = 1170, FY = 590;                                          // 折好后的中心
const FOLD = [[-80, 50], [-40, 70], [0, 54], [22, 16], [-14, -14], [-54, -24], [-86, -58], [-46, -92], [-4, -72], [36, -48], [74, -10], [112, 28]];
const TAIL = [[150, 66], [186, 104]];                                // 最后两颗是松垂的尾巴（低把握）
const PTS = [...FOLD.slice(0, 10), ...TAIL];
const LOW = new Set([10, 11]);
const CHX = 560, CHY = 430;
const KN = [1090, 1230, 1370], KY = 250;

const mini = (cx, cy, s) => PTS.slice(0, 10).map(([x, y]) => [cx + x * s, cy + y * s]);

const Scene = () => {
  const f = useCurrentFrame();
  const fold = span(f, E.fold.s, E.d3.l, Easing.inOut(Easing.cubic));
  const chainIn = span(f, E.chain.s, E.chain.l + 20, ease);
  const each = span(f, E.each.s, E.each.e, ease);
  const learn = span(f, E.learn.s, E.learn.l, Easing.in(Easing.quad));
  const give = span(f, E.give.s, E.give.l, ease);
  const guessOut = span(f, E.learn.s, E.learn.l, ease);
  const ai2af = span(f, E.af.s, E.af.l, ease);
  const glow = f > E.lrn.s ? Math.max(0, Math.sin(Math.PI * span(f, E.lrn.s, E.lrn.e))) : 0;
  const pos = (i) => {
    const r = [RX + i * RS, RY], c = [FX + PTS[i][0], FY + PTS[i][1]];
    const t = span(fold, i * 0.04, i * 0.04 + 0.56);
    return [r[0] + (c[0] - r[0]) * t, r[1] + (c[1] - r[1]) * t - Math.sin(Math.PI * t) * 60];
  };
  const P = [...Array(N)].map((_, i) => pos(i));
  const shown = (i) => span(chainIn, i / N * 0.8, i / N * 0.8 + 0.2);
  const bead = [[0, 130, 96], [E.title.l, 420, 96], [E.people.l, 200, 330], [E.fic.l, 420, 190], [E.ai.l, CHX, CHY - 110], [E.guess.l, 820, 230],
                [E.chain.l, RX - 40, RY], [E.fold.l, 860, 640], [E.d3.l, FX - 120, FY + 150], [E.order.l, RX - 40, RY + 40], [E.seq.l, 620, RY + 66],
                [E.af.l, CHX + 120, CHY + 110], [E.known.l, 980, KY], [E.learn.l, CHX + 110, CHY - 90], [E.give.l, 420, 640], [E.pred.l, 860, 470],
                [E.shape.l, 950, 430], [E.sure.l, 1470, 520], [E.each.l, 1820, 760], [K.len_f, 1821, 761]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("4-01.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>Objective 1</Write></div>
      <div style={{position: "absolute", left: 400, top: 82, fontSize: 30, fontStyle: "italic", color: SOFT}}><Write p={span(f, E.title.l, E.people.l)}>Tool: structure prediction</Write></div>

      {/* 团队和想法云 */}
      <Part name="person" cx={200} cy={440} w={190} at={E.people.s + 2} f={f} gate={[0.5, 1]} />
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {f >= E.cloud.s && (<g transform="translate(40 0)">
          <g stroke={INK} strokeWidth={3} fill="#F4F1EA" strokeLinejoin="round">
            <path d="M120,290 C70,290 70,230 120,226 C118,180 190,170 210,200 C236,160 320,166 330,206 C384,196 410,250 370,276 C384,310 330,322 300,300 C270,330 200,330 180,300 C160,316 120,316 120,290 Z"
                  pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(f, E.cloud.s, E.cloud.l + 10, ease)} fill="none" />
            {[[178, 330, 8], [190, 352, 5]].map(([x, y, r], i) => <circle key={i} cx={x} cy={y} r={r * span(f, E.cloud.s + 4 * i, E.cloud.l + 4 * i, out)} fill="none" />)}
          </g></g>
        )}
        {f >= E.like.s && [[100, 200, 76, 186], [432, 190, 460, 172], [464, 250, 492, 250], [116, 304, 90, 320]].map(([a, b, c, d], i) => {
          const p = span(f, E.like.s + 2 * i, E.like.l + 6 + 2 * i, out);
          return <line key={i} x1={a} y1={b} x2={a + (c - a) * p} y2={b + (d - b) * p} stroke={RED} strokeWidth={3} strokeLinecap="round" />;
        })}
        {/* 小人 → 芯片 */}
        {f >= E.ai.s && (() => { const p = span(f, E.ai.s + 6, E.ai.e, ease); return (
          <g stroke={INK} strokeWidth={3} fill="none" strokeLinecap="round">
            <path d={`M310,440 L${310 + (452 - 310) * p},440`} />
            {p > 0.9 && <path d="M440,428 L454,440 L440,452" />}
          </g>); })()}
        {/* 猜形状：虚线泡泡 */}
        {f >= E.guess.s && (
          <g opacity={1 - guessOut}>
            <path d="M760,300 C750,250 820,236 850,256 C900,250 910,310 890,340 C900,390 830,410 800,390 C750,400 730,340 760,300 Z" fill="none" stroke={INK} strokeWidth={3}
                  strokeDasharray="10 8" pathLength={300} strokeDashoffset={0} opacity={span(f, E.guess.s, E.guess.l + 6)} />
            <line x1={670} y1={410} x2={670 + 70 * span(f, E.guess.s, E.guess.l, ease)} y2={410 - 50 * span(f, E.guess.s, E.guess.l, ease)} stroke={INK} strokeWidth={3} strokeDasharray="4 6" />
          </g>
        )}
        {/* 一串珠子之间的线：原位置的虚线，和移动中的链 */}
        {chainIn > 0 && <polyline points={[...Array(N)].map((_, i) => `${RX + i * RS},${RY}`).join(" ")} fill="none" stroke={INK} strokeWidth={2.5}
                                  opacity={(1 - 0.75 * fold) * span(chainIn, 0, 0.9)} strokeDasharray={fold > 0 ? "6 8" : "none"} />}
        {fold > 0 && <polyline points={P.map(([x, y]) => `${x},${y}`).join(" ")} fill="none" stroke={INK} strokeWidth={3} />}
        {/* 编号括号 */}
        {f >= E.seq.s && (() => { const p = span(f, E.seq.s, E.seq.l + 4, ease); return (
          <path d={`M${RX - BR},${RY + 32} L${RX - BR},${RY + 44} L${RX - BR + (RX + (N - 1) * RS + BR - RX + BR) * p},${RY + 44}${p > 0.98 ? ` L${RX + (N - 1) * RS + BR},${RY + 32}` : ""}`}
                fill="none" stroke={INK} strokeWidth={3} />); })()}
        {/* 已知结构 → 芯片 */}
        {KN.map((kx, j) => {
          const g = span(f, E.known.s + 6 * j, E.known.l + 6 * j, out);
          if (g <= 0 || learn >= 1) return null;
          const t = span(learn, j * 0.15, j * 0.15 + 0.7);
          const cx = kx + (CHX - kx) * t, cy = KY + (CHY - KY) * t, s = 0.32 * (1 - 0.6 * t);
          const m = mini(cx, cy, s);
          return <g key={j} opacity={g * (1 - span(t, 0.8, 1))}>
            <polyline points={m.map(([x, y]) => `${x},${y}`).join(" ")} fill="none" stroke={INK} strokeWidth={2.5} />
            {m.map(([x, y], i) => <circle key={i} cx={x} cy={y} r={6 * (1 - 0.4 * t)} fill={INK} />)}
          </g>;
        })}
        {f >= E.how.s && learn < 1 && (() => { const p = span(f, E.how.s, E.how.e, ease); return (
          <g stroke={SOFT} strokeWidth={3} fill="none" strokeDasharray="8 8" opacity={1 - learn}>
            <path d={`M1020,${KY + 20} L${1020 + (680 - 1020) * p},${KY + 20 + (CHY - 60 - KY - 20) * p}`} />
          </g>); })()}
        {/* 芯片 → 预测 */}
        {f >= E.pred.s && (() => { const p = span(f, E.pred.s, E.pred.e, ease); return (
          <g stroke={INK} strokeWidth={4} fill="none" strokeLinecap="round">
            <path d="M660,450 C780,470 860,520 960,560" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
            {p > 0.95 && <path d="M940,544 L962,561 L936,568" />}
          </g>); })()}
        {f >= E.shape.s && <rect x={980} y={440} width={460} height={300} rx={10} fill="none" stroke={INK} strokeWidth={2.5} strokeDasharray="10 8" opacity={span(f, E.shape.s, E.shape.l + 6)} />}
        {/* 图例 */}
        {f >= E.plus.s && (
          <g opacity={span(f, E.plus.s, E.plus.l + 6)}>
            <rect x={1490} y={500} width={320} height={190} rx={10} fill="none" stroke={INK} strokeWidth={2.5} />
            <circle cx={1530} cy={600} r={BR} fill={INK} opacity={span(f, E.sure.s, E.sure.l)} />
            <circle cx={1530} cy={652} r={BR} fill="#F4F1EA" stroke={RED} strokeWidth={3.5} strokeDasharray="6 5" opacity={span(f, E.sure.l, E.sure.l + 12)} />
          </g>
        )}
      </svg>
      <Pen x={144} y={214} p={span(f, E.fic.s, E.fic.e)} size={38} rot={-3}>science fiction</Pen>

      {/* 芯片 */}
      <div style={{filter: glow > 0 ? `drop-shadow(0 0 ${18 * glow}px rgba(200,16,46,0.6))` : "none"}}>
        <Part name="chip" cx={CHX} cy={CHY} w={180} at={E.ai.s + 2} f={f} gate={[0.5, 0.5]} />
      </div>
      <Label x={CHX} y={CHY + 98} w={260} size={28} italic color={SOFT} p={span(f, E.ai.l, E.ai.e) * (1 - ai2af)}>an AI</Label>
      <Label x={CHX} y={CHY + 98} w={260} size={30} p={span(f, E.af.s, E.af.e)}>AlphaFold</Label>
      {f >= E.guess.s && <div style={{position: "absolute", left: 790, top: 262, width: 60, textAlign: "center", fontSize: 96, lineHeight: "110px", color: RED,
                                      opacity: 1 - guessOut, transform: `scale(${span(f, E.guess.s + 4, E.guess.l + 6, Easing.out(Easing.back(1.6)))})`}}>?</div>}
      <Label x={820} y={420} w={260} size={26} italic p={span(f, E.guess.l - 6, E.guess.e) * (1 - guessOut)}>guess the shape</Label>
      <Label x={1230} y={300} w={300} size={24} italic color={SOFT} p={span(f, E.known.l, E.known.e) * (1 - learn)}>known structures</Label>

      {/* 珠子 */}
      <Label x={RX + (N - 1) * RS / 2} y={RY - 98} w={600} size={30} p={span(f, E.prot.s, E.prot.e)}>a protein</Label>
      <Label x={RX + (N - 1) * RS / 2} y={RY - 60} w={600} size={26} italic p={span(f, E.blocks.s, E.blocks.e)}>a chain of building blocks</Label>
      {[...Array(N)].map((_, i) => {
        const a = shown(i);
        if (a <= 0) return null;
        // 原位置留虚线圈，编号写在里面
        const lowC = LOW.has(i) ? span(each, 0.5, 1) : 0, hiC = LOW.has(i) ? 0 : span(each, i / 10 * 0.5, i / 10 * 0.5 + 0.3);
        return <React.Fragment key={i}>
          {fold > 0 && <div style={{position: "absolute", left: RX + i * RS - BR, top: RY - BR, width: 2 * BR, height: 2 * BR, borderRadius: BR, boxSizing: "border-box",
                                    border: `2px dashed ${SOFT}`, opacity: Math.min(1, fold * 2), textAlign: "center", font: `22px/${2 * BR - 4}px Serif`, color: INK}}>
            <span style={{opacity: span(f, E.order.s + 3 * i, E.order.s + 3 * i + 8)}}>{i + 1}</span></div>}
          <div style={{position: "absolute", left: P[i][0] - BR, top: P[i][1] - BR, width: 2 * BR, height: 2 * BR, borderRadius: BR, boxSizing: "border-box",
                       border: `3px ${lowC > 0 ? "dashed" : "solid"} ${lowC > 0 ? RED : INK}`, background: hiC > 0 ? `rgba(31,30,28,${hiC})` : "#F4F1EA", transform: `scale(${a})`}} />
        </React.Fragment>;
      })}
      <Label x={RX + (N - 1) * RS / 2} y={RY + 52} w={400} size={30} italic color={RED} p={span(f, E.seq.l - 6, E.seq.e)}>the sequence</Label>
      <Label x={FX - 40} y={FY + 160} w={300} size={30} p={span(f, E.d3.s, E.d3.e)}>a 3D shape</Label>
      <Label x={1210} y={402} w={460} size={26} italic p={span(f, E.shape.s, E.shape.e)}>the predicted shape</Label>
      {/* 给它一条序列：缩小的编号条飞进芯片 */}
      {f >= E.give.s && give < 1 && (
        <div style={{position: "absolute", left: 0, top: 0, opacity: 1 - span(give, 0.8, 1),
                     transform: `translate(${(RX + (N - 1) * RS / 2) + (CHX - RX - (N - 1) * RS / 2) * give}px, ${RY + (CHY - RY) * give}px) scale(${0.5 - 0.3 * give})`}}>
          <div style={{position: "absolute", left: -(N * RS) / 2, top: -BR, display: "flex", gap: RS - 2 * BR}}>
            {[...Array(N)].map((_, i) => <div key={i} style={{width: 2 * BR, height: 2 * BR, borderRadius: BR, border: `3px solid ${RED}`, boxSizing: "border-box", background: "#F4F1EA"}} />)}
          </div>
        </div>
      )}
      <Label x={1650} y={514} w={300} size={26} italic p={span(f, E.sure.s - 10, E.sure.e)}>how sure it is</Label>
      <Label x={1566} y={582} w={220} size={28} align="left" p={span(f, E.sure.s, E.sure.l + 6)}>sure</Label>
      <Label x={1566} y={634} w={220} size={28} align="left" color={RED} p={span(f, E.sure.l, E.sure.l + 16)}>less sure</Label>
      <Label x={FX + 10} y={FY + 200} w={460} size={24} italic color={SOFT} p={span(f, E.each.l - 20, E.each.e)}>about each part</Label>

      <Source p={span(f, E.title.l, E.title.l + 20)}>Jumper et al., Nature 2021; Ren et al., Chem. Sci. 2023 · Illustration (not to scale)</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual401" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
