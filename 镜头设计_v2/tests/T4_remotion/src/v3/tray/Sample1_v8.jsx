// v8 copy of Sample1.jsx: person framed by frame8.json.
// HKBU SCIE1007 课程作业的科普视频。托盘样板 1（11-16）：只覆盖 3-01，时间线 84（2-08 末帧开始拉远）到 466（推近落到 3-02 第一帧前一帧），声音只有 3-01 录音。由 Tray2.jsx 复制，Tray2.jsx 不动。
// 原注：出镜段"托盘"试片 1 第 2 版（台面格子、低机位、大物体；成片从第 30 帧起，到 3-02 的 protein 字出现为止）：2-08 末尾拉远 → 3-01（D 出镜，托盘上锁和钥匙）→ 推近进 3-02。
// 底：细胞纸底（D 的 wideplate）；托盘和三维物体：inserts/bl_tray.py 的透明帧；人：prep.py 出的带阴影 RGBA 帧；批注、字、转场在这里。
import React from "react";
import {AbsoluteFill, Composition, Freeze, Img, OffthreadVideo, Sequence, Audio, interpolate, Easing, registerRoot, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import B from "./beats2.json";
import F8 from "./frame8.json";   // v8：人像构图（restill8.py 写）

const INK = "#111113", RED = "#E8190F", BONE = "rgb(236,234,228)";
const SERIF = "TraySerif", PEN = "TrayPen";
const fontHandle = delayRender("fonts");
Promise.all([new FontFace(SERIF, `url(${staticFile("fonts/InstrumentSerif-Regular.ttf")})`), new FontFace(PEN, `url(${staticFile("fonts/Caveat.ttf")})`)].map((f) => f.load().then((x) => document.fonts.add(x)))).then(() => continueRender(fontHandle));

const ease = Easing.bezier(0.45, 0, 0.25, 1);
const ramp = (f, a, b, from = 0, to = 1) => interpolate(f, [a, b], [from, to], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease});
const pad = (n) => String(n).padStart(4, "0");
const [P0, P1] = B.pull, [U0, U1] = B.push, T = B.t301;
const TRAY_FIRST = 84, TRAY_LAST = 570, CUT = 84, END = 467;

// 收尾（v2）：3-02 第一帧从托盘中心长到满屏，最后一帧就是 3-02 首帧（同 Tray3.jsx 的 Grow）
const Grow = ({f, a, b, cx, cy, src}) => {
  if (f < a) return null;
  const z = ramp(f, a, b), s = 0.46 + 0.54 * z, feather = 160 * (1 - z), o = Math.min(1, (f - a + 1) / 4);
  const m = `linear-gradient(to right, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%), linear-gradient(to bottom, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%)`;
  const tx = (cx - 960) * (1 - z) + 960 * (1 - s), ty = (cy - 540) * (1 - z) + 540 * (1 - s);
  return <AbsoluteFill style={{opacity: o, transformOrigin: "0 0", transform: `translate(${tx}px, ${ty}px) scale(${s})`}}>
    <AbsoluteFill style={{WebkitMaskImage: m, maskImage: m, WebkitMaskComposite: "source-in", maskComposite: "intersect"}}><Img src={staticFile(src)} style={{width: 1920, height: 1080}} /></AbsoluteFill>
  </AbsoluteFill>;
};

// 笔写：Caveat，从左到右写出（裁切），略斜
const Pen = ({f, a, b, out, x, y, size = 46, children, color = INK, rot = -3}) => {
  const w = ramp(f, a, b), o = 1 - ramp(f, out, out + 8);
  if (f < a) return null;
  return <div style={{position: "absolute", left: x, top: y, transform: `rotate(${rot}deg)`, fontFamily: PEN, fontSize: size, color, opacity: o, whiteSpace: "nowrap", clipPath: `inset(-20% ${100 - w * 100}% -20% -5%)`}}>{children}</div>;
};
// Instrument Serif 名字：10 帧淡入上移
const Word = ({f, a, b, out, x, y, size = 64, children}) => {
  if (f < a) return null;
  const k = ramp(f, a, b), o = k * (1 - ramp(f, out, out + 8));
  return <div style={{position: "absolute", left: x, top: y + 12 * (1 - k), fontFamily: SERIF, fontSize: size, color: INK, opacity: o, whiteSpace: "nowrap", lineHeight: 1}}>{children}</div>;
};

