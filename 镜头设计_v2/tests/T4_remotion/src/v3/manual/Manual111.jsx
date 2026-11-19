// HKBU SCIE1007 课程作业的科普视频：第 1 章二维说明书页 1-11（C 画外音）。
// 上方：七站的路（和三维大板的主料杆是同一条路，这里是说明书线稿），AI 芯片快步走过前三站。
// 下方两个框：① 一个真实案例（芯片拼到肝上） ② 从香港开始（地图上落红点）。
// 时间全部来自事件表 映射/events/1-11.json → resolve.py → keys_1-11.json。
//   node node_modules/@remotion/cli/remotion-cli.js render src/v3/manual/Manual111.jsx Manual111 <帧目录> --sequence --public-dir=<映射/_cache/ch1/public>
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_1-11.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Tag, Write, Step, Legend, evMap, Lens, guidePlan} from "./kit.jsx";

const E = evMap(K);
const GP = guidePlan(K);   // 视线引导（11-20，替代红色料珠）：事件表 guide 字段 → resolve.py → keys.guides
const AR = {chip: 696 / 696, liver: 1052 / 792, hk: 1174 / 791};
const ST = ["Target", "Hit", "Improve", "Cells", "Animals", "Trials", "Approval"];
const RX0 = 230, RX1 = 1690, RY = 236;
const sx = (i) => RX0 + ((RX1 - RX0) * i) / (ST.length - 1);
const BX = [96, 988], BY = 392, BW = 836, BH = 470;

const Label = ({x, y, w = 260, p, children, size = 26, color = INK, italic}) => (
  <div style={{position: "absolute", left: x - w / 2, top: y, width: w, textAlign: "center", fontSize: size, color, fontStyle: italic ? "italic" : "normal"}}>
    <Write p={p}>{children}</Write>
  </div>
);

