// HKBU SCIE1007 课程作业的科普视频：第 4 章二维说明书页 4-06（画外音）化学家一直以来的试错循环。
// 主线：一把小钥匙沿循环走 Imagine → Make → Test → fails（变灰打叉）→ Tweak（改形）→ Try again；
// 最后一圈圈转，每过顶站掉一张钞票、日历翻一页，字牌 costs time and money。
// 循环位置、半径、四站字和 Manual407.jsx 开头的旧循环一致（L0 = 300,590，R = 120），两页剪在一起连得上。
// 时间全读 keys_4-06.json（事件表 映射/events/4-06.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_4-06.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, evMap, Label, PageFrame, Source, Plate, Lens, guidePlan} from "./kit.jsx";

const E = evMap(K);
const GP = guidePlan(K);   // 视线引导（11-20，替代红色料珠）：事件表 guide 字段 → resolve.py → keys.guides
const CX = 300, CY = 590, R = 120;
const NAMES = ["Imagine", "Make", "Test", "Tweak"], ANG = [-90, 0, 90, 180];
const LAP = 50;                                                        // 最后几圈每圈帧数
const BX = 1620, BY = 700, CALX = 1300, CALY = 690;

const Scene = () => {
  const f = useCurrentFrame();
  const io = Easing.inOut(Easing.cubic);
  // 小钥匙在圈上的角度
  const laps = Math.max(0, (f - E.round.s) / LAP);
  const ang = -90 + 90 * span(f, E.make.s, E.make.l, io) + 90 * span(f, E.test.s, E.test.l, io) + 90 * span(f, E.tweak.s, E.tweak.l, io)
            + 90 * span(f, E.try.s, E.again.l, io) + 360 * Math.min(3, laps);
  const done = Math.min(3, Math.floor(laps));                           // 转完几圈
  // 箭头转角：平时慢转，again 时快转一圈，最后跟着钥匙
  let rot = 0;
  for (let t = E.always.s; t <= f; t++) rot += t >= E.round.s ? 7.2 : 0.5 + 9 * span(t, E.again.s, E.again.l) * (1 - span(t, E.again.e, E.again.e + 20));
  const circ = span(f, E.always.s, E.always.l + 8, ease);
  const cur = f >= E.round.s ? Math.round(((ang + 90) % 360) / 90) % 4 : f >= E.tweak.l ? 3 : f >= E.test.l ? 2 : f >= E.make.l ? 1 : f >= E.imagine.s ? 0 : -1;
  const failed = f >= E.fails.s && f < E.tweak.l;
  const grey = span(f, E.fails.s, E.fails.l) * (1 - span(f, E.tweak.s, E.tweak.l));
  const ghost = 1 - span(f, E.make.s, E.make.l);
  const squash = f > E.tweak.l ? 1 - 0.25 * Math.exp(-(f - E.tweak.l) / 6) * Math.cos((f - E.tweak.l) / 2.5) : 1;
  const kx = CX + R * Math.cos(ang * Math.PI / 180), ky = CY + R * Math.sin(ang * Math.PI / 180);
  return (
    <Lens plan={GP} f={f}>
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("4-06.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 52}}><Write p={span(f, E.title.s, E.title.e)}>How chemists have always found a key</Write></div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 预告：淡虚线圈和闪线 */}
        {f >= E.tease.s && <circle cx={CX} cy={CY} r={R} fill="none" stroke={SOFT} strokeWidth={3} strokeDasharray="10 10" pathLength={754}
                                   strokeDashoffset={754 * (1 - span(f, E.tease.s, E.tease.l + 20, ease))} opacity={0.7 * (1 - circ)} />}
        {f >= E.mind.s && [0, 60, 120, 180, 240, 300].map((a, i) => {
          const p = span(f, E.mind.s + i, E.mind.l + 8 + i, out), t = (a - 30) * Math.PI / 180, r0 = R + 30, r1 = R + 30 + 30 * p;
          return <line key={i} x1={CX + r0 * Math.cos(t)} y1={CY + r0 * Math.sin(t)} x2={CX + r1 * Math.cos(t)} y2={CY + r1 * Math.sin(t)}
                       stroke={RED} strokeWidth={3.5} strokeLinecap="round" opacity={1 - span(f, E.title.s, E.chem.s)} />;
        })}
        {/* 实线循环和箭头 */}
        {circ > 0 && <circle cx={CX} cy={CY} r={R} fill="none" stroke={INK} strokeWidth={4} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - circ} />}
        {circ >= 1 && [0, 90, 180, 270].map((a) => {
          const t = (a + 45 + rot) * Math.PI / 180;
          return <path key={a} d="M-10,-8 L4,0 L-10,8" fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round"
                       transform={`translate(${CX + R * Math.cos(t)} ${CY + R * Math.sin(t)}) rotate(${a + 45 + rot + 90})`} />;
        })}
        {circ >= 1 && ANG.map((a, i) => <circle key={i} cx={CX + R * Math.cos(a * Math.PI / 180)} cy={CY + R * Math.sin(a * Math.PI / 180)} r={9}
                                                fill={cur === i ? RED : INK} opacity={f >= [E.imagine, E.make, E.test, E.tweak][i].s ? 1 : 0.35} />)}
        {/* 失败的红叉 */}
        {failed && (() => { const p = span(f, E.fails.s, E.fails.l + 6, out); return (
          <g stroke={RED} strokeWidth={6} strokeLinecap="round" transform={`translate(${kx} ${ky - 50})`}>
            <path d={`M-22,-22 L${-22 + 44 * span(p, 0, 0.5)},${-22 + 44 * span(p, 0, 0.5)}`} />
            <path d={`M22,-22 L${22 - 44 * span(p, 0.5, 1)},${-22 + 44 * span(p, 0.5, 1)}`} />
          </g>); })()}
      </svg>

      {/* 四站的字（和 4-07 同一套位置） */}
      {ANG.map((a, i) => {
        const ev = [E.imagine, E.make, E.test, E.tweak][i];
        const t = a * Math.PI / 180, x = CX + (R + (i % 2 ? 84 : 46)) * Math.cos(t), y = CY + (R + 34) * Math.sin(t);
        return <div key={i} style={{position: "absolute", left: x - 90, top: y - 18, width: 180, textAlign: "center", fontSize: 30, lineHeight: "36px", color: cur === i ? RED : INK}}>
          <Write p={span(f, ev.s, ev.l + 6)}>{NAMES[i]}</Write></div>;
      })}
      <Label x={CX} y={CY + R + 66} w={200} size={30} italic color={RED} p={span(f, E.fails.s, E.fails.l + 6) * (1 - span(f, E.tweak.l, E.tweak.l + 14))}>fails</Label>
      <Label x={CX - 150} y={CY - R - 70} w={220} size={28} italic color={RED} p={span(f, E.try.s, E.again.e) * (1 - span(f, E.every.s, E.every.l))}>try again</Label>
      <Part name="person" cx={CX} cy={CY} w={120} at={E.chem.s + 2} f={f} gate={[0.5, 1]} />

      {/* 要找的钥匙：右上虚影 */}
      <div style={{opacity: 0.35}}><Part name="key" cx={680} cy={330} w={230} at={E.key.s + 2} f={f} gate={[0.1, 0.5]} /></div>
      <Label x={680} y={372} w={200} size={28} italic p={span(f, E.key.s, E.key.e)}>a key</Label>

      {/* 沿圈走的小钥匙 */}
      {f >= E.mol.s && (
        <div style={{position: "absolute", left: 0, top: 0, opacity: 0.45 + 0.55 * (1 - ghost),
                     filter: `grayscale(${grey}) brightness(${1 - 0.25 * grey})`, transform: `translate(${kx}px, ${ky}px) scale(${squash}, ${2 - squash})`}}>
          <Part name="key" cx={0} cy={0} w={86} at={E.mol.s + 2} f={f} gate={[0.1, 0.5]} />
        </div>
      )}

      {/* 右边：每一圈都花时间和钱 */}
      <Label x={1300} y={280} w={460} size={34} p={span(f, E.every.s, E.every.e)}>every single round</Label>
      {f >= E.every.l && <div style={{position: "absolute", left: 1150, top: 330, width: 300, textAlign: "center", fontSize: 30}}>
        round <span style={{fontSize: 64, color: RED, display: "inline-block", transform: `scale(${1 + 0.15 * Math.exp(-((f - E.round.s) % LAP) / 5) * (f > E.round.s ? 1 : 0)})`}}>{1 + done}</span></div>}
      <Part name="flask" cx={960} cy={690} w={130} at={E.lab.s + 2} f={f} gate={[0.5, 1]} />
      <Label x={960} y={780} w={240} size={26} italic p={span(f, E.lab.s, E.lab.e)}>in a real lab</Label>
      <div style={{position: "absolute", left: 0, top: 0, transformOrigin: `${CALX}px ${CALY - 70}px`,
                   transform: `scaleY(${1 - 0.22 * Math.sin(Math.PI * Math.min(1, laps > 0 ? (laps % 1) * 3 : 0))})`}}>
        <Part name="cal" cx={CALX} cy={CALY} w={150} at={E.round.s} f={f} gate={[0.5, 0.2]} />
      </div>
      {done > 0 && <div style={{position: "absolute", left: CALX + 82, top: CALY - 96, fontSize: 32, color: RED}}>+{done}</div>}
      {/* 钞票：每转完一圈掉一张 */}
      {[...Array(done)].map((_, i) => {
        const t0 = E.round.s + (i + 1) * LAP, p = span(f, t0, t0 + 14, Easing.in(Easing.quad));
        return <Part key={i} name="banknote" cx={BX + (i - 1) * 12} cy={BY - i * 18 - 260 * (1 - p)} w={200} at={-100} f={f} />;
      })}

      <Plate x={1000} y={860} w={840} p={span(f, E.costs.s, E.costs.s + 14, out)}>
        <span style={{fontSize: 54, fontStyle: "italic"}}>costs <span style={{borderBottom: `4px solid rgba(200,16,46,${span(f, E.time.s, E.time.l)})`}}>time</span> and{" "}
          <span style={{borderBottom: `4px solid rgba(200,16,46,${span(f, E.money.s, E.money.l)})`}}>money</span></span>
      </Plate>

      <Source p={span(f, E.title.l, E.title.l + 20)}>Lengauer 2007 · Illustration</Source>
    </AbsoluteFill>
    </Lens>
  );
};

const Root = () => <Composition id="Manual406" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
