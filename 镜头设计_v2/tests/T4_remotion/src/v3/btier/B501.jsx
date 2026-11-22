// HKBU SCIE1007 课程作业的科普视频：B 档 5-01（C 画外音）"So, the moment of truth."（第 5 章第一页）
// 插座比喻（06_插座比喻.md）：CDK20 = 蓝插座，药 = 金色假插头（001、A–F 只是画面代号）。
// moment of truth：插座落位、灯一闪；seven real molecules：插座让到右边，料杆上七个金插头依次落位；made in a real lab：烧瓶；
// Do any actually grab CDK20?：001 从料杆上掰下来，飞到插座口前停住，红色问号（答案在 5-03）；
// Kd：十个小插座，烧瓶里的插头一个个飞进去，第五个插上 = half（十个里五个），T7 一抖；Lower means tighter：Kd 刻度的标往下，插上的五个压紧。
// 接点：开头 T5 料杆擦除（4-11+12 出镜段）+ T6 光扫，结尾 T5 料杆擦除（5-02 出镜段）。L0 第 5 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_5-01.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, Engrave, camBreath, Stage, Sprite, Slab, Gate, Runner, Label, Pen, Source, anchorOf, pathOf, evMapB, T5In, T5Out, T6Sweep, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, RULE} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 5;
const at = (name, key, x, y, w) => { const [dx, dy] = anchorOf(name, key, w); return [x + dx, y + dy]; };

// ---- 第一、二幕
const SOCK0 = {x: 960, y: 470, w: 700}, SOCK1 = {x: 1330, y: 400, w: 500};
const PLUGS = ["001", "A", "B", "C", "D", "E", "F"];
const ROW_Y = 600, SPRUE_Y = 712, PW = 150;
const ROW_X = (i) => 150 + i * 142;
const FLASK1 = {x: 1720, y: 770, w: 180}, FLASK2 = {x: 330, y: 610, w: 260};
// 001 飞到插座口前：尖对准插座的 approach 点，再往 contact 走 25% 停住
const SOCK_APP = at("socket/hero_34", "approach", SOCK1.x, SOCK1.y, SOCK1.w);
const SOCK_CON = at("socket/hero_34", "contact", SOCK1.x, SOCK1.y, SOCK1.w);
const PW_NEAR = 264;                           // 插头飞近插座时按实物比例：插座 50 mm 显示 500 px，插头 26.5 mm → 264 px
const tipOff = (w) => anchorOf("plug/001_34", "tip", w);
const HOVER = [SOCK_APP[0] + (SOCK_CON[0] - SOCK_APP[0]) * 0.25, SOCK_APP[1] + (SOCK_CON[1] - SOCK_APP[1]) * 0.25];
const TRY_END = [HOVER[0] - tipOff(PW_NEAR)[0], HOVER[1] - tipOff(PW_NEAR)[1]];
const TRY = pathOf([[ROW_X(0), ROW_Y], [640, 290], [1360, 250], TRY_END]);

