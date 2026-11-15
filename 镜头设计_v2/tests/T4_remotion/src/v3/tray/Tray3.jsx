// HKBU SCIE1007 课程作业的科普视频。托盘样板 2（4-11 D → 4-12 A，托盘镜像正反打，推近进 5-01）和样板 3（3-09 B，托盘压暗，推近进 W2）。
// 底：说话人的细胞纸底；托盘和三维物体：inserts/bl_tray3.py 的透明帧（只渲偶数帧，奇数帧用前一帧）；人：prep3.py 的 RGBA 帧；字、压暗、拉远推近在这里。节拍：sample3.json。
// 用法：remotion render Tray3.jsx TraySample<309|411> --public-dir=<prep3 的目录>
import React from "react";
import {AbsoluteFill, Composition, Img, OffthreadVideo, Sequence, Audio, interpolate, Easing, registerRoot, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import S from "./sample3.json";

const INK = "#111113", RED = "#E8190F", BONE = "rgb(236,234,228)";
const SERIF = "TraySerif", PEN = "TrayPen";
const fontHandle = delayRender("fonts");
Promise.all([new FontFace(SERIF, `url(${staticFile("fonts/InstrumentSerif-Regular.ttf")})`), new FontFace(PEN, `url(${staticFile("fonts/Caveat.ttf")})`)].map((f) => f.load().then((x) => document.fonts.add(x)))).then(() => continueRender(fontHandle));

const ease = Easing.bezier(0.45, 0, 0.25, 1);
const ramp = (f, a, b, from = 0, to = 1) => interpolate(f, [a, b], [from, to], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease});
const pad = (n) => String(n).padStart(4, "0");

const Note = ({f, n, at, lit = 0}) => {          // lit: 0 墨色 … 1 骨白（托盘压暗时字跟着变浅，读得清）
  if (f < at) return null;
  const w = ramp(f, at, at + n.d), o = n.until ? 1 - ramp(f, n.until - 8, n.until) : 1;
  const pen = n.kind === "pen";
  if (n.kind === "strike") {
    const len = n.text.length * n.size * (n.pen ? 0.36 : 0.42);          // under: 红线画在字下面（不是划掉）
    return <div style={{position: "absolute", left: n.x, top: n.y + n.size * (n.under ? 1.0 : 0.55), width: len * w, height: 6, background: RED, opacity: o, transform: n.pen ? "rotate(-2deg)" : undefined, transformOrigin: "0 0"}} />;
  }
  return <div style={{position: "absolute", left: n.x, top: n.y, transform: pen ? "rotate(-2deg)" : undefined, fontFamily: pen ? PEN : SERIF, fontSize: n.size, lineHeight: 1,
    color: n.red ? RED : n.light ? `rgb(${Math.round(17 + 219 * lit)},${Math.round(17 + 217 * lit)},${Math.round(19 + 209 * lit)})` : INK, opacity: o, whiteSpace: "nowrap", clipPath: `inset(-20% ${100 - w * 100}% -20% -5%)`}}>{n.text}</div>;
};

// 下一段第一帧从 (cx,cy) 的 0.46 倍长到满屏：边缘羽化跟着收，前 4 帧淡入（小图），到 b 帧正好是那一帧本身
export const Grow = ({f, a, b, cx, cy, src}) => {
  if (f < a) return null;
  const z = ramp(f, a, b), s = 0.46 + 0.54 * z, feather = 160 * (1 - z), o = Math.min(1, (f - a + 1) / 4);
  const m = `linear-gradient(to right, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%), linear-gradient(to bottom, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%)`;
  const tx = (cx - 960) * (1 - z) + 960 * (1 - s), ty = (cy - 540) * (1 - z) + 540 * (1 - s);
  return <AbsoluteFill style={{opacity: o, transformOrigin: "0 0", transform: `translate(${tx}px, ${ty}px) scale(${s})`}}>
    <AbsoluteFill style={{WebkitMaskImage: m, maskImage: m, WebkitMaskComposite: "source-in", maskComposite: "intersect"}}><Img src={staticFile(src)} style={{width: 1920, height: 1080}} /></AbsoluteFill>
  </AbsoluteFill>;
};

