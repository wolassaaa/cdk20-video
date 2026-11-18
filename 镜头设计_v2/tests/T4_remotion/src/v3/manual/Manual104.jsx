// HKBU SCIE1007 课程作业的科普视频：第 1 章二维说明书页 1-04（D 画外音）。
// 三个步骤框：① 治疗换过一次（Nexavar → atezolizumab + bevacizumab） ② 五年后约三成在世 ③ 论文原话 a huge unmet need。
// 时间全部来自事件表 映射/events/1-04.json，经 resolve.py 算成 keys/1-04.json（复制到本目录 keys_1-04.json）。
//   node node_modules/@remotion/cli/remotion-cli.js render src/v3/manual/Manual104.jsx Manual104 <帧目录> --sequence --public-dir=<映射/_cache/ch1/public>
import React from "react";
import {AbsoluteFill, Audio, Composition, Easing, registerRoot, staticFile, useCurrentFrame} from "remotion";
import K from "./keys_1-04.json";
import {PAPER, INK, SOFT, RED, ease, out, span, Part, Tag, Arrow, Write, Step, Legend, Bead, evMap} from "./kit.jsx";

const E = evMap(K);
const AR = {liver: 1052 / 792, capsule: 530 / 229, ivbag: 474 / 773, person_w: 413 / 682, paper1: 441 / 582};
const BX = [96, 686, 1276], BY = 84, BW = 548, BH = 640;

const Title = ({p, children}) => (
  <div style={{position: "absolute", left: 112, top: 14, fontSize: 48, lineHeight: "64px"}}>
    <Write p={p}>{children}</Write>
  </div>
);
const Label = ({x, y, w = 240, p, children, size = 28, color = INK, italic}) => (
  <div style={{position: "absolute", left: x - w / 2, top: y, width: w, textAlign: "center", fontSize: size, color, fontStyle: italic ? "italic" : "normal"}}>
    <Write p={p}>{children}</Write>
  </div>
);

const PEOPLE = [...Array(10)].map((_, i) => [72 + (i % 5) * 101, 250 + Math.floor(i / 5) * 168]);

