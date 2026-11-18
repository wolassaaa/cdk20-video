// HKBU SCIE1007 课程作业的科普视频：第 5 章二维说明书页 5-07（C 画外音）"Not at all. This is where the loop kicks in again … Sixteen new designs. Six made and tested. All within 30 days of that first hit."
// 主线：一个设计循环（顶上 design 节点是 001 钥匙，右下 flask，左下 results）。Not at all 钥匙一颤、红叉；loop 循环画出转起来；lab flask 长出，吐出数据卡（real lab data），
// 数据卡顺着循环经过 results 回到 design；旁边长出 predicted pose 小图（锁里插 001，口袋红圈）；16 把新钥匙从 design 扇到右边；其中 6 把落到下面一排、flask、打勾；
// 底下时间线：first hit 红点到 30 days。数字只写旁白说的。时间全读 keys_5-07.json（事件表 映射/events/5-07.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_5-07.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source} from "./kit.jsx";

const E = evMap(K);
const LC = [620, 580], LR = 220;
const at = (deg) => [LC[0] + LR * Math.cos(deg * Math.PI / 180), LC[1] + LR * Math.sin(deg * Math.PI / 180)];
const ND = at(-90), NL = at(30), NR = at(150);              // design、lab、results
const GX = [1120, 270 + 1000, 1420, 1570], GY = [250, 320, 390, 460];
const PICK = [1, 4, 6, 9, 11, 14];
const TL = [260, 1640, 900];                                  // 时间线

