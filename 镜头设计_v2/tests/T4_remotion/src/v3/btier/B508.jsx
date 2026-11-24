// HKBU SCIE1007 课程作业的科普视频：B 档 5-08（C 画外音）"And one of them, 048, grabbed about fifteen times tighter."
// 料杆上一排金插头，一个抬起来刻上 048；grabbed：048 飞到 Kd 横尺 0.6 处（001 在 9.2，5-03 留下的）；
// fifteen times：0 到 9.2 之间依次铺出 15 段，每段是 048 的那一小截；tighter：手写 ≈ 15× tighter。
// enzyme test：十个小插座落位，灯亮（酶在干活）；001 needed more than 6,000 nanomolar：对数表盘的针一路转到 6,000 以外；
// 048 needed just 33.4：001 的针变灰留着，新针只转一点停在 33.4，十个里五个插座被 048 卡死（拧 90°、红卡扣、灯灭），T7 一抖。
// 接点：开头 T2 从右甩进（5-07 是 B 页），结尾 T5 料杆擦除（5-09 出镜段）。L0 第 5 区大板。数字照旁白：fifteen、6,000、33.4。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_5-08.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, SERIF, Tag, camBreath, Stage, Sprite, Slab, Gate, Runner, Label, Pen, Source, Counter, Engrave, Dial, Lamp, anchorOf, pathOf, evMapB, T5Out, whipX, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 5;