const Scene = () => {
  const f = useCurrentFrame();
  // ---- 路 ----
  const road = span(f, E.road.s, E.road.e, ease);
  const walk = span(f, E.chip_walk.s, E.chip_walk.l, Easing.inOut(Easing.cubic));
  const cx = RX0 - 70 + (sx(2) + 20 - (RX0 - 70)) * walk;
  const hop = Math.abs(Math.sin(walk * Math.PI * 3)) * -16 * (walk > 0 && walk < 1 ? 1 : 0);
  const speed = span(f, E.chip_walk.s, E.chip_walk.s + 20) * (1 - span(f, E.chip_walk.l, E.chip_walk.l + 24));
  // ---- 第 1 步：芯片拼到肝上 ----
  const snapP = span(f, E.case_snap.s, E.case_snap.l, Easing.in(Easing.quad));
  const snapK = f > E.case_snap.l ? Math.exp(-(f - E.case_snap.l) / 5) * Math.cos((f - E.case_snap.l) / 2.6) : 0;
  // ---- 第 2 步：红点 ----
  const pinP = span(f, E.pin.s, E.pin.l, Easing.in(Easing.quad));
  const pinK = f > E.pin.l ? Math.exp(-(f - E.pin.l) / 5) * Math.cos((f - E.pin.l) / 2.4) : 0;
  const PIN = [BX[1] + 418 + 50, BY + 250 - 20];

  return (
    <Lens plan={GP} f={f}>
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("1-11.wav")} />
      <div style={{position: "absolute", inset: "34px 40px 44px 40px", border: `1.5px solid rgba(31,30,28,0.22)`, borderRadius: 4}} />

      {/* ============ 路：七个站点 ============ */}
      <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
        <path d={`M${RX0 - 110},${RY} L${RX1 + 60},${RY}`} stroke={INK} strokeWidth={7} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - road} />
        {ST.map((s, i) => {
          const p = span(road, (i + 0.4) / (ST.length + 0.6), (i + 1.2) / (ST.length + 0.6), out);
          const done = i < 3 && walk > (i + 0.5) / 3;
          return <circle key={s} cx={sx(i)} cy={RY} r={15 * p} fill={done ? RED : PAPER} stroke={INK} strokeWidth={4} />;
        })}
        {/* 速度线 */}
        {[0, 1, 2].map((k) => (
          <path key={k} d={`M${cx - 70 - k * 8},${RY - 82 + k * 16} L${cx - 120 - k * 26},${RY - 82 + k * 16}`} stroke={INK} strokeWidth={3} strokeLinecap="round" opacity={0.7 * speed} />
        ))}
      </svg>
      {ST.map((s, i) => (
        <Label key={s} x={sx(i)} y={RY + 28} w={180} p={span(road, (i + 0.6) / (ST.length + 0.6), (i + 1.4) / (ST.length + 0.6))} size={28}>{s}</Label>
      ))}
      <div style={{position: "absolute", left: cx - 44, top: RY - 128 + hop}}>
        <Part name="chip" cx={44} cy={44} w={88} ar={1} at={E.chip.s + 2} f={f} gate={[0.5, 1]} flood={16} />
      </div>
      <div style={{position: "absolute", left: sx(1) + 40, top: RY - 160, font: "44px Hand", color: RED, transform: "rotate(-4deg)"}}>
        <Write p={span(f, E.q.s, E.q.e)}>faster?</Write>
      </div>

      {/* ============ 第 1 步：一个真实案例 ============ */}
      {[[BX[1], E.step2.l]].map(([x, at]) => (
        <div key={x} style={{position: "absolute", left: x, top: BY, width: BW, height: BH, border: "2px dashed rgba(31,30,28,0.16)", borderRadius: 10, boxSizing: "border-box",
                             opacity: span(f, E.step1.l, E.step1.l + 24) * (1 - span(f, at, at + 30))}} />
      ))}
      <Step n="1" x={BX[0]} y={BY} w={BW} h={BH} at={E.step1.l} f={f}>
        <div style={{position: "absolute", left: 122, top: 10, fontSize: 56, lineHeight: "72px"}}><Write p={span(f, E.title1.s, E.title1.e)}>One real case</Write></div>
        <div style={{position: "absolute", left: 92 * snapP - 5 * snapK, top: 0}}>
          <Part name="chip" cx={300} cy={262} w={140} ar={1} at={E.chip2.s + 2} f={f} gate={[0.5, 1]} flood={16} />
        </div>
        <Part name="liver" cx={600} cy={262} w={280} ar={AR.liver} at={E.liver.s + 2} f={f} gate={[1, 0.45]} />
        <Label x={300} y={350} w={200} p={span(f, E.chip2.s, E.chip2.e) * (1 - snapP)} size={26} italic>AI tools</Label>
        <Label x={600} y={378} w={240} p={span(f, E.liver.s, E.liver.e)} size={26} italic>liver cancer</Label>
        <Tag n="04" x={760} y={150} at={E.liver.l + 18} f={f} />
        <Tag n="13" x={196} y={170} at={E.chip2.l + 18} f={f} />
      </Step>

      {/* ============ 第 2 步：从香港开始 ============ */}
      <Step n="2" x={BX[1]} y={BY} w={BW} h={BH} at={E.step2.l} f={f}>
        <div style={{position: "absolute", left: 122, top: 10, fontSize: 56, lineHeight: "72px"}}><Write p={span(f, E.title2.s, E.title2.e)}>Starts here</Write></div>
        <Part name="hk" cx={418} cy={270} w={400} ar={AR.hk} at={E.hk.s + 2} f={f} gate={[0, 0]} />
        <Tag n="07" x={680} y={150} at={E.hk.l + 18} f={f} />
      </Step>
      {pinP > 0 && (
        <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0}}>
          <circle cx={PIN[0]} cy={PIN[1] - 120 * (1 - pinP) + 4 * pinK} r={13} fill={RED} stroke={PAPER} strokeWidth={3} />
          <circle cx={PIN[0]} cy={PIN[1]} r={13 + 30 * span(f, E.pin.l, E.pin.l + 24)} fill="none" stroke={RED} strokeWidth={3} opacity={1 - span(f, E.pin.l, E.pin.l + 24)} />
        </svg>
      )}
      <div style={{position: "absolute", left: PIN[0] + 150, top: PIN[1] + 40, font: "40px Hand", color: RED, transform: "rotate(-4deg)"}}>
        <Write p={span(f, E.pin.s, E.pin.e + 10)}>right here</Write>
      </div>

      <Legend x={BX[0]} y={884} w={BW} at={E.chip2.l} f={f} rows={[[["13", "AI tools", E.chip2.l + 18], ["04", "liver cancer", E.liver.l + 18]]]} />
      <Legend x={BX[1]} y={884} w={BW} at={E.hk.l} f={f} rows={[[["07", "Hong Kong", E.hk_label.l]]]} />

      <div style={{position: "absolute", left: 44, top: 1046, fontSize: 17, color: SOFT, opacity: span(f, E.road.l, E.road.l + 20)}}>
        Ren et al., Chem. Sci. 2023 · Illustration
      </div>
    </AbsoluteFill>
    </Lens>
  );
};

const Root = () => <Composition id="Manual111" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
