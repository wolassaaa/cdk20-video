// HKBU SCIE1007 课程作业的科普视频：出镜 2-04（C）"We set ourselves two objectives."
// 讲解位：一张说明书便签纸展开（set），标题写出；说到 two 时红色圈号 1、2 先后钉上带回弹；objectives 时两条空白签条拉开，留给 2-05 填字。
// 人像右缘在屏幕 x≈1120，讲解位放在 1260 以右。时间全读 oncam_2-04.json（事件表 映射/events/2-04.json）。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_2-04.json";
import {INK, RED, SOFT, ease, out, span, Write} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const X = 1290, Y = 250, W = 520, H = 520;

const Num = ({n, ev, y, f}) => {
  const p = span(f, ev.s, ev.l, Easing.out(Easing.back(2.2)));
  if (p <= 0) return null;
  const wob = f > ev.l ? Math.exp(-(f - ev.l) / 6) * Math.sin((f - ev.l) / 1.8) * 6 : 0;
  return (
    <div style={{position: "absolute", left: X + 40, top: y - 46, width: 92, height: 92, borderRadius: 46, background: RED, color: "#F6F3EC",
                 fontSize: 60, lineHeight: "92px", textAlign: "center", transform: `scale(${p}) rotate(${wob}deg)`, boxShadow: "0 6px 12px rgba(120,10,30,0.25)"}}>{n}</div>
  );
};

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const card = span(f, E.board.s, E.board.l, Easing.out(Easing.cubic));
  const sl = span(f, E.slots.s, E.slots.s + 26, ease);
  const sl2 = span(f, E.slots.s + 8, E.slots.s + 34, ease);
  return (
    <OnCamFrame D={D} f={f} wav="2-04.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        {/* 便签纸：从上往下展开 */}
        <div style={{position: "absolute", left: X, top: Y, width: W, height: H, background: "#F6F3EC", border: `2.5px solid ${INK}`, borderRadius: 10,
                     boxShadow: "0 14px 28px rgba(31,30,28,0.16)", clipPath: `inset(0 0 ${100 - card * 100}% 0)`, transform: `rotate(${-1.5 * card}deg)`}}>
          <div style={{position: "absolute", left: 40, top: 34, fontSize: 52}}><Write p={span(f, E.board.s + 6, E.board.e)}>Our objectives</Write></div>
          <div style={{position: "absolute", left: 40, top: 112, width: W - 80, height: 3, background: INK, opacity: 0.6, transform: `scaleX(${span(f, E.board.l, E.board.e)})`, transformOrigin: "0 50%"}} />
          {/* 两条空白签条：等 2-05 填字 */}
          {[[230, sl], [400, sl2]].map(([y, p], i) => (
            <div key={i} style={{position: "absolute", left: 160, top: y - 30, width: (W - 200) * p, height: 60, border: `2px dashed ${SOFT}`, borderRadius: 8, opacity: p > 0 ? 1 : 0}} />
          ))}
        </div>
        <Num n="1" ev={E.one} y={Y + 230} f={f} />
        <Num n="2" ev={E.two} y={Y + 400} f={f} />
        <div style={{position: "absolute", left: X + 260, top: Y + H + 26, font: "42px Hand", color: RED, transform: "rotate(-4deg)"}}>
          <Write p={span(f, E.slots.l + 10, E.slots.e)}>coming up…</Write>
        </div>
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Our review plan · Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam204" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
