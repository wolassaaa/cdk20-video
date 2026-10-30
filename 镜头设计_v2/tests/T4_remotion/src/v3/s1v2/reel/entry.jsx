// S1 preview reel v1 (00:00–02:21): the picked option per beat, cut together on the storyboard timecodes. Visuals only.
// Public dir = 镜头设计_v3/styleframes/S1/v2/_code/reel/public (recoloured plates + fontana re-renders + placeholder_hand.mp4).
// Reuses the option modules as-is; two small local copies (1-02 liver, W1 Klein v2) exist only because those modules hard-code an old red.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, Sequence, Img, staticFile, useCurrentFrame} from "remotion";
import {C, W, H, BoilProvider, ramp, inOut, outExpo, clamp01} from "../../core";
import {Grain} from "../../texture";
import {OnCamCard} from "../../oncam/Card";
// s102
import {OVitrine} from "../s102/Frames103";
import {T as T2, Src, GM, SRC_HK, SRC_WORLD} from "../s102/lib";
// s104
import {OPTIONS_104} from "../s104/S104";
import {LAYOUTS} from "../s104/Talk";
// s108
import {P as P108} from "../s108/common";
import {LedgerTime, LedgerMoney, LedgerTen} from "../s108/cost";
import {RoadNeon} from "../s108/over3d";
// s110
import {OPTIONS_110} from "../s110/F110";
import {OPTIONS_111} from "../s110/F111";
import {Plate as Plate110, RoadFaint, Finish, K as K110, GROT, SERIF, MONO, SUB, COURSE, MEMBERS} from "../s110/lib";

// s108 keeps its red in a shared palette object (#FF1A2E, pinkish): point it at blood red for the reel without touching the file.
P108.red = C.verm;

const FPS = 30, DUR = 141 * FPS;
const sec = s => Math.round(s * FPS);
const O2_104 = OPTIONS_104.find(o => o.id === "O2").C;
const L3 = LAYOUTS.find(o => o.id === "L3").C;
const S110o2 = OPTIONS_110.find(o => o.id === "S110o2").C;
const M3Blue = OPTIONS_111.find(o => o.id === "S111o3a").C;

// ------------------------------------------------------------------ local: 1-02 glass liver, one continuous push, three type states
// (copy of s102 Opt2Liver hero layout; s102/lib hard-codes RED = #EE1430, so the red accents use C.verm here)
const RED = C.verm;
const SRC_HK23 = "SOURCE  Hong Kong Cancer Registry, Hospital Authority";
const Liver = ({len}) => {
  const f = useCurrentFrame();
  const s = 1 + 0.07 * inOut(f / len);
  const a = 1 - ramp(f, sec(5) - 8, sec(5) + 8), b = Math.min(ramp(f, sec(5) - 8, sec(5) + 8), 1 - ramp(f, sec(10.7) - 8, sec(10.7) + 8)), c = ramp(f, sec(10.7) - 8, sec(10.7) + 8);
  return <AbsoluteFill style={{background: "#000", overflow: "hidden"}}>
    <Img src={staticFile("liver_hero.png")} style={{position: "absolute", left: 0, top: 0, width: W, height: H,
      transform: `translate(${70 - 30 * f / len}px, ${-10 * f / len}px) scale(${s})`, transformOrigin: "62% 45%"}}/>
    <AbsoluteFill style={{background: "linear-gradient(90deg, rgba(6,6,6,0.92) 0%, rgba(6,6,6,0.6) 27%, rgba(6,6,6,0) 44%)"}}/>
    <AbsoluteFill style={{background: "linear-gradient(0deg, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0) 12%)"}}/>
    <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
      <g opacity={a}>
        <T2 x={92} y={560} size={250} weight={100} ls={-10}>1,412</T2>
        <T2 x={104} y={630} size={42} weight={300}>deaths in Hong Kong, 2022</T2>
        <rect x={106} y={662} width={64} height={3} fill={RED}/>
        <Src>{SRC_HK}</Src>
      </g>
      <g opacity={b}>
        <T2 x={104} y={400} size={30} weight={400} font={GM} ls={4} opacity={0.75}>Hong Kong:</T2>
        <T2 x={92} y={560} size={170} weight={100} ls={-6}>Top 3</T2>
        <T2 x={104} y={630} size={42} weight={300}>deadliest cancers</T2>
        <T2 x={104} y={720} size={38} weight={300} opacity={0.8}>lung · colorectal · <tspan fill={RED} fontWeight={400}>liver</tspan></T2>
        <Src>{SRC_HK23}</Src>
      </g>
      <g opacity={c}>
        <T2 x={104} y={400} size={30} weight={400} font={GM} ls={4} opacity={0.75}>World:</T2>
        <T2 x={92} y={560} size={170} weight={100} ls={-6}>6<tspan fontSize={72} dy={-74}>th</tspan></T2>
        <T2 x={268} y={560} size={44} weight={300}>most common</T2>
        <T2 x={92} y={760} size={170} weight={100} ls={-6} color={RED}>3<tspan fontSize={72} dy={-74}>rd</tspan></T2>
        <T2 x={268} y={760} size={44} weight={300}>deadliest</T2>
        <Src>{SRC_WORLD}</Src>
      </g>
      <T2 x={1840} y={1036} size={13} weight={400} font={GM} anchor="end" opacity={0.5} ls={1}>BODYPARTS3D © DBCLS, CC BY 4.0 · RED PORTAL VEIN · BLUE HEPATIC VEINS</T2>
    </svg>
    <Grain opacity={0.14}/>
  </AbsoluteFill>;
};

