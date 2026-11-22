// HKBU SCIE1007 课程作业的科普视频：B 档 6-09 "...further down the road. Fewer failed molecules, lower costs, fewer animal tests, less chemical waste.
// Computing costs electricity too. And the real prize? New treatments for patients."
// 规则 v2：一条骨白长路横穿第 6 区台面，镜头沿路一直往右走（同一个世界，不切）。路边四个站，每站一件真东西，念到时"变少"：
// b1 failed molecules：废料桶里一堆灰插头（失败的分子）一个个弹走，只剩两个；b2 costs：金币堆矮下去，两枚金币飞走；
// b3 animal tests：三只小鼠两只退出路边，只剩一只；b4 chemical / waste：三排样本管两排退走，结晶皿里的废液缩成一小滩。
// 开头手写批注 possible gains（这些是可能的好处，没有实测）。
// elec：路边的服务器机架升起，电线从插座一路亮过来（电流珠沿线跑），too：一枚金币飞进机架（算力也花钱），名牌 electricity, too。
// prize：镜头推到路尽头，奖牌升起；treatments：奖牌翻转成一粒胶囊；patients：胶囊飞进玻璃肝（病人的器官），肝亮起，名牌 for patients。
// 不用人、钞票、烧瓶（规则 v2 黑名单）。开头 T2 甩进，结尾 T2 往左甩。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_6-09.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, shade, Stage, Sprite, Runner, Tag, Pen, Source, Capsule1, evMapB, whipX, impact, pathOf} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 6;
const mix = (a, b, t) => a + (b - a) * t;
const cl = (t) => Math.max(0, Math.min(1, t));
const ROAD_Y = 720;
const Z = 1.8, ROAD_SY = 690;                       // 世界放大 1.8 倍：路在屏幕 y 690，站上的件占画面中部（初版件太小、上半屏空）
// 各站在世界里的 x（屏幕 x = 世界 x − 镜头 x + 960）
const ST = {b1: 700, b2: 1450, b3: 2200, b4: 2950, el: 3750, end: 4600};
const FAIL = [...Array(7)].map((_, k) => ({dx: [-110, -30, 50, 130, -70, 10, 90][k], dy: k < 4 ? -10 : -62, r: -20 + k * 11}));     // 一堆灰插头（失败的分子），堆在路上
const ROADD = `M -400 ${ROAD_Y} C 600 ${ROAD_Y - 40}, 1400 ${ROAD_Y + 40}, 2400 ${ROAD_Y} S 4200 ${ROAD_Y - 30}, 5400 ${ROAD_Y}`;
const WIRE = pathOf([[ST.el - 330, ROAD_Y + 20], [ST.el - 220, ROAD_Y + 60], [ST.el - 90, ROAD_Y + 50], [ST.el - 40, ROAD_Y - 10]]);

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    // 镜头沿路走：每个站在念到它的时候正好到画面中间偏左
    const legs = [[0, E.b1.l, ST.b1 - 160, ST.b1 + 40], [E.b1.l + 20, E.b2.l, ST.b1 + 40, ST.b2], [E.b2.l + 16, E.b3.l, ST.b2, ST.b3],
                  [E.b3.l + 16, E.b4.l, ST.b3, ST.b4], [E.b4l.l + 10, E.elec.l, ST.b4, ST.el - 60], [E.too.l + 20, E.prize.l, ST.el - 60, ST.end + 150]];
    S.cx = ST.b1 - 160;
    legs.forEach(([a, b, x0, x1]) => tl.fromTo(S, {cx: x0}, {cx: x1, duration: (b - a) / 60, ease: "power2.inOut", immediateRender: false}, a / 60));
    X.tw("road", 0, 1, 0, E.road.l + 30, "power2.out");
    X.tw("b1", 0, 1, E.b1.s - 6, E.b1.l + 10, "none");
    X.tw("b2", 0, 1, E.b2.s, E.b2.l + 6, "power2.inOut");
    X.tw("b3", 0, 1, E.b3.s, E.b3.l + 8, "power2.in");
    X.tw("b4", 0, 1, E.b4.s, E.b4.l + 8, "power2.in");
    X.tw("b4l", 0, 1, E.b4l.s, E.b4l.l + 10, "power2.out");
    X.tw("rack", 0, 1, E.elec.s - 10, E.elec.s + 14, "power2.out");
    X.tw("wire", 0, 1, E.elec.s + 4, E.elec.l, "power1.inOut");
    X.tw("coin", 0, 1, E.too.s - 10, E.too.l, "power2.in");
    X.land("medal", 0, 1, E.prize.l, {antic: false, dur: 18});
    X.tw("flip", 0, 1, E.treat.s - 4, E.treat.l, "power2.inOut");
    X.tw("cap", 0, 1, E.pat.s - 10, E.pat.l, "power2.inOut");
    X.tw("glow", 0, 1, E.pat.l, E.pat.l + 24, "power2.out");
  });
  const whip = f < 7 ? whipX(f, 0, "in", -1) : f > LEN - 8 ? whipX(f, LEN - 7, "out", -1) : 0;
  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  // 站 1：废料桶里的灰插头一个个弹走（剩 2 个）
  const fails = FAIL.map((p, k) => {
    const u = k < 2 ? 0 : cl((S.b1 * 6 - (k - 2)) / 1.8);
    if (u >= 1) return null;
    return <Sprite key={k} name="plug/blank_34" x={ST.b1 + p.dx + 60 * u} y={ROAD_Y - 60 + p.dy - 160 * Math.sin(Math.PI * u * 0.6)} w={96} rot={p.r + 120 * u}
                   op={1 - u} shadow={false} style={{filter: "grayscale(1) brightness(0.8)"}} />;
  });
  const ccoin = (k) => {
    const u = cl(S.b2 * 2 - k * 0.6);
    if (u <= 0 || u >= 1) return null;
    const x = ST.b2 + 40 + 220 * u * (k ? 1 : -0.6), y = ROAD_Y - 230 - 160 * Math.sin(Math.PI * u);
    return <div key={k} style={{position: "absolute", left: x - 30, top: y - 30, width: 60, height: 60, borderRadius: 30, opacity: 1 - u,
                                background: `radial-gradient(circle at 35% 30%, ${C.bone}, ${C.gold} 45%, ${shade(C.gold, 0.3)})`, boxShadow: "0 4px 6px rgba(0,0,0,0.4)"}} />;
  };
  const wireDots = [...Array(8)].map((_, k) => {
    const u = ((f - E.elec.s) / 40 + k / 8) % 1;
    if (S.wire < 0.3 || u > S.wire) return null;
    const [x, y] = WIRE.at(u);
    return <div key={k} style={{position: "absolute", left: x - 8, top: y - 8, width: 16, height: 16, borderRadius: 8, background: C.yellow, boxShadow: "0 0 12px rgba(255,243,63,0.9)"}} />;
  });
  const flip = S.flip, capT = S.cap;
  const LIV = {x: ST.end + 300, y: ROAD_Y - 200, w: 300};
  const capP = {x: mix(ST.end, LIV.x - 10, capT), y: mix(ROAD_Y - 260, LIV.y + 10, capT) - 120 * Math.sin(Math.PI * capT)};
  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} shakeX={impact(f, E.prize.l) + impact(f, E.pat.l)}>
        <Layer id={["road", "b1", "b3", "b4", "elec"]}>
          <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: "0 0", transform: `translate(960px, ${ROAD_SY}px) scale(${Z}) translate(${(-S.cx).toFixed(1)}px, ${-ROAD_Y}px)`}}>
            <Runner d={ROADD} width={64} draw={S.road} />
            {/* 站 1 */}
            {fails}
            <Tag x={ST.b1} y={ROAD_Y + 36} op={cl((f - E.b1.s) / (E.b1.l - E.b1.s + 2))}>fewer failed molecules</Tag>
            {/* 站 2 */}
            <Sprite name="coins/34" x={ST.b2} y={ROAD_Y - 60} w={210} sy={1 - 0.45 * S.b2} />
            {ccoin(0)}{ccoin(1)}
            <Tag x={ST.b2} y={ROAD_Y + 36} op={cl((f - E.b2.s) / (E.b2.l - E.b2.s + 2))}>lower costs</Tag>
            {/* 站 3 */}
            {[0, 1, 2].map((k) => {
              const u = k === 1 ? 0 : S.b3;
              return <Sprite key={k} name="mouse/34" x={ST.b3 - 190 + k * 190 + (k === 0 ? -140 : 140) * u * (k === 1 ? 0 : 1)} y={ROAD_Y - 80 - k * 6 + 90 * u * (k === 1 ? 0 : 1) + id(k + 3).y}
                             w={200} op={1 - u * (k === 1 ? 0 : 1)} sx={k === 2 ? -1 : 1} />;
            })}
            <Tag x={ST.b3} y={ROAD_Y + 36} op={cl((f - E.b3.s) / (E.b3.l - E.b3.s + 2))}>fewer animal tests</Tag>
            {/* 站 4 */}
            {[0, 1, 2].map((k) => {
              const u = k === 0 ? 0 : S.b4;
              return <Sprite key={k} name="tube/34" x={ST.b4 - 170 + k * 75 + 160 * u} y={ROAD_Y - 150 - 70 * u} w={150} op={1 - u} />;
            })}
            <Sprite name="dish/34" x={ST.b4 + 120} y={ROAD_Y - 60} w={mix(220, 130, S.b4l)} />
            <Tag x={ST.b4} y={ROAD_Y + 36} op={cl((f - E.b4l.s) / (E.b4l.l - E.b4l.s + 2))}>less chemical waste</Tag>
            {/* 站 5：算力也要电 */}
            {S.rack > 0.01 && <Sprite name="dbrack/34" x={ST.el} y={ROAD_Y - 120 + 60 * (1 - S.rack)} w={330} op={cl(S.rack * 2)} />}
            {S.wire > 0.01 && <svg width={5600} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
              <path d={WIRE.d} fill="none" stroke={C.black} strokeWidth={10} strokeLinecap="round" strokeDasharray={`${WIRE.length * S.wire} ${WIRE.length}`} />
            </svg>}
            {S.wire > 0.01 && <Sprite name="plugbin/34" x={ST.el - 420} y={ROAD_Y - 10} w={190} op={cl(S.wire * 3)} />}
            {wireDots}
            {S.coin > 0.01 && S.coin < 1 && (
              <div style={{position: "absolute", left: mix(ST.el - 420, ST.el, S.coin) - 30, top: mix(ROAD_Y - 330, ROAD_Y - 160, S.coin) - 30 - 100 * Math.sin(Math.PI * S.coin), width: 60, height: 60, borderRadius: 30,
                           background: `radial-gradient(circle at 35% 30%, ${C.bone}, ${C.gold} 45%, ${shade(C.gold, 0.3)})`, boxShadow: "0 4px 6px rgba(0,0,0,0.4)", opacity: 1 - 0.7 * Math.max(0, S.coin - 0.8) / 0.2}} />
            )}
            <Tag x={ST.el} y={ROAD_Y + 36} op={cl((f - E.too.s) / (E.too.l - E.too.s + 2))} on="dbrack">electricity, too</Tag>
            {/* 路尽头：奖牌 → 胶囊 → 玻璃肝 */}
            {S.medal > 0.01 && flip < 0.5 && <Sprite name="medal/34" x={ST.end} y={ROAD_Y - 250 + 60 * (1 - Math.min(1, S.medal)) + id(8).y} w={240} sx={Math.max(0.02, 1 - 2 * flip)} op={cl(S.medal * 2)} />}
            {flip >= 0.5 && <Capsule1 x={capP.x} y={capP.y + id(9).y} w={mix(170, 90, capT)} sx={capT > 0 ? 1 : Math.max(0.02, 2 * flip - 1)} op={capT > 0.97 ? 0 : 1} />}
            {S.cap > 0.01 && <Sprite name="liver/34" x={LIV.x} y={LIV.y} w={LIV.w} op={cl(S.cap * 3)} rim={0.9 * S.glow * (1 - 0.5 * cl((f - E.pat.l - 24) / 30))} />}
            {S.glow > 0.01 && <Tag x={LIV.x} y={ROAD_Y + 36} op={S.glow} on="liver">for patients</Tag>}
          </div>
        </Layer>
        <Layer id="txt" exempt>
          <Pen text="possible gains" x={180} y={110} at={E.b1.l + 4} out={E.elec.s} rot={-3} />
          <Source>Illustration · possible benefits and costs as discussed in Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B609" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
