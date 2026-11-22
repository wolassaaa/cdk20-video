// HKBU SCIE1007 课程作业的科普视频：B 档 2-05（C 画外音）"One: to identify the major computer-aided methods used in cancer drug discovery. Two: …"
// 上栏 Aim 1：编号牌 1；identify：放大镜从左扫过来；computer-aided methods：三块 AI 芯片依次落位（放大镜停在中间那块上）；cancer drug discovery：玻璃肝。
// 下栏 Aim 2：编号牌 2；evaluate：料杆和检测门长出来；these methods：上栏芯片一块块亮；scientists：小人；
// assess：五个金插头沿料杆走过检测门，过门时各长一根分数条；potential drug candidates：插头排好，分数最高的打勾。
// 导演 11-18 看二维样片 2-05 时要求加说明文字：两栏各一行 Aim 1 / Aim 2 的标签。
// 接点：开头 T5 料杆擦除（2-04 出镜段），结尾 T2 往左甩（2-06 是 B 页）。L0 第 2 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_2-05.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, camBreath, Stage, Sprite, Slab, Runner, Plate, Label, Source, Tick, LoupeRing, Person1, evMapB, T5In, whipX} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 2;

const NUM = (row) => ({x: 90, y: row === 1 ? 150 : 540, w: 120, h: 120});
const CHIPS = ["pandaomics", "alphafold", "chemistry42"];
const CHIP_X = [760, 1080, 1400], CHIP_Y = 330, CHIP_W = 290;
const LIVER = {x: 1730, y: 320, w: 250};
const RUN_Y = 790, RUN_X0 = 560, RUN_X1 = 1800;
const GATE_X = 1080;
const PL = ["A", "B", "C", "D", "E"];
const SCORE = [0.5, 0.72, 0.4, 0.95, 0.6];
const BEST = 3;
const PW = 120;
const SLOT_X = (i) => 1180 + i * 125;

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("n1", 0, 1, E.aim1.l);
    X.tw("lp", 0, 1, E.identify.s, E.methods.l + 60, "power2.inOut");
    X.group(CHIPS.map((_, i) => `c${i}`), 0, 1, E.methods.l, {step: 14, antic: false});
    X.land("liver", 0, 1, E.cancer.l, {antic: false});
    X.land("n2", 0, 1, E.aim2.l);
    X.tw("run", 0, 1, E.eval.s, E.eval.e, "power2.out");
    X.land("gate", 0, 1, E.eval.l + 6, {antic: false});
    X.land("sci", 0, 1, E.sci.l, {antic: false});
    X.group(PL.map((_, i) => `p${i}`), 0, 1, E.sci.l + 10, {step: 4, antic: false});
    X.tw("walk", 0, 1, E.assess.s, E.cands.l, "none");
    X.tw("tick", 0, 1, E.cands.l + 6, E.cands.l + 26, "power2.out");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const whip = whipX(f, LEN - 7, "out", -1);

  // 放大镜：从左边扫过三块芯片，最后停在中间那块上
  const lp = S.lp;
  const lx = lp < 0.75 ? mix(420, CHIP_X[2] + 40, lp / 0.75) : mix(CHIP_X[2] + 40, CHIP_X[1] + 30, (lp - 0.75) / 0.25);
  const ly = CHIP_Y - 10 + 18 * Math.sin(lp * Math.PI * 3);
  // these methods：三块芯片一块块亮
  const chipRim = (i) => { const t = (f - E.these.s - i * 10) / 24; return t > 0 && t < 1 ? Math.sin(Math.PI * t) : 0; };
  // 插头：排在料杆左段，assess 时依次走过检测门到右边的位置
  const plugX = (i) => {
    const start = RUN_X0 + 30 + i * 95;
    const u = clamp01(S.walk * 1.6 - (PL.length - 1 - i) * 0.15);
    return mix(start, SLOT_X(i), u);
  };
  const passed = (i) => clamp01((plugX(i) - GATE_X) / 90);

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} cam={camBreath(f, K, ["s1"])} over={<T5In name="runner" f={f} />}>
        <Layer id="aim1">
          {S.n1 > 0.01 && <Plate x={NUM(1).x} y={NUM(1).y - 30 * (1 - Math.min(1, S.n1))} w={120} h={120} text="1" size={96} op={Math.min(1, S.n1 * 1.5)} r={24} depth={12} id="n1" />}
        </Layer>
        <Layer id="chips">
          {CHIPS.map((n, i) => {
            const a = S[`c${i}`];
            return a > 0.01 && <Sprite key={i} name={`chip_${n}/34`} x={CHIP_X[i]} y={CHIP_Y - 40 * (1 - Math.min(1, a)) + id(1 + i).y} w={CHIP_W} op={Math.min(1, a * 1.5)} rot={id(1 + i).r} rim={chipRim(i)} />;
          })}
          {S.liver > 0.01 && <Sprite name="liver/34" x={LIVER.x} y={LIVER.y - 40 * (1 - Math.min(1, S.liver)) + id(4).y} w={LIVER.w} op={Math.min(1, S.liver * 1.5)} rot={id(4).r} />}
          {lp > 0.001 && <LoupeRing x={lx} y={ly} r={78} op={Math.min(1, lp * 8)} />}
        </Layer>

        <Layer id="aim2">
          {S.n2 > 0.01 && <Plate x={NUM(2).x} y={NUM(2).y - 30 * (1 - Math.min(1, S.n2))} w={120} h={120} text="2" size={96} op={Math.min(1, S.n2 * 1.5)} r={24} depth={12} id="n2" />}
          {S.run > 0.001 && <Runner d={`M${RUN_X0},${RUN_Y} L${RUN_X1},${RUN_Y}`} draw={S.run} width={18} />}
          {S.gate > 0.01 && (
            <>
              <Slab x={GATE_X - 70} y={RUN_Y - 230 * Math.min(1, S.gate)} w={20} h={230 * Math.min(1, S.gate)} r={8} color={C.bone} depth={6} id="gL" />
              <Slab x={GATE_X + 50} y={RUN_Y - 230 * Math.min(1, S.gate)} w={20} h={230 * Math.min(1, S.gate)} r={8} color={C.bone} depth={6} id="gR" />
              <Slab x={GATE_X - 80} y={RUN_Y - 240 * Math.min(1, S.gate)} w={160} h={24} r={10} color={C.blue} depth={6} id="gT" />
            </>
          )}
          {S.sci > 0.01 && <Person1 x={380} y={RUN_Y - 110 - 40 * (1 - Math.min(1, S.sci)) + id(5).y} w={440} op={Math.min(1, S.sci * 1.5)} />}
          {PL.map((n, i) => {
            const a = S[`p${i}`];
            if (a <= 0.01) return null;
            const x = plugX(i), pb = passed(i);
            const hop = Math.abs(Math.sin((x - RUN_X0) / 40)) * 10 * (S.walk > 0 && S.walk < 1 ? 1 : 0);
            return (
              <React.Fragment key={i}>
                <Sprite name={`plug/${n}_34`} x={x} y={RUN_Y - 52 - 30 * (1 - Math.min(1, a)) - hop + id(10 + i).y} w={PW} op={Math.min(1, a * 1.5)} sx={-1}
                        rim={i === BEST ? S.tick : 0} />
                {pb > 0.01 && <Slab x={x - 20} y={RUN_Y - 120 - 170 * SCORE[i] * pb} w={40} h={170 * SCORE[i] * pb} r={9} color={i === BEST ? C.blue : C.blueHi} depth={5} id={`sc${i}`} />}
              </React.Fragment>
            );
          })}
          <Tick x={SLOT_X(BEST) + 46} y={RUN_Y - 300} s={70} p={S.tick} sw={12} />
        </Layer>

        <Layer id="txt" exempt>
          <Label text="Aim 1 · identify the methods" size={52} x={250} y={168} at={E.aim1.l + 6} />
          <Label text="Aim 2 · evaluate how they help" size={52} x={250} y={558} at={E.aim2.l + 6} />
          <Source>Illustration · our two aims for this review</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B205" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
