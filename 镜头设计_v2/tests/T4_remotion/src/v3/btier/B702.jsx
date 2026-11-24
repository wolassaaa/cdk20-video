// HKBU SCIE1007 课程作业的科普视频：B 档 7-02 "One: walk 048 further. It's public now, so anyone could try. Test it in more liver cancer cells
// and normal liver cells, then animals, and check how the body handles it and what else it hits. The authors had already listed these steps."
// 规则 v2：第 7 区台面上一条骨白长路，镜头沿路往右走（同一个世界，不切），最后拉远看全路。
// p1：左上角 1 号步骤牌落下；walk：048 分子（金色球棍 + 048 吊牌）沿路一步一步往前走；048：走到第一站停住，路边插一面小旗；
// public：挂在 048 吊牌旁的蓝色挂锁弹开；anyone：后面升起一个地球，上面一个个亮起蓝点（各地的实验室都能拿去试）；
// test：镜头沿路右移到培养皿站；cancer：肝癌细胞培养皿一变二、二变四；normal：下面一排正常肝细胞培养皿展开；cells：两排各挂名牌；
// animals：镜头再右移，小鼠走上路；check：两块检查牌立起；handles：第一块翻出 ADME（身体怎么吸收、分布、代谢、排出它），牌上一个玻璃肝；
// what else：第二块翻出 selectivity，牌上一排灰插座，只有 CDK20 那个是蓝的；hits：两块一起轻抖。
// authors：镜头拉远看全路，论文书落在上方，名牌 Ren et al. 2023；listed：培养皿站、小鼠、检查牌三处同时打绿勾；steps：手写 next steps。
// 不用人（规则 v2 黑名单：anyone 用地球上的点表示）。开头 T5 runner 接 7-01 出镜，结尾 T2 往左甩。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_7-02.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Stage, Sprite, Slab, Plate, Runner, Tag, Pen, Tick, Engrave, Label, Source, evMapB, whipX, impact, T5In, camBreath} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 7;
const mix = (a, b, t) => a + (b - a) * t;
const cl = (t) => Math.max(0, Math.min(1, t));
const ROAD_Y = 780;
const ROADD = `M -300 ${ROAD_Y} C 900 ${ROAD_Y - 30}, 1900 ${ROAD_Y + 30}, 2800 ${ROAD_Y} S 3900 ${ROAD_Y - 20}, 4500 ${ROAD_Y}`;
const MOL = {x0: 120, x1: 560, y: ROAD_Y - 110, w: 300};
const LOCK = {x: 780, y: 560, w: 120};
const GLOBE = {x: 1120, y: 500, w: 300};
const GDOTS = [[-60, -40], [40, -70], [70, 10], [-20, 30], [-80, 50], [20, 80], [90, -30]];
const DC = (k) => ({x: 1880 + k * 230, y: 520});            // 肝癌细胞皿（4 个）
const DN = (k) => ({x: 2110 + k * 230, y: 700});            // 正常肝细胞皿（2 个）
const MOUSE = {x: 3150, y: 640, w: 330};
const CARD = (k) => ({x: 3460 + k * 320, y: 450, w: 260, h: 260});
const CAM = {A: 760, B: 2230, C: 3560, all: 2910};
// 世界放大：路在屏幕 y 720，平时 1.6 倍（初版 1 倍件太小、上半屏空），authors 时拉远到 0.75 倍看全路
const ZN = 1.6, ZA = 0.76, ROAD_SY = 720;