// ---- 第一幕：料杆一排，Kd 横尺（线性 0–10 µM）
const ROW = ["A", "B", "C", "blank", "D", "E"];
const ONE = 3;
const ROW_X = (i) => 330 + i * 190, ROW_Y = 330, SPRUE_Y = 432, PW = 170;
const RAIL_Y = 760;
const X = (v) => 360 + v * 132;                 // 0–10 µM → x 360–1680
const tipDX = (n, w) => -anchorOf(`plug/${n}_34`, "tip", w)[0];
const K48 = 9.2 / 15;                           // ≈ 0.6 µM（fifteen times tighter）
// ---- 第二幕：十个小插座（5 × 2，右边），左边对数表盘
const MW = 160;
const GRID = [...Array(10)].map((_, i) => ({x: 1030 + (i % 5) * 170, y: 400 + Math.floor(i / 5) * 240}));
const CLAMP = [1, 3, 5, 7, 9];
// 剂量条：对数刻度 1 nM（x0）到 10,000 nM（x0 + SPAN）；上面一根 001，下面一根 048，左头各停一个插头
const DOSE = {x0: 400, span: 480, y1: 470, y2: 640, h: 36};
const xv = (lg) => DOSE.x0 + (DOSE.span * Math.max(0, lg)) / 4;     // lg = log10(nM)
const PARK1 = [DOSE.x0 - 110, DOSE.y1 + 12], PARK2 = [DOSE.x0 - 110, DOSE.y2 + 12];

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X_) => {
    X_.tw("sprue", 0, 1, E.row.s + 4, E.row.s + 40, "power2.out");
    X_.group(ROW.map((_, i) => `r${i}`), 0, 1, E.row.l + 14, {step: RULE.stagger, antic: false});
    X_.tw("rail", 0, 1, E.row.s + 10, E.row.s + 50, "power2.out");
    X_.land("one", 0, 1, E.one.l);
    X_.tw("k48", 0, 1, E.k48.s, E.k48.l, "power2.inOut");
    X_.tw("grab", 0, 1, E.grab.s, E.grab.l, "power2.inOut");
    X_.jiggle("grabJ", E.grab.l, 3);
    X_.group([...Array(15)].map((_, i) => `g${i}`), 0, 1, E.fif.l - 7 * 4, {step: RULE.stagger, antic: false});
    X_.count("n15", 0, 15, E.fif.l, 24);
    X_.tw("clear", 0, 1, E.clear.s, E.clear.e, "power3.in");
    X_.group(GRID.map((_, i) => `m${i}`), 0, 1, E.grid.l, {step: RULE.stagger, antic: false});
    X_.land("dial", 0, 1, E.dial.l);
    X_.land("p001", 0, 1, E.p001.l);
    X_.tw("sw1", 0, Math.log10(6000), E.sweep.s, E.sweep.l, "power1.inOut");
    X_.tw("park", 0, 1, E.clear.s, E.dial.l, "power2.inOut");
    X_.jiggle("sw1J", E.sweep.l, 3, 0);
    X_.count("n6000", 0, 6000, E.sweep.l, 83);
    X_.tw("nm", 0, 1, E.nm.s, E.nm.l + 6, "power2.out");
    X_.tw("swap", 0, 1, E.p48.s, E.p48.l, "power2.inOut");
    X_.tw("sw2", 0, Math.log10(33.4), E.need.s, E.need.l, "power2.inOut");
    X_.count("n334", 0, 33.4, E.need.l, 30);
    CLAMP.forEach((g, k) => X_.tw(`c${g}`, 0, 1, E.clamp.l - 6 + k * 4, E.clamp.l + 6 + k * 4, "power2.out"));
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const clearX = -2000 * S.clear * S.clear;
  const whip = f < 7 ? whipX(f, 0, "in", -1) : 0;
  const shake = impact(f, E.clamp.l);

  // 048：料杆上抬起 → 飞到横尺 0.6
  const startP = [ROW_X(ONE), ROW_Y - 50 * S.one];
  const endP = [X(K48) + tipDX("048", 200), RAIL_Y - 90];
  const P = pathOf([startP, [(startP[0] + endP[0]) / 2 - 80, startP[1] + 60], endP]);
  const gp = P.at(S.grab);
  const p48 = S.grab > 0 ? {x: gp[0], y: gp[1] + S.grabJ, w: mix(PW, 200, S.grab)} : {x: startP[0], y: startP[1] + id(13).y, w: PW};
  const segW = X(K48) - X(0);

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s2"])} whip={whip} shakeX={shake} shakeY={shake * 0.5} over={<T5Out name="runner" f={f} len={LEN} />}>
        <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${clearX}px)`}}>
          <Layer id="row">
            <Runner d={`M220,${SPRUE_Y} L1390,${SPRUE_Y}`} draw={S.sprue} width={18} />
            {ROW.map((n, i) => {
              const a = S[`r${i}`];
              if (a <= 0.01) return null;
              const isOne = i === ONE;
              if (isOne && S.grab > 0) return <Gate key={i} x1={ROW_X(i)} y1={SPRUE_Y} x2={ROW_X(i)} y2={SPRUE_Y - 54} w={14} broken={Math.min(1, S.grab * 4)} />;
              const y = ROW_Y - 40 * (1 - Math.min(1, a)) + id(10 + i).y - (isOne ? 50 * S.one : 0);
              return (
                <React.Fragment key={i}>
                  <Gate x1={ROW_X(i)} y1={SPRUE_Y} x2={ROW_X(i)} y2={SPRUE_Y - 54 * Math.min(1, a)} w={14} />
                  {isOne && S.k48 > 0 ? (
                    <>
                      <Sprite name="plug/blank_34" x={ROW_X(i)} y={y} w={PW} op={1 - S.k48} rot={id(10 + i).r} />
                      <Sprite name="plug/048_34" x={ROW_X(i)-174*(1-S.k48)} y={y-38*Math.sin(Math.PI*S.k48)} w={PW} op={S.k48>0?1:0} rot={id(10 + i).r} shadow={false} rim={S.k48 * (1 - S.grab)} />
                    </>
                  ) : (
                    <Sprite name={`plug/${n}_34`} x={ROW_X(i)} y={y} w={PW} op={Math.min(1, a * 1.6)} rot={id(10 + i).r} />
                  )}
                </React.Fragment>
              );
            })}
          </Layer>
          <Layer id="rail">
            <Runner d={`M300,${RAIL_Y} L1740,${RAIL_Y}`} draw={S.rail} width={18} />
            {S.rail > 0.5 && [0, 2, 4, 6, 8, 10].map((v) => (
              <Slab key={v} x={X(v) - 3} y={RAIL_Y + 14} w={6} h={20} r={3} color={C.bone} depth={3} shadow={false} op={Math.min(1, (S.rail - 0.5) * 2)} id={`tk${v}`} />
            ))}
            {S.rail > 0.6 && (
              <>
                <Gate x1={X(9.2)} y1={RAIL_Y} x2={X(9.2)} y2={RAIL_Y - 60} w={12} />
                {S.park <= 0 && <Sprite name="plug/001_34" x={X(9.2) + tipDX("001", 200)} y={RAIL_Y - 90 + id(2).y} w={200} op={Math.min(1, (S.rail - 0.6) * 3)} />}
              </>
            )}
            {[...Array(15)].map((_, i) => {
              const a = S[`g${i}`];
              return a > 0.01 && <Slab key={i} x={X(0) + i * segW + 1} y={RAIL_Y + 40 - 16 * (1 - Math.min(1, a))} w={segW - 3} h={22} r={7} color={C.blueHi} depth={5}
                                       op={Math.min(1, a)} sheen={Math.min(1, a)} shadow={false} id={`sg${i}`} />;
            })}
          </Layer>
          <Layer id="p48">
            {(S.grab > 0) && <Gate x1={X(K48)} y1={RAIL_Y} x2={X(K48)} y2={RAIL_Y - 60 * Math.min(1, S.grab * 1.2)} w={12} />}
          </Layer>
        </div>

        {/* 两个插头：第一幕在横尺上，清场时飞到剂量条左头 */}
        <Layer id="plugs2">
          {S.grab > 0 && (() => {
            const a = [p48.x, p48.y], b = PARK2, u = S.park;
            return <Sprite name="plug/048_34" x={mix(a[0], b[0], u)} y={mix(a[1], b[1], u) - 120 * Math.sin(Math.PI * u) + (u > 0.99 ? id(5).y : 0)} w={mix(p48.w, 170, u)}
                           lift={30 * Math.sin(Math.PI * Math.max(S.grab < 1 ? S.grab : 0, u))} rot={-5 * Math.sin(Math.PI * S.grab)}
                           style={u > 0.5 ? {filter: `grayscale(${0.7 * (1 - S.swap)}) brightness(${1 - 0.1 * (1 - S.swap)})`} : undefined} rim={S.swap * (1 - S.swap) * 4} />;
          })()}
          {S.park > 0 && (() => {
            const a = [X(9.2) + tipDX("001", 200), RAIL_Y - 90], b = PARK1, u = S.park;
            return <Sprite name="plug/001_34" x={mix(a[0], b[0], u)} y={mix(a[1], b[1], u) - 160 * Math.sin(Math.PI * u) + id(2).y} w={mix(200, 170, u)} lift={30 * Math.sin(Math.PI * u)}
                           rim={Math.sin(Math.PI * Math.min(1, S.p001))} />;
          })()}
        </Layer>

        {/* 第二幕：十个小插座 + 两根剂量条 */}
        <Layer id="grid">
          {GRID.map((g, i) => {
            const a = S[`m${i}`];
            if (a <= 0.01) return null;
            const c = S[`c${i}`] || 0;
            const touch = Math.max(0,1-Math.abs(f-E.nm.l-i*5)/18);
            const y = g.y - 40 * (1 - Math.min(1, a)) + id(20 + i).y - (i<4?18*touch:0);
            return (
              <React.Fragment key={i}>
                <Sprite name="mini/m34_on" x={g.x} y={y} w={MW} op={Math.min(1, a * 1.6) * (1 - c)} rot={id(20 + i).r} />
                <Lamp name="mini/m34_on" x={g.x} y={y} w={MW} on={Math.min(1, a) * (1 - c) * (f > E.dial.s && f < E.clamp.l ? 0.78 + 0.22 * Math.sin((2 * Math.PI * (f + 9 * i)) / 40) : 1)} />
                {i<4 && f>=E.nm.l+i*5 && c<.01 && <Sprite name="mini/m34_001" x={g.x} y={y} w={MW} op={Math.min(1,(f-E.nm.l-i*5)/12)} shadow={false}/>}
                {c > 0 && <Sprite name="mini/m34_048clamp" x={g.x} y={y} w={MW} op={c} rot={id(20 + i).r} shadow={false} />}
              </React.Fragment>
            );
          })}
        </Layer>
        <Layer id="dial">
          {S.dial > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: Math.min(1, S.dial * 1.5), transform: `translateY(${(1 - Math.min(1, S.dial)) * 40}px)`}}>
              {/* 刻度轴 */}
              <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
                <line x1={DOSE.x0} y1={DOSE.y2 + 96} x2={DOSE.x0 + DOSE.span} y2={DOSE.y2 + 96} stroke={C.ink} strokeWidth={3} />
                {[0, 1, 2, 3, 4].map((k) => <line key={k} x1={xv(k)} y1={DOSE.y2 + 86} x2={xv(k)} y2={DOSE.y2 + 106} stroke={C.ink} strokeWidth={3} />)}
                {[0, 1, 2, 3].flatMap((k) => [2, 3, 4, 5, 6, 7, 8, 9].map((m) => <line key={`${k}${m}`} x1={xv(k + Math.log10(m))} y1={DOSE.y2 + 90} x2={xv(k + Math.log10(m))} y2={DOSE.y2 + 102} stroke={C.ink} strokeWidth={1.5} opacity={0.6} />))}
              </svg>
              {/* 两根条：001 灰（要很多），048 蓝（一点就够） */}
              <Slab x={DOSE.x0} y={DOSE.y1} w={Math.max(4, xv(S.sw1 + (S.sw1J || 0) * 0.01) - DOSE.x0)} h={DOSE.h} r={12} color={C.grey} depth={7} sheen={S.sw1 > 0 && f < E.sweep.l + 10 ? (S.sw1 / 3.78) : -1} id="bar001" />
              {f >= E.sweep.l && <div style={{position: "absolute", left: xv(Math.log10(6000)) + 14, top: DOSE.y1 - 6, opacity: Math.min(1, (f - E.sweep.l) / 10)}}><Engrave size={52}>›</Engrave></div>}
              {S.sw2 > 0.001 && <Slab x={DOSE.x0} y={DOSE.y2} w={Math.max(4, xv(S.sw2) - DOSE.x0)} h={DOSE.h} r={12} color={C.gold} depth={7} sheen={S.sw2 < Math.log10(33.4) ? S.sw2 / 1.52 : -1} id="bar048" />}
            </div>
          )}
        </Layer>

        <Layer id="txt" exempt>
          {/* Z19（11-23）：刻度数字放进不虚的字层（在 dial 层里被视线引导一起虚掉，con 0.15），字号 34 → 38 */}
          {S.dial > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, opacity: Math.min(1, S.dial * 1.5), transform: `translateY(${(1 - Math.min(1, S.dial)) * 40}px)`}}>
              {["1", "10", "100", "1,000", "10,000 nM"].map((t, k) => (
                <div key={k} style={{position: "absolute", left: xv(k), top: DOSE.y2 + 112, transform: k === 4 ? "translateX(-22%)" : "translateX(-50%)"}}><Engrave size={38}>{t}</Engrave></div>
              ))}
            </div>
          )}
          <Label text="001 · 9.2 µM" size={44} x={1574 + clearX} y={535} at={E.one.l + 10} out={E.clear.s} align="center" />
          <Label text="048 · 566.7 nM" size={44} x={435 + clearX} y={535} at={E.grab.l} out={E.clear.s} align="center" />
          {S.rail > 0.6 && <Tag x={1710 + clearX} y={RAIL_Y - 20} op={Math.min(1, (S.rail - 0.6) * 3)}>Kd</Tag>}
          <Label text="048" size={60} x={ROW_X(ONE)} y={186} at={E.k48.l} out={E.grab.l} align="center" />
          {S.n15 > 0.05 && S.clear < 1 && (
            <div style={{position: "absolute", left: 150 + clearX, top: RAIL_Y - 44}}>
              <Counter value={S.n15} digits={2} size={64} x={0} y={0} />
            </div>
          )}
          <Pen text="≈ 15× tighter" x={760 + clearX} y={560} at={E.tig.l} size={68} />
          <Label text="enzyme test" size={60} x={1370} y={196} at={E.lab.l} out={E.p001.s} align="center" />
          <Label text="001" size={52} x={PARK1[0]} y={DOSE.y1 - 110} at={E.p001.l} align="center" />
          <Label text="048" size={52} x={PARK2[0]} y={DOSE.y2 - 110} at={E.p48.l} align="center" />
          {S.n6000 > 0.5 && (
            <div style={{position: "absolute", left: DOSE.x0 + 40, top: DOSE.y1 - 120, opacity: 1}}>
              <div style={{display: "flex", alignItems: "baseline"}}><Engrave size={72}>&gt;</Engrave></div>
              <div style={{position: "absolute", left: 46, top: -6}}><Counter value={S.n6000} digits={4} comma size={84} x={0} y={0} /></div>
              <div style={{position: "absolute", left: 46 + 4 * 42 + 44, top: 18, opacity: S.nm}}><Engrave size={52}>nM</Engrave></div>
            </div>
          )}
          {S.n334 > 0.05 && (
            <div style={{position: "absolute", left: xv(Math.log10(33.4)) + 24, top: DOSE.y2 - 16}}>
              <Counter value={S.n334} digits={2} decimals={1} size={84} x={0} y={0} />
              <div style={{position: "absolute", left: 3 * 42 + 20, top: 24}}><Engrave size={52}>nM</Engrave></div>
              {/* R2-13：论文摘要 IC50 = 33.4 ± 22.6 nM (n = 3)，已对 Ren2023 正文核过 */}
              <div style={{position: "absolute", left: 3 * 42 + 20 + 92, top: 38, fontFamily: SERIF, fontSize: 30, color: C.soft, whiteSpace: "nowrap", opacity: Math.max(0, Math.min(1, (f - 963) / 10))}}>± 22.6</div>
            </div>
          )}
          <Source>Illustration · data: Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B508" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
