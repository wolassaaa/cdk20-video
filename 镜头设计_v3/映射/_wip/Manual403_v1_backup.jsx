// HKBU SCIE1007 课程作业的科普视频：第 4 章二维说明书页 4-03（画外音）一段把握很低的尾巴压在锁孔上。
// 左：锁（= 蛋白）长出，一截尾巴从锁体右上伸出来；说起来 low confidence 时它软塌下来、变成红虚线。
// 右：放大圈罩住锁孔（示意），尾巴横过锁孔口，口袋里坐着一块标 ATP 的积木；最后在下面切钥匙、锁孔打叉。
// 时间全读 keys_4-03.json（事件表 映射/events/4-03.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_4-03.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, Bead, evMap, Label, Pen, PageFrame, Source, Placeholder} from "./kit.jsx";

const E = evMap(K);
const LKX = 470, LKY = 560, LKW = 380, LKH = (LKW * 743) / 520;      // 锁（蛋白）
const KHY = LKY + 0.132 * LKH;                                        // 锁孔中心
const ZR = 200, ZX = 1255, ZY = 420;                                  // 放大圈
// 尾巴四态：直挺 → 垂 → 更垂 → 横过锁孔（锁上的坐标）
const TA = [[612, 528], [648, 556], [674, 594], [692, 640], [700, 690]];
const TB = [[612, 528], [632, 574], [630, 624], [606, 664], [568, 688]];
const TC = [[612, 528], [634, 580], [628, 636], [598, 674], [552, 694]];
const TD = [[612, 528], [594, 580], [542, 610], [492, 628], [440, 646]];
// 放大圈里同一段尾巴（圈内坐标）
const ZA = [[262, 150], [286, 130], [308, 110], [328, 90], [344, 70]];
const ZB = [[262, 150], [278, 186], [270, 222], [246, 250], [212, 264]];
const ZC = [[262, 150], [282, 192], [272, 234], [242, 264], [204, 278]];
const ZD = [[262, 150], [238, 176], [200, 192], [158, 204], [116, 210]];
const mix = (A, B, t) => A.map(([x, y], i) => [x + (B[i][0] - x) * t, y + (B[i][1] - y) * t]);
const poly = (P) => P.map(([x, y]) => `${x},${y}`).join(" ");
const KEYS = [[1200, 868], [1430, 868], [1660, 868]];