const Sample = ({name}) => {
  const C = S[name], f = useCurrentFrame();
  const parts = C.parts || [{...C.audio[0], until: C.frames, box: C.box, person_side: C.person_side}];
  const pi = parts.findIndex((p) => f >= p.at && f < p.until), part = parts[Math.max(0, pi)];
  const box = part.box, bx = (box[0] + box[2]) / 2, by = (box[1] + box[3]) / 2;
  const [P0, P1] = C.pull, [U0, U1] = C.push;
  // 拉远：上一段末帧缩到托盘上（0.46 倍，中心到托盘中心），边缘羽化，后 10 帧淡出
  const z = ramp(f, P0, P1), s = 1 - 0.54 * z, feather = 160 * z;
  const m = `linear-gradient(to right, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%), linear-gradient(to bottom, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%)`;
  const aStart = 1 - ramp(f, P1 - 10, P1);
  const trayO = ramp(f, P0 + 6, P1);
  const pIn = pi === 0 ? ramp(f, C.person_in[0], C.person_in[1]) : 1;
  // 收尾（v2）：画面不放大；下一段第一帧从托盘上长出来（拉远的反向），最后一帧和它完全重合，不叠化、不出全屏暗帧
  const zoom = 1, pOut = ramp(f, U0, U0 + 12);
  const dark = C.dark ? interpolate(f, C.dark.map((d) => d[0]), C.dark.map((d) => d[1]), {extrapolateLeft: "clamp", extrapolateRight: "clamp"}) : 0;
  const tf = f - (f % 2);
  const W = C.words;
  return (
    <AbsoluteFill style={{background: BONE}}>
      <AbsoluteFill style={{transformOrigin: `${bx}px ${by}px`, transform: `scale(${zoom})`}}>
        {parts.map((p, i) => (f >= p.at && f < p.until) && <Sequence key={"pl" + i} from={p.at}><OffthreadVideo src={staticFile(`plate${i}.mp4`)} muted style={{width: 1920, height: 1080}} /></Sequence>)}
        {f >= P0 + 6 && <Img src={staticFile(`tray/${name === "t309" ? "t309" : "t411"}_${pad(tf)}.png`)} style={{position: "absolute", width: 1920, height: 1080, opacity: trayO, filter: dark > 0 ? `brightness(${1 - dark})` : undefined}} />}
        {pi >= 0 && pOut < 1 && <Img src={staticFile(`person${pi}/p_${pad(f - part.at)}.png`)} style={{position: "absolute", width: 1920, height: 1080, opacity: pIn * (1 - pOut),
          transform: `translate(${(part.person_side === "left" ? -80 : 80) * pOut}px, ${40 * (1 - pIn)}px)`}} />}
        {C.notes.map((n, i) => <Note key={i} f={f} n={n} at={W[n.word]} lit={Math.min(1, dark / 0.5)} />)}
      </AbsoluteFill>
      {f < P1 && <AbsoluteFill style={{opacity: aStart, transformOrigin: "0 0", transform: `translate(${(bx - 960) * z + 960 * (1 - s)}px, ${(by - 540) * z + 540 * (1 - s)}px) scale(${s})`}}>
        <AbsoluteFill style={{WebkitMaskImage: m, maskImage: m, WebkitMaskComposite: "source-in", maskComposite: "intersect"}}>
          <Img src={staticFile("start.png")} style={{width: 1920, height: 1080}} />
        </AbsoluteFill>
      </AbsoluteFill>}
      <Grow f={f} a={U0} b={U1 - 1} cx={bx} cy={by} src="end.png" />
      <Audio src={staticFile("audio.wav")} />
    </AbsoluteFill>
  );
};

const Root = () => <>
  <Composition id="TraySample309" component={Sample} defaultProps={{name: "t309"}} durationInFrames={S.t309.frames} fps={60} width={1920} height={1080} />
  <Composition id="TraySample411" component={Sample} defaultProps={{name: "t411"}} durationInFrames={S.t411.frames} fps={60} width={1920} height={1080} />
</>;
registerRoot(Root);
