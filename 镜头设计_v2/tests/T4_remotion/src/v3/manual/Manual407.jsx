// HKBU SCIE1007 课程作业的科普视频：第 4 章二维说明书页 4-07（画外音）生成式 AI 把循环搬进电脑。
// 左边旧循环（Imagine Make Test Tweak）飞进屏幕；名牌 Chemistry42；几十个模型小方块排齐；底座 known chemistry；
// 循环四站依次改写成 invent / score / learn / go again；右边新钥匙、这把锁、打分条、回流箭头；最后 new structures + within hours。
// 时间全读 keys_4-07.json（事件表 映射/events/4-07.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_4-07.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const SX0 = 620, SY0 = 300, SW = 680, SH = 460;                 // 屏幕
const L0 = [300, 590], L1 = [960, 600], R0 = 120, R1 = 88;      // 循环：起点和屏幕里
const OLD = ["Imagine", "Make", "Test", "Tweak"], NEW = ["invent", "score", "learn", "go again"];
const ANG = [-90, 0, 90, 180];
const KX = 1430, KY = [440, 530, 620], SC = [0.45, 0.9, 0.62];
const LX = 1765, LY = 520;
// 模型小方块：12 × 2，排齐前散开
const BOX = [...Array(24)].map((_, i) => ({c: i % 12, r: Math.floor(i / 12), dx: ((i * 53) % 41) - 20, dy: ((i * 29) % 31) - 15, rot: ((i * 37) % 30) - 15}));