// ------------------------------------------------------------------ local: W1 Klein field v2 (s110 FW1 hard-codes the "?" as #E0102A)
// "先静半拍，片名砸下": half a second of bare pigment, the title lands, subtitle and credits follow.
const W1 = () => {
  const f = useCurrentFrame();
  const land = ramp(f, 15, 19), slam = 1 + 0.06 * (1 - outExpo(ramp(f, 15, 24)));
  return <AbsoluteFill style={{background: K110.klein, overflow: "hidden"}}>
    <Plate110 src="w_pigment.png" style={{transform: `scale(${1.0 + 0.03 * f / sec(18)})`}}/>
    <div style={{opacity: ramp(f, 60, 90)}}><RoadFaint y={830} color="rgba(237,235,228,0.25)"/></div>
    <div style={{position: "absolute", left: 0, top: 170, width: W, textAlign: "center", fontFamily: GROT, fontWeight: 900, fontSize: 250, letterSpacing: -10,
      color: K110.ink, lineHeight: 0.86, opacity: land, transform: `scale(${slam})`, transformOrigin: "50% 40%"}}>WORTH<br/>TESTING<span style={{color: C.verm}}>?</span></div>
    <div style={{position: "absolute", left: 0, top: 640, width: W, textAlign: "center", fontFamily: SERIF, fontSize: 44, color: K110.ink, opacity: ramp(f, 36, 54)}}>{SUB}</div>
    <div style={{position: "absolute", left: 0, top: 960, width: W, textAlign: "center", fontFamily: MONO, fontSize: 13, letterSpacing: 3, color: K110.ink, opacity: ramp(f, 66, 90)}}>{COURSE}   ·   {MEMBERS.join("  ·  ")}</div>
    <Finish grain={0.18} vignette={0.25}/>
    <AbsoluteFill style={{background: "#000", opacity: ramp(f, sec(18) - 20, sec(18))}}/>
  </AbsoluteFill>;
};

const Bg = ({src}) => <Img src={staticFile(src)} style={{position: "absolute", left: 0, top: 0, width: W, height: H}}/>;

// ------------------------------------------------------------------ 1-01: fontana four cuts + A's card live
const Fontana101 = () => <AbsoluteFill style={{background: "#000"}}>
  <Bg src="fontana_1-01.png"/>
  <Grain opacity={0.08}/>
</AbsoluteFill>;

// ------------------------------------------------------------------ 1-05..1-07: one continuous take of the L3 strip, re-laid per speaker
// Each speaker's segment is offset so the cards (and their footage) keep running instead of re-growing on every line.
const TALK = [["D", 52, 54.7], ["B", 54.7, 57.0], ["C", 57.0, 60]];
// C's layout lifts the prints 60 px: a 6-frame dissolve hides the jump.
const Fade = ({n, children}) => { const f = useCurrentFrame(); return <AbsoluteFill style={{opacity: n ? inOut(ramp(f, 0, n)) : 1}}>{children}</AbsoluteFill>; };
const Talk = () => <>{TALK.map(([who, a, b]) => { const n = who === "C" ? 6 : 0, st = sec(a) - sec(52) - n;
  return <Sequence key={who} from={st} durationInFrames={sec(b) - sec(a) + n}>
    <Fade n={n}><Sequence from={-st}><L3 who={who}/></Sequence></Fade>
  </Sequence>; })}</>;

// 1-04 a: "Nexavar" gets struck through in blood red on "从 Nexavar 换成……" (the module only greys it)
const Strike = () => { const f = useCurrentFrame(), d = inOut(ramp(f, sec(3.0), sec(3.5)));
  return <svg width={W} height={H} style={{position: "absolute", left: 0, top: 0}}>
    <line x1={104} y1={180} x2={104 + 250 * d} y2={178} stroke={C.verm} strokeWidth={4} opacity={d > 0 ? 1 : 0}/>
  </svg>; };

