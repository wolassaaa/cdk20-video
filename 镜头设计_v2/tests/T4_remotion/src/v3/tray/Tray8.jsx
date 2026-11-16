// HKBU SCIE1007 课程作业的科普视频。托盘出镜 v8（导演 11-16）：Tray4.jsx 的副本；人像按 prep8 的 ps/px 缩放平移（以画面底边为轴），
// 托盘上的字放进一个 BOX 大小的层，用 matrix3d 贴到 Blender 量出的台面四角上（随透视，印在台面上）。
// 旧说明：托盘出镜模板（cut_v6）：Tray3.jsx 的通用版，一组一个 Composition（id = T4_<组名去掉横线>）。
// 底：说话人的细胞纸底 plate<i>.mp4；托盘和物件：bl_tray4.py 的透明帧（只渲偶数帧）；人：prep4.py 的 RGBA 帧（dx 平移到自己那一边）；
// 字（落在词上）、拉远（上一段末帧缩到托盘上）、推近（下一段首帧从托盘中心长到满屏）在这里。节拍：_resolved/all.json（prep4.py 写）。
// 用法：remotion render Tray4.jsx T4_<id> out.mp4 --public-dir=<prep4 的目录>
import React from "react";
import {AbsoluteFill, Composition, Img, OffthreadVideo, Sequence, Audio, interpolate, Easing, registerRoot, staticFile, useCurrentFrame, continueRender, delayRender} from "remotion";
import ALL from "./_resolved8/all.json";

const INK = "#111113", RED = "#E8190F", BONE = "rgb(236,234,228)";
const SERIF = "Tray4Serif", PEN = "Tray4Pen";
const fontHandle = delayRender("fonts");
Promise.all([new FontFace(SERIF, `url(${staticFile("fonts/InstrumentSerif-Regular.ttf")})`), new FontFace(PEN, `url(${staticFile("fonts/Caveat.ttf")})`)].map((f) => f.load().then((x) => document.fonts.add(x)))).then(() => continueRender(fontHandle));

const ease = Easing.bezier(0.45, 0, 0.25, 1);
const ramp = (f, a, b, from = 0, to = 1) => interpolate(f, [a, b], [from, to], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease});
const pad = (n) => String(n).padStart(4, "0");
const BOX = {right: [900, 220, 1780, 820], left: [140, 220, 1020, 820]};

// 下一段第一帧从 (cx,cy) 的 0.46 倍长到满屏：边缘羽化跟着收，前 4 帧淡入（小图），到 b 帧正好是那一帧本身
const Grow = ({f, a, b, cx, cy, src}) => {
  if (f < a) return null;
  const z = ramp(f, a, b), s = 0.46 + 0.54 * z, feather = 160 * (1 - z), o = Math.min(1, (f - a + 1) / 4);
  const m = `linear-gradient(to right, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%), linear-gradient(to bottom, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%)`;
  const tx = (cx - 960) * (1 - z) + 960 * (1 - s), ty = (cy - 540) * (1 - z) + 540 * (1 - s);
  return <AbsoluteFill style={{opacity: o, transformOrigin: "0 0", transform: `translate(${tx}px, ${ty}px) scale(${s})`}}>
    <AbsoluteFill style={{WebkitMaskImage: m, maskImage: m, WebkitMaskComposite: "source-in", maskComposite: "intersect"}}><Img src={staticFile(src)} style={{width: 1920, height: 1080}} /></AbsoluteFill>
  </AbsoluteFill>;
};

// BOX 矩形 (0,0)-(w,h) → 台面四角 q 的单应矩阵，写成 CSS matrix3d（transform-origin 0 0）
const homography = (w, h, q) => {
  const [[x0, y0], [x1, y1], [x2, y2], [x3, y3]] = q;
  const dx1 = x1 - x2, dx2 = x3 - x2, dy1 = y1 - y2, dy2 = y3 - y2, sx = x0 - x1 + x2 - x3, sy = y0 - y1 + y2 - y3;
  const den = dx1 * dy2 - dx2 * dy1;
  const g = (sx * dy2 - dx2 * sy) / den, hh = (dx1 * sy - sx * dy1) / den;
  const a = x1 - x0 + g * x1, b = x3 - x0 + hh * x3, c = x0, d = y1 - y0 + g * y1, e = y3 - y0 + hh * y3, f = y0;
  const A = a / w, B = b / h, D = d / w, E = e / h, G = g / w, Hh = hh / h;
  return `matrix3d(${A},${D},0,${G},${B},${E},0,${Hh},0,0,1,0,${c},${f},0,1)`;
};