// ---- 第四幕：十个小插座（5 × 2），左边烧瓶
const MW = 170;
const GRID = [...Array(10)].map((_, i) => ({x: 820 + (i % 5) * 200, y: 380 + Math.floor(i / 5) * 250}));
const FILL = [0, 6, 2, 8, 4];                  // 依次插上的五个（交错，不是一排）
const FLY_W = 92;                              // 小插座按 0.4 缩：插头 27 mm × 0.4 → 显示 92 px
const KD = {x: 470, y: 200, h: 300};

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    X.land("sock", 0, 1, E.sock.l + 6, {antic: false});
    X.tw("lamp", 0, 1, E.sock.l + 26, E.sock.l + 36, "power2.out");
    X.tw("lamp", 1, 0, E.sock.l + 46, E.sock.l + 80, "power2.inOut");
    X.tw("mv", 0, 1, E.rack.s - 20, E.rack.l + 10, "power3.inOut");
    X.tw("sprue", 0, 1, E.rack.s - 10, E.rack.s + 20, "power2.out");
    X.group(PLUGS.map((_, i) => `p${i}`), 0, 1, E.rack.l, {step: RULE.stagger});
    X.land("flask", 0, 1, E.flask.l);
    PLUGS.forEach((_, i) => X.jiggle(`pj${i}`, E.any.s + i * 5, 4, 0));
    X.tw("try", 0, 1, E.try.s, E.try.l, "power2.inOut");
    X.tw("gate0", 0, 1, E.try.s, E.try.s + 8, "power2.out");
    X.jiggle("tryJ", E.try.l, 3);
    X.tw("clear", 0, 1, E.clear.s - 6, E.clear.e, "power3.in");
    X.tw("fl2", 0, 1, E.clear.s, E.clear.e + 20, "power3.inOut");
    X.tw("kd", 0, 1, E.kd.s, E.kd.l + 10, "power2.out");
    X.group(GRID.map((_, i) => `m${i}`), 0, 1, E.grid.l - 18, {step: RULE.stagger, antic: false});
    X.jiggle("muchJ", E.much.l - 4, 6, 0);
    X.tw("bub", 0, 1, E.much.s, E.much.e, "power1.inOut");
    FILL.forEach((g, k) => {
      const land = E.half.l - (FILL.length - 1 - k) * 30;   // 第一个从 much 句尾起飞（Gemini 初审：molecule 后停 2 秒）
      X.tw(`fly${k}`, 0, 1, land - 46, land, "power2.inOut");
      X.jiggle(`mj${g}`, land, 3, 1);
    });
    X.tw("kdm", 0, 1, E.lower.s, E.lower.l + 12, "power3.inOut");
    FILL.forEach((g, k) => X.jiggle(`tj${g}`, E.tight.l + k * 3, 4, 0));
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.6});
  const mix = (a, b, t) => a + (b - a) * t;
  const sk = {x: mix(SOCK0.x, SOCK1.x, S.mv) + 1400 * S.clear, y: mix(SOCK0.y, SOCK1.y, S.mv), w: mix(SOCK0.w, SOCK1.w, S.mv)};
  const rowDX = -1500 * S.clear;
  const flask = {x: mix(FLASK1.x, FLASK2.x, S.fl2), y: mix(FLASK1.y, FLASK2.y, S.fl2), w: mix(FLASK1.w, FLASK2.w, S.fl2)};
  const shake = impact(f, E.half.l);
  const flaskMouth = [flask.x, flask.y - (flask.w * 828 / 626) / 2 + 30];

  // 001：料杆上 → 掰下来飞到插座口前
  const tp = TRY.at(S.try);
  // 停在插座口前犹豫：一进一退（问句说完到下一句之间画面不停）
  const hes = f > E.try.l ? 9 * Math.sin((2 * Math.PI * (f - E.try.l)) / 46) * Math.min(1, (f - E.try.l) / 20) : 0;
  const p0 = S.try > 0 ? {x: tp[0] + hes + 1400 * S.clear, y: tp[1] + S.tryJ + hes * 0.45, w: mix(PW, PW_NEAR, S.try)} : null;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, ["s1", "s3"])} shakeX={shake} shakeY={shake * 0.5}
             over={<><T6Sweep f={f} at={E.sweep.l + 8} /><T5In name="runner" f={f} /><T5Out name="runner" f={f} len={LEN} /></>}>
        <Layer id="sock">
          {S.sock > 0.01 && S.clear < 1 && (
            <>
              <Sprite name="socket/hero_34" x={sk.x} y={sk.y + id(1).y - 40 * (1 - Math.min(1, S.sock))} w={sk.w} op={Math.min(1, S.sock * 1.5)} rot={id(1).r} />
              {S.lamp > 0.01 && (() => {
                const [lx, ly] = at("socket/hero_34", "lamp_on", sk.x, sk.y + id(1).y, sk.w);
                return <div style={{position: "absolute", left: lx - 26, top: ly - 26, width: 52, height: 52, borderRadius: 26, background: C.yellow, opacity: 0.55 * S.lamp, filter: "blur(10px)"}} />;
              })()}
            </>
          )}
          {p0 && <Sprite name="plug/001_34" x={p0.x} y={p0.y} w={p0.w} rot={-6 * Math.sin(Math.PI * S.try)} lift={40 * Math.sin(Math.PI * S.try)} />}
        </Layer>

        <Layer id="rack">
          {S.sprue > 0.001 && S.clear < 1 && (
            <div style={{position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${rowDX}px)`}}>
              <Runner d={`M70,${SPRUE_Y} L1080,${SPRUE_Y}`} draw={S.sprue} width={18} />
              {PLUGS.map((n, i) => {
                const a = S[`p${i}`];
                if (a <= 0.01) return null;
                if (i === 0 && S.try > 0) return <Gate key={i} x1={ROW_X(i)} y1={SPRUE_Y} x2={ROW_X(i)} y2={SPRUE_Y - 50} w={14} broken={S.gate0} />;
                const y = ROW_Y - 60 * (1 - a) + (S[`pj${i}`] || 0) * -1 + id(10 + i).y;
                return (
                  <React.Fragment key={i}>
                    <Gate x1={ROW_X(i)} y1={SPRUE_Y} x2={ROW_X(i)} y2={SPRUE_Y - 50 * Math.min(1, a)} w={14} />
                    <Sprite name={`plug/${n}_34`} x={ROW_X(i)} y={y} w={PW} op={Math.min(1, a * 1.6)} rot={id(10 + i).r} />
                  </React.Fragment>
                );
              })}
            </div>
          )}
        </Layer>

        <Layer id="flask">
          {S.flask > 0.01 && (
            <Sprite name="flask/34" x={flask.x} y={flask.y + id(3).y - (S.muchJ || 0)} w={flask.w} op={Math.min(1, S.flask * 1.5)}
                    sx={0.8 + 0.2 * S.flask} sy={0.8 + 0.2 * S.flask} rot={id(3).r} />
          )}
        </Layer>

        {/* 第四幕：十个小插座，插头从烧瓶飞进去 */}
        <Layer id="grid">
          {GRID.map((g, i) => {
            const a = S[`m${i}`];
            if (a <= 0.01) return null;
            const k = FILL.indexOf(i);
            const done = k >= 0 && S[`fly${k}`] >= 1;
            const y = g.y - 40 * (1 - Math.min(1, a)) + (S[`mj${i}`] || 0) + (S[`tj${i}`] || 0) + id(20 + i).y;
            return <Sprite key={i} name={done ? "mini/m34_plugA" : "mini/m34_on"} x={g.x} y={y} w={MW} op={Math.min(1, a * 1.6)} rot={id(20 + i).r} />;
          })}
          {FILL.map((gi, k) => {
            const u = S[`fly${k}`];
            if (u <= 0 || u >= 1) return null;
            const g = GRID[gi];
            const app = at("mini/m34_on", "approach", g.x, g.y, MW);
            const tip = anchorOf("plug/A_34", "tip", FLY_W);
            const end = [app[0] - tip[0], app[1] - tip[1]];
            const P = pathOf([flaskMouth, [(flaskMouth[0] + end[0]) / 2, Math.min(flaskMouth[1], end[1]) - 160], end]);
            const p = P.at(u);
            return <Sprite key={k} name="plug/A_34" x={p[0]} y={p[1]} w={FLY_W} lift={30 * Math.sin(Math.PI * u)} />;
          })}
        </Layer>

        {/* Kd 刻度：一根骨白竖牌，蓝色的标在 lower 时往下走 */}
        <Layer id="kd">
          {S.kd > 0.01 && (
            <div style={{position: "absolute", left: 0, top: 0, opacity: S.kd, transform: `translateY(${(1 - S.kd) * 20}px)`}}>
              <Slab x={KD.x} y={KD.y} w={44} h={KD.h} r={14} color={C.bone} depth={8} id="kdbar" />
              <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
                {[0, 1, 2, 3, 4].map((k) => <line key={k} x1={KD.x + 50} y1={KD.y + 30 + k * (KD.h - 60) / 4} x2={KD.x + (k % 2 ? 66 : 76)} y2={KD.y + 30 + k * (KD.h - 60) / 4} stroke={C.ink} strokeWidth={3} strokeLinecap="round" />)}
              </svg>
              <div style={{position: "absolute", left: KD.x + 88, top: KD.y + 8}}><Engrave size={40}>high Kd</Engrave></div>
              <div style={{position: "absolute", left: KD.x + 88, top: KD.y + KD.h - 52}}><Engrave size={40}>low Kd</Engrave></div>
              <Slab x={KD.x - 8} y={KD.y + 40 + (KD.h - 110) * S.kdm} w={60} h={26} r={9} color={C.blue} depth={6} sheen={S.kdm > 0 && S.kdm < 1 ? S.kdm : -1} id="kdmark" />
            </div>
          )}
        </Layer>

        <Layer id="txt" exempt>
          <Label text="seven real molecules" size={56} x={576} y={430} at={E.rack.e - 30} out={E.try.s} align="center" />
          <Pen text="made in a real lab" x={1180} y={830} at={E.made.l} out={E.clear.s} size={58} />
          <Pen text="?" x={1560} y={150} at={E.q.l - 4} out={E.clear.s} size={220} color={C.red} rot={8} dur={24} />
          <Label text="Kd" size={110} x={KD.x - 40} y={KD.y + 20} at={E.kd.l} align="right" />
          <Pen text="half" x={1010} y={782} at={E.half.l} size={76} />
          <Pen text="lower = tighter" x={150} y={800} at={E.tight.l - 10} size={64} />
          <Source>Illustration · data: Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B501" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
