// HKBU SCIE1007 课程作业的科普视频：B 档 2-01（A 画外音）"Hong Kong first. In 2011, a team at the Chinese University of Hong Kong studied liver tumours…"
// Hong Kong first：香港地图落在中间；In 2011：地图缩到左上角，年份牌 2011 落下；a team：三个小人；Chinese University of Hong Kong：标牌，地图上沙田一点亮；
// liver tumours：玻璃肝和样本管；patients：两个病人小人；Prince of Wales Hospital：标牌；
// One protein kept showing up raised：清场，六支样本管剖面，蓝色液柱一支支升过灰线；CCRK：小插座落下，also called CDK20；
// Fast forward to 2023：样本管清场，年份牌数字轮 2011 → 2023；AI：芯片；study：论文书；the same protein：小插座挪到书旁边；
// co-authors：两个小人站上一块底板（Insilico Medicine）；Hong Kong office in Science Park：左上角地图放大一点，那一点再亮，标 Science Park。
// 地图上的点只示意沙田一带（中大、威尔斯亲王医院、科学园都在那一片），不是精确坐标。
// 接点：开头、结尾都是 T5 料杆擦除（1-12 和 2-02 都不是 B 页）。L0 第 2 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_2-01.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Tag, camBreath, Stage, Sprite, Slab, Plate, Label, Source, Counter, Person1, evMapB, T5In, T5Out} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 2;