const Note = ({f, n, box}) => {
  if (f < n.at) return null;
  const w = ramp(f, n.at, n.at + n.d), o = n.until ? 1 - ramp(f, n.until - 8, n.until) : 1;
  if (o <= 0) return null;
  const x = n.x * (box[2] - box[0]), y = n.y * (box[3] - box[1]);
  const pen = n.kind === "pen";
  if (n.kind === "strike") {
    const len = n.text.length * n.size * (n.pen ? 0.36 : 0.42);
    return <div style={{position: "absolute", left: x, top: y + n.size * (n.under ? 1.0 : 0.55), width: len * w, height: 6, background: RED, opacity: o, transform: n.pen ? "rotate(-2deg)" : undefined, transformOrigin: "0 0"}} />;
  }
  return <div style={{position: "absolute", left: x, top: y, transform: pen ? "rotate(-2deg)" : undefined, fontFamily: pen ? PEN : SERIF, fontSize: n.size, lineHeight: 1,
    color: n.red ? RED : INK, opacity: o, whiteSpace: "nowrap", clipPath: `inset(-20% ${100 - w * 100}% -20% -5%)`}}>{n.text}</div>;
};

const Group = ({id}) => {
  const C = ALL[id], f = useCurrentFrame();
  const parts = C.parts;
  let pi = 0;
  parts.forEach((p, i) => { if (f >= p.at) pi = i; });
  const part = parts[pi];
  const box = BOX[part.tray], bx = (box[0] + box[2]) / 2, by = (box[1] + box[3]) / 2;
  const P = C.pull, U = C.push;
  const z = P ? ramp(f, P[0], P[1]) : 1, s = 1 - 0.54 * z, feather = 160 * z;
  const m = `linear-gradient(to right, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%), linear-gradient(to bottom, transparent 0, black ${feather}px, black calc(100% - ${feather}px), transparent 100%)`;
  const aStart = P ? 1 - ramp(f, P[1] - 10, P[1]) : 0;
  const trayO = P ? ramp(f, P[0] + 6, P[1]) : 1;
  const pIn = pi === 0 ? ramp(f, C.person_in[0], C.person_in[1]) : 1;
  const pOut = U ? ramp(f, U[0], U[0] + 12) : C.fade_out ? ramp(f, C.fade_out[0], C.fade_out[1]) : 0;
  const tf = f - (f % 2);
  const k = f - part.at;
  const nPerson = part.until - part.at;
  const pf = Math.min(k, nPerson - 1);
  return (
    <AbsoluteFill style={{background: BONE}}>
      {parts.map((p, i) => (i === pi) && <Sequence key={"pl" + i} from={p.at}><OffthreadVideo src={staticFile(`plate${i}.mp4`)} muted style={{width: 1920, height: 1080}} /></Sequence>)}
      {(!P || f >= P[0] + 6) && <Img src={staticFile(`tray/tm4_${pad(tf)}.png`)} style={{position: "absolute", width: 1920, height: 1080, opacity: trayO}} />}
      {pOut < 1 && <Img src={staticFile(`person${pi}/p_${pad(pf)}.png`)} style={{position: "absolute", width: 1920, height: 1080, opacity: pIn * (1 - pOut),
        transformOrigin: `${part.ox}px 1080px`,
        transform: `translate(${part.px + (part.person_side === "left" ? -80 : 80) * pOut}px, ${40 * (1 - pIn)}px) scale(${part.ps})`}} />}
      <div style={{position: "absolute", left: 0, top: 0, width: box[2] - box[0], height: box[3] - box[1], transformOrigin: "0 0", mixBlendMode: "multiply",
        transform: homography(box[2] - box[0], box[3] - box[1], part.quad), opacity: trayO}}>
        {C.notes.map((n, i) => <Note key={i} f={f} n={n} box={box} />)}
      </div>
      {P && f < P[1] && <AbsoluteFill style={{opacity: aStart, transformOrigin: "0 0", transform: `translate(${(bx - 960) * z + 960 * (1 - s)}px, ${(by - 540) * z + 540 * (1 - s)}px) scale(${s})`}}>
        <AbsoluteFill style={{WebkitMaskImage: m, maskImage: m, WebkitMaskComposite: "source-in", maskComposite: "intersect"}}>
          <Img src={staticFile("start.png")} style={{width: 1920, height: 1080}} />
        </AbsoluteFill>
      </AbsoluteFill>}
      {U && <Grow f={f} a={U[0]} b={U[1] - 1} cx={bx} cy={by} src="end.png" />}
      <Audio src={staticFile("audio.wav")} />
    </AbsoluteFill>
  );
};

const Root = () => <>
  {Object.keys(ALL).map((id) => <Composition key={id} id={"T8-" + id.replace(/_/g, "-")} component={Group} defaultProps={{id}} durationInFrames={ALL[id].frames} fps={60} width={1920} height={1080} />)}
</>;
registerRoot(Root);