const Scene = () => {
  const f = useCurrentFrame();
  const io = Easing.inOut(Easing.cubic);
  const loop = span(f, E.loop.s, E.loop.l + 14, ease);
  const no = f > E.no.s ? Math.exp(-(f - E.no.s) / 6) * Math.sin((f - E.no.s) / 1.7) * 3 : 0;
  // 数据卡：lab → results → design
  const r1 = span(f, E.res.s, E.res.l + 20, io), r2 = span(f, E.back.s, E.back.l + 10, io);
  const cardA = 30 + 120 * r1 + 120 * r2;
  const cp = at(cardA);
  const cardOn = span(f, E.data.s, E.data.l) * (1 - span(f, E.back.l + 6, E.back.l + 20));
  const pose = span(f, E.pose.s, E.pose.l + 10, ease);
  const s16 = span(f, E.s16.s, E.s16.l + 30, io);
  const six = span(f, E.six.s, E.six.l + 20, io);
  const tl = span(f, E.all.s, E.all.l + 20, ease);
  const bead = [[0, 800, 220], [E.no.l, 820, 330], [E.loop.l, 900, 470], [E.kick.l, 620, 470], [E.lab.l, 930, 780], [E.data.l, 1090, 600],
                [E.res.l, 300, 760], [E.back.l, 760, 290], [E.pose.l, 480, 250], [E.k001.l, 180, 390], [E.pock.l, 470, 320],
                [E.s16.l, 1720, 300], [E.six.l, 1000, 560], [E.test.l, 1760, 560], [E.all.l, 200, 840], [E.d30.l, 1720, 860],
                [E.fh.l, 420, 960], [K.len_f, 421, 961]];
  const gpos = (i) => [GX[i % 4], GY[Math.floor(i / 4)]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("5-07.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.loop.s, E.kick.l + 30)}>The loop kicks in again</Write></div>

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 循环：顺时针 */}
        {loop > 0 && <circle cx={LC[0]} cy={LC[1]} r={LR} fill="none" stroke={INK} strokeWidth={5} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - loop}
                             transform={`rotate(-90 ${LC[0]} ${LC[1]})`} />}
        {loop > 0.9 && [-30, 90, 210].map((d) => { const [x, y] = at(d); return (
          <path key={d} d="M-14,-12 L4,0 L-14,12" fill="none" stroke={INK} strokeWidth={5} strokeLinecap="round" strokeLinejoin="round" transform={`translate(${x} ${y}) rotate(${d + 90})`} />); })}
        {/* 转起来：沿圈走的小点 */}
        {f >= E.kick.s && [...Array(8)].map((_, k) => { const [x, y] = at(-90 + k * 45 + (f - E.kick.s) * 1.1); return <circle key={k} cx={x} cy={y} r={6} fill={RED} opacity={span(f, E.kick.s, E.kick.l + 10) * 0.85} />; })}
        {[ND, NL, NR].map(([x, y], i) => <circle key={i} cx={x} cy={y} r={i ? 52 : 0} fill={PAPER} stroke={INK} strokeWidth={3} opacity={i === 1 ? span(f, E.lab.s, E.lab.l) : i === 2 ? span(f, E.res.s, E.res.l) : 0} />)}
        {/* Not at all：红叉 */}
        {f >= E.no.s && (() => { const p = span(f, E.no.s, E.no.l + 10); return <g stroke={RED} strokeWidth={5} strokeLinecap="round">
          <path d={`M716,318 L${716 + 26 * span(p, 0, 0.5)},${318 + 26 * span(p, 0, 0.5)}`} />{p > 0.5 && <path d={`M742,318 L${742 - 26 * span(p, 0.5, 1)},${318 + 26 * span(p, 0.5, 1)}`} />}</g>; })()}
        {/* 口袋红圈 */}
        {f >= E.pock.s && <circle cx={360} cy={318} r={24} fill="none" stroke={RED} strokeWidth={4} pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(f, E.pock.s, E.pock.l + 10)} />}
        {/* 6 把：打勾 */}
        {PICK.map((_, k) => { const p = span(f, E.test.s + 3 * k, E.test.l + 10 + 3 * k); const x = 1110 + 100 * k; return p > 0 &&
          <path key={k} d={`M${x - 12},598 L${x - 3},608 L${x + 14},588`} fill="none" stroke={RED} strokeWidth={4.5} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - p} />; })}
        {/* 时间线 */}
        {tl > 0 && <path d={`M${TL[0]},${TL[2]} L${TL[0] + (TL[1] - TL[0]) * tl},${TL[2]}`} stroke={span(f, E.d30.s, E.d30.l) > 0.5 ? RED : INK} strokeWidth={5} strokeLinecap="round" />}
        {tl > 0.98 && <path d={`M${TL[1]},${TL[2] - 14} L${TL[1]},${TL[2] + 14}`} stroke={INK} strokeWidth={4} />}
        {f >= E.fh.s && <circle cx={TL[0]} cy={TL[2]} r={14 * (1 + 0.4 * Math.exp(-Math.max(0, f - E.fh.l) / 7))} fill={RED} opacity={span(f, E.fh.s, E.fh.s + 6)} />}
      </svg>

      {/* design 节点：001 钥匙 */}
      <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: `${ND[0]}px ${ND[1]}px`, transform: `rotate(${no}deg)`}}>
        <Part name="key" cx={ND[0]} cy={ND[1]} w={150} at={0} f={f} gate={[0, 0.5]} flood={12} />
      </div>
      <Label x={ND[0]} y={ND[1] + 30} w={120} size={30} color={RED} p={1}>001</Label>
      <Part name="flask" cx={NL[0]} cy={NL[1]} w={62} at={E.lab.s} f={f} gate={[0.5, 1]} flood={14} />
      <Label x={NL[0] + 64} y={NL[1] - 18} w={240} size={30} italic align="left" p={span(f, E.data.s, E.data.e)}>real lab data</Label>
      <Part name="paper1" cx={NR[0]} cy={NR[1]} w={46} at={E.res.l + 10} f={f} gate={[0.5, 0.5]} flood={12} />
      <Label x={NR[0] - 64 - 160} y={NR[1] - 18} w={160} size={30} italic align="left" p={span(f, E.res.s, E.res.e)}>results</Label>
      {cardOn > 0 && <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: cardOn}}>
        <Part name="paper1" cx={cp[0]} cy={cp[1] - (cardA < 40 ? 70 * span(f, E.data.s, E.data.l + 12, out) : 0)} w={46} at={E.data.s} f={f} gate={[0.5, 0.5]} flood={10} />
      </div>}
      <Label x={LC[0]} y={LC[1] - 24} w={240} size={40} italic p={span(f, E.kick.s, E.kick.e)}>the loop</Label>

      {/* predicted pose 小图 */}
      {pose > 0 && <Part name="key" cx={300} cy={320} w={100} at={E.pose.s + 6} f={f} gate={[0, 0.5]} flood={12} />}
      <Part name="lock" cx={360} cy={300} w={80} at={E.pose.s} f={f} gate={[0.5, 1]} flood={14} />
      <Label x={345} y={372} w={260} size={30} italic p={span(f, E.pose.s, E.pose.e)}>predicted pose</Label>
      <Label x={215} y={300} w={80} size={28} color={RED} p={span(f, E.k001.s, E.k001.l + 12)}>001</Label>

      {/* 16 把新钥匙 → 6 把落到下面一排 */}
      {[...Array(16)].map((_, i) => {
        const k = PICK.indexOf(i);
        const t = span(s16, (i / 16) * 0.7, (i / 16) * 0.7 + 0.3, out);
        if (f < E.s16.s) return null;
        let [x, y] = gpos(i);
        x = ND[0] + (x - ND[0]) * t; y = ND[1] + (y - ND[1]) * t - Math.sin(Math.PI * t) * 60;
        if (k >= 0) { const p = span(six, k * 0.08, k * 0.08 + 0.6); x += (1110 + 100 * k - x) * p; y += (640 - y) * p; }
        const dim = k < 0 ? 1 - 0.65 * six : 1;
        return <div key={i} style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: dim * span(t, 0, 0.3)}}>
          <Part name="key" cx={x} cy={y} w={k >= 0 ? 92 : 104} at={E.s16.s + i} f={f} gate={[0, 0.5]} flood={10} />
        </div>;
      })}
      <Label x={1345} y={180} w={460} size={40} p={span(f, E.s16.s + 10, E.s16.e)}>Sixteen new designs</Label>
      <Part name="flask" cx={1730} cy={636} w={56} at={E.six.s + 6} f={f} gate={[0.5, 1]} flood={14} />
      <Label x={1360} y={680} w={460} size={38} color={RED} p={span(f, E.six.s, E.test.e)}>Six made and tested</Label>

      <Label x={TL[0]} y={TL[2] + 24} w={200} size={32} color={RED} p={span(f, E.fh.s, E.fh.e)}>first hit</Label>
      <Label x={TL[1]} y={TL[2] + 24} w={200} size={32} color={RED} p={span(f, E.d30.s, E.d30.e)}>30 days</Label>
      <Label x={(TL[0] + TL[1]) / 2} y={TL[2] - 54} w={300} size={32} italic p={span(f, E.all.s, E.all.e)}>all within</Label>

      <Source p={span(f, E.loop.l, E.loop.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual507" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
