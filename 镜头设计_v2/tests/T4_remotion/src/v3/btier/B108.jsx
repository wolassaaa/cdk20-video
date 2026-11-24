// HKBU SCIE1007 课程作业的科普视频：B 档 1-08（C 画外音）"Start the search the year we were born, and it might only be ready now…"
// Start the search：一条带刻度的长路铺开，胶囊在起点；the year：起点立日历；we were born：小人站在起点，标 born；might only be ready：胶囊沿路慢慢走；now：走到头，标 now；
// It can cost：清场，钞票一张张落成一摞；2.8：数字轮；billion US dollars：标签；
// of drugs：十粒胶囊排上路；tested in people：路边小人；one：其中一粒亮；in ten：另外九粒掉下去；reaches the market：那一粒走到奖章。
// 接点：开头、结尾都是 T5 料杆擦除（1-07 出镜段、1-09 C 档大板）。L0 第 1 区大板。数字照旁白：2.8 billion、one in ten。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_1-08.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Plate, Calendar1, camBreath, Stage, Sprite, Slab, Runner, Label, Pen, Source, Counter, Engrave, Capsule1, Person1, evMapB, T5In, T5Out} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 1;

const ROAD_Y = 690, X0 = 180, X1 = 1740;
const CAP_W = 445;
const BILLS = [...Array(8)].map((_, i) => ({x: 700 + ((i * 37) % 60) - 30, y: 650 - i * 15, r: ((i * 53) % 14) - 7}));   // 钞票一直落到句尾（Gemini 初审：一摞钞票落完就不动）
const CAPS = [...Array(10)].map((_, i) => ({x: 260 + i * 132, y: ROAD_Y - 52}));
const WIN = 6;
const MEDAL = {x: 1690, y: 470, w: 260};
// 路下面四块阶段牌（Gemini 初审：只有图标，没画出研发的真实阶段）：胶囊走过时依次亮起
const STAGES = [["find a target", 480], ["lab tests", 800], ["trials in people", 1120], ["approval", 1440]];

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.tw("road", 0, 1, E.born.s, E.born.l, "power2.out");
    X.land("cap0", 0, 1, E.road.s + 30, {antic: false});
    X.land("cal", 0, 1, E.year.l, {antic: false});
    X.land("born", 0, 1, E.born.l, {antic: false});
    X.tw("walk", 0, 1, E.walk.s, E.now.l, "sine.inOut");
    X.tw("clear1", 0, 1, E.cost.s - 8, E.cost.l + 20, "power3.in");
    X.group(BILLS.map((_, i) => `b${i}`), 0, 1, E.n28.l, {step: 6, antic: false});
    X.tw("billsettle",0,1,E.n28.l+42,E.bil.e,"sine.out");
    X.count("n28", 0, 2.8, E.n28.l, 36);
    X.tw("clear2", 0, 1, E.drugs.s - 8, E.drugs.l + 16, "power3.in");
    X.group(CAPS.map((_, i) => `c${i}`), 0, 1, E.people.l, {step: 3, antic: false});
    X.land("ppl", 0, 1, E.people.l, {antic: false});
    X.tw("one", 0, 1, E.one.s, E.one.l + 8, "power2.out");
    CAPS.forEach((_, i) => i !== WIN && X.tw(`d${i}`, 0, 1, E.drop.s - 6 + (i % 5) * 4, E.drop.s + (i % 5) * 4 + 30, "power2.in"));
    X.land("medal", 0, 1, E.market.s + 6, {antic: false});
    X.tw("go", 0, 1, E.market.s, E.market.e, "power2.inOut");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const c1 = -2000 * S.clear1, c2 = -2000 * S.clear2;
  const hop = (t, n) => Math.abs(Math.sin(Math.PI * n * t));
  const walkX = mix(X0 + 330, X1 - 110, S.walk);

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s2"])} over={<><T5In name="runner" f={f} /><T5Out name="runner" f={f} len={LEN} /></>}>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${c1}px)`}}>
          <Layer id="road">
            {S.road > 0.001 && <Runner d={`M${X0},${ROAD_Y} L${X1},${ROAD_Y}`} draw={S.road} width={20} />}
            {S.road > 0.3 && [...Array(21)].map((_, i) => {
              const x = X0 + 20 + i * 76, a = Math.max(0, Math.min(1, (S.road * 1.2 - i / 21) * 3));
              return a > 0 && <Slab key={i} x={x - 3} y={ROAD_Y + 16} w={6} h={i % 5 === 0 ? 34 : 20} r={3} color={C.bone} depth={3} shadow={false} op={a} id={`yt${i}`} />;
            })}
            {S.cap0 > 0.01 && <Capsule1 x={walkX} y={ROAD_Y - 96 - 30 * hop(S.walk, 9)} w={CAP_W} op={Math.min(1, S.cap0 * 1.5)} lift={10} rot={-6 * Math.sin(Math.PI * 9 * S.walk)} />}
          </Layer>
          <Layer id="stages">
            {STAGES.map(([t, x], i) => {
              const a = Math.max(0, Math.min(1, (S.walk - i * 0.22) * 6));
              return a > 0.01 && <Plate key={i} x={x - 140} y={ROAD_Y + 62 - 20 * (1 - a)} w={280} h={58} text={t} size={38} op={a} id={`stg${i}`} sheen={a < 1 ? a : -1} />;
            })}
          </Layer>
          <Layer id="roadtxt" exempt>
            {S.born > 0.01 && <Plate x={X0} y={ROAD_Y+55} w={118} h={62} text="born" size={36} op={Math.min(1,S.born)}/>}
            <Label text="now" size={52} x={X1 - 110} y={ROAD_Y + 52} at={E.now.l} align="center" />
          </Layer>
        </div>

        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${c2}px)`}}>
          <Layer id="bills">
            {BILLS.map((b, i) => {
              const a = S[`b${i}`];
              if (a <= 0.01) return null;
              return <Sprite key={i} name="bill/34" x={b.x} y={b.y - 120 * (1 - Math.min(1, a)) + 26*S.billsettle} w={452} rot={b.r * (1.6 - 0.6 * Math.min(1, a))} op={Math.min(1, a * 2)} lift={i ? 0 : 0} shadow={i === 0} />;
            })}
          </Layer>
          <Layer id="money" exempt>
            {S.n28 > 0.05 && (
              <div style={{position: "absolute", left: 1080, top: 300}}>
                <Counter value={S.n28} digits={1} decimals={1} size={150} x={0} y={0} />
              </div>
            )}
            <Label text="billion US dollars" size={60} x={1080} y={490} at={E.bil.l} />
          </Layer>
        </div>

        <Layer id="caps">
          {S.c0 > 0.001 && <Runner d={`M${X0},${ROAD_Y} L${X1},${ROAD_Y}`} draw={Math.min(1, S.c0 * 1.5)} width={20} />}
          {CAPS.map((c, i) => {
            const a = S[`c${i}`];
            if (a <= 0.01) return null;
            const d = S[`d${i}`] || 0;
            const win = i === WIN;
            const x = win ? mix(c.x, MEDAL.x - 105, S.go) : mix(c.x, 960 + (i-5)*15,d);
            const y = c.y - 40 * (1 - Math.min(1, a)) + 182 * d - (win ? 30 * S.one + 20 * Math.sin(Math.PI * S.go) : 0) + id(20 + i).y;
            return <Capsule1 key={i} x={x} y={y} w={win?160:123} rot={-90+60*d+id(20+i).r} op={Math.min(1, a * 1.5) * (1 - d)} lift={win ? 20 * S.one : 4}
                             style={{filter: win && S.one > 0.01 ? `brightness(${1 + 0.15 * S.one}) drop-shadow(0 0 ${10 * S.one}px rgba(255,250,235,0.9))` : undefined}} />;
          })}
          {S.medal > .01 && <Plate x={1540} y={464} w={240} h={115} text="market" size={52} sheen={S.go} op={Math.min(1,S.medal)}/>}
        </Layer>

        <Layer id="txt" exempt>
          <Label text="did not reach the market" size={44} x={1020} y={712} at={E.drop.l} align="center" />
          <Label text="tested in people" size={48} x={160} y={ROAD_Y - 400} at={E.people.l} out={E.market.s} align="left" />
          {S.one > 0.05 && (
            <div style={{position: "absolute", left: 820, top: 250, opacity: Math.min(1, S.one * 1.5), display: "flex", alignItems: "baseline", gap: 20}}>
              <Engrave size={120}>1</Engrave><Engrave size={64}>in 10</Engrave>
            </div>
          )}
          <Source>Illustration · data: Wang et al., Pharmaceuticals 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B108" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
