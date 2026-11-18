// HKBU SCIE1007 课程作业的科普视频：第 5 章二维说明书页 5-08（C 画外音）"And one of them, 048, grabbed about fifteen times tighter … 048 needed just 33.4."
// 主线：001 和 048 两行，上下两张横条图共用这两行。一排六把钥匙里一把抬起来、标 048、落到第二行；上半 grabbed：001 一格，048 一格一格长到 15 格，写 about fifteen times tighter；
// 下半 the enzyme test：001 的条长出图外带箭头，写 more than 6,000 nanomolar；048 只有很短一截，红字 just 33.4。条长是示意，数字只写旁白说的。
// 时间全读 keys_5-08.json（事件表 映射/events/5-08.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_5-08.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const BX = 320, U = 80, BH = 34;                    // 条起点、一格宽、条高
const YA = [300, 380], YB = [670, 770];             // 上半两行、下半两行（条的中线）
const ROW = [740, 820, 900, 980, 1060, 1140], PICKK = 3;
const ST = ["Target", "Hit", "Improve", "Cells", "Animals", "Trials", "Approval"], RY2 = 935;
const sx = (i) => 230 + (1460 * i) / 6;   // 开头一排六把钥匙

const Scene = () => {
  const f = useCurrentFrame();
  const io = Easing.inOut(Easing.cubic);
  const one = span(f, E.one.s, E.one.l + 10, out);
  const mv = span(f, E.k48.s, E.k48.l + 10, io);
  const grab = span(f, E.grab.s, E.grab.l + 14, ease);
  const fif = span(f, E.fif.s, E.tig.l, Easing.inOut(Easing.quad));
  const n15 = 1 + 14 * fif;
  const enz = span(f, E.enz.s, E.enz.l + 20, ease);
  const need = span(f, E.need.s, E.big.l + 20, Easing.in(Easing.quad));
  const big = span(f, E.big.s, E.big.l + 16, ease);
  const n48 = span(f, E.n48.s, E.just.l, Easing.out(Easing.cubic));
  const imp = span(f, E.just.s, E.just.l + 10, ease);
  const jj = f > E.just.l ? Math.exp(-(f - E.just.l) / 7) * Math.sin((f - E.just.l) / 1.8) * 4 : 0;
  const kx = ROW[PICKK] + (150 - ROW[PICKK]) * mv, ky = 240 - 40 * one + (YA[1] - 200) * mv;
  const bead = [[0, 600, 200], [E.one.l, 1260, 240], [E.k48.l, 600, 210], [E.grab.l, 520, 470], [E.fif.l, 1720, 300], [E.tig.l, 1720, 470],
                [E.enz.l, 1000, 560], [E.r001.l, 120, 600], [E.need.l, 1000, 600], [E.big.l, 1820, 720], [E.r048.l, 120, 840],
                [E.n48.l, 600, 840], [E.just.l, 760, 860], [K.len_f, 761, 861]];
  const rowLab = (txt, y, p, col = INK) => (
    <div style={{position: "absolute", left: 212, top: y - 24, fontSize: 40, lineHeight: "48px", color: col, opacity: p}}>{txt}</div>
  );
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("5-08.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.one.s, E.k48.e)}>048</Write></div>

      {/* 开头一排六把钥匙（接 5-07），048 抬起来落到第二行 */}
      {ROW.map((x, i) => i !== PICKK && (
        <div key={i} style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: 1 - 0.6 * span(f, E.k48.s, E.k48.l)}}>
          <Part name="key" cx={x} cy={240} w={70} at={0} f={f} gate={[0, 0.5]} />
        </div>
      ))}
      <Part name="key" cx={kx} cy={ky} w={70 + 20 * mv} at={0} f={f} gate={[0, 0.5]} />
      <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: span(f, E.grab.s - 10, E.grab.s)}}>
        <Part name="key" cx={150} cy={YA[0]} w={90} at={E.grab.s - 10} f={f} gate={[0, 0.5]} flood={10} />
      </div>
      {rowLab("001", YA[0], span(f, E.grab.s - 6, E.grab.s + 6))}
      {rowLab("048", YA[1], span(f, E.k48.l - 10, E.k48.l + 4), RED)}

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 上半：grabbed */}
        {grab > 0 && <rect x={BX} y={YA[0] - BH / 2} width={U * grab} height={BH} fill={INK} />}
        {grab > 0 && [...Array(Math.ceil(n15))].map((_, i) => {
          const w = Math.min(1, n15 - i) * U * grab;
          return w > 0 && <rect key={i} x={BX + i * U} y={YA[1] - BH / 2} width={Math.max(0, w - 4)} height={BH} fill={RED} />;
        })}
        {/* 下半：enzyme test 两行底线 */}
        {enz > 0 && [0, 1].map((r) => <path key={r} d={`M${BX - 10},${YB[r] + BH / 2 + 10} L${BX - 10 + 1380 * enz},${YB[r] + BH / 2 + 10}`} stroke={SOFT} strokeWidth={2} />)}
        {need > 0 && <rect x={BX} y={YB[0] - BH / 2} width={1360 * need} height={BH} fill={INK} />}
        {big > 0 && <g fill="none" stroke={INK} strokeWidth={4} strokeLinecap="round" strokeLinejoin="round">
          <path d={`M${BX + 1370},${YB[0]} L${BX + 1370 + 110 * big},${YB[0]}`} strokeDasharray="10 8" />
          {big > 0.9 && <path d={`M${BX + 1462},${YB[0] - 14} L${BX + 1482},${YB[0]} L${BX + 1462},${YB[0] + 14}`} />}
        </g>}
        {n48 > 0 && <rect x={BX} y={YB[1] - BH / 2} width={10 * n48} height={BH} fill={RED} transform={`translate(${jj} 0)`} />}
      </svg>
      <Label x={BX} y={210} w={300} size={34} italic align="left" p={span(f, E.grab.s, E.grab.e + 10)}>grabbed</Label>
      <div style={{position: "absolute", left: BX + 15 * U - 560, top: YA[1] + 34, width: 560, textAlign: "right", fontSize: 36, color: RED}}>
        <Write p={span(f, E.tig.s, E.tig.e + 10)}>about fifteen times tighter</Write>
      </div>
      <Label x={BX} y={540} w={400} size={34} italic align="left" p={span(f, E.enz.s, E.enz.e)}>the enzyme test</Label>
      {rowLab("001", YB[0], span(f, E.r001.s, E.r001.l))}
      {rowLab("048", YB[1], span(f, E.r048.s, E.r048.l), RED)}
      <div style={{position: "absolute", left: BX + 1480 - 600, top: YB[0] - 80, width: 600, textAlign: "right", fontSize: 36}}>
        <Write p={span(f, E.big.s, E.big.e)}>more than 6,000 nanomolar</Write>
      </div>
      <div style={{position: "absolute", left: BX + 40, top: YB[1] - 26, fontSize: 44, color: RED}}><Write p={span(f, E.just.s - 10, E.just.l + 20)}>just 33.4</Write></div>

      {/* 七站路：Improve 在 just 33.4 时亮 */}
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <path d={`M120,${RY2} L1750,${RY2}`} stroke={INK} strokeWidth={5} strokeLinecap="round" />
        <path d={`M120,${RY2} L${sx(1) + (sx(2) - sx(1)) * imp},${RY2}`} stroke={RED} strokeWidth={5} strokeLinecap="round" />
        {ST.map((n, i) => { const on = i < 2 || (i === 2 && imp > 0.9); const j = i === 2 ? 1 + 0.5 * Math.exp(-Math.max(0, f - E.just.l - 10) / 8) * (f > E.just.l ? 1 : 0) : 1;
          return <circle key={n} cx={sx(i)} cy={RY2} r={12 * j} fill={on ? RED : PAPER} stroke={i < 3 ? INK : "#9A968C"} strokeWidth={3.5} />; })}
      </svg>
      {ST.map((n, i) => <Label key={n} x={sx(i)} y={RY2 + 18} w={160} size={24} color={i === 2 && imp > 0.9 ? RED : i < 3 ? INK : "#8A867C"} p={1}>{n}</Label>)}
      <Source p={span(f, E.grab.l, E.grab.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual508" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
