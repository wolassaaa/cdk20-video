// S1 preview reel v2 (00:00–02:21): v1 plus the director's 10-30 notes: animated W0/1-01, 1-08, 1-09; glass organs in 1-02;
// a readable drug switch and 3-in-10 in 1-04; a recognisable Hong Kong map in 1-11 (modules in ./organs102, ./drugs104, ./map111, ./motion).
// Public dir = 镜头设计_v3/styleframes/S1/v2/_code/reel/public (recoloured plates + fontana re-renders + placeholder_hand.mp4).
// Reuses the option modules as-is; two small local copies (1-02 liver, W1 Klein v2) exist only because those modules hard-code an old red.
// Every frame number here and in the modules counts at 30 fps; the fps prop (30 or 60) only changes how finely they are sampled, see ../../time30.jsx.
import React from "react";
import {registerRoot, Composition, AbsoluteFill, Img, staticFile} from "remotion";
import {C, W, H, BoilProvider, ramp, inOut, outExpo, clamp01} from "../../core";
import {useFrame30, Seq30, toFps} from "../../time30";
import {Grain, GrainScale, BakedNoise} from "../../texture";
import {OnCamCard} from "../../oncam/Card";
// s102
import {OVitrine} from "../s102/Frames103";
// s104
import {LAYOUTS} from "../s104/Talk";
// s108
import {P as P108} from "../s108/common";
// reel2 modules
import {BeatW0, Beat101Bg, Beat108, Beat109} from "./motion";
import {Beat102} from "./organs102";
import {Beat104} from "./drugs104";
import {Beat111} from "./map111";
// s110
import {OPTIONS_110} from "../s110/F110";
import {Plate as Plate110, RoadFaint, Finish, K as K110, GROT, SERIF, MONO, SUB, COURSE, MEMBERS} from "../s110/lib";

// s108 keeps its red in a shared palette object (#FF1A2E, pinkish): point it at blood red for the reel without touching the file.
P108.red = C.verm;

const FPS = 30, DUR = 141 * FPS;
const sec = s => Math.round(s * FPS);
const L3 = LAYOUTS.find(o => o.id === "L3").C;
const S110o2 = OPTIONS_110.find(o => o.id === "S110o2").C;

// ------------------------------------------------------------------ local: W1 Klein field v2 (s110 FW1 hard-codes the "?" as #E0102A)
// "先静半拍，片名砸下": half a second of bare pigment, the title lands, subtitle and credits follow.
const W1 = () => {
  const f = useFrame30();
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

// ------------------------------------------------------------------ 1-05..1-07: one continuous take of the L3 strip, re-laid per speaker
// Each speaker's segment is offset so the cards (and their footage) keep running instead of re-growing on every line.
const TALK = [["D", 52, 54.7], ["B", 54.7, 57.0], ["C", 57.0, 60]];
// C's layout lifts the prints 60 px: a 6-frame dissolve hides the jump.
const Fade = ({n, children}) => { const f = useFrame30(); return <AbsoluteFill style={{opacity: n ? inOut(ramp(f, 0, n)) : 1}}>{children}</AbsoluteFill>; };
const Talk = () => <>{TALK.map(([who, a, b]) => { const n = who === "C" ? 6 : 0, st = sec(a) - sec(52) - n;
  return <Seq30 key={who} from={st} durationInFrames={sec(b) - sec(a) + n}>
    <Fade n={n}><Seq30 from={-st}><L3 who={who}/></Seq30></Fade>
  </Seq30>; })}</>;

// ------------------------------------------------------------------ shot list: [from s, to s, fade-in frames, push [s0, s1], render]
// fade-in = the shot dissolves in over the one below it (which is held under it for those frames). 0 = hard cut.
const kick = f => 1 + 0.035 * (1 - outExpo(ramp(f, 0, 9)));
const SHOTS = [
  {a: 0, b: 2, fi: 0, el: <BeatW0/>},
  // 1-01 A on camera: the canvas keeps moving under A's card
  {a: 2, b: 8, fi: 0, el: <Beat101Bg/>, over: <OnCamCard who="A" src={staticFile("placeholder_hand.mp4")} videoStart={40} dur={sec(6)}/>},
  {a: 8, b: 25, fi: 18, el: <Beat102/>},
  {a: 25, b: 31, fi: 0, push: [1.0, 1.015], el: <OVitrine obj="row"/>},
  {a: 31, b: 52, fi: 15, el: <Beat104/>},
  {a: 52, b: 60, fi: 0, el: <Talk/>},
  {a: 60, b: 76, fi: 0, el: <Beat108/>},
  {a: 76, b: 96, fi: 15, el: <Beat109/>},
  {a: 96, b: 112, fi: 15, push: [1.0, 1.06], el: <S110o2/>},
  {a: 112, b: 123, fi: 15, el: <Beat111/>},
  {a: 123, b: 141, fi: 0, el: <W1/>},
];

const Shot = ({s, tail}) => {
  const f = useFrame30(), len = sec(s.b) - sec(s.a) + tail;
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
  const f = useFrame30(), t = f / FPS;
  const c = CAP.find(([a, b]) => t >= a && t < b);
  return <AbsoluteFill style={{pointerEvents: "none"}}>
    <div style={{position: "absolute", left: 0, right: 0, bottom: 0, height: 52, background: "linear-gradient(0deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.35) 70%, rgba(0,0,0,0) 100%)"}}/>
    <div style={{position: "absolute", left: 40, right: 170, bottom: 9, fontFamily: "'Microsoft YaHei', 'PingFang SC', sans-serif", fontSize: 22,
      color: C.ink, opacity: 0.62, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis"}}>{c ? c[2] : ""}</div>
    <div style={{position: "absolute", right: 40, bottom: 11, fontFamily: "Consolas, monospace", fontSize: 18, color: C.ink, opacity: 0.45, letterSpacing: 1}}>{tc(f)}</div>
  </AbsoluteFill>;
};

// Director (10-30): grain and boil read as blur and flicker. Default: no moving grain, boil frozen (lines stop re-drawing),
// plus one very faint static dither so dark gradients don't band. grain/boil props bring the textured look back.
// noiseDir: public/ folder of baked 4K noise plates (see BakedNoise in texture.jsx), for --scale=2 only. null = live filters.
export const S1Reel = ({captions = true, grain = 0, boil = false, dither = 0.035, noiseDir = null}) => <BakedNoise.Provider value={noiseDir}><GrainScale.Provider value={grain}><BoilProvider rate={2.5} frozen={!boil}>
  <AbsoluteFill style={{background: "#000"}}>
    {SHOTS.map((s, i) => {
      const tail = SHOTS[i + 1] ? SHOTS[i + 1].fi : 0;
      return <Seq30 key={i} from={sec(s.a)} durationInFrames={sec(s.b) - sec(s.a) + tail}><Shot s={s} tail={tail}/></Seq30>;
    })}
    {dither ? <GrainScale.Provider value={1}><BoilProvider frozen><Grain opacity={dither}/></BoilProvider></GrainScale.Provider> : null}
    {captions ? <Captions/> : null}
  </AbsoluteFill>
</BoilProvider></GrainScale.Provider></BakedNoise.Provider>;

const Root = () => <>
  <Composition id="S1Reel" component={S1Reel} durationInFrames={DUR} fps={FPS} width={1920} height={1080} defaultProps={{captions: true, grain: 0, boil: false, dither: 0.035, noiseDir: null, fps: FPS}}
    calculateMetadata={({props}) => ({fps: props.fps, durationInFrames: toFps(DUR, props.fps)})}/>
</>;
registerRoot(Root);
