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
import {C, Plate, Person1, Runner, camBreath, Stage, Sprite, Slab, Label, Pen, Tag, Source, Counter, Engrave, Capsule1, evMapB, T5In, T5Out, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 1;

const POD = {x: 960, y: 636, w: 420, h: 160};            // 药座
const CAP = {x: 1170, y: 551, w: 362};
const BAG = [{x: 1045, y: 429}, {x: 1510, y: 429}], BAG_W = 363;
const LIVER = {x: 550, y: 473, w: 636};
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
    X.land("cap", 0, 1, E.nex.l, {antic: false});
    X.land("liver", 0, 1, E.liver.l, {antic: false});
    X.tw("eject", 0, 1, E.combo.s - 6, E.combo.l + 14, "power3.in");
    X.land("b0", 0, 1, E.atezo.l, {antic:false});
    X.land("b1", 0, 1, E.atezo.l, {antic:false});
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
  const once = K.words.find(w=>w.key === "once#1").f0;
  const cancer = K.words.find(w=>w.key === "cancer#1").f0;
  const need = K.words.find(w=>w.key === "need#1").f0;
  const u = (a,b)=>Math.max(0,Math.min(1,(f-a)/Math.max(1,b-a)));
  const flip = 0;   // P14：药囊不翻转，Nexavar 的名字一直看得到
  const out2 = 0;
  // the study we follow：十个人不走，缩到下面一排（Gemini 初审：上一段的人直接消失，和 unmet need 接不上）；huge unmet need 时七个灰的轻轻起伏
  const ej = S.eject;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s2"])} shakeX={impact(f, E.combo.l)} over={<><T5In name="capsule" f={f} /><T5Out name="runner" f={f} len={LEN} /></>}>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translate(${g1.x + out2}px, ${g1.y}px) scale(${g1.s})`, transformOrigin: "960px 540px", opacity: 1 - u(E.study.s, E.study.l + 10)}}>
          <Layer id="stand" exempt>
            {S.pod > 0.01 && <div style={{position:"absolute",left:0,top:0,width:1920,height:1080,transformOrigin:"1170px 710px",transform:`perspective(1400px) rotateY(${180*flip}deg)`}}><Plate size={44} x={POD.x} y={POD.y + 40 * (1 - Math.min(1, S.pod)) + (S.podJ || 0) + (f<cancer?6*Math.sin(f*.14):0)} w={POD.w} h={POD.h} r={20} color={C.bone} depth={14} op={Math.min(1, S.pod * 1.5)} id="pod" text={flip>.5 ? "" : "first treatment"}/></div>}
            {S.cap > 0.01 && flip < 0.52 && (
              <Capsule1 x={CAP.x + 38*Math.sin(Math.PI*flip)} y={CAP.y - 50 * (1 - Math.min(1, S.cap)) - 180 * Math.sin(Math.PI * Math.min(1, ej))} w={CAP.w}
                        rot={-40 * ej + id(1).r} op={Math.min(1, S.cap * 1.5)} lift={8 + 80 * ej} />
            )}
            {BAG.map((b, i) => S[`b${i}`] > 0.01 && (
              <Sprite key={i} name="ivbag/34" x={b.x} y={b.y - 60 * (1 - Math.min(1, S[`b${i}`])) + id(2 + i).y} w={BAG_W} op={Math.min(1, S[`b${i}`] * 1.5)} rot={id(2 + i).r} style={i?{filter:"sepia(.24) hue-rotate(285deg) saturate(1.18)"}:undefined} />
            ))}
            {[0, 1].map((i) => (S[`ab${i}`] || 0) > 0.01 && (
              <Antibody key={`ab${i}`} x={BAG[i].x} y={BAG[i].y - 230 + id(7 + i).y} s={Math.min(1.1, S[`ab${i}`])} color={i ? C.gold : C.blueHi} op={Math.min(1, S[`ab${i}`] * 2)} rot={i ? 8 : -8} />
            ))}
            {S.b1 > .01 && <Runner d="M1045 469 L1158 552 L1280 610 M1510 469 L1405 552 L1280 610" width={10} draw={Math.min(1,S.b1)} color={C.blueHi}/>}
            {S.b1 > 1.5 && <div style={{position: "absolute", left: 960, top: 470, transform: "translateX(-50%)", opacity: Math.min(1, (S.b1 - 0.3) * 2)}}><Engrave size={72}>+</Engrave></div>}
          </Layer>
          <Layer id="liver">
            {f >= cancer - 14 && <Sprite hero name="liver/34" x={LIVER.x} y={LIVER.y + id(4).y - 60*(1-u(cancer-14,cancer))} w={LIVER.w} op={u(cancer-14,cancer) * (1 - S.away)} rot={id(4).r} />}
            {S.les > 0.01 && LESION.map(([dx, dy, r], k) => {
              const v = Math.max(0, Math.min(1, u(cancer-5,cancer+22) * 4 - k));
              return v > 0 && <div key={k} style={{position: "absolute", left: LIVER.x + dx - r * v, top: LIVER.y + dy - r * v + id(4).y, width: 2 * r * v, height: 2 * r * v, borderRadius: r,
                                                   background: `radial-gradient(circle, ${C.red} 0%, rgba(200,16,46,0.55) 60%, rgba(200,16,46,0) 100%)`, opacity: 0.9 * (1 - S.away)}} />;
            })}
          </Layer>
          <Layer id="names" exempt>
            <Label text="Nexavar" size={52} x={1400} y={735} at={E.nex.l} out={E.combo.l} align="left" />
            <Label text="atezolizumab" size={48} x={780} y={735} at={E.atezo.l} out={E.clear.s} align="center" />
            <Label text="bevacizumab" size={48} x={BAG[1].x + 30} y={735} at={E.beva.l} out={E.clear.s} align="center" />
          </Layer>
        </div>

        <Layer id={["people","book","chart"]}>
          {f >= E.three.s && f < need + 20 && (() => {
            const fade = 1 - u(need-8,need+20);
            return <div style={{opacity:fade}}>
              <Runner d="M250 420 H1660" width={18} draw={u(E.three.s,E.three.l)}/>
              {Array.from({length:10}, (_,i)=>{
                const a = u(E.three.s+i*2,E.three.l+i*2);
                const grey = i >= 3 && f >= E.ten.l;
                return a>0 && <Person1 key={i} red={!grey} x={278+145*i} y={507-68*(1-a)+16*(grey?u(E.ten.s,E.ten.l):0)} w={132} op={a} style={{filter:grey ? "grayscale(1)" : undefined}}/>;
              })}
              {f>=E.years.s && <Runner d="M275 655 H1650" width={18} draw={u(E.years.s,E.years.e)} color={C.blueHi}/>}
            </div>;
          })()}
          {f>=E.study.l && <Slab x={560} y={180} w={800} h={150} r={16} depth={12} id="studyPlate" op={u(E.study.l,E.study.l+12)}>
            <div style={{width:800,height:150,display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",gap:8}}>
              <Engrave size={36}>Ren et al., Chem. Sci. 2023</Engrave>
              <Engrave size={40}>“a huge unmet medical need”</Engrave>
            </div>
          </Slab>}
        </Layer>
        <Layer id="txt" exempt>
          <Label text="5 years" x={950} y={705} at={E.years.l} out={need-12} align="center"/>
          <Label text="about 3 in 10" size={56} x={960} y={300} at={E.three.l} out={E.alive.s} align="center"/>
          <Label text="alive" size={44} x={423} y={572} at={E.alive.l} out={need-10} align="center"/>
          <Source>{f < E.clear.s ? "Illustration · treatments as described in Ren et al., Chem. Sci. 2023" : "Illustration · 5-year survival about 3 in 10: Hong Kong Cancer Registry 2022"}</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B104" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
