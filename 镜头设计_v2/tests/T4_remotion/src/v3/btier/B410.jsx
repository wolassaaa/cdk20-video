// HKBU SCIE1007 课程作业的科普视频：B 档 4-10（A 画外音）"It came back with 8,918 brand-new designs…"
// s1 8,918：数字轮转到 8,918；brand-new designs：小金插头一波一波铺满。s2 Way too many to make：手写。
// s3 each key：中间一个插头升起来，别的退下；a virtual lock：右边蓝线描出的线框插座。
// s4 That's docking：标 docking；the computer：一道扫描线扫过线框；a molecule：插头转向插孔；might sit in the pocket：插头尖进孔；scores the fit：表盘指针摆到高分。
// s5 Similar designs get grouped：插头回来，聚成六堆；54：数字轮滚到 54，每堆只留下几个；chemists：两个小人；pick just seven：七个插头飞进托盘；to make：烧瓶落下。
// 接点：开头 T5 芯片擦除（上一段 W3 是 A 段芯片），结尾 T5 料杆擦除（下一段 4-11+12 是出镜段）。L0 第 4 区大板。
import React from "react";
import {Composition, registerRoot, useCurrentFrame} from "remotion";
import K from "./keys_4-10.json";
import {Lens, Layer, guidePlan} from "../manual/kit.jsx";
import {C, camBreath, Stage, Sprite, Slab, Label, Pen, Source, Counter, Person1, anchorOf, evMapB, T5In, T5Out, impact} from "./bkit.jsx";
import {useGsapTimeline, idle, rand} from "./gsapFrame.jsx";

const E = evMapB(K);
const GP = guidePlan(K);
const LEN = K.len_f;
const ZONE = 4;

const NAMES = ["A", "B", "C", "D", "E", "F"];
const COLS = 12, ROWS = 5, NP = COLS * ROWS;
const PW = 82;
const PILE = [...Array(NP)].map((_, i) => [400 + (i % COLS) * 102 + ((Math.floor(i / COLS) % 2) * 40), 330 + Math.floor(i / COLS) * 88]);
const HERO = 29;                                  // 升起来的那一个
// 六堆的中心；每堆留下的个数（合起来 9 个代表 54 个里的一部分，七个进托盘）
const CL = [[480, 380], [800, 330], [1120, 380], [1440, 330], [640, 560], [1280, 560]];
const cluster = (i) => i % 6;
const KEEP = [0, 7, 14, 21, 28, 35, 42, 13, 44];   // 留下的 9 个（每堆至少一个）
const PICK = [0, 7, 14, 21, 28, 35, 42];           // 进托盘的 7 个
const TRAY = {x: 560, y: 700, w: 800, h: 112};
const SLOT = (k) => [TRAY.x + 70 + k * 110, TRAY.y + 46];
// 线框插座
const WF = {x: 1130, y: 300, w: 470, h: 360, d: 90};
const HOLE = [WF.x + WF.w / 2, WF.y + WF.h / 2 + 10];
const HERO_W = 240;
const [tipOX, tipOY] = anchorOf("plug/A_34", "tip", HERO_W);
const METER = {x: 420, y: 230, w: 76, h: 380};

const clamp01 = (v) => Math.max(0, Math.min(1, v));
const mix = (a, b, t) => a + (b - a) * t;
const sm = (t) => { const x = clamp01(t); return x * x * (3 - 2 * x); };

