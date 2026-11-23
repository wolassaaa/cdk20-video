// HKBU SCIE1007 课程作业的科普视频：B 档 1-11（画外音）"So can AI walk the first steps faster? …"
// can AI：AI 芯片落位；walk the first steps：一粒胶囊沿四级踏步一级级跳上去；faster?：手写；
// one real case：清场，论文书落下；AI tools：三块芯片依次落位；liver cancer：玻璃肝；
// part of it starts：清场；right here：香港地图落下；in Hong Kong：九龙塘一点亮起（墨色点 + 一圈扩散环，不用红点、不用黄）。
// 接点：开头、结尾都是 T5 料杆擦除。L0 第 1 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_1-11.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Plate, Runner, Tag, camBreath, Stage, Sprite, Slab, Label, Pen, Source, Capsule1, evMapB, T5In, T5Out, pathOf} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 1;

const CHIP = {x: 470, y: 420, w: 460};
const STEPS = [0, 1].map((i) => ({x: 720 + i * 551, y: 665, w: 315}));
const CAP_W = 300;
// 胶囊沿踏步跳：起点在第一级前面，每级一跳
const HOP = pathOf([[760, 640], ...STEPS.flatMap((s, i) => [[s.x + s.w * 0.5 - 60, s.y - 150 - (i === 0 ? 30 : 0)], [s.x + s.w * 0.5, s.y - 44]])]);
const BOOK = {x: 485, y: 470, w: 520};
const CHIPS = [["chip_pandaomics/34", 1100], ["chip_alphafold/34", 1390], ["chip_chemistry42/34", 1680]];
const LIVER = {x: 1380, y: 670, w: 440};
const MAP = {x: 1040, y: 489, w: 738};
const HK = {x: MAP.x + (0.597 - 0.5) * MAP.w, y: MAP.y + (0.46 - 0.5) * (MAP.w * 586 / 924)};   // 九龙塘（浸会大学）在贴图里的位置

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("chip", 0, 1, E.ai.l, {antic: false});
    X.group(STEPS.map((_, i) => `st${i}`), 0, 1, E.ai.l + 10, {step: 6, antic: false});
    X.tw("hop", 0, 1, E.faster.s - 9, E.faster.l + 14, "none");
    X.land("cap", 0, 1, E.ai.l + 30, {antic: false});
    X.tw("clear1", 0, 1, E.case.s - 8, E.case.l + 14, "power3.in");
    X.land("book", 0, 1, E.case.l, {antic: false});
    X.group(CHIPS.map((_, i) => `c${i}`), 0, 1, E.tools.l, {step: 10, antic: false});
    X.land("liver", 0, 1, E.liver.l, {antic: false});
    X.tw("clear2", 0, 1, E.starts.s - 4, E.starts.l + 16, "power3.in");
    X.land("map", 0, 1, E.here.l, {antic: false, dur: E.here.l - E.starts.l});   // Gemini 二审：starts 后空场，地图从 starts 起就开始落
    X.tw("dot", 0, 1, E.hk.s, E.hk.l, "back.out(2)");
    X.tw("ring", 0, 1, E.hk.l, E.hk.e, "power1.out");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const c1 = -2100 * S.clear1, c2 = -384 * S.clear2;
  // 胶囊位置：hop 0–1 沿路径，跳的那一下拉长一点
  const [hx, hy] = S.hop > 0 ? HOP.at(S.hop) : [760, 640];
  // faster? 之后的停顿：胶囊在顶上原地小跳、芯片轮廓光一明一暗，等下一句（Gemini 初审：这里画面停住）
  const top = f > E.faster.e - 6 ? Math.abs(Math.sin((Math.PI * (f - E.faster.e + 6)) / 24)) : 0;
  const chipRim = f > E.faster.s ? 0.5 + 0.5 * Math.sin((2 * Math.PI * (f - E.faster.s)) / 48) : 0;
  // 香港那一点：一圈圈往外扩，到段尾不停
  const ringT = f >= E.hk.l ? ((f - E.hk.l) % 54) / 54 : S.ring;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s2", "s3"])} over={<><T5In name="runner" f={f} /><T5Out name="runner" f={f} len={LEN} /></>}>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${c1}px)`}}>
          <Layer id="chip">
            {S.chip > 0.01 && <Sprite name="chip_pandaomics/34" x={CHIP.x} y={CHIP.y - 50 * (1 - Math.min(1, S.chip)) + id(1).y} w={CHIP.w} op={Math.min(1, S.chip * 1.5)} rot={id(1).r} rim={0.8 * chipRim} />}
          </Layer>
          <Layer id="steps">
            {STEPS.map((s, i) => S[`st${i}`] > 0.01 && (
              <Plate text={i === 0 ? "Target" : "Hit"} size={56} key={i} x={s.x} y={s.y + 30 * (1 - Math.min(1, S[`st${i}`]))} w={s.w} h={74} r={12} color={C.bone} depth={14} op={Math.min(1, S[`st${i}`] * 1.5)} id={`st${i}`} />
            ))}
            {S.cap > 0.01 && <Capsule1 x={hx} y={hy - 40 * (1 - Math.min(1, S.cap)) - 26 * top} w={CAP_W} op={Math.min(1, S.cap * 1.5)} lift={6} rot={-8 + 10 * Math.sin(Math.PI * 8 * S.hop)} />}
          </Layer>
          <Layer id="txt1" exempt>
            <Pen text="faster?" x={1240} y={170} at={E.faster.s - 4} size={92} />
          </Layer>
        </div>

        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin:"500px 300px", opacity: 1 - Math.max(0, Math.min(1, (f - (E.starts.s - 4)) / 12))}}>
          <Layer id="book" exempt>
            {S.book > 0.01 && <Plate x={BOOK.x-260} y={BOOK.y-180-60*(1-S.book)} w={520} h={360} text="Ren et al., Chem. Sci. 2023" size={42} op={Math.min(1,S.book)}/>}
          </Layer>
          <Layer id="tools" exempt>
            {S.c0>.01 && <Runner d="M700 412 H1670 M1100 412 V365 M1390 412 V365 M1680 412 V365 M1390 412 V530" width={14} draw={Math.min(1,S.c0)}/>}
            {CHIPS.map(([n, x], i) => S[`c${i}`] > 0.01 && (
              <React.Fragment key={i}>
                <Sprite name={n} x={x} y={300 - 50 * (1 - Math.min(1, S[`c${i}`])) + id(3 + i).y} w={260} op={Math.min(1, S[`c${i}`] * 1.5)} rot={id(3 + i).r} />
                <Tag x={x} y={407 - 50 * (1 - Math.min(1, S[`c${i}`]))} op={Math.min(1, S[`c${i}`] * 1.5)}>{["PandaOmics", "AlphaFold", "Chemistry42"][i]}</Tag>
              </React.Fragment>
            ))}
          </Layer>
          <Layer id="liver">
            {S.liver > 0.01 && <Sprite name="liver/34" x={LIVER.x} y={LIVER.y - 50 * (1 - Math.min(1, S.liver)) + id(7).y} w={LIVER.w} op={Math.min(1, S.liver * 1.5)} rot={id(7).r} />}
          </Layer>
        </div>

        <Layer id="map">
          {S.map > 0.01 && <Sprite name="hkmap/34" x={MAP.x+420*(1-S.map)} y={MAP.y - 60 * (1 - Math.min(1, S.map)) + id(8).y} w={MAP.w} op={Math.min(1, S.map * 1.5)} rot={id(8).r} />}
        </Layer>
        <Layer id="txt3" exempt>
          {S.book > 0.8 && S.clear2 < 0.82 && <Source>Illustration · data: Ren et al., Chem. Sci. 2023</Source>}
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B111" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