const Scene = () => {
  const f = useCurrentFrame();
  const m1 = span(f, E.floppy.s, E.floppy.l, ease);
  const m2 = span(f, E.had.s, E.had.l, ease);
  const m3 = span(f, E.across.s, E.across.l, Easing.inOut(Easing.cubic));
  const ch = (A, B, C, D) => mix(mix(mix(A, B, m1), C, m2), D, m3);
  const TL = ch(TA, TB, TC, TD), TZ = ch(ZA, ZB, ZC, ZD);
  const lowP = span(f, E.low.s, E.low.l + 4);
  const tCol = lowP > 0.6 ? RED : INK, tDash = lowP > 0.6 ? "15 11" : undefined;
  const zp = span(f, E.zoom.s, E.zoom.l + 10, out);
  const surf = span(f, E.zoom.s + 4, E.zoom.l + 18, ease);
  const ring = span(f, E.zoom.s, E.zoom.l, out);
  const ring2 = span(f, E.keyhole.s, E.keyhole.l + 6, out);
  const flash = f >= E.blindly.s && f < E.blindly.l + 40 ? 0.5 + 0.5 * Math.cos((f - E.blindly.s) / 5) : 0;
  const socket = span(f, E.with.s, E.with.l + 6, out) * (1 - span(f, E.sitting.s, E.sitting.l));
  const blockIn = span(f, E.block.s, E.block.l + 8, Easing.out(Easing.back(1.3)));
  const sit = span(f, E.sitting.s, E.sitting.l, ease);
  const cross = span(f, E.blocked.s, E.blocked.l + 6, ease);
  const box = span(f, E.and.s, E.and.l + 12, ease);
  const bead = [[0, 130, 96], [E.lock.l, 460, 96], [E.title.l, 620, 196], [E.zoom.l, 980, 250], [E.end.l, 700, 460],
                [E.protein.l, 190, 700], [E.floppy.l, 700, 500], [E.tail.l, 900, 500], [E.had.l, 980, 545], [E.low.l, 880, 560],
                [E.conf.l, 780, 560], [E.model.l, 300, 200], [E.across.l, 190, 620], [E.keyhole.l, 720, 720],
                [E.with.l, 900, 770], [E.block.l, 1000, 700], [E.sitting.l, 860, 700], [E.pocket.l, 780, 700],
                [E.trust.l, 700, 760], [E.blindly.l, 600, 700], [E.and.l, 900, 940], [E.cut.l, 1000, 900],
                [E.keys.l, 1020, 970], [E.blocked.l, 1020, 760], [E.door.l, 960, 700], [K.len_f, 961, 699]];
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("4-03.wav")} />
      <PageFrame />
      <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>Look closer</Write></div>

      {/* 锁 = 蛋白 */}
      <Part name="lock" cx={LKX} cy={LKY} w={LKW} at={E.lock.s} f={f} gate={[0.5, 1]} />

      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        {/* 锁上这段尾巴：从锁体右上伸出来，再软塌、再横过锁孔 */}
        <polyline points={poly(TL)} fill="none" stroke={tCol} strokeWidth={13} strokeLinejoin="round" strokeLinecap="round" strokeDasharray={tDash}
                  opacity={span(f, E.end.s - 4, E.end.l + 8)} />
        {TL.map(([x, y], i) => <circle key={i} cx={x} cy={y} r={i === TL.length - 1 ? 8.5 : 7} fill={tCol} opacity={span(f, E.end.s + 2 * i, E.end.l + 2 * i)} />)}
        {/* 尾巴起点：一端 */}
        {f >= E.end.s && <circle cx={612} cy={528} r={26} fill="none" stroke={RED} strokeWidth={3} strokeDasharray="6 6"
                                  opacity={span(f, E.end.s, E.end.l) * (0.65 + 0.35 * flash)} />}
        {/* 锁孔：红圈跟着放大圈一起亮，blocked 时打叉 */}
        {ring > 0 && <circle cx={LKX} cy={KHY} r={64} fill="none" stroke={RED} strokeWidth={3.5} strokeDasharray="8 6"
                             opacity={ring * (0.85 + 0.15 * flash)} />}
        {cross > 0 && (
          <g stroke={RED} strokeWidth={8} strokeLinecap="round">
            <path d={`M${LKX - 46},${KHY - 46} L${LKX - 46 + 92 * span(cross, 0, 0.5)},${KHY - 46 + 92 * span(cross, 0, 0.5)}`} />
            <path d={`M${LKX + 46},${KHY - 46} L${LKX + 46 - 92 * span(cross, 0.5, 1)},${KHY - 46 + 92 * span(cross, 0.5, 1)}`} />
          </g>
        )}
        {/* Trust it blindly 的时候，锁孔外面扫出两道红圈（警示，跟着这句走） */}
        {[0, 1].map((k) => {
          const a = E.trust.s + k * 60, p = span(f, a, a + 60, Easing.out(Easing.quad));
          if (p <= 0 || p >= 1) return null;
          return <circle key={k} cx={LKX} cy={KHY} r={64 + 126 * p} fill="none" stroke={RED} strokeWidth={9 * (1 - 0.6 * p)} opacity={0.85 * (1 - p)} />;
        })}
        {/* 锁孔 → 放大圈的两条引线 */}
        {zp > 0 && (
          <g stroke={RED} strokeWidth={2.5} strokeDasharray="7 7" fill="none" opacity={Math.min(1, zp)}>
            <path d="M540,640 L1045,590" />
            <path d="M540,690 L1045,650" />
          </g>
        )}
      </svg>

      {/* 放大圈：锁孔示意（大图） */}
      {zp > 0 && (
        <div style={{position: "absolute", left: ZX - ZR, top: ZY - ZR, width: ZR * 2, height: ZR * 2, borderRadius: ZR,
                     border: `4px solid ${INK}`, background: "#F4F1EA", boxSizing: "border-box", overflow: "hidden", transform: `scale(${zp})`}}>
          <svg width={ZR * 2} height={ZR * 2} style={{position: "absolute", left: 0, top: 0}}>
            {/* 蛋白表面（半透明蓝），中间是锁孔（挖空成纸色） */}
            <circle cx={200} cy={200} r={ZR} fill="rgba(36,62,170,0.20)" opacity={surf} />
            <g opacity={surf}>
              <circle cx={200} cy={142} r={86} fill="#F4F1EA" stroke="#2A3F9E" strokeWidth={4} />
              <rect x={152} y={142} width={96} height={154} fill="#F4F1EA" />
              <path d="M152,142 L152,296 M248,142 L248,296 M152,296 L248,296" fill="none" stroke="#2A3F9E" strokeWidth={4} strokeLinecap="round" />
            </g>
            {/* 锁孔红圈 */}
            {ring2 > 0 && <circle cx={200} cy={158} r={112} fill="none" stroke={RED} strokeWidth={4} strokeDasharray="9 7"
                                   opacity={ring2 * (0.85 + 0.15 * flash)} />}
            {/* 尾巴横过锁孔口 */}
            <polyline points={poly(TZ)} fill="none" stroke={tCol} strokeWidth={18} strokeLinejoin="round" strokeLinecap="round" strokeDasharray={tDash}
                      opacity={span(f, E.tail.s - 6, E.tail.l + 10)} />
            {TZ.map(([x, y], i) => <circle key={i} cx={x} cy={y} r={11} fill={tCol} opacity={span(f, E.tail.s + 2 * i, E.tail.l + 2 * i)} />)}
            {/* 口袋里的座：虚线座 → 积木长进去 → 坐实 */}
            {socket > 0 && <rect x={158} y={238} width={84} height={48} rx={6} fill="none" stroke={RED} strokeWidth={2.5} strokeDasharray="6 5" opacity={socket} />}
            {blockIn > 0 && (
              <g transform={`translate(200 ${262 + 26 * (1 - blockIn) + 6 * sit}) scale(${blockIn}) translate(-200 -262)`}>
                <rect x={158} y={238} width={84} height={48} rx={6} fill="#F4F1EA" stroke={INK} strokeWidth={3} />
                <text x={200} y={270} textAnchor="middle" fontSize={27} fontFamily="Serif" fill={INK}>ATP</text>
              </g>
            )}
          </svg>
        </div>
      )}
      <Label x={ZX} y={638} w={320} size={24} align="center" p={span(f, E.pocket.s, E.pocket.l + 10)}>the ATP pocket</Label>

      {/* 字 */}
      <Label x={470} y={236} w={220} size={26} italic color={SOFT} p={span(f, E.model.s, E.model.l + 10)}>in the model</Label>
      <Label x={470} y={858} w={260} size={30} p={span(f, E.protein.s, E.protein.l + 10)}>the protein</Label>
      <Label x={700} y={190} w={240} size={26} align="left" p={span(f, E.end.s, E.end.l + 10)}>one end</Label>
      <Label x={700} y={240} w={300} size={28} align="left" p={span(f, E.tail.s, E.tail.l + 10)}>a floppy tail</Label>
      <Label x={ZX} y={176} w={300} size={24} align="center" p={span(f, E.keyhole.s, E.keyhole.l + 8)}>the keyhole</Label>
      <Pen x={690} y={298} p={span(f, E.conf.s, E.conf.l + 14)} size={34} rot={-3}>really low confidence</Pen>
      <Pen x={700} y={386} p={span(f, E.trust.s, E.blindly.l + 8)} size={34} rot={-2}>Trust it blindly</Pen>

      {/* 下面：照它配出来的钥匙 */}
      <Placeholder x={1080} y={808} w={690} h={118} show={box} hide={0} />
      {KEYS.map(([x, y], i) => (
        <Part key={i} name="key" cx={x} cy={y} w={210} at={i === 0 ? E.cut.s : E.keys.s + 6 * (i - 1)} f={f} gate={[0.06, 0.45]} />
      ))}
      {cross > 0 && <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <path d={`M1092,882 L${1092 + 656 * span(cross, 0.4, 1)},${882 - 28 * span(cross, 0.4, 1)}`} stroke={RED} strokeWidth={7} fill="none" strokeLinecap="round" />
      </svg>}
      <Label x={1420} y={940} w={420} size={28} p={span(f, E.door.s, E.door.l + 10)}>for a blocked door</Label>

      <Source p={span(f, E.title.l, E.title.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration (not to scale)</Source>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};
const Root = () => <Composition id="Manual403" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