const Scene = () => {
  const f = useCurrentFrame();
  const S = useGsapTimeline((tl, S, X) => {
    S.n = 0;
    X.count("n", 0, 8918, E.n8918.l, 60, "power3.out");
    X.tw("pile", 0, 1, E.n8918.s, E.pile.l + 30, "power1.inOut");
    X.tw("rise", 0, 1, E.each.s, E.each.l + 20, "power2.out");
    X.tw("wf", 0, 1, E.vlock.s, E.vlock.l + 30, "power2.out");
    X.tw("scan", 0, 1, E.comp.s, E.comp.e + 10, "power1.inOut");
    X.tw("turn", 0, 1, E.mol.s, E.mol.e, "power2.inOut");
    X.tw("sit", 0, 1, E.sit.s, E.sit.l, "power2.in");
    X.jiggle("sitJ", E.sit.l, 5, 0);
    X.tw("dial", 0, 1, E.scorefit.s, E.scorefit.l, "power2.out");
    X.tw("needle", 0, 1, E.scorefit.l - 4, E.scorefit.e, "back.out(1.3)");
    X.tw("back", 0, 1, E.group.s - 30, E.group.s, "power2.inOut");
    X.tw("group", 0, 1, E.group.s, E.group.e + 20, "power2.inOut");
    tl.fromTo(S, {n: 8918}, {n: 54, duration: 40 / 60, ease: "power3.out", immediateRender: false}, (E.n54.l - 40) / 60);
    X.tw("cut", 0, 1, E.n54.s, E.n54.l + 20, "power2.in");
    X.tw("chem", 0, 1, E.chem.s, E.chem.l + 14, "power2.out");
    X.tw("seven", 0, 1, E.seven.s, E.seven.l, "power2.inOut");
    tl.fromTo(S, {n: 54}, {n: 7, duration: 24 / 60, ease: "power2.out", immediateRender: false}, (E.seven.l - 24) / 60);
    X.jiggle("trayJ", E.seven.l, 4, 0);
    X.land("flask", 0, 1, E.make.l, {antic: false});
  });

  const id = (s) => idle(f, s, {rot: 0.6, bob: 1.4});
  const shake = impact(f, E.sit.l);
  const rise = S.rise, back = S.back, grp = S.group, cut = S.cut, seven = S.seven;

  // 小插头：铺开（波）→ s3 退下 → s5 回来、聚堆 → 54 时多数淡出 → 七个进托盘
  const plugs = PILE.map((p0, i) => {
    const wave = sm((S.pile * 90 - (rand(i + 3) * 70 + (i % COLS) * 1.5)) / 10);
    let x = p0[0], y = p0[1] - 30 * (1 - wave), op = wave, rot = (rand(i) - 0.5) * 30;
    if (i !== HERO) { y += 260 * sm(rise * 1.2) * (1 - back); op *= 1 - sm(rise * 1.5) * (1 - back); }
    else if (rise > 0) op = 0;
    if (grp > 0) {
      const c = CL[cluster(i)], k = Math.floor(i / 6);
      const tx = c[0] + Math.cos(k * 2.4) * (22 + 9 * k), ty = c[1] + Math.sin(k * 2.4) * (16 + 6 * k);
      x = mix(x, tx, grp); y = mix(y, ty, grp); rot = mix(rot, (rand(i + 9) - 0.5) * 50, grp);
    }
    if (i === HERO && back > 0) op = sm(back * 2);
    const keep = KEEP.includes(i);
    if (!keep) op *= 1 - sm(cut * 1.4 - rand(i + 5) * 0.4);
    const pk = PICK.indexOf(i);
    if (pk >= 0 && seven > 0) {
      const u = sm(seven * 1.25 - pk * 0.04);
      const s = SLOT(pk);
      x = mix(x, s[0], u); y = mix(y, s[1], u) - 120 * Math.sin(Math.PI * u); rot = mix(rot, 0, u);
    }
    return {i, x, y, op, rot, n: NAMES[i % 6]};
  });

  // 升起来的那一个：s3 到左边，s4 转向、插进线框孔
  const heroTip0 = [600, 520];
  const tipAt = [mix(heroTip0[0], HOLE[0] - 30, S.sit), mix(heroTip0[1], HOLE[1], S.sit) + (S.sitJ || 0)];
  const heroRot = mix(-18, 0, S.turn);
  const heroOp = rise > 0 ? clamp01(rise * 4) * (1 - sm(back * 2)) : 0;
  const heroP = [mix(PILE[HERO][0], tipAt[0] + tipOX, sm(rise * 1.2)), mix(PILE[HERO][1], tipAt[1] - tipOY, sm(rise * 1.2))];
  const wfOut = 1 - sm(back * 1.5);

  const wfLines = (() => {
    const {x, y, w, h, d} = WF;
    return [
      `M${x},${y} L${x + w},${y} L${x + w},${y + h} L${x},${y + h} Z`,
      `M${x},${y} L${x + d},${y - d * 0.6} L${x + w + d},${y - d * 0.6} L${x + w},${y}`,
      `M${x + w},${y + h} L${x + w + d},${y + h - d * 0.6} L${x + w + d},${y - d * 0.6}`,
      `M${HOLE[0] - 92},${HOLE[1]} A92,92 0 1,0 ${HOLE[0] + 92},${HOLE[1]} A92,92 0 1,0 ${HOLE[0] - 92},${HOLE[1]}`,
      `M${HOLE[0] - 56},${HOLE[1]} A56,56 0 1,0 ${HOLE[0] + 56},${HOLE[1]} A56,56 0 1,0 ${HOLE[0] - 56},${HOLE[1]}`,
      `M${x + 30},${y + h - 40} L${x + w - 30},${y + h - 40}`,
    ];
  })();
  const scanY = WF.y - 60 + (WF.h + 80) * S.scan;

  return (
    <Lens plan={GP} f={f}>
      <Stage zone={ZONE} f={f} cam={camBreath(f, K, [])} shakeX={shake} over={<><T5In name="key" f={f} /><T5Out name="runner" f={f} len={LEN} /></>}>
        <Layer id="traybase">
          {seven > 0.001 && (
            <Slab x={TRAY.x} y={TRAY.y + 40 * (1 - sm(seven * 3)) + (S.trayJ || 0)} w={TRAY.w} h={TRAY.h} r={22} color={C.bone} depth={14} op={sm(seven * 3)} id="tray10" />
          )}
        </Layer>
        <Layer id="pile">
          {plugs.map((p) => p.op > 0.01 && (
            <Sprite key={p.i} name={`plug/${p.n}_34`} x={p.x} y={p.y + id(p.i).y} w={PW} sx={-1} rot={p.rot + id(p.i).r} op={p.op} shadowSq={0.3} />
          ))}
        </Layer>

        <Layer id="socket">
          {S.wf > 0.01 && wfOut > 0.01 && (
            <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: id(70).y, overflow: "visible", opacity: wfOut}}>
              {wfLines.map((d, k) => (
                <path key={k} d={d} fill="none" stroke={C.blueHi} strokeWidth={5} strokeLinejoin="round" strokeLinecap="round" pathLength={1} strokeDasharray="1 1"
                      strokeDashoffset={1 - clamp01(S.wf * 1.4 - k * 0.07)} />
              ))}
              {S.wf > 0.5 && <rect x={WF.x} y={WF.y} width={WF.w} height={WF.h} fill={C.blueHi} opacity={0.08 * (S.wf - 0.5) * 2} />}
              {S.scan > 0.01 && S.scan < 1 && (
                <g>
                  <rect x={WF.x - 20} y={scanY - 3} width={WF.w + WF.d + 40} height={6} fill={C.blueHi} opacity={0.85} />
                  <rect x={WF.x - 20} y={scanY - 40} width={WF.w + WF.d + 40} height={40} fill={C.blueHi} opacity={0.12} />
                </g>
              )}
            </svg>
          )}
        </Layer>
        <Layer id="hero">
          {heroOp > 0.01 && (
            <Sprite name="plug/A_34" x={heroP[0]} y={heroP[1] + id(71).y * (1 - S.sit)} w={HERO_W} sx={-1} rot={heroRot * sm(rise * 1.2)} op={heroOp} lift={18 * (1 - S.sit) * sm(rise)} />
          )}
          {/* 插进去以后线框的前沿压在插头上面一截：孔边的圆再描一遍 */}
          {S.sit > 0.5 && wfOut > 0.01 && (
            <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: id(70).y, overflow: "visible", opacity: wfOut * clamp01((S.sit - 0.5) * 4)}}>
              <path d={wfLines[3]} fill="none" stroke={C.blueHi} strokeWidth={5} />
            </svg>
          )}
        </Layer>
        <Layer id="dial">
          {S.dial > 0.01 && wfOut > 0.01 && (
            <div style={{position: "absolute", left: -400 * (1 - S.dial), top: id(72).y, opacity: Math.min(1, S.dial * 1.4) * wfOut}}>
              <Slab x={METER.x} y={METER.y} w={METER.w} h={METER.h} r={18} color={C.bone} depth={10} id="meter" />
              <Slab x={METER.x + 10} y={METER.y + METER.h - 10 - (METER.h - 20) * 0.86 * S.needle} w={METER.w - 20} h={Math.max(6, (METER.h - 20) * 0.86 * S.needle)} r={10} color={C.blue} depth={5}
                    shadow={false} sheen={S.needle > 0 && S.needle < 1 ? S.needle : -1} id="meterfill" />
              <svg width={1920} height={1080} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
                {[0, 1, 2, 3, 4].map((k) => <line key={k} x1={METER.x + METER.w + 8} y1={METER.y + 10 + k * (METER.h - 20) / 4} x2={METER.x + METER.w + (k % 2 ? 22 : 30)} y2={METER.y + 10 + k * (METER.h - 20) / 4} stroke={C.ink} strokeWidth={3} strokeLinecap="round" />)}
              </svg>
            </div>
          )}
        </Layer>

        <Layer id="tray">
          {S.chem > 0.01 && [0, 1].map((k) => (
            <Person1 key={k} red={k === 1} x={1500 + k * 200} y={700 + id(73 + k).y - 40 * (1 - S.chem)} w={470} op={Math.min(1, S.chem * 1.5)} rot={id(73 + k).r} />
          ))}
          {S.flask > 0.01 && <Sprite name="flask/34" x={1600} y={380 - 50 * (1 - Math.min(1, S.flask)) + id(75).y} w={250} op={Math.min(1, S.flask * 1.5)} rot={id(75).r} />}
        </Layer>

        <Layer id="txt" exempt>
          {S.n > 0.5 && (
            <div style={{position: "absolute", left: 960, top: 110, opacity: clamp01((f - E.n8918.s) / 10)}}>
              <Counter value={S.n} digits={4} comma size={120} x={0} y={0} align="center" />
            </div>
          )}
          <Label text="brand-new designs" size={52} x={960} y={250} at={E.pile.l + 10} out={E.each.s} align="center" />
          <Pen text="way too many" x={1380} y={760} at={E.many.s} out={E.each.s + 20} size={84} rot={-5} />
          <Label text="fit score" size={52} x={METER.x + 38} y={650} at={E.scorefit.l} out={E.group.s - 34} align="center" />
          <Label text="docking" size={60} x={WF.x + WF.w / 2} y={720} at={E.dock.l} out={E.group.s - 34} align="center" />
          <Label text="shortlist" size={52} x={960} y={250} at={E.n54.l + 20} out={E.seven.s} align="center" />
          <Label text="chemists" size={52} x={1600} y={820} at={E.chem.l + 4} align="center" />
          <Source>Illustration · data: Ren et al., Chem. Sci. 2023</Source>
        </Layer>
      </Stage>
    </Lens>
  );
};

const Root = () => <Composition id="B410" component={Scene} durationInFrames={LEN} fps={60} width={1920} height={1080} />;
registerRoot(Root);