// ------------------------------------------------------------------ shot list: [from s, to s, fade-in frames, push [s0, s1], render]
// fade-in = the shot dissolves in over the one below it (which is held under it for those frames). 0 = hard cut.
const kick = f => 1 + 0.035 * (1 - outExpo(ramp(f, 0, 9)));
const SHOTS = [
  // W0: one cut per drum hit (0, 0.67, 1.33 s), each lands with a small settle
  {a: 0, b: 0.67, fi: 0, kick: true, el: <Bg src="fontana_hit1.png"/>},
  {a: 0.67, b: 1.33, fi: 0, kick: true, el: <Bg src="fontana_hit2.png"/>},
  {a: 1.33, b: 2, fi: 0, kick: true, el: <Bg src="fontana_hit3.png"/>},
  // 1-01 A on camera
  {a: 2, b: 8, fi: 0, push: [1.0, 1.04], el: <Fontana101/>, over: <OnCamCard who="A" src={staticFile("placeholder_hand.mp4")} videoStart={40} dur={sec(6)}/>},
  // 1-02 A VO: glass liver (its own push inside)
  {a: 8, b: 25, fi: 18, el: <Liver len={sec(17)}/>},
  // 1-03 A on camera: capsule row (vitrine), card inside the module
  {a: 25, b: 31, fi: 0, push: [1.0, 1.015], el: <OVitrine obj="row"/>},
  // 1-04 D VO: pigment field a v2 -> b -> c
  {a: 31, b: 39, fi: 15, push: [1.0, 1.04], el: <><O2_104 part="a" v={2}/><Strike/></>},
  {a: 39, b: 46, fi: 20, push: [1.02, 1.05], el: <O2_104 part="b"/>},
  {a: 46, b: 52, fi: 20, push: [1.0, 1.035], el: <O2_104 part="c"/>},
  // 1-05..1-07 D, B, C on camera
  {a: 52, b: 60, fi: 0, el: <Talk/>},
  // 1-08 C VO: Swiss ledger
  {a: 60, b: 66, fi: 0, push: [1.0, 1.02], el: <LedgerTime/>},
  {a: 66, b: 70.5, fi: 8, push: [1.0, 1.02], el: <LedgerMoney/>},
  {a: 70.5, b: 76, fi: 8, push: [1.0, 1.02], el: <LedgerTen/>},
  // 1-09 D VO: neon metro, lit as the line walks the road: WE ARE HERE (2) -> 4 -> all six + "Any step can fail."
  {a: 76, b: 82.5, fi: 15, push: [1.0, 1.03], el: <RoadNeon lit={2} flag={1}/>},
  {a: 82.5, b: 89, fi: 15, push: [1.01, 1.04], el: <RoadNeon lit={4}/>},
  {a: 89, b: 96, fi: 15, push: [1.02, 1.05], el: <RoadNeon lit={6}/>},
  // 1-10 B VO: pLDDT lacquer AlphaFold
  {a: 96, b: 112, fi: 15, push: [1.0, 1.06], el: <S110o2/>},
  // 1-11 C VO: blue sea a -> b
  {a: 112, b: 118, fi: 15, push: [1.0, 1.06], el: <M3Blue part="a"/>},
  {a: 118, b: 123, fi: 18, push: [1.0, 1.03], el: <M3Blue part="b"/>},
  // W1 title on the Klein field
  {a: 123, b: 141, fi: 0, el: <W1/>},
];

const Shot = ({s, tail}) => {
  const f = useCurrentFrame(), len = sec(s.b) - sec(s.a) + tail;
  const op = s.fi ? inOut(ramp(f, 0, s.fi)) : 1;
  const sc = s.kick ? kick(f) : s.push ? s.push[0] + (s.push[1] - s.push[0]) * (f / len) : 1;
  return <AbsoluteFill style={{opacity: op, overflow: "hidden", background: "#000"}}>
    <AbsoluteFill style={{transform: `scale(${sc})`, transformOrigin: "50% 50%"}}>{s.el}</AbsoluteFill>
    {s.over ? <AbsoluteFill>{s.over}</AbsoluteFill> : null}
  </AbsoluteFill>;
};