const MAP0 = {x: 960, y: 470, w: 720}, MAP1 = {x: 290, y: 200, w: 400}, MAP2 = {x: 330, y: 230, w: 480};
const MAP_AR = 639 / 1000, DOT = [0.615, 0.36];
const YEAR = {x: 820, y: 70, w: 290, h: 120};
const TEAM = [520, 680, 840], TEAM_Y = 520, P_W = 300;
const LIVER = {x: 1500, y: 430, w: 380};
const TUBES = {x: 1720, y: 640, w: 300};
const PATS = [1180, 1320];
// 六支样本管剖面
const TB = [...Array(6)].map((_, i) => ({x: 560 + i * 130, y: 300, w: 74, h: 420}));
const LVL = [0.62, 0.78, 0.55, 0.84, 0.7, 0.9], NORM = 0.32;
const MINI0 = {x: 1560, y: 470, w: 300}, MINI1 = {x: 1080, y: 520, w: 240};
const BOOK = {x: 760, y: 500, w: 480};
const AICHIP = {x: 760, y: 280, w: 300};
const CO = [1400, 1560], CO_Y = 560;
const BASE = {x: 1300, y: 640, w: 360, h: 50};

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("map", 0, 1, E.map.l, {antic: false});
    X.tw("mapA", 0, 1, E.y2011.s - 6, E.y2011.l + 24, "power2.inOut");
    X.land("year", 0, 1, E.y2011.l, {antic: false});
    X.group(TEAM.map((_, i) => `t${i}`), 0, 1, E.team.l, {antic: false});
    X.tw("dot1", 0, 1, E.cuhk.s, E.cuhk.l + 20, "back.out(2)");
    X.land("liver", 0, 1, E.tum.l, {antic: false});
    X.land("tubes", 0, 1, E.tum.l + 10, {antic: false});
    X.group(PATS.map((_, i) => `pt${i}`), 0, 1, E.pat.l, {antic: false, step: 6});
    X.tw("clear1", 0, 1, E.prot.s - 6, E.prot.l + 20, "power2.in");
    X.group(TB.map((_, i) => `tb${i}`), 0, 1, E.prot.l + 4, {antic: false, step: 4});
    TB.forEach((_, i) => X.tw(`lv${i}`, 0, LVL[i], E.raised.s + i * 10, E.raised.l + 20 + i * 10, "power2.out"));
    X.land("mini", 0, 1, E.ccrk.l, {antic: false});
    X.tw("clear2", 0, 1, E.ff.s, E.ff.s + 40, "power2.in");
    X.count("yr", 2011, 2023, E.ff.l, E.ff.l - E.ff.s);
    X.land("chip", 0, 1, E.ai.l, {antic: false});
    X.land("book", 0, 1, E.study.l, {antic: false});
    X.tw("same", 0, 1, E.same.s, E.same.l, "power2.inOut");
    X.group(CO.map((_, i) => `co${i}`), 0, 1, E.coauth.l, {antic: false, step: 6});
    X.land("base", 0, 1, E.ins.l, {antic: false});
    X.tw("map2", 0, 1, E.hk3.s, E.hk3.l + 20, "power2.inOut");
    X.tw("dot2", 0, 1, E.sp.s, E.sp.l + 20, "back.out(2)");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const c1 = -2000 * S.clear1, c2 = -2000 * S.clear2;
  const m = {x: mix(mix(MAP0.x, MAP1.x, S.mapA), MAP2.x, S.map2), y: mix(mix(MAP0.y, MAP1.y, S.mapA), MAP2.y, S.map2), w: mix(mix(MAP0.w, MAP1.w, S.mapA), MAP2.w, S.map2)};
  const dot = [m.x + (DOT[0] - 0.5) * m.w, m.y + (DOT[1] - 0.5) * m.w * MAP_AR + id(1).y];
  const dotR = Math.max(S.dot1 * (1 - 0.3 * S.dot2), S.dot2) * (m.w / 760);
  const ringT = (at) => { const t = (f - at) / 50; return t > 0 && t < 1 ? t : null; };
  const rings = [ringT(E.cuhk.l), ringT(E.cuhk.l + 50), ringT(E.sp.l), ringT(E.sp.l + 50)].filter((v) => v !== null);
  // 小插座：CCRK 落在右边；同一个蛋白挪到书旁边
  const mi = {x: mix(MINI0.x, MINI1.x, S.same), y: mix(MINI0.y, MINI1.y, S.same) - 120 * Math.sin(Math.PI * S.same), w: mix(MINI0.w, MINI1.w, S.same)};
  const yearV = S.yr;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1"])} over={<><T5In name="runner" f={f} /><T5Out name="runner" f={f} len={LEN} /></>}>
        <Layer id="map">
          {S.map > 0.01 && <Sprite name="hkmap/34" x={m.x} y={m.y - 40 * (1 - Math.min(1, S.map)) + id(1).y} w={m.w} op={Math.min(1, S.map * 1.5)} rot={id(1).r} />}
          {dotR > 0.01 && (
            <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
              {rings.map((t, k) => <circle key={k} cx={dot[0]} cy={dot[1]} r={14 + 60 * t} fill="none" stroke={C.ink} strokeWidth={4} opacity={0.55 * (1 - t)} />)}
              <circle cx={dot[0] + 2} cy={dot[1] + 3} r={13 * dotR} fill="rgba(40,30,20,0.25)" />
              <circle cx={dot[0]} cy={dot[1]} r={13 * dotR} fill={C.blue} />
              <circle cx={dot[0] - 4} cy={dot[1] - 4} r={4 * dotR} fill={C.bone} opacity={0.7} />
            </svg>
          )}
        </Layer>

        <Layer id="year">
          {S.year > 0.01 && (
            <Slab x={YEAR.x} y={YEAR.y - 30 * (1 - Math.min(1, S.year))} w={YEAR.w} h={YEAR.h} r={22} color={C.bone} depth={12} op={Math.min(1, S.year * 1.5)}
                  sheen={f > E.ff.s && f < E.ff.l ? (f - E.ff.s) / (E.ff.l - E.ff.s) : -1} id="year">
              <div style={{position: "absolute", left: 30, top: 10}}><Counter value={yearV} digits={4} size={100} x={0} y={0} /></div>
            </Slab>
          )}
        </Layer>

        {/* 第一幕：2011 的团队、样本、医院 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${c1}px)`}}>
          <Layer id="team">
            {TEAM.map((x, i) => S[`t${i}`] > 0.01 && <Person1 key={i} x={x} y={TEAM_Y - 40 * (1 - Math.min(1, S[`t${i}`])) + id(3 + i).y} w={P_W} op={Math.min(1, S[`t${i}`] * 1.5)} />)}
          </Layer>
          <Layer id="samples">
            {S.liver > 0.01 && <Sprite name="liver/34" x={LIVER.x} y={LIVER.y - 40 * (1 - Math.min(1, S.liver)) + id(6).y} w={LIVER.w} op={Math.min(1, S.liver * 1.5)} rot={id(6).r} />}
            {S.tubes > 0.01 && <Sprite name="tube/34" x={TUBES.x} y={TUBES.y - 40 * (1 - Math.min(1, S.tubes)) + id(7).y} w={TUBES.w} op={Math.min(1, S.tubes * 1.5)} />}
            {PATS.map((x, i) => S[`pt${i}`] > 0.01 && <Person1 red key={i} x={x} y={600 - 40 * (1 - Math.min(1, S[`pt${i}`])) + id(8 + i).y} w={260} op={Math.min(1, S[`pt${i}`] * 1.5)} />)}
          </Layer>
        </div>

        {/* 第二幕：六支样本管剖面 */}
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${c2}px)`}}>
          <Layer id="tubes">
            {TB.map((t, i) => {
              const a = S[`tb${i}`];
              if (a <= 0.01) return null;
              const y = t.y - 40 * (1 - Math.min(1, a)) + id(12 + i).y, lv = S[`lv${i}`] || 0, ih = (t.h - 24) * lv;
              return (
                <React.Fragment key={i}>
                  <Slab x={t.x} y={y} w={t.w} h={t.h} r={t.w / 2} color={C.bone} depth={10} op={Math.min(1, a * 1.5)} id={`tb${i}`} />
                  {ih > 1 && <Slab x={t.x + 12} y={y + 12 + (t.h - 24 - ih)} w={t.w - 24} h={ih} r={(t.w - 24) / 2} color={C.blue} depth={0} shadow={false} sheen={lv < LVL[i] ? lv : -1} id={`lq${i}`} />}
                </React.Fragment>
              );
            })}
            {S.tb5 > 0.3 && (
              <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible", opacity: Math.min(1, (S.tb5 - 0.3) * 2)}}>
                <line x1={TB[0].x - 30} x2={TB[5].x + TB[5].w + 30} y1={TB[0].y + 12 + (TB[0].h - 24) * (1 - NORM)} y2={TB[0].y + 12 + (TB[0].h - 24) * (1 - NORM)}
                      stroke={C.grey} strokeWidth={6} strokeDasharray="18 12" strokeLinecap="round" />
              </svg>
            )}
          </Layer>
        </div>

        <Layer id="book">
          {S.chip > 0.01 && <Sprite name="chip_pandaomics/34" x={AICHIP.x} y={AICHIP.y - 40 * (1 - Math.min(1, S.chip)) + id(16).y} w={AICHIP.w} op={Math.min(1, S.chip * 1.5)} />}
          {S.book > 0.01 && <Sprite name="book/34" x={BOOK.x} y={BOOK.y - 40 * (1 - Math.min(1, S.book)) + id(17).y} w={BOOK.w} op={Math.min(1, S.book * 1.5)} rot={id(17).r} />}
          {S.mini > 0.01 && <Sprite name="mini/m34_on" x={mi.x} y={mi.y - 40 * (1 - Math.min(1, S.mini)) + id(18).y} w={mi.w} op={Math.min(1, S.mini * 1.5)} lift={20 * Math.sin(Math.PI * S.same)} />}
          {S.base > 0.01 && <Plate x={BASE.x} y={BASE.y + 30 * (1 - Math.min(1, S.base))} w={BASE.w} h={BASE.h} text="Insilico Medicine" size={40} op={Math.min(1, S.base * 1.5)} id="base" />}
          {CO.map((x, i) => S[`co${i}`] > 0.01 && <Person1 key={i} x={x} y={CO_Y - 40 * (1 - Math.min(1, S[`co${i}`])) - (S.base > 0.5 ? 0 : 0) + id(20 + i).y} w={260} op={Math.min(1, S[`co${i}`] * 1.5)} />)}
        </Layer>

        <Layer id="txt" exempt>
          <Label text="Chinese University of Hong Kong" size={48} x={680 + c1} y={720} at={E.cuhk.l} out={E.pwh.s} align="center" />
          <Label text="Prince of Wales Hospital" size={48} x={1450 + c1} y={800} at={E.pwh.l} align="center" />
          <Label text="CCRK" size={56} x={MINI0.x} y={680} at={E.ccrk.l} out={E.cdk20.s} align="center" />
          <Label text="also called CDK20" size={56} x={MINI0.x} y={680} at={E.cdk20.l} out={E.ff.l} align="center" />
          {S.tb0 > 0.5 && f < E.ff.s + 30 && <Tag x={TB[5].x + TB[5].w + 50 + c2} y={TB[0].y + 12 + (TB[0].h - 24) * (1 - NORM) - 22} align="left" op={Math.min(1, (S.tb0 - 0.5) * 2)}>normal</Tag>}
          {S.book > 0.5 && <Tag x={BOOK.x} y={BOOK.y + 150} op={Math.min(1, (S.book - 0.5) * 2)}>Ren et al., Chem. Sci. 2023</Tag>}
          <Label text="co-authors" size={52} x={1480} y={420} at={E.coauth.l} align="center" />
          <Label text="Science Park" size={52} x={dot[0] + 40} y={dot[1] + 60} at={E.sp.l} align="left" />
          <Source>Illustration · data: Feng et al., J. Clin. Invest. 2011; Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B201" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
