// HKBU SCIE1007 课程作业的科普视频：出镜对话 1-05（D）、1-06（B）、1-07（C）。说话人之间硬切，讲解位一张图连贯不断：
// 药 → why not? → 更好的药？→ 胶囊落到一条七站的路起点 → 路被拉长（harder）→ 尺子沿路长出，10–17 years。
// 时间全读 oncam_1-05_1-06_1-07.json（事件表 映射/events/1-05_1-06_1-07.json）。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_1-05_1-06_1-07.json";
import {INK, RED, SOFT, PAPER, ease, out, span, Part, Write} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const AR = {capsule: 530 / 229, ruler: 1130 / 150};
const ST = ["Target", "Hit", "Improve", "Cells", "Animals", "Trials", "Approval"];
const RY = 600;

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  // 胶囊：长出、变亮（better），再缩小落到路的起点
  const glow = span(f, E.better.s, E.better.s + 16, out) * (1 - span(f, E.road.s, E.road.s + 30));
  const go = span(f, E.road.s, E.road.s + 40, Easing.inOut(Easing.cubic));
  // 路：先画到 1700，说到 harder 时拉长到 1840，站点跟着拉开
  const rd = span(f, E.road.s, E.road.e, ease);
  const stretch = span(f, E.harder.s, E.harder.e, Easing.inOut(Easing.cubic));
  const RX0 = 1210, RX1 = 1700 + 140 * stretch;
  const sx = (i) => RX0 + 40 + ((RX1 - 40 - RX0 - 40) * i) / (ST.length - 1);
  const cx = 1420 + (RX0 + 10 - 1420) * go, cy = 380 + (RY - 52 - 380) * go - Math.sin(Math.PI * go) * 60;
  const plate = span(f, E.plate.s, E.plate.s + 14, out);
  const sink = f > E.hard.s ? Math.exp(-(f - E.hard.s) / 6) * Math.sin((f - E.hard.s) / 2.6) * 10 : 0;
  const ul = span(f, E.hard.s + 4, E.hard.s + 24, ease);
  return (
    <OnCamFrame D={D} f={f} wav="1-05_1-06_1-07.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <div style={{position: "absolute", left: 1500, top: 230, font: "46px Hand", color: RED, transform: "rotate(-5deg)", opacity: 1 - span(f, E.road.s, E.road.s + 20)}}>
          <Write p={span(f, E.why.s, E.why.e)}>why not?</Write>
        </div>
        <div style={{position: "absolute", left: 1520, top: 420, font: "44px Hand", color: RED, transform: "rotate(-3deg)", opacity: 1 - span(f, E.road.s, E.road.s + 20)}}>
          <Write p={span(f, E.better.s, E.better.l + 10)}>+ better?</Write>
        </div>
        <div style={{position: "absolute", left: cx - 1420, top: cy - 380, transform: `scale(${1 - 0.55 * go})`, transformOrigin: "1420px 380px", filter: `brightness(${1 + 0.35 * glow}) drop-shadow(0 0 ${18 * glow}px rgba(255,240,200,0.9))`}}>
          <Part name="capsule" cx={1420} cy={380} w={170} ar={AR.capsule} at={E.cap.s + 2} f={f} gate={[0, 0.5]} flood={18} />
        </div>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <path d={`M${RX0},${RY} L${RX1},${RY}`} stroke={INK} strokeWidth={7} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - rd} />
          {ST.map((s, i) => {
            const p = span(rd, (i + 0.4) / (ST.length + 0.6), (i + 1.2) / (ST.length + 0.6), out);
            return <circle key={s} cx={sx(i)} cy={RY} r={12 * p} fill={i === 0 && go >= 1 ? RED : PAPER} stroke={INK} strokeWidth={3.5} />;
          })}
        </svg>
        {ST.map((s, i) => (
          <div key={s} style={{position: "absolute", left: sx(i) - 60, top: RY + 20, width: 120, textAlign: "center", fontSize: 21, opacity: span(rd, (i + 0.6) / (ST.length + 0.6), (i + 1.4) / (ST.length + 0.6))}}>{s}</div>
        ))}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, clipPath: `inset(0 ${100 - (RX0 + (RX1 - RX0) * span(f, E.ruler.s, E.ruler.e, ease)) / 19.2}% 0 0)`}}>
          <Part name="ruler" cx={(RX0 + RX1) / 2} cy={RY + 96} w={RX1 - RX0} ar={AR.ruler} at={E.ruler.s} f={f} gate={[0, 0.5]} wipe={6} flood={10} />
        </div>
        <div style={{position: "absolute", left: RX0, top: RY + 150 + sink, width: RX1 - RX0, textAlign: "center", opacity: plate, transform: `scale(${1.08 - 0.08 * plate})`}}>
          <span style={{fontSize: 80}}>10–17</span><span style={{fontSize: 46, fontStyle: "italic"}}> years</span>
        </div>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <path d={`M${RX0 + 110},${RY + 260 + sink} C${RX0 + 260},${RY + 252 + sink} ${RX1 - 260},${RY + 266 + sink} ${RX1 - 110},${RY + 256 + sink}`} stroke={RED} strokeWidth={5} fill="none" strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - ul} />
        </svg>
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Wang et al., Pharmaceuticals 2023 · Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam105" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