const Scene = () => {
  const f = useCurrentFrame();
  const mv = span(f, E.move.s, E.move.l, Easing.inOut(Easing.cubic));
  const cx = L0[0] + (L1[0] - L0[0]) * mv, cy = L0[1] + (L1[1] - L0[1]) * mv - Math.sin(Math.PI * mv) * 90, R = R0 + (R1 - R0) * mv;
  const loopIn = span(f, E.loop.s, E.loop.l + 10, out);
  // 转角：慢转，进屏幕后转快，go again 时再快一圈
  let rot = 0;
  for (let t = E.loop.s; t <= f; t++) rot += t < E.move.l ? 0.6 : 1.6 + 6 * span(t, E.again.s, E.again.s + 8) * (1 - span(t, E.again.e, E.again.e + 30));
  const screen = span(f, E.screen.s, E.screen.l + 10, ease);
  const side = span(f, E.side.s, E.side.l, Easing.inOut(Easing.cubic));
  const stage = [E.invent, E.score, E.learn, E.again];
  const cur = stage.reduce((k, ev, i) => (f >= ev.s ? i : k), -1);
  const bar = span(f, E.score.s, E.score.l + 16, out);
  const flash = f >= E.scores.s && f < E.scores.e ? 0.5 + 0.5 * Math.cos((f - E.scores.s) / 3) : 0;
  const back = span(f, E.learn.s, E.learn.e, ease);
  const bead = [[0, 130, 96], [E.title.l, 470, 96], [E.loop.l, L0[0], L0[1] - R0 - 60], [E.screen.l, SX0 - 30, SY0 - 30], [E.move.l, SX0 + 40, SY0 + 40],
                [E.c42.l, 760, SY0 - 50], [E.side.l, SX0 + SW + 30, SY0 + 70], [E.chem.l, 600, 900], [E.invent.l, L1[0], L1[1] - R1 - 80],
                [E.exact.l, LX, LY - 170], [E.score.l, 1620, 700], [E.learn.l, 1360, 330], [E.again.l, L1[0] + 150, L1[1] + 120],
                [E.makers.l, 1380, 780], [E.struct.l, 1830, 850], [E.hours.l, 1360, 948], [K.len_f, 1361, 949]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("4-07.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>Generative AI</Write></div>
      <div style={{position: "absolute", left: 470, top: 82, fontSize: 30, fontStyle: "italic", color: SOFT}}><Write p={span(f, E.ai.s, E.ai.e)}>Tool: generative design</Write></div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 屏幕、支架、底座 */}
        {screen > 0 && (
          <g fill="none" stroke={INK} strokeWidth={4} strokeLinejoin="round">
            <rect x={SX0} y={SY0} width={SW} height={SH} rx={14} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - screen} />
            <path d={`M${SX0 + SW / 2 - 30},${SY0 + SH} L${SX0 + SW / 2 - 40},${SY0 + SH + 40} M${SX0 + SW / 2 + 30},${SY0 + SH} L${SX0 + SW / 2 + 40},${SY0 + SH + 40}`} opacity={span(screen, 0.7, 1)} />
          </g>
        )}
        {f >= E.built.s && <rect x={700} y={SY0 + SH + 40} width={520} height={52} rx={8} fill="#F4F1EA" stroke={INK} strokeWidth={3}
                                 transform={`translate(960 ${SY0 + SH + 66}) scale(${span(f, E.built.s, E.built.l + 6, out)} 1) translate(-960 ${-(SY0 + SH + 66)})`} />}
        {/* 名牌框 */}
        {f >= E.plat.s && <rect x={660} y={SY0 - 72} width={260} height={54} rx={6} fill="#2B2B2D" opacity={span(f, E.plat.s, E.plat.l + 4)} />}
        {/* 模型方块 */}
        {BOX.map((b, i) => {
          const g = span(f, E.dozens.s + i * 2.2, E.dozens.s + i * 2.2 + 10, out);
          if (g <= 0) return null;
          const x = SX0 + 46 + b.c * 50 + b.dx * (1 - side), y = SY0 + 28 + b.r * 40 + b.dy * (1 - side);
          return <rect key={i} x={x} y={y} width={38} height={28} rx={4} fill="none" stroke={INK} strokeWidth={2.5}
                       transform={`rotate(${b.rot * (1 - side)} ${x + 19} ${y + 14}) translate(${x + 19} ${y + 14}) scale(${g}) translate(${-x - 19} ${-y - 14})`} />;
        })}
        {/* 循环 */}
        {loopIn > 0 && (
          <g transform={`translate(${cx} ${cy}) scale(${loopIn})`}>
            <circle r={R} fill="none" stroke={INK} strokeWidth={4} />
            {[0, 90, 180, 270].map((a) => {
              const t = (a + rot) * Math.PI / 180;
              return <path key={a} d="M-10,-8 L4,0 L-10,8" fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round"
                           transform={`translate(${R * Math.cos(t)} ${R * Math.sin(t)}) rotate(${a + rot + 90})`} />;
            })}
            {ANG.map((a, i) => <circle key={i} cx={R * Math.cos(a * Math.PI / 180)} cy={R * Math.sin(a * Math.PI / 180)} r={9} fill={cur === i ? RED : INK} />)}
          </g>
        )}
        {/* 旧循环留下的虚线影子 */}
        {mv > 0.3 && <circle cx={L0[0]} cy={L0[1]} r={R0} fill="none" stroke={SOFT} strokeWidth={3} strokeDasharray="10 10" opacity={span(mv, 0.3, 1) * 0.8} />}
        {/* 打分条和回流箭头 */}
        {KY.map((y, i) => bar > 0 && (
          <g key={i}>
            <rect x={1510} y={y - 10} width={110} height={20} fill="none" stroke={INK} strokeWidth={2} />
            <rect x={1510} y={y - 10} width={110 * SC[i] * span(bar, i * 0.2, i * 0.2 + 0.6)} height={20} fill={RED} opacity={0.75 + 0.25 * flash} />
          </g>
        ))}
        {back > 0 && (
          <g stroke={RED} strokeWidth={3.5} fill="none" strokeLinecap="round">
            <path d={`M1560,${KY[0] - 30} C1540,330 1420,300 ${SX0 + SW + 8},350`} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - back} />
            {back > 0.95 && <path d={`M${SX0 + SW + 26},338 L${SX0 + SW + 6},351 L${SX0 + SW + 26},364`} />}
          </g>
        )}
        {/* 锁孔红圈 */}
        {f >= E.keyhole.s && <circle cx={LX} cy={LY + 40} r={30 + 10 * (1 - span(f, E.keyhole.s, E.keyhole.l, out))} fill="none" stroke={RED} strokeWidth={3.5}
                                     strokeDasharray="7 5" opacity={span(f, E.keyhole.s, E.keyhole.l)} />}
        {/* 钟 */}
        {f >= E.hours.s && (() => { const p = span(f, E.hours.s, E.hours.l + 6, out); return (
          <g transform={`translate(1380 948) scale(${p})`} stroke={INK} strokeWidth={3.5} fill="#F4F1EA" strokeLinecap="round">
            <circle r={30} />
            <line x1={0} y1={0} x2={0} y2={-20} />
            <line x1={0} y1={0} x2={16 * Math.cos((f - E.hours.s) / 4)} y2={16 * Math.sin((f - E.hours.s) / 4)} stroke={RED} />
          </g>); })()}
      </svg>
      {/* 循环四站的字：旧的在左，飞进屏幕后依次改写 */}
      {loopIn > 0 && ANG.map((a, i) => {
        const t = a * Math.PI / 180, x = cx + (R + (i % 2 ? 84 : 46)) * Math.cos(t), y = cy + (R + 34) * Math.sin(t);
        const sw = stage[i] ? span(f, stage[i].s - 4, stage[i].l + 6) : 0;
        return <div key={i} style={{position: "absolute", left: x - 90, top: y - 18, width: 180, textAlign: "center", fontSize: 30, lineHeight: "36px",
                                    color: cur === i ? RED : INK, opacity: loopIn, fontStyle: sw > 0 ? "italic" : "normal"}}>
          {sw > 0 ? <Write p={sw}>{NEW[i]}</Write> : OLD[i]}
        </div>;
      })}
      <div style={{position: "absolute", left: 660, top: SY0 - 72, width: 260, height: 54, textAlign: "center", font: "32px/54px Serif", color: "#E8E4DA"}}>
        <Write p={span(f, E.c42.s, E.c42.l + 6)}>Chemistry42</Write></div>
      <Label x={1110} y={SY0 - 62} w={380} size={26} italic color={SOFT} p={span(f, E.plat.s, E.plat.e)}>the platform here</Label>
      <Label x={L0[0]} y={L0[1] + R0 + 20} w={300} size={28} italic color={SOFT} p={span(f, E.loop.l, E.loop.e)}>that loop</Label>
      <Label x={L1[0]} y={SY0 + 112} w={400} size={24} italic p={span(f, E.models.s, E.models.e)}>dozens of AI models</Label>
      <Part name="book" cx={630} cy={SY0 + SH + 66} w={90} at={E.chem.s} f={f} gate={[0.5, 1]} />
      <Label x={960} y={SY0 + SH + 50} w={500} size={28} p={span(f, E.chem.s, E.chem.e)}>known chemistry</Label>

      {/* 新钥匙和这把锁 */}
      {KY.map((y, i) => <Part key={i} name="key" cx={KX} cy={y} w={130} at={E.mol.s + 4 * i} f={f} gate={[0.1, 0.5]} />)}
      <Label x={KX} y={KY[2] + 34} w={240} size={24} italic p={span(f, E.mol.l, E.mol.e)}>new molecules</Label>
      <Part name="lock" cx={LX} cy={LY} w={150} at={E.exact.s} f={f} gate={[0.5, 1]} />
      <Label x={LX} y={LY + 120} w={280} size={24} italic p={span(f, E.keyhole.s, E.keyhole.e)}>this exact keyhole</Label>

      {/* 最后：新结构冒出，within hours */}
      <Label x={1380} y={760} w={300} size={24} italic color={SOFT} align="left" p={span(f, E.makers.s, E.makers.e)}>its makers say:</Label>
      {[...Array(6)].map((_, i) => <Part key={i} name="key" cx={1420 + i * 70} cy={830} w={60} at={E.turns.s + 8 * i} f={f} gate={[0.1, 0.5]} />)}
      <Label x={1600} y={856} w={300} size={26} p={span(f, E.struct.s, E.struct.e)}>new structures</Label>
      <Pen x={1430} y={920} p={span(f, E.hours.s, E.hours.e)} size={44} rot={-3}>within hours</Pen>

      <Source p={span(f, E.title.l, E.title.l + 20)}>Ivanenkov et al., J. Chem. Inf. Model. 2023; Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual407" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
