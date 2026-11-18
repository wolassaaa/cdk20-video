// HKBU SCIE1007 课程作业的科普视频：出镜 6-12（B）"048 is at the very start of the road. But for this case, that start took weeks, not years."（第 2 版，重写）
// 讲解卡：小牌子 048 立起；very start 起点圆点，牌子移到起点；road 一条长路从起点画出；this case 红圈圈住起点；
// that start 红括号括住起点那一小段，weeks 标在括号上；years 标在远处的长路上并被红线划掉。时间全读 oncam_6-12.json。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_6-12.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Write} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const FX1 = 1290, FY1 = 200, FX2 = 1870, FY2 = 900;
const SEG = [[[1405, 740], [1560, 780], [1560, 610], [1650, 570]], [[1650, 570], [1740, 530], [1800, 440], [1765, 355]], [[1765, 355], [1745, 305], [1790, 270], [1820, 240]]];
const PATH = `M${SEG[0][0]} C${SEG[0][1]} ${SEG[0][2]} ${SEG[0][3]} C${SEG[1][1]} ${SEG[1][2]} ${SEG[1][3]} C${SEG[2][1]} ${SEG[2][2]} ${SEG[2][3]}`;
const bez = (c, t) => { const u = 1 - t; return [0, 1].map((k) => u * u * u * c[0][k] + 3 * u * u * t * c[1][k] + 3 * u * t * t * c[2][k] + t * t * t * c[3][k]); };
const dbez = (c, t) => { const u = 1 - t; return [0, 1].map((k) => 3 * u * u * (c[1][k] - c[0][k]) + 6 * u * t * (c[2][k] - c[1][k]) + 3 * t * t * (c[3][k] - c[2][k])); };
const S0 = SEG[0][0];
const back = Easing.out(Easing.back(1.6));

// 起点那一小段上方的括号：沿第一段 t 从 0 到 0.62，向外（上方）偏移 off
const braceAt = (t, off) => { const [x, y] = bez(SEG[0], t), [dx, dy] = dbez(SEG[0], t), n = Math.hypot(dx, dy); return [x + (dy / n) * off, y - (dx / n) * off]; };

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.s + 40, ease);
  const pl = span(f, E.plate.s, E.plate.l, back);
  const mk = span(f, E.mark.s, E.mark.l + 6, back);
  const mv = span(f, E.move.s, E.move.l, ease);
  const rd = span(f, E.road.s, E.road.l, ease);
  const rg = span(f, E.ring.s, E.ring.l + 10, ease);
  const br = span(f, E.brace.s, E.brace.l + 10, ease);
  const wk = span(f, E.weeks.s, E.weeks.l + 14);
  const yr = span(f, E.years.s, E.years.l + 12), st = span(f, E.strike.s, E.strike.e - 6, ease);
  const px = 1580 + (S0[0] - 1580) * mv, py = 420 + (S0[1] - 76 - 420) * mv - Math.sin(Math.PI * mv) * 40;
  const B = [...Array(13)].map((_, i) => braceAt(0.2 + 0.5 * i / 12, -50));
  const bracePath = `M${braceAt(0.2, -30)} L${B[0]} ` + B.slice(1).map((p) => `L${p}`).join(" ") + ` L${braceAt(0.7, -30)}`;
  const mid = braceAt(0.45, -50 - 40);
  return (
    <OnCamFrame D={D} f={f} wav="6-12.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
          {rd > 0 && (<g fill="none" strokeLinecap="round">
            <path d={PATH} stroke={INK} strokeWidth={26} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - rd} />
            <path d={PATH} stroke="#DCD7CA" strokeWidth={18} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - rd} />
          </g>)}
          {mk > 0 && <circle cx={S0[0]} cy={S0[1]} r={15 * mk} fill={RED} stroke={INK} strokeWidth={3.5} />}
          {rg > 0 && <ellipse cx={S0[0]} cy={S0[1] - 36} rx={84} ry={78} fill="none" stroke={RED} strokeWidth={5} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - rg} transform={`rotate(0 0 0)`} />}
          {br > 0 && <path d={bracePath} fill="none" stroke={RED} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - br} />}
          {pl > 0 && (<g transform={`translate(${px},${py}) scale(${pl})`}>
            <line x1={0} y1={30} x2={0} y2={76} stroke={INK} strokeWidth={5} strokeLinecap="round" opacity={mv} />
            <rect x={-58} y={-30} width={116} height={60} rx={10} fill={PAPER} stroke={INK} strokeWidth={4} />
            <text x={0} y={14} textAnchor="middle" fontFamily="Serif" fontSize={44} fill={INK}>048</text>
          </g>)}
        </svg>
        <div style={{position: "absolute", left: mid[0] - 80, top: mid[1] - 36, width: 160, textAlign: "center", fontSize: 40, color: RED, fontStyle: "italic"}}><Write p={wk}>weeks</Write></div>
        <div style={{position: "absolute", left: 1480, top: 290, width: 160, textAlign: "center", fontSize: 44, fontStyle: "italic"}}>
          <Write p={yr}><span style={{position: "relative"}}>years<span style={{position: "absolute", left: -6, top: 24, height: 6, width: `${st * 116}%`, background: RED, borderRadius: 3}} /></span></Write>
        </div>
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Ren et al., Chem. Sci. 2023 · Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam612" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
