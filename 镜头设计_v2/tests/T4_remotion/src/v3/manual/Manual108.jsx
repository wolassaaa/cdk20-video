// HKBU SCIE1007 课程作业的科普视频：第 1 章二维说明书页 1-08（C 画外音）。
// 三个步骤框：① 时间（从我们出生那年到现在） ② 花费（约 28 亿美元） ③ 进到人体试验的药，十个里约一个上市。
// 时间全部来自事件表 映射/events/1-08.json → resolve.py → keys_1-08.json。
//   node node_modules/@remotion/cli/remotion-cli.js render src/v3/manual/Manual108.jsx Manual108 <帧目录> --sequence --public-dir=<映射/_cache/ch1/public>
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_1-08.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Tag, Write, Step, Legend, evMap, Lens, guidePlan} from "./kit.jsx";

const E = evMap(K);
const GP = guidePlan(K);   // 视线引导（11-20，替代红色料珠）：事件表 guide 字段 → resolve.py → keys.guides
const AR = {cal: 520 / 511, ruler: 1130 / 150, banknote: 1040 / 520, capsule: 530 / 229};
const BX = [96, 686, 1276], BY = 84, BW = 548, BH = 640;
const CAPS = [...Array(10)].map((_, i) => [78 + (i % 5) * 98, 262 + Math.floor(i / 5) * 72]);
const KEEP = 2;                       // 留下的那一粒
const TRAY = [274, 470];

const Title = ({p, children}) => (
  <div style={{position: "absolute", left: 112, top: 14, fontSize: 48, lineHeight: "64px"}}><Write p={p}>{children}</Write></div>
);
const Label = ({x, y, w = 240, p, children, size = 26, color = INK, italic, align = "center"}) => (
  <div style={{position: "absolute", left: align === "left" ? x : x - w / 2, top: y, width: w, textAlign: align, fontSize: size, color, fontStyle: italic ? "italic" : "normal"}}>
    <Write p={p}>{children}</Write>
  </div>
);