const WB = K.words.find((w) => w.key === "body#1").f0, WW = K.words.find((w) => w.key === "what#1").f0;
const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    S.cx = CAM.A - 200;
    tl.fromTo(S, {cx: CAM.A - 200}, {cx: CAM.A, duration: E.tag48.l / 60, ease: "power1.inOut", immediateRender: false}, 0);
    tl.fromTo(S, {cx: CAM.A}, {cx: CAM.B, duration: (E.dishes.s - E.clear.s) / 60, ease: "power2.inOut", immediateRender: false}, E.clear.s / 60);
    tl.fromTo(S, {cx: CAM.B}, {cx: CAM.C, duration: (E.mouse.l - E.mouse.s + 14) / 60, ease: "power2.inOut", immediateRender: false}, (E.mouse.s - 14) / 60);
    tl.fromTo(S, {cx: CAM.C}, {cx: CAM.all, duration: (E.src.l + 16 - E.src.s + 10) / 60, ease: "power2.inOut", immediateRender: false}, (E.src.s - 10) / 60);
    X.tw("zoom", 0, 1, E.src.s - 10, E.src.l + 16, "power2.inOut");
    X.tw("plate", 0, 1, E.p1.s, E.p1.l + 8, "power3.out");
    X.tw("walk", 0, 1, E.walk.s, E.tag48.l, "none");
    X.tw("flag", 0, 1, E.tag48.l - 4, E.tag48.l + 10, "back.out(2)");
    X.tw("lockIn", 0, 1, E.tag48.l + 10, E.tag48.l + 40, "power2.out");
    X.jiggle("lj0", E.unlock.s, 5, 0);
    X.jiggle("lj", E.unlock.l, 6, 0);
    X.tw("globe", 0, 1, E.anyone.s - 10, E.anyone.l, "power2.out");
    X.tw("dots", 0, 1, E.anyone.l, E.anyone.l + 50, "none");
    X.tw("dc", 0, 1, E.dishes.s, E.dishes.l + 18, "none");
    X.tw("dn", 0, 1, E.norm.s, E.norm.l + 10, "power2.out");
    X.tw("mouse", 0, 1, E.mouse.s, E.mouse.l, "power2.out");
    // R2-12：两张卡各自带着内容一起落下，落下前不显示（ADME 在 "body" 732，selectivity 在 "what" 817）
    X.tw("cardA", 0, 1, WB, WB + 13, "power3.out");
    X.tw("cardB", 0, 1, WW, WW + 13, "power3.out");
    X.tw("c1", 0, 1, E.adme.s, E.adme.l, "power2.inOut");
    X.tw("c2", 0, 1, E.sel.s, E.sel.l, "power2.inOut");
    X.jiggle("cj", E.hits.l, 6, 0);
    X.jiggle("cs0", E.adme.s, 8, 0);
    X.jiggle("cs1", E.sel.s, 8, 0);
    X.tw("book", 0, 1, E.src.s, E.src.l, "power2.out");
    X.tw("tk", 0, 1, E.ticks.s, E.ticks.l + 8, "power2.out");
  });
  const z = mix(ZN, ZA, S.zoom);            // 拉远到 0.75：牌上刻字 44 × 0.75 ≈ 33 px（R04 下限 26）
  const world = `translate(960px, ${mix(ROAD_SY, 780, S.zoom).toFixed(1)}px) scale(${z.toFixed(4)}) translate(${(-S.cx).toFixed(1)}px, ${-ROAD_Y}px)`;
  const whip = f > LEN - 8 ? whipX(f, LEN - 7, "out", -1) : 0;
  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const tagOp = 1 - cl(S.zoom * 2.5);
  // 048 一步一步走：每步 1/4，步间抬一下
  const st = S.walk * 4, step = Math.floor(st), ph = st - step;
  const mx = mix(MOL.x0, MOL.x1, (step + (1 - Math.cos(Math.PI * Math.min(1, ph * 1.3))) / 2) / 4);
  const my = MOL.y - 26 * Math.sin(Math.PI * Math.min(1, ph * 1.3)) * (S.walk < 1 ? 1 : 0);
  const publicAt = K.words.find(w=>w.key==="public#1")?.f0??E.unlock.l;
  const opened = f >= publicAt;
  const dishC = [0, 1, 2, 3].map((k) => {
    const at = [0, 0.33, 0.66, 0.66][k];
    const u = cl((S.dc - at) / 0.3);
    if (u <= 0) return null;
    const from = DC(k < 2 ? 0 : k - 2);
    const x = mix(from.x, DC(k).x, u), y = DC(k).y;
    return (
      <React.Fragment key={k}>
        <Sprite name="dish/34" x={x} y={y + id(k + 10).y} w={200} op={k === 0 ? 1 : cl(u * 3)} />
        <Sprite name="cells/34" x={x} y={y - 6 + id(k + 10).y} w={120} op={(k === 0 ? 1 : cl(u * 3)) * 0.9} shadow={false} style={{filter: "hue-rotate(-20deg) saturate(1.3)"}} />
      </React.Fragment>
    );
  });
  const dishN = [0, 1].map((k) => (S.dn > 0.01 &&
    <React.Fragment key={k}>
      <Sprite name="dish/34" x={DN(k).x} y={DN(k).y + 40 * (1 - S.dn) + id(k + 20).y} w={200} op={cl(S.dn * 2)} />
      <Sprite name="cell/34" x={DN(k).x} y={DN(k).y - 6 + 40 * (1 - S.dn) + id(k + 20).y} w={90} op={cl(S.dn * 2) * 0.9} shadow={false} />
    </React.Fragment>
  ));
  const card = (k, p, body, title) => {
    const c = CARD(k);
    const rise = k === 0 ? S.cardA : S.cardB;
    if (rise < 0.01) return null;
    const flip = Math.abs(Math.cos(Math.PI * p));        // 翻牌：宽度 1 → 0 → 1，过半换成正面
    const front = p >= 0.5;
    return (
      <div key={k} style={{position: "absolute", left: c.x, top: c.y + 80 * (1 - rise) - (S.cj || 0) - (S[`cs${k}`] || 0), width: c.w, height: c.h, opacity: cl(rise * 2),
                           transform: `scaleX(${Math.max(0.03, flip).toFixed(3)})`, transformOrigin: "50% 50%"}}>
        <Slab x={0} y={0} w={c.w} h={c.h} r={18} color={front ? C.bone : C.inkLight} depth={12} id={`card${k}`}>
          {front && <div style={{position: "absolute", left: 0, top: 24, width: c.w, textAlign: "center"}}><Engrave size={44}>{title}</Engrave></div>}
          {front && body}
        </Slab>
      </div>
    );
  };
  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s2", "s3"], 36)} whip={whip} shakeX={impact(f, E.unlock.l) + impact(f, E.hits.l)} over={<T5In name="runner" f={f} />}>
        <Layer id={["road", "tag48", "dishes", "mouse", "cards"]}>
          <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: "0 0", transform: world}}>
            <Runner d={ROADD} width={64} />
            {/* 站 1：048 往前走，小旗，挂锁，地球 */}
            <Sprite name="mol048/34" x={mx+cl((f-E.clear.s)/65)*1280} y={my + (S.walk >= 1 ? id(1).y : 0)} w={MOL.w} rot={S.walk < 1 ? 4 * Math.sin(Math.PI * 2 * st) : 0} />
            {S.lockIn > 0.01 && <Sprite name={opened ? "lock/open" : "lock/closed"} x={LOCK.x} y={LOCK.y - 40 * (1 - S.lockIn) - (S.lj || 0) - (S.lj0 || 0)} w={LOCK.w} op={cl(S.lockIn * 2)} rot={opened ? 6 : 0} />}
            {opened && <Tag x={LOCK.x} y={LOCK.y + 100} op={tagOp} on="lock">public</Tag>}
            {/* 站 2：培养皿 */}
            {dishC}
            {dishN}
            <Tag x={DC(1).x + 115} y={DC(0).y - 120} op={cl((f - E.dish_l.l) / 10) * tagOp}>liver cancer cells</Tag>
            <Tag x={(DN(0).x + DN(1).x) / 2} y={ROAD_Y + 34} op={cl((f - E.dish_l.l) / 10) * tagOp}>normal liver cells</Tag>
            {/* 站 3：小鼠 + 两块检查牌 */}
            {S.mouse > 0.01 && <Sprite name="mouse/34" x={mix(MOUSE.x - 300, MOUSE.x, S.mouse)} y={MOUSE.y + id(6).y - 10 * Math.abs(Math.sin(S.mouse * Math.PI * 4))} w={MOUSE.w} op={cl(S.mouse * 3)} />}
            {card(0,1,<>
              <Sprite name="liver/34" x={CARD(0).w/2} y={174} w={174}/>
              <svg width={260} height={260} style={{position:"absolute",inset:0}}><path d="M92 185 Q101 138 136 148 T154 194 Q115 218 92 185" fill="none" stroke={C.red} strokeWidth={4} pathLength={1} strokeDasharray="1" strokeDashoffset={1-cl((f-(K.words.find(w=>w.key==="handles#1")?.f0??E.adme.l))/26)} /></svg>
            </>,"ADME")}
            {card(1, 1, [0, 1, 2].map((k) => (
              <Sprite key={k} name="socket/hero_34" x={50 + k * 54} y={190+(k%2)*22-(k===1?10*Math.max(0,1-Math.abs(f-E.hits.l)/13):0)} rim={k===2&&f>=E.hits.l?.85:0} w={66} shadow={false} style={k === 2 ? undefined : {filter: "grayscale(1) brightness(1.1)"}} />
            )), "selectivity")}
            {S.mouse > 0.01 && <Tag x={MOUSE.x} y={MOUSE.y + 79} op={cl(S.mouse * 3) * tagOp}>animals</Tag>}
            {/* 三处打勾 */}
            <Tick x={DC(3).x + 60} y={DC(0).y - 140} s={150} p={S.tk} sw={22} />
            <Tick x={MOUSE.x + 40} y={MOUSE.y - 200} s={150} p={cl(S.tk * 1.2 - 0.1)} sw={22} />
            <Tick x={CARD(1).x + CARD(1).w - 10} y={CARD(0).y - 90} s={150} p={cl(S.tk * 1.2 - 0.2)} sw={22} />
          </div>
        </Layer>
        <Layer id="txt" exempt>
          <div style={{position: "absolute", left: 0, top: 0, opacity: cl(S.plate * 2), transform: `translateY(${(-80 * (1 - S.plate)).toFixed(1)}px)`}}>
            <Plate x={70} y={60} w={110} h={110} text="1" size={80} color={C.bone} id="step1" />
          </div>
          {S.book > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, opacity: cl(S.book * 2), transform: `translateY(${(-60 * (1 - S.book)).toFixed(1)}px)`}}>
              <Sprite name="book/34" x={880} y={230} w={300} rot={-4} />
              <Label text="Ren et al., Chem. Sci. 2023" size={40} x={1060} y={210} at={E.src.l} on="book" />
            </div>
          )}
          <Pen text="next steps" x={1080} y={300} at={E.steps.l} rot={-3} />
          <Source>Illustration · next steps as listed in Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B702" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