const Scene = () => {
  const f = useCurrentFrame();
  // ---- 第 1 步 ----
  const dim = span(f, E.nexavar_dim.s, E.nexavar_dim.e, ease);
  const snapP = span(f, E.combo_snap.s, E.combo_snap.l, Easing.in(Easing.quad));
  const snapK = f > E.combo_snap.l ? Math.exp(-(f - E.combo_snap.l) / 5) * Math.cos((f - E.combo_snap.l) / 2.6) : 0;
  const plusP = span(f, E.plus.s, E.plus.e, out);
  // ---- 第 2 步 ----
  const fade = span(f, E.rest_fade.s, E.rest_fade.e, ease);
  const lit = span(f, E.three.s, E.three.s + 14, out);
  const litBump = f > E.three.s + 14 ? 0.05 * Math.exp(-(f - E.three.s - 14) / 6) * Math.cos((f - E.three.s - 14) / 3) : 0;
  const plateP = span(f, E.plate_3in10.s, E.plate_3in10.s + 14, out);
  // ---- 第 3 步 ----
  const ul = span(f, E.underline.s, E.underline.s + 22, ease);

  // 料珠路线：每一站落在对应事件的落点帧
  const bead = [
    [0, 150, 60], [E.step1.l, 150, 128], [E.liver.l, BX[0] + 150, BY + 210], [E.note_changed.l, BX[0] + 380, BY + 196],
    [E.nexavar.l, BX[0] + 110, BY + 420], [E.bag1.l, BX[0] + 330, BY + 420], [E.bag2.l, BX[0] + 452, BY + 420],
    [E.step2.l, BX[1] + 46, BY + 46], [E.people.l, BX[1] + PEOPLE[0][0], BY + 200], [E.three.l, BX[1] + PEOPLE[2][0], BY + 200],
    [E.plate_3in10.e, BX[1] + 274, BY + 560], [E.step3.l, BX[2] + 46, BY + 46], [E.paper.l, BX[2] + 274, BY + 270],
    [E.quote.l, BX[2] + 120, BY + 488], [E.underline.e, BX[2] + 440, BY + 532], [K.len_f, BX[2] + 444, BY + 532],
  ];

  return (
    <AbsoluteFill style={{background: PAPER, fontFamily: "Serif", color: INK}}>
      <Audio src={staticFile("1-04.wav")} />
      <div style={{position: "absolute", inset: "34px 40px 44px 40px", border: `1.5px solid rgba(31,30,28,0.22)`, borderRadius: 4}} />

      {/* ============ 第 1 步：治疗换过一次 ============ */}
      <Step n="1" x={BX[0]} y={BY} w={BW} h={BH} at={E.step1.l} f={f}>
        <Title p={span(f, E.title1.s, E.title1.e)}>First treatment</Title>
        <Part name="liver" cx={150} cy={212} w={200} ar={AR.liver} at={E.liver.s + 2} f={f} gate={[1, 0.45]} />
        <Tag n="04" x={52} y={150} at={E.liver.l + 18} f={f} />
        <Label x={150} y={296} w={260} p={span(f, E.liver.l + 4, E.liver.e)} size={24} color={SOFT} italic>advanced liver cancer</Label>
        <div style={{position: "absolute", left: 300, top: 176, font: "38px Hand", color: RED, transform: "rotate(-5deg)"}}>
          <Write p={span(f, E.note_changed.s, E.note_changed.e)}>changed once</Write>
        </div>
        <svg width={BW} height={BH} style={{position: "absolute", left: 0, top: 0, overflow: "visible"}}>
          <Arrow d="M150,330 C150,368 150,372 150,380" tip={[150, 384]} ang={90} a={E.nexavar.s - 10} b={E.nexavar.s} f={f} sw={3} />
          <Arrow d="M178,430 L226,430" tip={[232, 430]} ang={0} a={E.arrow1.s} b={E.arrow1.e} f={f} />
        </svg>
        <div style={{position: "absolute", left: 0, top: 0, filter: `grayscale(${dim}) opacity(${1 - 0.55 * dim})`}}>
          <Part name="capsule" cx={110} cy={430} w={120} ar={AR.capsule} at={E.nexavar.s + 2} f={f} gate={[0, 0.5]} flood={18} />
          <Label x={110} y={470} w={200} p={span(f, E.nexavar.l, E.nexavar.e + 4)}>Nexavar</Label>
        </div>
        <Tag n="08" x={52} y={386} at={E.nexavar.e} f={f} />
        <Part name="ivbag" cx={326} cy={430} w={86} ar={AR.ivbag} at={E.bag1.s + 2} f={f} gate={[0.5, 0]} flood={18} />
        <div style={{position: "absolute", left: 376, top: 398, fontSize: 52, opacity: plusP * (1 - snapP), transform: `translateY(${-14 * (1 - plusP)}px)`}}>+</div>
        <div style={{position: "absolute", left: -46 * snapP + 4 * snapK, top: 0}}>
          <Part name="ivbag" cx={478} cy={430} w={86} ar={AR.ivbag} at={E.bag2.s + 2} f={f} gate={[0.5, 0]} flood={18} />
        </div>
        <Tag n="09" x={500} y={330} at={E.bag2.e} f={f} />
        <Label x={380} y={516} w={300} p={span(f, E.bag1.s, E.bag1.e)} size={26}>atezolizumab</Label>
        <Label x={380} y={550} w={300} p={span(f, E.bag2.s, E.bag2.e)} size={26}>+ bevacizumab</Label>
        <Label x={380} y={590} w={300} p={span(f, E.combo_snap.l, E.combo_snap.l + 16)} size={24} color={SOFT} italic>used together</Label>
      </Step>

      {/* 还没讲到的步骤先用虚线框占位，步骤框画出时虚线退掉 */}
      {[[BX[1], E.step2.l], [BX[2], E.step3.l]].map(([x, at]) => (
        <div key={x} style={{position: "absolute", left: x, top: BY, width: BW, height: BH, border: "2px dashed rgba(31,30,28,0.16)", borderRadius: 10, boxSizing: "border-box",
                             opacity: span(f, E.step1.l, E.step1.l + 24) * (1 - span(f, at, at + 30))}} />
      ))}
      {/* ============ 第 2 步：五年后约三成在世 ============ */}
      <Step n="2" x={BX[1]} y={BY} w={BW} h={BH} at={E.step2.l} f={f}>
        <Title p={span(f, E.title2.s, E.title2.e)}>Five years on</Title>
        {PEOPLE.map(([x, y], i) => {
          const at = E.people.s + 2 + i * ((E.people.e - E.people.s) / 12);
          const keep = i < 3;
          const st = keep ? {transform: `scale(${1 + litBump})`, transformOrigin: `${x}px ${y + 60}px`} : {filter: `grayscale(1) opacity(${1 - 0.68 * fade})`};
          return (
            <div key={i} style={{position: "absolute", left: 0, top: 0, ...st}}>
              <Part name="person_w" cx={x} cy={y} w={76} ar={AR.person_w} at={at} f={f} gate={[0.5, 0]} wipe={8} flood={14} />
            </div>
          );
        })}
        {/* 前三个亮起：底下一道红线托住 */}
        <svg width={BW} height={BH} style={{position: "absolute", left: 0, top: 0}}>
          <path d={`M${PEOPLE[0][0] - 40},322 L${PEOPLE[2][0] + 40},322`} stroke={RED} strokeWidth={4} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - lit} />
        </svg>
        <Tag n="03" x={510} y={170} at={E.people.l + 20} f={f} />
        <div style={{position: "absolute", left: 0, top: 512, width: BW, textAlign: "center", opacity: plateP, transform: `scale(${1.08 - 0.08 * plateP})`}}>
          <span style={{fontSize: 74}}>~3</span><span style={{fontSize: 44, fontStyle: "italic"}}> in </span><span style={{fontSize: 74}}>10</span>
        </div>
        <Label x={BW / 2} y={600} w={BW} p={span(f, E.rest_fade.l, E.rest_fade.e + 10)} size={24} color={SOFT} italic>alive five years on (relative survival, Hong Kong)</Label>
      </Step>

      {/* ============ 第 3 步：论文原话 ============ */}
      <Step n="3" x={BX[2]} y={BY} w={BW} h={BH} at={E.step3.l} f={f}>
        <Title p={span(f, E.title3.s, E.title3.e)}>In the study's words</Title>
        <Part name="paper1" cx={274} cy={290} w={220} ar={AR.paper1} at={E.paper.s + 2} f={f} gate={[0.5, 0]} />
        <Tag n="17" x={430} y={190} at={E.paper.l + 20} f={f} />
        <div style={{position: "absolute", left: 0, top: 452, width: BW, textAlign: "center", fontSize: 50, fontStyle: "italic"}}>
          <Write p={span(f, E.quote.s - 4, E.quote.e)}>“a huge unmet need”</Write>
        </div>
        <svg width={BW} height={BH} style={{position: "absolute", left: 0, top: 0}}>
          <path d="M96,534 C200,528 340,540 452,530" stroke={RED} strokeWidth={5} fill="none" strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - ul} />
        </svg>
      </Step>

      {/* 零件说明栏 */}
      <Legend x={BX[0]} y={760} w={BW} at={E.liver.l} f={f} rows={[
        [["04", "advanced liver cancer", E.liver.l + 18], ["08", "Nexavar", E.nexavar.e]],
        [["09", "atezolizumab + bevacizumab", E.bag2.e]],
      ]} />
      <Legend x={BX[1]} y={760} w={BW} at={E.people.l} f={f} rows={[[["03", "patients, Hong Kong", E.people.l + 20]]]} />
      <Legend x={BX[2]} y={760} w={BW} at={E.paper.l} f={f} rows={[[["17", "Ren et al., Chem. Sci. 2023", E.paper.l + 20]]]} />

      <div style={{position: "absolute", left: 44, top: 1046, fontSize: 17, color: SOFT, opacity: span(f, E.step1.l, E.step1.l + 20)}}>
        Ren et al., Chem. Sci. 2023; Hong Kong Cancer Registry, 2022 (5-year relative survival, 2010–2021) · Illustration
      </div>
      <Bead K={bead} f={f} />
    </AbsoluteFill>
  );
};

const Root = () => <Composition id="Manual104" component={Scene} durationInFrames={K.len_f} fps={60} width={1920} height={1080} />;
registerRoot(Root);
