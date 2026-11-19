// HKBU SCIE1007 课程作业的科普视频：第 3 章二维说明书页 3-04（D 画外音）"Our lock is CDK20 …"
// 左：锁 = CDK20；标签 an enzyme / a protein with a chemical job；齿轮表示它在干活。
// 右：放大圈看口袋（示意），ATP 滑进去，齿轮转；钥匙把 ATP 顶出去、占住口袋，齿轮停，字牌。
// 11-20：红色料珠去掉，换成视线引导（Lens/Layer/RunnerPulse）。
// 时间全读 keys_3-04.json（事件表 映射/events/3-04.json）。
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_3-04.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Write, evMap, Lens, Layer, RunnerPulse, guidePlan, Label, Pen, PageFrame, Source, Plate} from "./kit.jsx";

const E = evMap(K);
const GP = guidePlan(K);
const CX = 470, CY = 560, CW = 400;            // CDK20 零件
const PK = [CX + 70, CY - 70];                 // 口袋示意位置（在零件上）
const IX = 1250, IY = 560, IR = 260;           // 放大圈
const NX = IX, NY = IY + 90;                   // 放大圈里口袋（槽）中心

const Gear = ({x, y, r, rot, color = INK}) => {
  const teeth = 10, pts = [];
  for (let i = 0; i < teeth * 2; i++) {
    const a = (i / (teeth * 2)) * Math.PI * 2, rr = i % 2 ? r : r * 0.78;
    pts.push(`${x + rr * Math.cos(a)},${y + rr * Math.sin(a)}`);
  }
  return (
    <g transform={`rotate(${rot} ${x} ${y})`}>
      <polygon points={pts.join(" ")} fill="none" stroke={color} strokeWidth={4} strokeLinejoin="round" />
      <circle cx={x} cy={y} r={r * 0.3} fill="none" stroke={color} strokeWidth={4} />
    </g>
  );
};

