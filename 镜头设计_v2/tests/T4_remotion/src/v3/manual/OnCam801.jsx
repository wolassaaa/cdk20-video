// HKBU SCIE1007 课程作业的科普视频：出镜 8-01（C）"So, back to where we started."（第 2 版，重写）
// 讲解卡：2-04 的便签纸 Our objectives，back 时从上方落回（带一点回弹）；we 圈号 1 亮起，started 圈号 2 亮起（和 2-04 同一张纸、同一个位置）。
// 时间全读 oncam_8-01.json（事件表 映射/events/8-01.json）。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_8-01.json";
import {INK, RED, SOFT, ease, span, Write} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const X = 1290, Y = 250, W = 520, H = 520;
const GREY = "#B3AFA4";

const Num = ({n, ev, y, f}) => {
  const lit = span(f, ev.s, ev.l, Easing.out(Easing.back(2.2)));
  const wob = f > ev.l ? Math.exp(-(f - ev.l) / 6) * Math.sin((f - ev.l) / 1.8) * 6 : 0;
  return (
    <div style={{position: "absolute", left: X + 40, top: y - 46, width: 92, height: 92, boxSizing: "border-box", borderRadius: 46,
                 background: lit > 0 ? RED : "transparent", border: lit > 0 ? "none" : `5px solid ${GREY}`, color: lit > 0 ? "#F6F3EC" : GREY,
                 fontSize: 60, lineHeight: lit > 0 ? "92px" : "82px", textAlign: "center", transform: `scale(${lit > 0 ? 0.7 + 0.3 * lit : 1}) rotate(${wob}deg)`,
                 boxShadow: lit > 0 ? "0 6px 12px rgba(120,10,30,0.25)" : "none"}}>{n}</div>
  );
};

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fall = span(f, E.note.s, E.note.l, Easing.out(Easing.back(1.3)));
  const ty = -(Y + H + 40) * (1 - fall);
  const tit = span(f, E.note.l - 10, E.note.l + 14);
  return (
    <OnCamFrame D={D} f={f} wav="8-01.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateY(${ty}px) rotate(${-1.5 * fall}deg)`, transformOrigin: `${X + W / 2}px ${Y}px`, opacity: Math.min(1, fall * 3)}}>
          <div style={{position: "absolute", left: X, top: Y, width: W, height: H, background: "#F6F3EC", border: `2.5px solid ${INK}`, borderRadius: 10, boxShadow: "0 14px 28px rgba(31,30,28,0.16)"}}>
            <div style={{position: "absolute", left: 40, top: 34, fontSize: 52}}>Our objectives</div>
            <div style={{position: "absolute", left: 40, top: 112, width: W - 80, height: 3, background: INK, opacity: 0.6}} />
            {[230, 400].map((y, i) => (
              <div key={i} style={{position: "absolute", left: 160, top: y - 30, width: W - 200, height: 60, border: `2px dashed ${SOFT}`, borderRadius: 8}} />
            ))}
          </div>
          <Num n="1" ev={E.n1} y={Y + 230} f={f} />
          <Num n="2" ev={E.n2} y={Y + 400} f={f} />
        </div>
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Our review plan · Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam801" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