export const TraySample1 = () => {
  const f = useCurrentFrame() + CUT;
  // 2-08：缩到托盘位置（0.46 倍，中心到 1340,520），边缘羽化，后 10 帧淡出
  const z = ramp(f, P0, P1);
  const s = 1 - 0.54 * z, feather = 160 * z;
  const m = `linear-gradient(to right, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%), linear-gradient(to bottom, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%)`;
  const a208 = 1 - ramp(f, P1 - 10, P1);
  const plateO = ramp(f, P0, P1) * (1 - ramp(f, U0, U1));
  const trayO = f < U0 ? ramp(f, P0 + 10, P1) : 1;
  const pIn = ramp(f, B.person_in[0], B.person_in[1]), pOut = ramp(f, B.person_out[0], B.person_out[1]);
  const pi = f - T;
  const s3 = ramp(f, B.s3_in[0], B.s3_in[1]);
  const notes = f < U0 + 8;
  return (
    <AbsoluteFill style={{background: BONE}}>
      {plateO > 0 && <AbsoluteFill style={{opacity: plateO}}>
        {f < T ? <Freeze frame={0}><OffthreadVideo src={staticFile("plate.mp4")} muted style={{width: 1920, height: 1080}} /></Freeze>
          : <Sequence from={T - CUT}><OffthreadVideo src={staticFile("plate.mp4")} muted style={{width: 1920, height: 1080}} /></Sequence>}
      </AbsoluteFill>}
      {f >= TRAY_FIRST && f <= TRAY_LAST && <Img src={staticFile(`tray2/tray2_${pad(f)}.png`)} style={{position: "absolute", width: 1920, height: 1080, opacity: trayO}} />}
      {pi >= 0 && pi < 373 && pOut < 1 && <Img src={staticFile(`person/p_${pad(pi)}.png`)} style={{position: "absolute", width: 1920, height: 1080, opacity: pIn * (1 - pOut), transformOrigin: `${F8.s1[0].ox}px 1080px`, transform: `translate(${F8.s1[0].px - 80 * pOut}px, ${40 * (1 - pIn)}px) scale(${F8.s1[0].ps})`}} />}
      {f < P1 && <AbsoluteFill style={{opacity: a208, transformOrigin: "0 0", transform: `translate(${(1340 - 960) * z + 960 * (1 - s)}px, ${(520 - 540) * z + 540 * (1 - s)}px) scale(${s})`}}>
        <AbsoluteFill style={{WebkitMaskImage: m, maskImage: m, WebkitMaskComposite: "source-in", maskComposite: "intersect"}}>
          <OffthreadVideo src={staticFile("a208.mp4")} muted style={{width: 1920, height: 1080}} />
        </AbsoluteFill>
      </AbsoluteFill>}
      {notes && <>
        <Pen f={f} a={175} b={205} out={250} x={925} y={286} size={62} color={RED}>station 1: target</Pen>
        <Word f={f} a={320} b={330} out={437} x={1420} y={392} size={60}>lock</Word>
        <Word f={f} a={430} b={440} out={437} x={1010} y={672} size={60}>key</Word>
        <div style={{position: "absolute", right: 140, top: 832, fontFamily: SERIF, fontSize: 22, color: "rgba(17,17,19,0.55)", opacity: ramp(f, P1, P1 + 12) * (1 - ramp(f, U0, U0 + 8))}}>Illustration · Lengauer 2007</div>
      </>}
      {f >= 544 && <Sequence from={544 - CUT}><AbsoluteFill style={{opacity: s3}}><OffthreadVideo src={staticFile("s3.mp4")} muted style={{width: 1920, height: 1080}} /></AbsoluteFill></Sequence>}
      <Grow f={f} a={END - 24} b={END - 1} cx={1340} cy={520} src="s302.png" />
      <Sequence from={-CUT}><Audio src={staticFile("audio301.wav")} /></Sequence>
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="TraySample1" component={TraySample1} durationInFrames={END - CUT} fps={60} width={1920} height={1080} />;
registerRoot(Root);