const Scene = () => {
  const f = useCurrentFrame();
  const eq = span(f, E.cdk.s, E.cdk.l, out);
  const gearIn = span(f, E.gear.s, E.gear.l, Easing.out(Easing.back(1.6)));
  // 齿轮转速：长出后慢转，ATP 在口袋里时转快，钥匙卡住后停下（带一点回弹）
  const atpIn = span(f, E.atp.s, E.atp.l, ease), atpOut = span(f, E.out.s, E.out.l, Easing.in(Easing.cubic));
  const keyIn = span(f, E.key.s, E.key.l, ease);
  const stopF = E.stop.l;
  const speed = (t) => (t < E.gear.s ? 0 : t >= stopF ? 0 : 1.2 + 3 * span(t, E.atp.l - 20, E.atp.l + 10) * (1 - span(t, E.out.s, E.out.l)));
  let rot = 0;
  for (let t = E.gear.s; t <= Math.min(f, stopF); t++) rot += speed(t);
  const jolt = f > stopF ? Math.exp(-(f - stopF) / 5) * Math.sin((f - stopF) / 1.6) * 6 : 0;
  const cross = span(f, E.stop.s, E.stop.e, ease);
  const ring = span(f, E.hole.s, E.hole.s + 16, out);
  const ins = span(f, E.inset.s, E.inset.l + 10, Easing.out(Easing.back(1.2)));
  const pocketDraw = span(f, E.inset.l, E.inset.e, ease);
  // ATP：从放大圈右上进来落到开口；被顶出时弹向右下、变灰
  const ax0 = IX + 190, ay0 = IY - 200;
  const ax = ax0 + (NX - ax0) * atpIn + 230 * atpOut, ay = ay0 + (NY - 6 - ay0) * atpIn - Math.sin(Math.PI * atpIn) * 30 + 150 * atpOut;
  // 钥匙：竖着从上方落下，齿插到槽底
  const kx = NX, ky = NY - 44 - 300 * (1 - keyIn);
  const plate = span(f, E.plate.s, E.plate.s + 14, out);
  const RN = GP.find((g) => g.kind === "runner");
  // 口袋 → 放大圈的引线：keyhole 之后画出，指向放大圈马上要长出的位置（11-20 改灰色，红色留给口袋红圈）
  const lead = span(f, E.hole.l + 14, E.hole.l + 32, ease);
  const A1 = [PK[0] + 32, PK[1] - 34], B1 = [IX - IR * 0.72, IY - IR * 0.7], A2 = [PK[0] + 32, PK[1] + 34], B2 = [IX - IR * 0.72, IY + IR * 0.7];
  const seg = (A, B, p) => `M${A[0]},${A[1]} L${A[0] + (B[0] - A[0]) * p},${A[1] + (B[1] - A[1]) * p}`;
  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("3-04.wav")} />
      <PageFrame />
      {/* 视线引导（05 文档 8.3，二维版）：CDK20 → 齿轮（job）→ 口袋（keyhole，预颤）→ 沿引线走料到放大圈（pocket，CDK20 到放大圈 41% 画面宽）
          → Plug 时回到放大圈（预颤）→ can't 时回到齿轮（预颤）。ATP、钥匙都在放大圈里，不另点名。 */}
      <Lens plan={GP} f={f}>
        <Layer id="cdk">
          {/* 锁 = CDK20 */}
          <Part name="lock" cx={300} cy={250} w={80} at={E.lock.s + 2} f={f} gate={[0.5, 1]} />
          <Part name="cdk20" cx={CX} cy={CY} w={CW} at={E.cdk.s + 2} f={f} gate={[0.5, 1]} />
          <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
            {/* 口袋红圈 */}
            {ring > 0 && <circle cx={PK[0]} cy={PK[1]} r={46 * (1.3 - 0.3 * ring)} fill="none" stroke={RED} strokeWidth={4} opacity={ring} strokeDasharray="8 6" />}
          </svg>
        </Layer>
        <Layer id="gear">
          <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
            {/* 齿轮：它的“工作” */}
            {gearIn > 0 && <g transform={`translate(800 260) scale(${gearIn}) translate(-800 -260)`}><Gear x={800} y={260} r={54} rot={rot + jolt} color={cross > 0 ? "#8A867C" : INK} /></g>}
            {cross > 0 && (
              <g stroke={RED} strokeWidth={8} strokeLinecap="round">
                <path d="M752,212 L848,308" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(cross, 0, 0.5)} />
                <path d="M848,212 L752,308" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - span(cross, 0.5, 1)} />
              </g>
            )}
          </svg>
        </Layer>
        <Layer id="inset">
          <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
            {lead > 0 && (
              <g stroke={SOFT} strokeWidth={2.5} strokeDasharray="6 6" fill="none">
                <path d={seg(A1, B1, lead)} />
                <path d={seg(A2, B2, lead)} />
              </g>
            )}
            {RN && <RunnerPulse d={seg(A1, B1, 1)} a={RN.gs} b={RN.gon} f={f} sw={2.5} color={SOFT} len={0.12} />}
          </svg>
          {/* 放大圈：口袋示意 */}
          {ins > 0 && (
            <div style={{position: "absolute", left: IX - IR, top: IY - IR, width: IR * 2, height: IR * 2, borderRadius: IR, border: `4px solid ${INK}`, background: "#F4F1EA",
                         boxSizing: "border-box", overflow: "hidden", transform: `scale(${ins})`}}>
              <svg width={IR * 2} height={IR * 2} style={{position: "absolute", left: 0, top: 0}}>
                {/* 蛋白表面，上方一个开口 */}
                <path d={`M0,${IR + 40} C${IR * 0.4},${IR + 10} ${IR * 0.62},${IR + 30} ${IR - 70},${IR + 20} L${IR - 60},${IR + 110} C${IR - 40},${IR + 150} ${IR + 40},${IR + 150} ${IR + 60},${IR + 110} L${IR + 70},${IR + 20} C${IR * 1.4},${IR + 30} ${IR * 1.7},${IR + 6} ${IR * 2},${IR + 40} L${IR * 2},${IR * 2} L0,${IR * 2} Z`}
                      fill="rgba(36,62,170,0.22)" stroke="#2A3F9E" strokeWidth={5} strokeLinejoin="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - pocketDraw} />
              </svg>
              <div style={{position: "absolute", left: 0, width: IR * 2, top: IR * 2 - 84, textAlign: "center", fontSize: 30, fontStyle: "italic", opacity: span(f, E.inset.l + 10, E.inset.e)}}>the pocket</div>
            </div>
          )}
          {/* ATP：圆角小块 */}
          {f >= E.atp.s && f < E.out.l + 40 && (
            <div style={{position: "absolute", left: ax - 52, top: ay - 26, width: 104, height: 52, borderRadius: 26, background: atpOut > 0 ? "#B9B4A8" : "#E9B44C", border: `3px solid ${INK}`,
                         boxSizing: "border-box", textAlign: "center", font: "30px/46px Serif", opacity: 1 - span(f, E.out.l + 10, E.out.l + 40)}}>ATP</div>
          )}
          {/* 钥匙 */}
          {f >= E.key.s && (
            <div style={{position: "absolute", left: kx - 90, top: ky - 26, width: 180, height: 51, transform: "rotate(90deg)", opacity: span(f, E.key.s, E.key.s + 8)}}>
              <Part name="key" cx={90} cy={26} w={180} at={-100} f={f} />
            </div>
          )}
        </Layer>
        <Layer exempt>
          <div style={{position: "absolute", left: 96, top: 62, fontSize: 56}}><Write p={span(f, E.title.s, E.title.e)}>Our lock</Write></div>
          <div style={{position: "absolute", left: 360, top: 222, fontSize: 48, opacity: eq}}>=</div>
          <div style={{position: "absolute", left: 420, top: 222, fontSize: 52, opacity: eq}}><Write p={span(f, E.cdk.l - 6, E.cdk.e)}>CDK20</Write></div>
          <Label x={CX} y={CY + 190} w={420} size={30} p={span(f, E.enz.s, E.enz.e)}>an enzyme:</Label>
          <Label x={CX} y={CY + 232} w={460} size={26} italic color={SOFT} p={span(f, E.prot.s, E.prot.e)}>a protein with a chemical job</Label>
          <Label x={IX} y={IY - IR - 58} w={360} size={28} italic p={span(f, E.hole.s, E.hole.e)}>the keyhole</Label>
          <Label x={IX + 200} y={IY - IR - 10} w={300} size={24} italic color={SOFT} p={span(f, E.atp.l - 40, E.atp.e) * (1 - span(f, E.out.s, E.out.s + 20))} align="left">a small molecule</Label>
          <Label x={IX + IR + 24} y={IY + 40} w={240} size={26} italic p={span(f, E.key.l - 10, E.key.e)} align="left">the right key</Label>
          <Plate x={1010} y={880} w={820} p={plate}><span style={{fontSize: 52, fontStyle: "italic"}}>…and the enzyme can't do its job.</span></Plate>
          <Source p={span(f, E.title.l, E.title.l + 20)}>Ren et al., Chem. Sci. 2023 · Illustration (not to scale)</Source>
        </Layer>
      </Lens>
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual304" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
