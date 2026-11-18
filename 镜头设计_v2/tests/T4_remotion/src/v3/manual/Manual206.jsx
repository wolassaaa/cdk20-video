// HKBU SCIE1007 课程作业的科普视频：第 2 章二维说明书页 2-06（C 画外音）。
// 左栏：我们读（书、a lot）、没有自己的实验（烧瓶打叉）→ a literature review。
// 中间：主论文（Ren et al. 2023）盖 original research 章，旁边是补充数据；周围一圈虚线，六张资料卡按类型弹出。
// 时间全读 keys_2-06.json（事件表 映射/events/2-06.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_2-06.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Tag, Bead, evMap, Label, Pen, PageFrame, Source, Plate, Write} from "./kit.jsx";

const E = evMap(K);
const AR = {book: 554 / 506, flask: 1, paper1: 441 / 582, disks: 1};
const CEN = [1200, 500];
const CARDS = [
  ["c1", [860, 330], "original study", "Feng et al. 2011 · Hong Kong"],
  ["c2", [1200, 170], "method paper", "AlphaFold · Jumper et al. 2021"],
  ["c3", [1540, 330], "method paper", "Chemistry42 · Ivanenkov et al. 2023"],
  ["c4", [1560, 740], "review", "Wang et al. 2023"],
  ["c5", [1200, 860], "book chapter", "Lengauer 2007"],
  ["c6", [860, 690], "Perspective", "Bender et al. 2026"],
];

const Card = ({id, pos, kind, name, f}) => {
  const ev = E[id];
  const p = span(f, ev.s, ev.l, Easing.out(Easing.back(1.4)));
  if (p <= 0) return null;
  const x = CEN[0] + (pos[0] - CEN[0]) * p, y = CEN[1] + (pos[1] - CEN[1]) * p;
  const nameP = span(f, ev.l, ev.l + 20);
  return (
    <div style={{position: "absolute", left: x - 175, top: y - 55, width: 350, height: 110, background: "#F6F3EC", border: `2px solid ${INK}`, borderRadius: 8,
                 boxSizing: "border-box", padding: "10px 14px", transform: `scale(${0.4 + 0.6 * Math.min(1, p)})`, boxShadow: "0 6px 14px rgba(31,30,28,0.12)"}}>
      <div style={{fontSize: 22, fontStyle: "italic", color: SOFT}}>{kind}</div>
      <div style={{fontSize: 22, marginTop: 6, whiteSpace: "nowrap"}}><Write p={nameP}>{name}</Write></div>
    </div>
  );
};

const Scene = () => {
  const f = useCurrentFrame();
  const cross = span(f, E.cross.s, E.cross.s + 20, ease);
  const review = span(f, E.review.s, E.review.s + 14, out);
  const stamp = span(f, E.stamp.s, E.stamp.s + 8, out);
  const ring = span(f, E.ring.s, E.ring.e, ease);
  const absP = span(f, E.abs.s, E.abs.s + 30);
  const bead = [
    [0, 120, 80], [E.title.l, 420, 90], [E.books.l, 240, 300], [E.alot.l, 380, 250], [E.flask.l, 240, 560], [E.review.l, 330, 780],
    [E.centre.l, CEN[0], CEN[1] - 200], [E.stamp.l, CEN[0] + 40, CEN[1] + 40], [E.si.l, CEN[0] + 190, CEN[1] - 50], [E.ring.l, CEN[0] - 330, CEN[1]],
    ...CARDS.map(([id, pos]) => [E[id].l, pos[0], pos[1] - 70]), [E.abs.l, 735, 790], [K.len_f, 737, 792],
  ];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("2-06.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>How we checked</Write></div>

      {/* 左栏 */}
      <Part name="book" cx={240} cy={320} w={210} ar={AR.book} at={E.books.s + 2} f={f} gate={[0.5, 1]} />
      <Pen x={360} y={240} p={span(f, E.alot.s, E.alot.e)} size={50}>a lot.</Pen>
      <Part name="flask" cx={240} cy={570} w={150} ar={AR.flask} at={E.flask.s + 2} f={f} gate={[0.5, 1]} />
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <path d="M150,480 L330,660" stroke={RED} strokeWidth={8} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(cross, 0, 0.5)} />
        <path d="M330,480 L150,660" stroke={RED} strokeWidth={8} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(cross, 0.5, 1)} />
        <circle cx={CEN[0]} cy={CEN[1]} r={360} fill="none" stroke={INK} strokeWidth={2} strokeDasharray="10 10" opacity={0.35} pathLength={1000} style={{strokeDashoffset: 0, clipPath: `inset(0 0 ${100 - ring * 100}% 0)`}} />
      </svg>
      <Label x={360} y={668} w={300} size={24} italic color={SOFT} p={span(f, E.cross.s + 10, E.cross.e)} align="left">no lab work of our own</Label>
      <Plate x={96} y={740} w={520} p={review}><span style={{fontSize: 46, fontStyle: "italic"}}>a literature review</span></Plate>

      {/* 中间：主论文 */}
      <Part name="paper1" cx={CEN[0]} cy={CEN[1]} w={250} ar={AR.paper1} at={E.centre.s + 2} f={f} gate={[0.5, 1]} />
      {stamp > 0 && (
        <div style={{position: "absolute", left: CEN[0] - 150, top: CEN[1] + 10, padding: "6px 14px", border: `4px solid ${RED}`, color: RED, borderRadius: 6, fontSize: 30,
                     fontStyle: "italic", transform: `rotate(-8deg) scale(${1.4 - 0.4 * stamp})`, opacity: stamp, background: "rgba(246,243,236,0.85)"}}>original research</div>
      )}
      <Label x={CEN[0]} y={CEN[1] + 186} w={420} size={24} p={span(f, E.cite.s, E.cite.e)}>Ren et al., Chemical Science, 2023</Label>
      <Part name="disks" cx={CEN[0] + 200} cy={CEN[1] + 20} w={100} ar={AR.disks} at={E.si.s + 2} f={f} gate={[0, 0.5]} flood={16} />
      <Label x={CEN[0] + 200} y={CEN[1] + 66} w={220} size={20} color={SOFT} italic p={span(f, E.si.l, E.si.e)}>supplementary data</Label>
      <Tag n="17" x={CEN[0] - 105} y={CEN[1] - 190} at={E.centre.l + 16} f={f} />

      {CARDS.map(([id, pos, kind, name]) => <Card key={id} id={id} pos={pos} kind={kind} name={name} f={f} />)}
      {absP > 0 && <Pen x={760} y={748} p={absP} size={34} rot={-3}>abstract only</Pen>}

      <Source p={span(f, E.title.l, E.title.l + 20)}>Ren et al., Chem. Sci. 2023 (and supplementary information); Feng et al. 2011; Jumper et al. 2021; Ivanenkov et al. 2023; Wang et al. 2023; Lengauer 2007; Bender et al. 2026 (abstract) · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual206" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
