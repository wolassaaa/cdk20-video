// HKBU SCIE1007 课程作业的科普视频：出镜 6-04+6-05（D）"Millions of compounds screened before. Here? Thirteen made. Thirteen. That's honestly wild."（第 2 版，重写）
// 讲解卡：满卡小点从左上漫开；screened 红线扫过，点变灰；Here? 红问号；Thirteen 点收缩，只剩 13 个聚成一团；made 13 个点变红轻跳；
// 写出 13，That's 13 个点起一阵波，honestly 红线，wild 数字 13 和点一起跳。时间全读 oncam_6-04_6-05.json。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_6-04_6-05.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Write} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const FX1 = 1290, FY1 = 200, FX2 = 1870, FY2 = 900;
const GX = 1325, GY = 325, GD = 20, NC = 26, NR = 24;
const back = Easing.out(Easing.back(1.8));
const rnd = (i) => { const x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
const DOTS = [...Array(NC * NR)].map((_, i) => ({i, x: GX + (i % NC) * GD, y: GY + Math.floor(i / NC) * GD, r: rnd(i)}));
const PICK = [...Array(13)].map((_, k) => 17 + 48 * k);
const TGT = (k) => (k < 7 ? [1580 + (k - 3) * 50, 490] : [1580 + (k - 7 - 2.5) * 50, 546]);
const mix = (a, b, t) => `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * t)).join(",")})`;

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.s + 40, ease);
  const scan = span(f, E.scan.s, E.scan.l, ease);
  const sx = GX - 14 + (NC * GD) * scan;
  const bf = span(f, E.before.s, E.before.l + 12);
  const made = span(f, E.made.s, E.made.l + 10);
  const pulse = 1 + 0.35 * Math.sin(Math.PI * span(f, E.made.l, E.made.l + 24));
  const jump = -26 * Math.sin(Math.PI * span(f, E.wild.s, E.wild.l + 22));
  const q = span(f, E.here.s, E.here.l + 8, back) * (1 - span(f, E.thirteen.s, E.thirteen.s + 14));
  const ul = span(f, E.under.s, E.under.l + 14, ease);
  const GREY = [196, 191, 180];
  return (
    <OnCamFrame D={D} f={f} wav="6-04_6-05.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
          <g transform={`translate(0 ${jump})`}>
            {DOTS.map((d) => {
              const k = PICK.indexOf(d.i);
              const tt = E.dots.s + ((d.x - GX) + (d.y - GY) * 0.6) / (NC * GD + NR * GD * 0.6) * (E.dots.l - E.dots.s) * 0.8;
              const p = span(f, tt, tt + 12, back);
              if (p <= 0) return null;
              const swept = d.x < sx ? 1 : 0;
              const grey = Math.max(swept, bf);
              if (k < 0) {
                const sh = 1 - span(f, E.thirteen.s + d.r * 24, E.thirteen.s + d.r * 24 + 16, ease);
                if (sh <= 0) return null;
                return <circle key={d.i} cx={d.x} cy={d.y} r={5.5 * p * sh} fill={mix([31, 30, 28], GREY, grey)} />;
              }
              const mp = span(f, E.thirteen.s + k * 2, E.thirteen.s + k * 2 + 28, ease);
              const [tx, ty] = TGT(k);
              const wv = -14 * Math.sin(Math.PI * span(f, E.wave.s + k * 2, E.wave.s + k * 2 + 16));
              const x = d.x + (tx - d.x) * mp, y = d.y + (ty - d.y) * mp - Math.sin(Math.PI * mp) * 40 + wv * mp;
              const r = (5.5 + 9.5 * mp) * p * (mp > 0.99 ? pulse : 1);
              return <circle key={d.i} cx={x} cy={y} r={r} fill={mix(mix([31, 30, 28], GREY, grey).match(/\d+/g).map(Number), [200, 16, 46], Math.max(made, mp > 0.99 ? 0 : 0))} />;
            })}
            {ul > 0 && <rect x={1500} y={736} width={160 * ul} height={7} rx={3.5} fill={RED} />}
          </g>
          {scan > 0 && scan < 1 && <line x1={sx} y1={GY - 16} x2={sx} y2={GY + NR * GD - 4} stroke={RED} strokeWidth={5} strokeLinecap="round" />}
        </svg>
        {q > 0 && <div style={{position: "absolute", left: 1690, top: 214, width: 100, textAlign: "center", font: "italic 100px/100px Serif", color: RED, opacity: q, transform: `scale(${0.6 + 0.4 * q})`}}>?</div>}
        <div style={{position: "absolute", left: 1480, top: 596 + jump, width: 200, textAlign: "center", font: "150px/150px Serif"}}><Write p={span(f, E.num.s, E.num.l + 16)}>13</Write></div>
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Ren et al., Chem. Sci. 2023 · Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam604" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
