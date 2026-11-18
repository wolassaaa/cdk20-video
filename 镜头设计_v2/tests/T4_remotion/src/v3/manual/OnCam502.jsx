// HKBU SCIE1007 课程作业的科普视频：出镜 5-02（C）"Six of them barely held on. But one stood out. Its name? 001."（第 2 版，重写）
// 讲解卡：七个小瓶站成一排；barely 六个瓶变灰，on 往下沉；one 剩下的一个往上浮，stood 发亮（红色光线），out 放大轻抖；
// name 红问号，001 问号换成标签 001。时间全读 oncam_5-02.json。
import React from "react";
import {Composition, Easing, registerRoot, useCurrentFrame} from "remotion";
import D from "./oncam_5-02.json";
import {PAPER, INK, RED, SOFT, ease, out, span, Write} from "./kit.jsx";
import {OnCamFrame, useOnCam} from "./oncam.jsx";

const FX1 = 1290, FY1 = 215, FX2 = 1870, FY2 = 750;      // 卡片收到内容的高度（下半截原来空着）
const X0 = 1390, DX = 68, Y0 = 520, PICK = 3;
const back = Easing.out(Easing.back(1.8));
const mix = (a, b, t) => `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * t)).join(",")})`;

const Vial = ({fill, op = 1, rim = INK}) => (
  <g opacity={op}>
    <rect x={-27} y={-22} width={54} height={66} rx={12} fill={PAPER} stroke={rim} strokeWidth={4} />
    <path d="M-23,10 H23 V32 a10,10 0 0 1 -10,10 H-13 a10,10 0 0 1 -10,-10 Z" fill={fill} />
    <rect x={-13} y={-40} width={26} height={20} fill={PAPER} stroke={rim} strokeWidth={4} />
    <rect x={-17} y={-52} width={34} height={14} rx={4} fill={rim} />
  </g>
);

const Scene = () => {
  const f = useCurrentFrame();
  const {E, head} = useOnCam(D);
  const [hx, hy] = head(f);
  const fr = span(f, E.frame.s, E.frame.s + 40, ease);
  const grey = span(f, E.grey.s, E.grey.l, ease);
  const snk = span(f, E.sink.s, E.sink.l, ease);
  const rise = span(f, E.rise.s, E.rise.l, ease);
  const gl = span(f, E.glow.s, E.glow.l + 10, ease);
  const bg = span(f, E.big.s, E.big.l, back);
  const shake = f > E.big.l && f < E.big.l + 26 ? 3 * Math.exp(-(f - E.big.l) / 7) * Math.sin((f - E.big.l) * 1.3) : 0;
  const q = span(f, E.q.s, E.q.l + 8, back), tg = span(f, E.tag.s, E.tag.l + 10);
  const qOut = 1 - span(f, E.tag.s, E.tag.s + 8);
  const px = X0 + DX * PICK - 34 * rise, py = Y0 - 110 * rise;
  const sc = 1 + 0.55 * rise + 0.4 * bg;
  return (
    <OnCamFrame D={D} f={f} wav="5-02.wav">
      <div style={{position: "absolute", left: hx, top: hy, width: 1920, height: 1080}}>
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill={PAPER} opacity={0.96 * span(fr, 0.2, 0.9)} />
          {fr > 0 && <rect x={FX1} y={FY1} width={FX2 - FX1} height={FY2 - FY1} rx={26} fill="none" stroke={INK} strokeWidth={3.5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - fr} />}
          {[...Array(7)].map((_, i) => {
            if (i === PICK) return null;
            const p = span(f, E.vials.s + i * 3, E.vials.l + i * 3 + 10, back);
            if (p <= 0) return null;
            return (
              <g key={i} transform={`translate(${X0 + DX * i},${Y0 + 95 * snk + 26 * (1 - p)}) scale(${p})`}>
                <Vial fill={mix([62, 91, 224], [160, 157, 148], grey)} op={1 - 0.5 * snk} rim={mix([31, 30, 28], [130, 128, 120], grey)} />
              </g>
            );
          })}
          {/* 亮瓶：浮起、放大、发光 */}
          {(() => {
            const p = span(f, E.vials.s + PICK * 3, E.vials.l + PICK * 3 + 10, back);
            if (p <= 0) return null;
            return (
              <g>
                {gl > 0 && <circle cx={px} cy={py} r={105 * gl} fill="rgba(255,255,255,0.7)" />}
                {gl > 0 && [...Array(12)].map((_, k) => { const a = k * 30 * Math.PI / 180, r1 = 92, r2 = 92 + 26 * gl; return <line key={k} x1={px + r1 * Math.cos(a)} y1={py + r1 * Math.sin(a)} x2={px + r2 * Math.cos(a)} y2={py + r2 * Math.sin(a)} stroke={RED} strokeWidth={5} strokeLinecap="round" opacity={gl} />; })}
                <g transform={`translate(${px + shake},${py + 26 * (1 - p)}) scale(${sc * p})`}><Vial fill="#3E5BE0" /></g>
              </g>
            );
          })()}
        </svg>
        {q > 0 && <div style={{position: "absolute", left: 1700, top: 342, width: 140, textAlign: "center", font: "italic 110px/110px Serif", color: RED, opacity: q * qOut, transform: `scale(${0.6 + 0.4 * q})`}}>?</div>}
        {tg > 0 && (
          <div style={{position: "absolute", left: 1700, top: 358, width: 140, height: 84, boxSizing: "border-box", border: `4px solid ${INK}`, borderRadius: 12, textAlign: "center", font: "72px/76px Serif", opacity: span(tg, 0, 0.2)}}>
            <Write p={span(tg, 0.1, 1)}>001</Write>
          </div>
        )}
      </div>
      <div style={{position: "absolute", right: 44, top: 1046, fontSize: 17, color: SOFT}}>Ren et al., Chem. Sci. 2023 · Illustration</div>
    </OnCamFrame>
  );
};

const Root = () => <Composition id="OnCam502" component={Scene} durationInFrames={D.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
