// HKBU SCIE1007 课程作业的科普视频：B 档 1-04（D 画外音）"The standard first treatment for advanced liver cancer has already changed once…"
// standard first treatment：骨白药座升起，一粒胶囊落座（右边玻璃肝 = advanced liver cancer）；changed once：手写；Nexavar：胶囊标名；
// a combo：胶囊被顶出画面，两袋输液落座，标 atezolizumab + bevacizumab；
// But here：药座一组缩到左上；three in ten：一张生存曲线图立起来（横轴 0–5 年，纵轴存活比例），数字轮 3 in 10；ten：曲线从 100% 往下画；
// alive：曲线下面填绿（还活着的那部分）；five years on：曲线画到 5 年刻度，停在 30%，刻度亮、标 5 years；
// The study we follow：图往中间收一点，角上落下论文名牌 Ren et al. 2023；huge unmet need：曲线上面那 70% 的空缺填成淡红，手写 huge unmet need。
// 11-21 规则 v2 返修（Gemini 初审）：两袋输液上各浮一个不同颜色的抗体（Y 形），标 anti-PD-L1 / anti-VEGF；玻璃肝上长出肿瘤病灶；
// 小人、日历、书本换成生存曲线（规则 v2 黑名单）。
// 接点：开头 T5 胶囊擦除（1-03 出镜段），结尾 T5 料杆擦除（1-05 出镜段）。L0 第 1 区大板。数字照旁白：three in ten、five years。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_1-04.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, camBreath, Stage, Sprite, Slab, Label, Pen, Tag, Source, Counter, Engrave, Capsule1, evMapB, T5In, T5Out, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 1;

