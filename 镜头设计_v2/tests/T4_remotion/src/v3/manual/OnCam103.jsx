// HKBU SCIE1007 课程作业的科普视频：出镜 1-03（A）"Here's the thing. We already have medicines. Just not good enough ones."
// 讲解位：一个刻度框；已经有的药（胶囊、输液袋）站在底线上；药效那一格升起，停在 good enough 虚线下面，红括号标出差距。
// 时间全读 oncam_1-03.json（事件表 映射/events/1-03.json）。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_1-03.json";
import {INK, RED, SOFT, ease, out, span, Part, Tag, Write} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const AR = {capsule: 530 / 229, ivbag: 474 / 773};
const X0 = 1470, X1 = 1830, YB = 760, YT = 250, YG = 330, YLEV = 470;   // 框左右、底线、顶、good enough 线、药停住的高度

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.e, ease);
  const bar = span(f, E.bar.s, E.bar.e, Easing.out(Easing.back(1.2)));
  const lvl = YB - (YB - YLEV) * bar;
  const tg = span(f, E.target.s, E.target.e, ease);
  const gp = span(f, E.gap.s, E.gap.s + 18, out);
  return (
    <OnCamFrame D={D} f={f} wav="1-03.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          {/* 刻度框：左竖线 + 底线 + 刻度 */}
          <path d={`M${X0},${YT} L${X0},${YB} L${X1},${YB}`} fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />
          {[...Array(6)].map((_, i) => (
            <path key={i} d={`M${X0},${YB - (i + 1) * 88} L${X0 + 18},${YB - (i + 1) * 88}`} stroke={INK} strokeWidth={3} opacity={span(fr, 0.4 + i * 0.08, 0.5 + i * 0.08)} />
          ))}
          {/* 药效那一格：从底线升起 */}
          {bar > 0 && <rect x={X0 + 30} y={lvl} width={X1 - X0 - 60} height={YB - lvl} fill="rgba(31,30,28,0.10)" stroke={INK} strokeWidth={2.5} />}
          {/* good enough 虚线 */}
          <path d={`M${X0},${YG} L${X1},${YG}`} stroke={INK} strokeWidth={3} strokeDasharray="14 10" opacity={tg} style={{clipPath: `inset(0 ${100 - tg * 100}% 0 0)`}} />
          {/* 红括号：差距 */}
          {gp > 0 && (
            <path d={`M${X1 + 18},${YG + 4} q16,0 16,16 L${X1 + 34},${YG + (YLEV - YG) / 2 - 10} q0,10 12,10 q-12,0 -12,10 L${X1 + 34},${YLEV - 20} q0,16 -16,16`}
                  fill="none" stroke={RED} strokeWidth={4} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - gp} />
          )}
        </svg>
        <div style={{position: "absolute", left: X0 + 30, top: YG - 54, fontSize: 36, fontStyle: "italic", opacity: tg}}><Write p={tg}>good enough</Write></div>
        <div style={{position: "absolute", left: X0 + 60, top: YG + (YLEV - YG) / 2 - 30, font: "40px Hand", color: RED, transform: "rotate(-6deg)"}}>
          <Write p={span(f, E.gap.s + 6, E.gap.e)}>not yet</Write>
        </div>
        <Part name="capsule" cx={1580} cy={YB - 34} w={130} ar={AR.capsule} at={E.caps.s + 2} f={f} gate={[0, 0.5]} flood={18} />
        <Part name="ivbag" cx={1752} cy={YB - 80} w={90} ar={AR.ivbag} at={E.bag.s + 2} f={f} gate={[0.5, 0]} flood={18} />
        <Tag n="08" x={1530} y={YB - 110} at={E.caps.l + 16} f={f} />
        <Tag n="09" x={1700} y={YB - 190} at={E.bag.l + 16} f={f} />
        <div style={{position: "absolute", left: X0 + 10, top: YB + 18, fontSize: 28, color: SOFT, fontStyle: "italic"}}>
          <Write p={span(f, E.bag.l, E.bag.e)}>medicines we already have</Write>
        </div>
      </div>
      <div style={{position: "absolute", left: 44, top: 1046, fontSize: 17, color: SOFT}}>Ren et al., Chem. Sci. 2023 · Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam103" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