// ------------------------------------------------------------------ caption strip for review (beat · who · Chinese reading line), timed per sentence
const CAP = [
  [0, 2, "W0 · 纯音乐 · 三下鼓点，每下割一刀"],
  [2, 8, "1-01 · A 出镜 · 在香港，每天大约有四个人死于肝癌。"],
  [8, 13, "1-02 · A 画外音 · 光是 2022 年，就有 1,412 人。"],
  [13, 18.7, "1-02 · A 画外音 · 在香港，它是最致命的三种癌症之一，另外两种是肺癌和大肠癌。"],
  [18.7, 25, "1-02 · A 画外音 · 而且不只是香港：在全世界，它是第六常见、第三致命的癌症。"],
  [25, 31, "1-03 · A 出镜 · 问题在于：药，我们是有的。只是还不够好。"],
  [31, 39, "1-04 · D 画外音 · 晚期肝癌的标准一线治疗已经换过一次，从 Nexavar（索拉非尼）换成阿替利珠单抗加贝伐珠单抗的组合。"],
  [39, 46, "1-04 · D 画外音 · 但在香港，五年后还活着的病人大约只有十分之三（和同龄人相比）。"],
  [46, 52, "1-04 · D 画外音 · 我们跟进的这项研究说：病人的需求还远远没有被满足。"],
  [52, 54.7, "1-05 · D 出镜 · 那……为什么不干脆做一种更好的药？"],
  [54.7, 57, "1-06 · B 出镜 · 因为这比听起来难太多了。"],
  [57, 60, "1-07 · C 出镜 · 难到什么程度？十到十七年的那种难。"],
  [60, 66, "1-08 · C 画外音 · 如果在我们出生那年开始找一种新药，它可能现在才刚刚准备好。"],
  [66, 70.5, "1-08 · C 画外音 · 花费可能将近 28 亿美元。"],
  [70.5, 76, "1-08 · C 画外音 · 而在人身上测试的药，大约只有十分之一能最终上市。"],
  [76, 82.5, "1-09 · D 画外音 · 要明白为什么，我们来跟着一种药走一遍。每一种药都走同一条路：找到靶点；找到命中物……"],
  [82.5, 89, "1-09 · D 画外音 · ……改进它；先在细胞、再在动物身上测试；"],
  [89, 96, "1-09 · D 画外音 · 然后是人体试验，一期、二期、三期；最后获批。每一步都可能失败。"],
  [96, 104, "1-10 · B 画外音 · 有意思的地方来了。2024 年诺贝尔化学奖的一部分，"],
  [104, 112, "1-10 · B 画外音 · 颁给了 Demis Hassabis 和 John Jumper，表彰 AlphaFold——一个能预测蛋白质形状的 AI。"],
  [112, 118, "1-11 · C 画外音 · 那么，AI 能不能把头几步走得更快？我们来跟一个真实案例：AI 工具向肝癌发起挑战。"],
  [118, 123, "1-11 · C 画外音 · 而这个故事有一部分，就从香港开始。"],
  [123, 141, "W1 · 纯音乐 · 片名"],
];
const tc = f => { const s = Math.floor(f / FPS); return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`; };
const Captions = () => {
  const f = useCurrentFrame(), t = f / FPS;
  const c = CAP.find(([a, b]) => t >= a && t < b);
  return <AbsoluteFill style={{pointerEvents: "none"}}>
    <div style={{position: "absolute", left: 0, right: 0, bottom: 0, height: 52, background: "linear-gradient(0deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.35) 70%, rgba(0,0,0,0) 100%)"}}/>
    <div style={{position: "absolute", left: 40, right: 170, bottom: 9, fontFamily: "'Microsoft YaHei', 'PingFang SC', sans-serif", fontSize: 22,
      color: C.ink, opacity: 0.62, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis"}}>{c ? c[2] : ""}</div>
    <div style={{position: "absolute", right: 40, bottom: 11, fontFamily: "Consolas, monospace", fontSize: 18, color: C.ink, opacity: 0.45, letterSpacing: 1}}>{tc(f)}</div>
  </AbsoluteFill>;
};

export const S1Reel = ({captions = true}) => <BoilProvider rate={2.5}>
  <AbsoluteFill style={{background: "#000"}}>
    {SHOTS.map((s, i) => {
      const tail = SHOTS[i + 1] ? SHOTS[i + 1].fi : 0;
      return <Sequence key={i} from={sec(s.a)} durationInFrames={sec(s.b) - sec(s.a) + tail}><Shot s={s} tail={tail}/></Sequence>;
    })}
    {captions ? <Captions/> : null}
  </AbsoluteFill>
</BoilProvider>;

const Root = () => <>
  <Composition id="S1Reel" component={S1Reel} durationInFrames={DUR} fps={FPS} width={1920} height={1080} defaultProps={{captions: true}}/>
</>;
registerRoot(Root);