const POD = {x: 600, y: 640, w: 720, h: 64};            // 药座
const CAP = {x: 960, y: 560, w: 560};
const BAG = [{x: 790, y: 500}, {x: 1130, y: 500}], BAG_W = 320;
const LIVER = {x: 1580, y: 430, w: 420};
// 生存曲线图（示意形状，只有 5 年 ≈ 30% 这一个点是数据：香港癌症登记 5 年相对存活约三成）
const CH = {x: 520, y: 250, w: 900, h: 540};
const surv = (t) => 0.3 + 0.7 * (Math.exp(-0.8 * t) - (t / 5) * Math.exp(-4)) / (1 - 0 * t);   // t 年 → 存活比例：t=0 为 1，t=5 约 0.3
const cx = (t) => CH.x + 90 + (t / 5) * (CH.w - 150);
const cy = (v) => CH.y + 40 + (1 - v) * (CH.h - 120);
const LESION = [[-60, -30, 34], [40, 10, 26], [-10, 60, 22], [90, -50, 18]];
// 抗体（Y 形）：两条重链 + 两条轻链，color 区分两种药
const Antibody = ({x, y, s = 1, color, op = 1, rot = 0}) => (
  <svg width={140} height={150} style={{position: "absolute", left: x - 70, top: y - 75, opacity: op, transform: `scale(${s}) rotate(${rot}deg)`, transformOrigin: "70px 75px", overflow: "visible"}}>
    <g strokeLinecap="round" fill="none">
      <path d="M70 140 L70 78 L30 30 M70 78 L110 30" stroke={color} strokeWidth={16} />
      <path d="M48 70 L18 34 M92 70 L122 34" stroke={C.bone} strokeWidth={10} opacity={0.9} />
    </g>
  </svg>
);

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("pod", 0, 1, E.stand.l);
    X.land("cap", 0, 1, E.stand.l + 8, {antic: false});
    X.land("liver", 0, 1, E.liver.l, {antic: false});
    X.tw("eject", 0, 1, E.combo.s - 6, E.combo.l + 14, "power3.in");
    X.group(["b0", "b1"], 0, 1, E.combo.l + 4, {step: 8, antic: false});
    X.jiggle("podJ", E.combo.l + 6, 4, 0);
    X.tw("away", 0, 1, E.clear.s - 4, E.clear.l + 30, "power2.inOut");
    X.count("n3", 0, 3, E.three.l, 30);
    X.tw("chart", 0, 1, E.clear.l, E.three.s + 6, "power3.out");
    X.tw("curve", 0, 1, E.ten.s, E.years.l, "power1.inOut");
    X.tw("alive", 0, 1, E.alive.s, E.alive.l + 14, "power2.out");
    X.tw("tick5", 0, 1, E.years.s, E.years.l, "back.out(2)");
    X.tw("study", 0, 1, E.study.s, E.study.l + 10, "power2.out");
    X.jiggle("srcJ", E.calls.l, 6, 0);
    X.tw("gap", 0, 1, E.huge.s, E.huge.l + 30, "power2.out");
    X.tw("ab0", 0, 1, E.atezo.s, E.atezo.l, "back.out(1.6)");
    X.tw("ab1", 0, 1, E.beva.s, E.beva.l, "back.out(1.6)");
    X.tw("les", 0, 1, E.liver.s + 8, E.liver.l + 30, "none");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  // s1 那一组退到左上角缩小（不是推镜头：是那组件自己挪开让位）
  const g1 = {s: mix(1, 0.42, S.away), x: mix(0, -520, S.away), y: mix(0, -330, S.away)};
  const out2 = -2000 * S.away2;
  // the study we follow：十个人不走，缩到下面一排（Gemini 初审：上一段的人直接消失，和 unmet need 接不上）；huge unmet need 时七个灰的轻轻起伏
  const ej = S.eject;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s2"])} shakeX={impact(f, E.combo.l)} over={<><T5In name="capsule" f={f} /><T5Out name="runner" f={f} len={LEN} /></>}>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translate(${g1.x + out2}px, ${g1.y}px) scale(${g1.s})`, transformOrigin: "960px 540px"}}>
          <Layer id="stand">
            {S.pod > 0.01 && <Slab x={POD.x} y={POD.y + 40 * (1 - Math.min(1, S.pod)) + (S.podJ || 0)} w={POD.w} h={POD.h} r={20} color={C.bone} depth={14} op={Math.min(1, S.pod * 1.5)} id="pod" />}
            {S.cap > 0.01 && ej < 1 && (
              <Capsule1 x={CAP.x + mix(0, -1500, ej) + id(1).y} y={CAP.y - 50 * (1 - Math.min(1, S.cap)) - 180 * Math.sin(Math.PI * Math.min(1, ej))} w={CAP.w}
                        rot={-40 * ej + id(1).r} op={Math.min(1, S.cap * 1.5)} lift={8 + 80 * ej} />
            )}
            {BAG.map((b, i) => S[`b${i}`] > 0.01 && (
              <Sprite key={i} name="ivbag/34" x={b.x} y={b.y - 60 * (1 - Math.min(1, S[`b${i}`])) + id(2 + i).y} w={BAG_W} op={Math.min(1, S[`b${i}`] * 1.5)} rot={id(2 + i).r} />
            ))}
            {[0, 1].map((i) => (S[`ab${i}`] || 0) > 0.01 && (
              <Antibody key={`ab${i}`} x={BAG[i].x} y={BAG[i].y - 230 + id(7 + i).y} s={Math.min(1.1, S[`ab${i}`])} color={i ? C.gold : C.blueHi} op={Math.min(1, S[`ab${i}`] * 2)} rot={i ? 8 : -8} />
            ))}
            {S.b1 > 0.3 && <div style={{position: "absolute", left: 960, top: 470, transform: "translateX(-50%)", opacity: Math.min(1, (S.b1 - 0.3) * 2)}}><Engrave size={72}>+</Engrave></div>}
          </Layer>
          <Layer id="liver">
            {S.liver > 0.01 && <Sprite name="liver/34" x={LIVER.x} y={LIVER.y + id(4).y} w={LIVER.w} op={Math.min(1, S.liver * 1.5) * (1 - S.away)} rot={id(4).r} />}
            {S.les > 0.01 && LESION.map(([dx, dy, r], k) => {
              const v = Math.max(0, Math.min(1, S.les * 4 - k));
              return v > 0 && <div key={k} style={{position: "absolute", left: LIVER.x + dx - r * v, top: LIVER.y + dy - r * v + id(4).y, width: 2 * r * v, height: 2 * r * v, borderRadius: r,
                                                   background: `radial-gradient(circle, ${C.red} 0%, rgba(200,16,46,0.55) 60%, rgba(200,16,46,0) 100%)`, opacity: 0.9 * (1 - S.away)}} />;
            })}
          </Layer>
          <Layer id="names" exempt>
            <Label text="Nexavar" size={52} x={CAP.x} y={POD.y + 90} at={E.nex.l} out={E.combo.s} align="center" />
            <Label text="atezolizumab" size={48} x={BAG[0].x - 30} y={POD.y + 90} at={E.atezo.l} out={E.clear.s} align="center" />
            <Label text="bevacizumab" size={48} x={BAG[1].x + 30} y={POD.y + 90} at={E.beva.l} out={E.clear.s} align="center" />
            <Pen text="changed once" x={150} y={190} at={E.changed.s} out={E.clear.s} size={44} />
            <Tag x={BAG[0].x - 30} y={POD.y + 160} op={Math.max(0, Math.min(1, (f - E.atezo.l) / 10)) * (1 - S.away)} on="ivbag">anti-PD-L1 antibody</Tag>
            <Tag x={BAG[1].x + 30} y={POD.y + 160} op={Math.max(0, Math.min(1, (f - E.beva.l) / 10)) * (1 - S.away)} on="ivbag">anti-VEGF antibody</Tag>
            <Tag x={LIVER.x} y={LIVER.y + 230} op={Math.max(0, Math.min(1, (f - E.liver.l) / 10)) * (1 - S.away)} on="liver">advanced liver cancer</Tag>
          </Layer>
        </div>

        <Layer id={["people", "book", "chart"]}>
          {S.chart > 0.01 && (() => {
            const N = 60, tEnd = 5 * S.curve;
            const pts = [...Array(N + 1)].map((_, k) => [cx((k / N) * tEnd), cy(surv((k / N) * tEnd))]);
            const line = "M" + pts.map((p) => p.map((v) => v.toFixed(1)).join(",")).join(" L");
            const under = `${line} L${cx(tEnd).toFixed(1)},${cy(0).toFixed(1)} L${cx(0).toFixed(1)},${cy(0).toFixed(1)} Z`;
            const full = [...Array(N + 1)].map((_, k) => [cx((k / N) * 5), cy(surv((k / N) * 5))]);
            const gapPath = `M${cx(0)},${cy(1)} L${cx(5)},${cy(1)} ` + full.slice().reverse().map((p) => `L${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" ") + " Z";
            const sc = 1 - 0.06 * S.study;
            return (
              <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: Math.min(1, S.chart * 1.5), transform: `translateY(${(40 * (1 - S.chart)).toFixed(1)}px) scale(${sc.toFixed(3)})`, transformOrigin: "960px 520px"}}>
                <Slab x={CH.x} y={CH.y} w={CH.w} h={CH.h} r={22} color={C.bone} depth={14} id="chart">
                  <svg width={CH.w} height={CH.h} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
                    <g transform={`translate(${-CH.x},${-CH.y})`}>
                      {S.gap > 0.01 && <path d={gapPath} fill={C.red} opacity={0.32 * S.gap} />}
                      {S.alive > 0.01 && <path d={under} fill={C.green} opacity={0.35 * S.alive} />}
                      <line x1={cx(0)} y1={cy(0)} x2={cx(5) + 20} y2={cy(0)} stroke={C.ink} strokeWidth={4} />
                      <line x1={cx(0)} y1={cy(0)} x2={cx(0)} y2={cy(1) - 14} stroke={C.ink} strokeWidth={4} />
                      <line x1={cx(0)} y1={cy(0.3)} x2={cx(5)} y2={cy(0.3)} stroke={C.ink} strokeWidth={2} strokeDasharray="10 8" opacity={0.5 * S.alive} />
                      {[0, 1, 2, 3, 4, 5].map((t) => <line key={t} x1={cx(t)} y1={cy(0)} x2={cx(t)} y2={cy(0) + (t === 5 ? 18 + 10 * S.tick5 : 14)} stroke={t === 5 && S.tick5 > 0.5 ? C.blue : C.ink} strokeWidth={t === 5 ? 6 : 3} />)}
                      {S.curve > 0.001 && <path d={line} fill="none" stroke={C.blue} strokeWidth={9} strokeLinecap="round" strokeLinejoin="round" />}
                      {S.curve > 0.999 && <circle cx={cx(5)} cy={cy(0.3)} r={11 + 4 * S.tick5} fill={C.blue} />}
                    </g>
                  </svg>
                  {[0, 1, 2, 3, 4, 5].map((t) => <div key={t} style={{position: "absolute", left: cx(t) - CH.x - 20, top: cy(0) - CH.y + 22, width: 40, textAlign: "center"}}><Engrave size={30}>{t}</Engrave></div>)}
                  <div style={{position: "absolute", left: 18, top: cy(1) - CH.y - 16}}><Engrave size={28}>100%</Engrave></div>
                  <div style={{position: "absolute", left: 18, top: cy(0.3) - CH.y - 16, opacity: S.alive}}><Engrave size={28}>30%</Engrave></div>
                </Slab>
              </div>
            );
          })()}
          {S.study > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, opacity: Math.min(1, S.study * 1.5), transform: `translateY(${(-40 * (1 - S.study) - (S.srcJ || 0)).toFixed(1)}px)`}}>
              <Slab x={1450} y={200} w={330} h={90} r={14} color={C.bone} depth={10} id="studyplate">
                <div style={{width: 330, height: 90, display: "flex", alignItems: "center", justifyContent: "center"}}><Engrave size={40}>Ren et al. 2023</Engrave></div>
              </Slab>
            </div>
          )}
        </Layer>
        <Layer id="count" exempt>
          {S.n3 > 0.05 && (
            <div style={{position: "absolute", left: 1480, top: 400, display: "flex", alignItems: "baseline", gap: 18, opacity: 1 - S.study}}>
              <Counter value={S.n3} digits={1} size={120} x={0} y={0} />
              <div style={{position: "relative", left: 70, top: 56}}><Engrave size={56}>in 10</Engrave></div>
            </div>
          )}
          <Label text="5 years" size={44} x={cx(5)} y={cy(0) + 64} at={E.years.l} out={E.study.s} align="center" />
        </Layer>

        <Layer id="txt" exempt>
          <Pen text="huge unmet need" x={1000} y={300} at={E.huge.s} size={44} rot={-4} />
          <Source>{f < E.clear.s ? "Illustration · treatments as described in Ren et al., Chem. Sci. 2023" : "Illustration · 5-year survival about 3 in 10: Hong Kong Cancer Registry 2022"}</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B104" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
