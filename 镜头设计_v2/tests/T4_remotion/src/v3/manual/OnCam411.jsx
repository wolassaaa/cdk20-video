// HKBU SCIE1007 课程作业的科普视频：出镜 4-11+4-12（D）"Wait. So the computer picked the winners? Not quite. A docking score is a clue, not proof. Only the lab can tell."（第 2 版，重写）
// 讲解卡：排名表三行（分数条）；picked the winners 依次打勾；Not quite 三个勾变成红问号；docking score 标签，a clue, not proof 字牌；
// Only the lab 烧瓶长出，三行各连一条线到烧瓶。时间全读 oncam_4-11_4-12.json。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_4-11_4-12.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Part, Label, Write} from "./kit.jsx";
import {OnCamFrame, useOnCam, PersonFront} from "./oncam.jsx";

const FX1 = 1290, FY1 = 200, FX2 = 1870, FY2 = 900;
const RX1 = 1322, RX2 = 1722, RH = 64, RY = [330, 410, 490];
const BW = [250, 210, 170];
const MX = 1688;
const FL = {cx: 1700, cy: 735, w: 120};
const back = Easing.out(Easing.back(1.8));

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.s + 40, ease);
  const tb = span(f, E.table.s, E.table.l + 24, ease);
  const T = [E.tick1, E.tick2, E.tick3], Q = [E.q1, E.q2, E.q3], L = [E.l1, E.l2, E.l3];
  const sp = span(f, E.score.s, E.score.s + 22);
  const pulse = 1 + 0.4 * Math.sin(Math.PI * sp);
  const pr = span(f, E.proof.s, E.proof.e - 4, ease);
  return (
    <OnCamFrame D={D} f={f} wav="4-11_4-12.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
          {RY.map((y, i) => {
            const p = span(tb, i * 0.22, i * 0.22 + 0.5, ease), t = span(f, T[i].s, T[i].l + 8, back), q = span(f, Q[i].s, Q[i].l + 8, back);
            const tickK = t * (1 - span(q, 0, 0.5));
            return (
              <g key={i}>
                <rect x={RX1} y={y - RH / 2} width={RX2 - RX1} height={RH} rx={12} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
                <rect x={RX1 + 18} y={y - 16 * pulse} width={BW[i] * span(p, 0.5, 1)} height={32 * pulse} rx={6} fill="rgba(31,30,28,0.16)" />
                {tickK > 0 && <path d={`M${MX - 15},${y + 2} L${MX - 4},${y + 14} L${MX + 16},${y - 13}`} fill="none" stroke={INK} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round"
                                   pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(t, 0, 0.8)} style={{transformOrigin: `${MX}px ${y}px`, transform: `scale(${tickK})`}} />}
                {q > 0.5 && <text x={MX} y={y + 20} textAnchor="middle" fontFamily="Serif" fontStyle="italic" fontSize={58} fill={RED} style={{transformOrigin: `${MX}px ${y}px`, transform: `scale(${span(q, 0.5, 1)})`}}>?</text>}
              </g>
            );
          })}
          {/* 三行各连一条线到烧瓶 */}
          {RY.map((y, i) => {
            const p = span(f, L[i].s, L[i].l + 10, ease);
            // 三条线各走各的（套着的 L 形，不交叉），各自落到烧瓶上不同的高度
            const vx = [1846, 1816, 1786][i], ey = [790, 755, 720][i], ex = [1758, 1752, 1738][i];
            return p > 0 ? (
              <g key={i}>
                <path d={`M${RX2},${y} H${vx - 14} Q${vx},${y} ${vx},${y + 14} V${ey - 14} Q${vx},${ey} ${vx - 14},${ey} H${ex}`} fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />
                {p > 0.97 && <path d={`M${ex + 13},${ey - 9} L${ex},${ey} L${ex + 13},${ey + 9}`} fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round" />}
              </g>
            ) : null;
          })}
        </svg>
        <Label x={RX1} y={245} w={200} align="left" p={span(f, E.table.l, E.table.l + 16)} size={28} italic color={INK}>computer</Label>
        <Label x={1522} y={540} w={360} p={span(f, E.dock.l - 4, E.dock.l + 22)} size={28} italic color={INK}>docking score</Label>
        <div style={{position: "absolute", left: 1330, top: 625, fontSize: 52, whiteSpace: "nowrap"}}><Write p={span(f, E.clue.s + 4, E.clue.l + 14)}>a clue,</Write></div>
        <div style={{position: "absolute", left: 1330, top: 692, fontSize: 52, whiteSpace: "nowrap"}}>
          <Write p={span(f, E.proof.s, E.proof.l + 12)}><span style={{position: "relative"}}>not proof<span style={{position: "absolute", left: 0, bottom: 2, height: 5, width: `${pr * 100}%`, background: RED, borderRadius: 3}} /></span></Write>
        </div>
        <Part name="flask" cx={FL.cx} cy={FL.cy} w={FL.w} at={E.flask.l} f={f} gate={[0.5, 1]} />
      </div>
      <PersonFront D={D} f={f} x0={FX1} />
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam411" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
