// HKBU SCIE1007 课程作业的科普视频：B 档 4-06（A 画外音）"And this next part honestly blew my mind. Think about how chemists have always found a key…"
// this next part：一圈骨白料杆环画出来；blew my mind：环一亮一抖（T7）；chemists：左边小人；a key：金插头落在环顶；
// Imagine / Make / Test / fails / Tweak / Try again：插头沿环走，四站牌依次弹出；Make 烧瓶，Test 小插座（插不进，弹回变灰），Tweak 换形；
// every single round … costs time and money：插头越跑越快，每过顶站掉一张钞票、日历翻一页。
// 接点：开头 T5 料杆擦除（4-04+05 出镜段），结尾 T2 往左甩（4-07 接着用同一个环，位置一样：LOOP）。L0 第 4 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_4-06.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Slab, Calendar1, camBreath, Stage, Sprite, Runner, Plate, Label, Pen, Source, Person1, evMapB, T5In, whipX, impact} from "./bkit.jsx";
import {useGsapTimeline, idle} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 4;

const LOOP = {cx: 910, cy: 470, r: 230};
const ringD = `M${LOOP.cx},${LOOP.cy - LOOP.r} a${LOOP.r},${LOOP.r} 0 1,1 -0.01,0`;
// 四站：顶 Imagine、右 Make、底 Test、左 Tweak（角度：-90 顶，顺时针）
const ST = [["Imagine", -90], ["Make", 0], ["Test", 90], ["Tweak", 180]];
// 站牌放在环里面、各自那一站的内侧（插头在环上走，不压牌子）
const PW = 200, PH = 66;
const plateXY = (a) => {
  const t = (a * Math.PI) / 180, R = 132;
  return [LOOP.cx + R * Math.cos(t) - PW / 2, LOOP.cy + R * Math.sin(t) - PH / 2];
};
const onRing = (a) => { const t = (a * Math.PI) / 180; return [LOOP.cx + LOOP.r * Math.cos(t), LOOP.cy + LOOP.r * Math.sin(t)]; };
const FLASK = {x: 1360, y: 330, w: 190};
const MINI = {x: 1250, y: 720, w: 230};
const BILL = {x: 1640, y: 760};
const CAL = {x: 1640, y: 440, w: 218};
const KEY_W = 170;

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.tw("ring", 0, 1, E.part.s, E.part.l + 30, "power2.out");
    X.tw("flash", 0, 1, E.mind.s, E.mind.e, "power2.out");
    X.land("chem", 0, 1, E.chem.l, {antic: false});
    X.land("key", 0, 1, E.key.l, {antic: false});
    // blew my mind：四块站牌一下全弹出来（T7）；说到哪一站，那块牌子再跳一下、亮一下
    ST.forEach((_, i) => X.land(`pl${i}`, 0, 1, E.mind.l + i * 6, {antic: false}));
    ST.forEach((_, i) => { const ev = [E.imag, E.make, E.test, E.tweak][i]; X.tw(`h${i}`, 0, 1, ev.s, ev.l + 24, "power1.inOut"); });
    // 插头沿环走（角度，度）
    X.tw("a1", -90, 0, E.make.s, E.make.l + 6, "power2.inOut");
    X.land("flask", 0, 1, E.make.l + 8, {antic: false});
    X.tw("a2", 0, 90, E.test.s, E.test.l + 6, "power2.inOut");
    X.land("mini", 0, 1, E.test.l + 6, {antic: false});
    X.tw("poke", 0, 1, E.fail.s - 10, E.fail.l, "power2.in");
    X.tw("back", 0, 1, E.fail.l, E.fail.l + 20, "power2.out");
    X.jiggle("failJ", E.fail.l, 8, 0);
    X.tw("grey", 0, 1, E.fail.l, E.fail.l + 12, "power2.out");
    X.tw("a3", 90, 180, E.tweak.s, E.tweak.l + 6, "power2.inOut");
    X.tw("morph", 0, 1, E.tweak.l, E.tweak.l + 18, "power2.inOut");
    X.tw("a4", 180, 270, E.again.s, E.again.l + 10, "power2.inOut");
    X.land("cal", 0, 1, K.words.find(w=>w.key==="time#1")?.f0??E.round.l, {antic: false});
    // every single round：越跑越快，到段尾跑三圈半
    X.tw("a5", 270, 270 + 360 * 3.5, E.round.s, LEN - 8, "power2.in");
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const clamp01 = (v) => Math.max(0, Math.min(1, v));
  const shake = impact(f, E.mind.l) + impact(f, E.fail.l);
  const whip = whipX(f, LEN - 7, "out", -1);

  // 插头的角度：按段落接力
  const ang = f >= E.round.s ? S.a5 : f >= E.again.s ? S.a4 : f >= E.tweak.s ? S.a3 : f >= E.test.s ? S.a2 : S.a1;
  const [kx, ky] = onRing(ang);
  // fails：在底站往外顶一下（朝小插座方向），弹回
  const pokeOut = S.poke * (1 - S.back);
  const kp = [kx + 120 * pokeOut + (S.failJ || 0), ky + 40 * pokeOut];
  const grey = S.grey * (1 - S.morph);
  const keyName = f >= E.make.l ? "plug/A_34" : "plug/blank_34";
  const morphSq = 1 - 0.25 * Math.sin(Math.PI * S.morph);
  // 每过顶站一次（270 + 360k）掉一张钞票、日历翻一页
  const laps = f >= E.round.s ? Math.max(0, (S.a5 - 270) / 360) : 0;
  const lapN = Math.floor(laps);
  const drop = (k) => clamp01((laps - k) * 4);
  const flip = lapN > 0 ? Math.max(0, 1 - (laps - lapN) * 6) : 0;
  const ringFlash = S.flash > 0 ? Math.sin(Math.PI * S.flash) : 0;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} whip={whip} shakeX={shake} shakeY={shake * 0.5} cam={camBreath(f, K, [])} over={<T5In name="runner" f={f} />}>
        <Layer id="loop">
          {S.ring > .001 && <Sprite hero name="track/34_codex2x" x={910} y={463} w={1100} op={Math.min(1,S.ring)}/>}
          {S.ring > 0.001 && <Runner d={ringD} draw={S.ring} width={14} />}
          {ringFlash > 0.01 && (
            <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
              <circle cx={LOOP.cx} cy={LOOP.cy} r={LOOP.r + 30 * S.flash} fill="none" stroke={C.bone} strokeWidth={10} opacity={0.8 * ringFlash} />
            </svg>
          )}
          {ST.map(([t, a], i) => {
            const p = S[`pl${i}`];
            if (p <= 0.01) return null;
            const [x, y] = plateXY(a);
            const h = S[`h${i}`], hop = h > 0 && h < 1 ? Math.sin(Math.PI * h) : 0;
            return <Plate key={i} x={x} y={y - 24 * (1 - Math.min(1, p)) + id(1 + i).y} w={PW} h={PH} text={t} size={46} op={Math.min(1, p * 1.5)} id={`st${i}`}
                          lift={16 * hop} sheen={h > 0 && h < 1 ? h : -1} />;
          })}
        </Layer>

        <Layer id="props">
          {S.flask > 0.01 && <Sprite name="flask/34" x={FLASK.x} y={FLASK.y - 50 * (1 - Math.min(1, S.flask)) + id(11).y} w={FLASK.w} op={Math.min(1, S.flask * 1.5)} rot={id(11).r} />}
          {S.mini > 0.01 && <Sprite name="mini/m34_on" x={MINI.x} y={MINI.y - 40 * (1 - Math.min(1, S.mini)) + id(8).y} w={MINI.w} op={Math.min(1, S.mini * 1.5)} />}
        </Layer>
        <Layer id="costs">
          {S.cal > 0.01 && <Calendar1 x={CAL.x} y={CAL.y - 40 * (1 - Math.min(1, S.cal)) - 14 * flip + id(9).y} w={CAL.w} op={Math.min(1, S.cal * 1.5)} rot={id(9).r - 3 * flip} />}
          {[0, 1, 2].map((k) => drop(k) > 0.01 && (
            <Sprite key={k} name="coins/34" x={BILL.x + (k % 2 ? 26 : -18)} y={mix(LOOP.cy - LOOP.r - 40, BILL.y - k * 26, drop(k))} w={300}
                    rot={mix(-30, ((k * 53) % 14) - 7, drop(k))} op={Math.min(1, drop(k) * 3)} shadow={drop(k) > 0.9} />
          ))}
        </Layer>

        <Layer id="key">
          {S.key > 0.01 && (
            <Sprite name={keyName} x={kp[0]} y={kp[1] - 50 * (1 - Math.min(1, S.key)) - 46} w={KEY_W} op={Math.min(1, S.key * 1.5)} lift={10}
                    sy={morphSq} rot={-6 * Math.sin((2 * Math.PI * f) / 40) * (f > E.round.s ? 1 : 0.3)}
                    style={{filter: grey > 0.01 ? `grayscale(${grey}) brightness(${1 - 0.15 * grey})` : undefined}} />
          )}
        </Layer>

        <Layer id="txt" exempt>
          <Pen text="fails" x={560} y={790} at={E.fail.l - 4} out={E.tweak.s} size={64} rot={-4} />
          <Label text="time and money" size={56} x={1230} y={120} at={E.cost.l} align="center" />
          <Source>Illustration · the classic design–make–test cycle</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B406" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
