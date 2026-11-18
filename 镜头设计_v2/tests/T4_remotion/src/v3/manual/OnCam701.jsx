// HKBU SCIE1007 课程作业的科普视频：出镜 7-01（A）"So, what should happen next? We'd suggest three things."（第 2 版，重写）
// 讲解卡：问号 next 时落一个红问号；three 圈号 1 弹出，things 圈号 2、3 接着弹出；三个圈号都是空圈，右边各留一条空白签条。
// 时间全读 oncam_7-01.json（事件表 映射/events/7-01.json）。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_7-01.json";
import {PAPER, INK, RED, SOFT, ease, out, span} from "./kit.jsx";
import {OnCamFrame, useOnCam, PersonFront} from "./oncam.jsx";

const FX1 = 1290, FY1 = 200, FX2 = 1870, FY2 = 900;
const ROWS = [400, 560, 720];
const back = Easing.out(Easing.back(2.2));

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.s + 40, ease);
  const q = span(f, E.q.s, E.q.l + 8, Easing.out(Easing.back(1.8)));
  const EV = [E.c1, E.c2, E.c3];
  return (
    <OnCamFrame D={D} f={f} wav="7-01.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
        </svg>
        {q > 0 && <div style={{position: "absolute", left: 1530, top: 222, width: 100, textAlign: "center", font: "italic 110px/110px Serif", color: RED, opacity: q, transform: `scale(${0.6 + 0.4 * q})`}}>?</div>}
        {ROWS.map((y, i) => {
          const p = span(f, EV[i].s, EV[i].l, back);
          const wob = f > EV[i].l ? Math.exp(-(f - EV[i].l) / 6) * Math.sin((f - EV[i].l) / 1.8) * 6 : 0;
          const sl = span(f, EV[i].l, EV[i].l + 26, ease);
          return (
            <React.Fragment key={i}>
              {p > 0 && <div style={{position: "absolute", left: 1340, top: y - 46, width: 92, height: 92, boxSizing: "border-box", borderRadius: 46, border: `6px solid ${RED}`, color: RED,
                                     font: "60px/80px Serif", textAlign: "center", transform: `scale(${p}) rotate(${wob}deg)`}}>{i + 1}</div>}
              {sl > 0 && <div style={{position: "absolute", left: 1470, top: y - 28, width: 340 * sl, height: 56, border: `2.5px dashed ${SOFT}`, borderRadius: 8}} />}
            </React.Fragment>
          );
        })}
      </div>
      <PersonFront D={D} f={f} x0={FX1} />
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam701" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
