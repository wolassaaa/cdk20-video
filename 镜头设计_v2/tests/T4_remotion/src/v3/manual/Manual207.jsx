// HKBU SCIE1007 课程作业的科普视频：第 2 章二维说明书页 2-07（D 画外音）。
// 上半：左边六张资料卡，放大镜扫过；右边核对表五问逐条写出打勾。
// 下半：主论文的 Conflicts of interest：多数作者在英矽智能（它造了这些 AI 工具），论文里公开写明；结论字牌。
// 时间全读 keys_2-07.json（事件表 映射/events/2-07.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_2-07.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Tag, Arrow, Bead, evMap, Label, Pen, PageFrame, Source, Plate, Write} from "./kit.jsx";

const E = evMap(K);
const AR = {magnifier1: 458 / 688, tower: 184 / 677, chip: 1};
const KINDS = ["original study", "method paper", "method paper", "review", "book chapter", "Perspective"];
const Q = [["q1", "What kind of source is it?"], ["q2", "How much of it did we read?"], ["q3", "How strong is the evidence?"], ["q4", "Who did the work?"], ["q5", "Were there controls and repeats?"]];
const QX = 700, QY = 200;

const Scene = () => {
  const f = useCurrentFrame();
  const mv = span(f, E.mag.s, E.mag.e, Easing.inOut(Easing.sin));
  const md = span(f, E.magdown.s, E.magdown.e, Easing.inOut(Easing.cubic));
  const mx = 150 + 400 * mv + (660 - 550) * md, my = 250 + Math.sin(mv * Math.PI * 2) * 120 + 120 * mv + (640 - 370) * md - Math.sin(Math.PI * md) * 40;
  const coi = span(f, E.coi.s, E.coi.e);
  const stamp = span(f, E.open.s, E.open.s + 8, out);
  const u1 = span(f, E.useful.s, E.useful.s + 14, out), u2 = span(f, E.notind.s, E.notind.s + 14, out);
  const bead = [
    [0, 140, 120], [E.cards.l, 160, 170], [E.head.l, QX, QY - 20], ...Q.map(([id], i) => [E[id].l, QX - 40, QY + 70 + i * 64]),
    [E.note.l, 200, 640], [E.coi.l, 520, 660], [E.tower.l, 560, 760], [E.chip.l, 300, 800], [E.open.l, 700, 860], [E.useful.l, 1240, 720], [E.notind.l, 1080, 900], [K.len_f, 1082, 902],
  ];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("2-07.wav")} />
      <PageFrame />
      {/* 六张小卡 */}
      {KINDS.map((k, i) => {
        const p = span(f, E.cards.s + i * 8, E.cards.s + i * 8 + 14, out);
        const x = 110 + (i % 2) * 250, y = 110 + Math.floor(i / 2) * 130;
        const lit = mv < 1 && mv > i / 6 && mv < i / 6 + 0.35;
        return (
          <div key={i} style={{position: "absolute", left: x, top: y + 10 * (1 - p), width: 220, height: 100, opacity: p, background: "#F6F3EC", border: `2px solid ${INK}`, borderRadius: 8,
                               boxSizing: "border-box", padding: "10px 12px", fontSize: 22, fontStyle: "italic", color: lit ? INK : SOFT, boxShadow: lit ? "0 0 0 3px rgba(200,16,46,0.35)" : "none"}}>
            {k}<div style={{height: 3, width: 140, background: "rgba(31,30,28,0.2)", marginTop: 16}} /><div style={{height: 3, width: 100, background: "rgba(31,30,28,0.2)", marginTop: 10}} />
          </div>
        );
      })}
      <div style={{position: "absolute", left: mx - 60, top: my - 60, transform: `rotate(${-20 + 30 * mv - 25 * md}deg)`, opacity: span(f, E.mag.s, E.mag.s + 10)}}>
        <Part name="magnifier1" cx={60} cy={90} w={120} ar={AR.magnifier1} at={E.mag.s} f={f} gate={[0.5, 1]} flood={14} />
      </div>

      {/* 核对表 */}
      <div style={{position: "absolute", left: QX, top: QY - 90, fontSize: 44}}><Write p={span(f, E.head.s, E.head.e)}>For every source, we asked:</Write></div>
      {Q.map(([id, q], i) => {
        const ev = E[id], p = span(f, ev.s, ev.s + 26), tick = span(f, ev.l + 30, ev.l + 42, ease);
        return (
          <React.Fragment key={id}>
            <div style={{position: "absolute", left: QX, top: QY + 50 + i * 64, width: 34, height: 34, border: `2.5px solid ${INK}`, borderRadius: 4, opacity: span(f, ev.s - 6, ev.s)}} />
            <svg width={60} height={60} style={{position: "absolute", left: QX - 6, top: QY + 30 + i * 64}}>
              <path d="M10,34 L22,46 L50,12" fill="none" stroke={RED} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - tick} />
            </svg>
            <div style={{position: "absolute", left: QX + 56, top: QY + 44 + i * 64, fontSize: 36}}><Write p={p}>{q}</Write></div>
          </React.Fragment>
        );
      })}
      <Tag n="18" x={640} y={90} at={E.mag.s + 10} f={f} />

      {/* 下半：利益声明 */}
      <Pen x={110} y={560} p={span(f, E.note.s, E.note.e)} size={44}>one thing worth knowing</Pen>
      <div style={{position: "absolute", left: 110, top: 640, fontSize: 34, fontWeight: 600, letterSpacing: 1}}><Write p={coi}>Conflicts of interest</Write></div>
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <path d="M100,700 L92,700 L92,950 L100,950" fill="none" stroke={INK} strokeWidth={3} opacity={coi} />
        <Arrow d="M300,850 L470,850" tip={[476, 850]} ang={0} a={E.chip.s} b={E.chip.e} f={f} sw={3} />
      </svg>
      <Label x={110} y={690} w={460} size={24} italic color={SOFT} align="left" p={span(f, E.coi.s + 20, E.coi.e)}>most authors of the main study work for</Label>
      <Part name="tower" cx={540} cy={820} w={46} ar={AR.tower} at={E.tower.s + 2} f={f} gate={[0.5, 1]} />
      <Label x={600} y={760} w={300} size={28} align="left" p={span(f, E.tower.s, E.tower.e)}>Insilico Medicine</Label>
      <Part name="chip" cx={220} cy={850} w={110} ar={1} at={E.chip.s + 2} f={f} gate={[0.5, 1]} />
      <div style={{position: "absolute", left: 220 - 34, top: 850 - 9, width: 68, height: 18, background: "#2B2B2D", color: "#C9C6BE", fontSize: 11, textAlign: "center", lineHeight: "18px", opacity: span(f, E.chip.s + 6, E.chip.s + 14)}}>Chemistry42</div>
      <Label x={380} y={870} w={200} size={22} italic color={SOFT} p={span(f, E.chip.s + 10, E.chip.e)}>built its AI tools</Label>
      {stamp > 0 && (
        <div style={{position: "absolute", left: 600, top: 830, padding: "6px 14px", border: `4px solid ${INK}`, borderRadius: 6, fontSize: 28, fontStyle: "italic",
                     transform: `rotate(-6deg) scale(${1.4 - 0.4 * stamp})`, opacity: stamp}}>declared in the paper</div>
      )}
      <Plate x={1010} y={690} w={820} p={u1}><span style={{fontSize: 56}}>Useful evidence,</span></Plate>
      <Plate x={1010} y={780} w={820} p={u2}><span style={{fontSize: 56, fontStyle: "italic"}}>not an independent check.</span></Plate>

      <Source p={span(f, E.cards.l, E.cards.l + 20)}>Ren et al., Chem. Sci. 2023, author affiliations and Conflicts of interest · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual207" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