const Scene = () => {
  const f = useCurrentFrame();
  // ---- 第 1 步：时间线先起一小截，再一路画到 now ----
  const reveal = 0.1 * span(f, E.tl_born.s, E.tl_born.e, out) + 0.9 * span(f, E.tl_run.s, E.tl_run.l, Easing.inOut(Easing.sin));
  // ---- 第 2 步 ----
  const plateC = span(f, E.plate_cost.s, E.plate_cost.s + 14, out);
  const squash = f > E.bill_settle.s ? 0.06 * Math.exp(-(f - E.bill_settle.s) / 7) * Math.sin((f - E.bill_settle.s) / 2.4) : 0;
  // ---- 第 3 步 ----
  const fade = span(f, E.caps_fade.s, E.caps_fade.e, ease);
  const plate1 = span(f, E.plate_1in10.s, E.plate_1in10.s + 14, out);
  const mv = span(f, E.market.s, E.market.l, Easing.inOut(Easing.cubic));
  const lift = Math.sin(Math.PI * mv) * -60;
  const kx = CAPS[KEEP][0] + (TRAY[0] - CAPS[KEEP][0]) * mv, ky = CAPS[KEEP][1] + (TRAY[1] - 6 - CAPS[KEEP][1]) * mv + lift;
  const trayP = span(f, E.market.s - 20, E.market.s + 10, out);
  const land = f > E.market.l ? Math.exp(-(f - E.market.l) / 5) * Math.cos((f - E.market.l) / 2.6) * 5 : 0;

  const tl0 = BX[0] + 44, tl1 = BX[0] + 504, tly = BY + 420;

  return (
    <Lens plan={GP} f={f}>
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("1-08.wav")} />
      <div style={{position: "absolute", inset: "34px 40px 44px 40px", border: `1.5px solid rgba(31,30,28,0.22)`, borderRadius: 4}} />
      {[[BX[1], E.step2.l], [BX[2], E.step3.l]].map(([x, at]) => (
        <div key={x} style={{position: "absolute", left: x, top: BY, width: BW, height: BH, border: "2px dashed rgba(31,30,28,0.16)", borderRadius: 10, boxSizing: "border-box",
                             opacity: span(f, E.step1.l, E.step1.l + 24) * (1 - span(f, at, at + 30))}} />
      ))}

      {/* ============ 第 1 步：时间 ============ */}
      <Step n="1" x={BX[0]} y={BY} w={BW} h={BH} at={E.step1.l} f={f}>
        <Title p={span(f, E.title1.s, E.title1.e)}>Time</Title>
        <Part name="cal" cx={274} cy={236} w={170} ar={AR.cal} at={E.calendar.s + 2} f={f} gate={[0.5, 1]} />
        <Tag n="10" x={400} y={170} at={E.calendar.l + 20} f={f} />
        <div style={{position: "absolute", left: 0, top: 0, width: BW, height: BH, clipPath: `inset(0 ${100 - (4 + 92 * reveal)}% 0 0)`}}>
          <Part name="ruler" cx={274} cy={420} w={460} ar={AR.ruler} at={E.tl_born.s} f={f} gate={[0, 0.5]} wipe={6} flood={10} />
        </div>
        <Label x={44} y={462} w={240} p={span(f, E.tl_born.s, E.tl_born.e + 10)} align="left" size={24} italic>the year we were born</Label>
        <Label x={504 - 120} y={462} w={120} p={span(f, E.tl_now.s, E.tl_now.s + 12)} align="left" size={30}>now</Label>
        <div style={{position: "absolute", left: 160, top: 520, font: "40px Hand", color: RED, transform: "rotate(-3deg)"}}>
          <Write p={span(f, E.tl_now.s + 6, E.tl_now.e)}>≈ our whole lives</Write>
        </div>
      </Step>

      {/* ============ 第 2 步：花费 ============ */}
      <Step n="2" x={BX[1]} y={BY} w={BW} h={BH} at={E.step2.l} f={f}>
        <Title p={span(f, E.title2.s, E.title2.e)}>Cost</Title>
        <div style={{position: "absolute", left: 0, top: 0, transform: `scaleY(${1 - squash})`, transformOrigin: "274px 380px"}}>
          {[0, 1, 2, 3].map((i) => (
            <Part key={i} name="banknote" cx={274 + (i % 2 ? 8 : -6)} cy={350 - i * 34} w={250} ar={AR.banknote}
                  at={E.bills.s + 2 + i * ((E.bills.e - E.bills.s) / 5)} f={f} gate={[0.5, 1]} wipe={8} flood={16} />
          ))}
        </div>
        <Tag n="11" x={450} y={190} at={E.bills.l + 20} f={f} />
        <div style={{position: "absolute", left: 0, top: 462, width: BW, textAlign: "center", opacity: plateC, transform: `scale(${1.08 - 0.08 * plateC})`}}>
          <span style={{fontSize: 44}}>~US$</span><span style={{fontSize: 84}}>2.8</span><span style={{fontSize: 44, fontStyle: "italic"}}> billion</span>
        </div>
        <Label x={BW / 2} y={570} w={BW} p={span(f, E.bill_settle.l, E.bill_settle.e)} size={24} color={SOFT} italic>to bring one new drug to market</Label>
      </Step>

      {/* ============ 第 3 步：十个里约一个上市 ============ */}
      <Step n="3" x={BX[2]} y={BY} w={BW} h={BH} at={E.step3.l} f={f}>
        <Title p={span(f, E.title3.s, E.title3.e)}>Tested in people</Title>
        {CAPS.map(([x, y], i) => i === KEEP ? null : (
          <div key={i} style={{position: "absolute", left: 0, top: 0, filter: `grayscale(${fade}) opacity(${1 - 0.7 * fade})`}}>
            <Part name="capsule" cx={x} cy={y} w={84} ar={AR.capsule} at={E.caps.s + 2 + i * ((E.caps.e - E.caps.s) / 12)} f={f} gate={[0, 0.5]} wipe={8} flood={12} />
          </div>
        ))}
        {/* 托架：market */}
        <svg width={BW} height={BH} style={{position: "absolute", left: 0, top: 0, opacity: trayP}}>
          <path d={`M${TRAY[0] - 90},${TRAY[1] - 22} L${TRAY[0] - 90},${TRAY[1] + 20} L${TRAY[0] + 90},${TRAY[1] + 20} L${TRAY[0] + 90},${TRAY[1] - 22}`} fill="none" stroke={INK} strokeWidth={3} strokeLinejoin="round" />
        </svg>
        <Label x={TRAY[0]} y={TRAY[1] + 28} w={240} p={span(f, E.market.s - 10, E.market.s + 14)} size={24} italic>the market</Label>
        <div style={{position: "absolute", left: kx - CAPS[KEEP][0], top: ky - CAPS[KEEP][1] + land}}>
          <Part name="capsule" cx={CAPS[KEEP][0]} cy={CAPS[KEEP][1]} w={84} ar={AR.capsule} at={E.caps.s + 2 + KEEP * ((E.caps.e - E.caps.s) / 12)} f={f} gate={[0, 0.5]} wipe={8} flood={12} />
        </div>
        <Tag n="08" x={500} y={200} at={E.caps.l + 20} f={f} />
        <div style={{position: "absolute", left: 0, top: 560, width: BW, textAlign: "center", opacity: plate1, transform: `scale(${1.08 - 0.08 * plate1})`}}>
          <span style={{fontSize: 64}}>~1</span><span style={{fontSize: 40, fontStyle: "italic"}}> in </span><span style={{fontSize: 64}}>10</span>
        </div>
      </Step>

      <Legend x={BX[0]} y={760} w={BW} at={E.calendar.l} f={f} rows={[[["10", "years of searching", E.calendar.l + 20]]]} />
      <Legend x={BX[1]} y={760} w={BW} at={E.bills.l} f={f} rows={[[["11", "cost of one new drug", E.bills.l + 20]]]} />
      <Legend x={BX[2]} y={760} w={BW} at={E.caps.l} f={f} rows={[[["08", "drugs tested in people", E.caps.l + 20]]]} />

      <div style={{position: "absolute", left: 44, top: 1046, fontSize: 17, color: SOFT, opacity: span(f, E.step1.l, E.step1.l + 20)}}>
        Wang et al., Pharmaceuticals 2023 · Illustration
      </div>
    </AbsoluteFill>
    </Lens>
  );
};

const Root = () => <Composition id="Manual108" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
